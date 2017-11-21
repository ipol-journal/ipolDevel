#!/usr/bin/python
# -*- coding: utf-8 -*-

# GNU General Public Licence (GPL)
#
# This program is free software; you can redistribute it and/or modify it under
# the terms of the GNU General Public License as published by the Free Software
# Foundation; either version 2 of the License, or (at your option) any later
# version.
# This program is distributed in the hope that it will be useful, but WITHOUT
# ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS
# FOR A PARTICULAR PURPOSE.  See the GNU General Public License for more
# details.
# You should have received a copy of the GNU General Public License along with
# this program; if not, write to the Free Software Foundation, Inc., 59 Temple
# Place, Suite 330, Boston, MA  02111-1307  USA
"""
The archive module serves thumbnails for blobs.
In 2017-10, it was detected that no thumbnails have been yet produced.
The archive client page has been rewrited and needs thumbnail of 128px height, and ratio preserved.
The script scan the archive.db for blobs,
create a thubnail for found blob,
or send a message for not found blob on stderr.
"""

from __future__ import absolute_import, division, print_function

import os
import sqlite3
import sys
import traceback
import warnings

sys.path.append(os.path.join(os.path.dirname(__file__), '../../ipol_demo/modules/conversion/lib/'))
from IPOLImage import IPOLImage


import av
import numpy as np
from PIL import Image


archive_dir = os.path.join(
    os.path.dirname(os.path.dirname(os.path.dirname(os.path.realpath(__file__)))),
    'ipol_demo/modules/archive/'
)
db_file = os.path.join(archive_dir, 'db/archive.db')
src_dir = os.path.join(archive_dir, 'staticData/blobs/')
dest_dir = os.path.join(archive_dir, 'staticData/blobs_thumbs_new/')

def hash_subdir(hash_name, depth=2):
    """
    Return a relative folder for blobs in the archive, from a hash_name
    ex:  abvddff => a/b
    """
    l = min(len(hash_name), depth)
    subdirs = '/'.join(list(hash_name[:l]))
    return subdirs

def image_thumb(src, dest):
    """
    From src image path, create a thumbnail to dest path
    """
    with Image.open(src) as im:
        # supposed to work with Pillow
        return pil_thumb(im, dest)

def video_thumb(src, dest):
    """
    From src video path, create a thumbnail to dest path
    """
    # av.open seems do not like unicode filepath
    container = av.open(src, mode='r')
    container.seek(int(container.duration/4) - 1)
    # hacky but I haven't found way to make work a better writing like next()
    for frame in container.decode(video=0):
        im = frame.to_image()
        break
    # can't close the video file descriptor
    with im:
        return pil_thumb(im, dest)

def pil_thumb(im, dest_jpeg, dest_height=128):
    """
    This function make a thumbnail from a pil image (can come from image or video)
    General case: dest_height, preserve ratio
    Special cases: src_height < dest_height, extreme ratios (horizontal or vertical lines)
    Exactly same logic should be shared with the sendarchive logic
    [2017-10-17] is in core/Tools/sendarchive.py
    Should be in conversion module
    """
    max_width = 2*dest_height # avoid extreme ratio

    src_width = im.width
    src_height = im.height
    # if src image is for example a line of 1 pixel height, keep original height
    dest_height = min(src_height, dest_height)
    dest_width = int(round(float(src_width*dest_height)/src_height))
    dest_width = min(dest_width, src_width, max_width)
    if dest_width <= 0:
        dest_width = src_width
    # get L or RGB for jpeg export
    im = pil_4jpeg(im)
    if not im: # conversion failed
        return None
    # resize after normalisation,
    im = im.resize((dest_width, dest_height), Image.LANCZOS)
    if not os.path.isdir(os.path.dirname(dest_jpeg)):
        os.makedirs(os.path.dirname(dest_jpeg))
    im.save(dest_jpeg, 'JPEG', progression=True, subsampling='4:4:4')
    return True # say that all is OK

def pil_4jpeg(im, bgcolor=(255, 255, 255)):
    """
    Return an image object compatible with jpeg (ex: resolve transparency, 32bits…)
    or nothing when it is known that the format is not compatible with jpeg and not converted.
    """
    if im.mode == 'RGB' or im.mode == 'L': # should work
        return im
    # Grey with transparency
    if im.mode == 'LA':
        l = im
        bg = int(np.round(0.21*bgcolor[0] + 0.72*bgcolor[1] + 0.07*bgcolor[2])) # grey luminosity
        im = Image.new('L', l.size, bg)
        im.paste(l, mask=l.split()[1]) # 1 is the alpha channel
        l.close()
        return im
    # im.info['transparency'], hack from image.py for palette with RGBA
    if im.mode == 'P' and 'transparency' in im.info and im.info['transparency'] is not None:
        im = im.convert('RGBA') # convert Palette with transparency to RGBA, handle just after
    # RGBA, full colors with canal alpha, resolve transparency with a white background
    if im.mode == 'RGBA':
        rgba = im
        im = Image.new('RGB', rgba.size, bgcolor)
        im.paste(rgba, mask=rgba.split()[3]) # 3 is the alpha channel
        rgba.close()
        return im
    # recognized as a 32-bit signed integer pixels, but not sure
    if im.mode == 'I':
        extrema = im.getextrema()
        # seems a 1 channel 32 bits
        if len(extrema) == 2 and (extrema[0] >= 0 and extrema[1] >= 256):
            return im.point(lambda i: i*(1./256)).convert('L')
        # not encountered for now
        return False
    if im.mode != 'RGB': # last try
        im = im.convert('RGB')
    return im



enc = sys.getfilesystemencoding()
if enc == 'ANSI_X3.4-1968': # IO encoding bug
    enc = 'UTF-8'
warnings.filterwarnings('error') # handle warning like error to log file path
conn = sqlite3.connect(db_file)
cur = conn.cursor()
# order is inverse chronological, new cases seems to be
for row in cur.execute("SELECT id, hash, type, format FROM blobs ORDER BY id DESC"):
    src_path = os.path.join(src_dir, hash_subdir(row[1]), row[1] + '.' + row[2]).encode(enc)
    # destination path without extension, jpeg is default, but png is possible for sound
    dest_path = os.path.join(dest_dir, hash_subdir(row[1]), row[1]).encode(enc)
    if not os.path.isfile(src_path):
        sys.stderr.write("\nBLOB NOT FOUND: {}\n".format(src_path))
        continue
    try:
        if row[3] == 'image':
            if row[2] in ['svg']:
                continue
            # tiff is usually used as a container for data
            im = IPOLImage(src_path, uint8=True)
            # a tiff used as a data container, not correctly loaded by OpenCV
            if row[2] == 'tiff' and im.data is None :
                continue
            im.resize(height=128)
            im.save(dest_path+'.jpeg')
            sys.stdout.write('.')
            sys.stdout.flush()
            continue
        if row[3] == 'video':
            video_thumb(src_path, dest_path+'.jpeg')
            sys.stdout.write('V')
            sys.stdout.flush()
            continue
    except Exception as ex:
        sys.stderr.write("\n{}\n{}\n".format(src_path, ex))
        print(traceback.format_exc())
sys.stdout.write('\nFinished\n')

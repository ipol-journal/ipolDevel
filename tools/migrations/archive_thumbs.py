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

import av
from PIL import Image
import json # used to print dict
import os
import sqlite3
import sys


"""
The archive module serves thumbnails for blobs.
In 2017-10, it was detected that no thumbnails have been yet produced.
The archive client page has been rewrited and needs thumbnail of 128px height, and ratio preserved.
The script scan the archive.db for blobs,
create a thubnail for found blob,
or send a message for not found blob on stderr.
"""

archive_dir = os.path.join(
    os.path.dirname(os.path.dirname(os.path.dirname(os.path.realpath(__file__)))),
    "ipol_demo/modules/archive/"
)
db_file = os.path.join(archive_dir, "db/archive.db")
src_dir = os.path.join(archive_dir, "staticData/blobs/")
dest_dir = os.path.join(archive_dir, "staticData/blobs_thumbs_new/")

def hash_subdir(hash_name, depth=2):
    """
    This function return a relative folder for blobs in the archive, from a hash_name
    input  abvddff
    output a/b
    """
    l = min(len(hash_name), depth)
    subdirs = '/'.join(list(hash_name[:l]))
    return subdirs

def image_thumb(src, dest):
    """ From src image path, create a thumbnail to dest path """
    im = Image.open(src)
    """
    Bug seen UserWarning: Palette images with Transparency   expressed in bytes should be converted to RGBA images
    /f/0/f09a51e7c535e946d7ba80256550022fcb91c25b.png
    """
    return pil_thumb(im, dest)

def video_thumb(src, dest):
    """ From src video path, create a thumbnail to dest path """
    # av.open seems to not like unicode filepath
    container = av.open(src.encode(sys.getfilesystemencoding()), mode='r')
    container.seek(int(container.duration/4) - 1)
    # hacky but I haven found way to make work a better writing like next()
    for frame in container.decode(video=0): break
    im = frame.to_image()
    # impossible to close the file descriptor ?
    # 'av.container.input.InputContainer' object has no attribute 'close' ?
    return pil_thumb(im, dest)

def pil_thumb(im, dest_jpeg, dest_height=128):
    """
    This function make a thumbnail from a pil image (can come from file or video)
    General case: dest_height, preserve ratio
    Special cases: src_height < dest_height, extreme ratios (horizontal or vertical lines)
    Exactly same logic should be shared with the sendarchive logic
    [2017-10-17] is in core/Tools/sendarchive.py
    Should be in conversion module
    Video will provide a PIL object
    3D, ??? png ?
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
    # resize before RGB problems
    im = im.resize((dest_width, dest_height), Image.LANCZOS)

    # im.info['transparency'], hack from image.py for palette with RGBA
    if im.mode == "P" and "transparency" in im.info and im.info['transparency'] is not None:
        im = im.convert('RGBA') # convert Palette with transparency to RGBA, handle just after
    # RGBA, full colors with canal alpha, resolve transparency with a white background
    if im.mode == "RGBA":
        rgba = im
        im = Image.new("RGB", rgba.size, (255, 255, 255))
        im.paste(rgba, mask=rgba.split()[3]) # 3 is the alpha channel
    if im.mode == "P":
        im = im.convert("RGB")

    if not os.path.isdir(os.path.dirname(dest_jpeg)):
        os.makedirs(os.path.dirname(dest_jpeg))
    im.save(dest_jpeg, 'JPEG', progression=True, subsampling='4:4:4')
    # return something ?

conn = sqlite3.connect(db_file)
cur = conn.cursor()
# order is inverse chronological
for row in cur.execute("SELECT hash, type, format FROM blobs ORDER BY id DESC"):
    hash = row[0]
    type = row[1]
    format = row[2]
    src_path = os.path.join(src_dir, hash_subdir(hash), hash + '.' + type)
    if not os.path.isfile(src_path):
        sys.stderr.write("\nBLOB NOT FOUND: {}\n".format(src_path))
        continue
    if format == 'image':
        # TODO svg ?
        # tiff is usually used as a container for data
        if type not in ['png', 'jpeg', 'jpg']: continue
        # for image, thumbnail is jpeg
        dest_path = os.path.join(dest_dir, hash_subdir(hash), hash + '.jpeg')
        image_thumb(src_path, dest_path)
        sys.stdout.write('.')
        sys.stdout.flush()
        continue
    if format == 'video':
        # for video, thumbnail is jpeg
        dest_path = os.path.join(dest_dir, hash_subdir(hash), hash + '.jpeg')
        video_thumb(src_path, dest_path)
        sys.stdout.write('V')
        sys.stdout.flush()
        continue
sys.stdout.write('\nFinished\n')

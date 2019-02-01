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
from ipolimage import Image


import av
import cv2
import numpy as np


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
            im = Image(src=src_path)
            # a tiff used as a data container, not correctly loaded by OpenCV
            if row[2] == 'tiff' and im.data is None :
                continue
            sys.stdout.write('.')
        if row[3] == 'video':
            im = Image.video_frame(src_file)
            sys.stdout.write('V')
        im.resize(height=128)
        im.write(dest_path+'.jpeg')
        sys.stdout.flush()
    except Exception as ex:
        sys.stderr.write("\n{}\n{}\n".format(src_path, ex))
        print(traceback.format_exc())
sys.stdout.write('\nFinished\n')

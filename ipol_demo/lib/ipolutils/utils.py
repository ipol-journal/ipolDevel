#!/usr/bin/env python3
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
Utils shared among IPOL modules.
"""
import mimetypes
import os
from shutil import rmtree

from .image.Image import Image


def thumbnail(src_file, height, dst_file):
    """
    Return a jpeg thumbnail for the src parameter (file path relative to shared_folder/run).
    If it is not possible to create a thumbnail it will return false.
    """
    if not os.path.isfile(src_file):
        return False
    mime_type, _ = mimetypes.guess_type(src_file)
    if not mime_type:
        return False
    media_type, _ = mime_type.split('/')
    if media_type not in ('image', 'video') or mime_type == 'image/svg+xml':
        return False
    if media_type == "image":
        im = Image(src=src_file)
    elif media_type == "video":
        im = Image.video_frame(src_file)
    if im.width() > 3 * im.height(): # avoid too wide thumbnail
        im.resize(width=(3*height))
    else:
        im.resize(height=height)
    im.write(dst_file)
    return True

def rmdir_contents(target):
    for entry in os.listdir(target):
        file_path = os.path.join(target, entry)
        if os.path.isfile(file_path):
            os.unlink(file_path)
        else:
            rmtree(file_path)

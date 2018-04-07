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
Utils shared among IPOL modules.
"""
import os
import mimetypes
import errno
import sys
sys.path.append("../ipolimage")
from ipolimage import Image


def get_thumbnail(src_file, width=None, height=None, preserve_ratio=False):
    """
    Return a jpeg thumbnail for the src parameter (file path relative to shared_folder/run).
    """
    # height=256 -- forced height with preserved ratio
    # width=256 -- forced width with preserved ratio
    # width=256&height=256 -- containing box with preserved ratio
    # width=256&height=256&preserve_ratio=False --forced width height (ratio is not preserved)
    if not os.path.isfile(src_file):
        raise OSError(errno.ENOENT, "get_thumbnail(), file not found", src_file)
    mime_type, _ = mimetypes.guess_type(src_file)
    media_type, _ = mime_type.split('/')
    if media_type not in ('image', 'video') or mime_type == 'image/svg+xml':
        raise OSError(errno.EINVAL, "get_thumbnail(), format {} not yet supported.".format(mime_type), src_file)
    if media_type == "image":
        im = Image.load(src_file)
    elif media_type == "video":
        im = Image.video_frame(src_file)
    im.resize(
        max_height=max(im.height(), 500),
        max_width=max(im.width(), 500),
        width=width,
        height=height,
        preserve_ratio=preserve_ratio
    )
    data = im.encode('.jpg')
    return data

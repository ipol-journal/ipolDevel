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

# Print the frames per second (FPS) of the input video

import argparse
import errno

import cv2

# Parse command line arguments
parser = argparse.ArgumentParser()
parser.add_argument("filename", type=str, help="Input filename")
args = parser.parse_args()

capture = cv2.VideoCapture(args.filename)
if not capture:
    raise OSError(errno.ENODATA, "Could not load.", args.filename)

fps = int(capture.get(cv2.CAP_PROP_FPS))
print(fps)

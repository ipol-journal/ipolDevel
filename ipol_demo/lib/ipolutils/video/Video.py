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
Video wrapper for conversion, resizing, reencode.
"""

import errno
import mimetypes
import os
import shutil
import datetime

import cv2
import numpy as np
import struct
import sys
from subprocess import call
from subprocess import Popen, PIPE

from errors import IPOLConvertInputError


class Video(object):
    """
    Generic video class.
    """

    def __init__(self, src):
        """
        Constructor.
        """
        self.src = src

    def load(self):
        """
        Returns a video object build from file.
        """
        if not os.path.isfile(self.src):
            raise OSError(errno.ENOENT, "File not found", self.src)
        self.capture = cv2.VideoCapture(self.src)
        if self.capture is None:
            raise OSError(errno.ENODATA, "Could not load.", self.src)
        self.capture.set(cv2.cv2.CAP_PROP_POS_FRAMES, 0)
        self.frame_count = int(self.capture.get(cv2.CAP_PROP_FRAME_COUNT))
        self.fps = self.capture.get(cv2.CAP_PROP_FPS)
        self.duration = float(self.frame_count / self.fps)
        self.fourcc = int(self.capture.get(cv2.CAP_PROP_FOURCC))
        self.full_path = os.path.realpath(self.src)
        self.input_dir, self.input_filename = os.path.split(self.full_path)
        self.input_name, self.input_ext = os.path.splitext(self.input_filename)

    def extract_frames(self, dst_folder=None):
        """
        Extract frames from video given a destination folder.
        """
        if dst_folder is None:
            dst_folder = self.input_dir + '/' + self.input_name

        if not os.path.exists(dst_folder):
            os.makedirs(dst_folder)
        
        for frame_number in range(self.frame_count):
            ret, frame = self.capture.read()
            if not ret:
                break
            imwrite = cv2.imwrite(dst_folder + '/frame_{:03d}.png'.format(frame_number), frame)
            if not imwrite:
                raise IPOLConvertInputError('Conversion error, frames could not be extracted')


    def create_avi(self, n_frames=None):
        """
        Create avi file from frames of uploaded input
        """
        processed_video = self.input_dir + '/' + self.input_name + ".avi"

        ffmpeg_command = "ffmpeg -i " + self.full_path + " -c:v huffyuv -pix_fmt rgb24 " #ffmpeg base command line
        if n_frames:
            ffmpeg_command += self.get_time_for_frames(n_frames)

        convert_proc = Popen([ffmpeg_command + " " + processed_video], shell=True)

        convert_proc.wait()
        if convert_proc.returncode != 0:
            raise IPOLConvertInputError('Conversion error, video could not be converted to avi')

    def get_time_for_frames(self, n_frames):
        if n_frames < self.frame_count:
            required_time = float(n_frames) / self.fps
            from_time = self.duration / 2.0 - required_time / 2.0 
            to_time = self.duration / 2.0 + required_time / 2.0

            frame_time = float(required_time/n_frames)
            frame_to = abs(to_time*n_frames/required_time)
            frame_from = abs(from_time*n_frames/required_time)
            if frame_to - frame_from + 1 > n_frames:
                to_time = to_time - frame_time
                
            return "-ss " + str(datetime.timedelta(seconds=from_time)) + " -to " + str(datetime.timedelta(seconds=to_time))  
        return ""

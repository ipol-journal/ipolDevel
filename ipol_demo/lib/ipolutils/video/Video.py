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
import os
import datetime
import math

from subprocess import Popen
import cv2
import numpy as np

from errors import IPOLConvertInputError
from ipolutils.evaluator.evaluator import evaluate


class Video(object):
    """
    Video conversion object
    """

    def __init__(self, src):
        """
        Constructor.
        """
        if not os.path.isfile(src):
            raise OSError(errno.ENOENT, "File not found", src)
        self.capture = cv2.VideoCapture(src)
        if self.capture is None:
            raise OSError(errno.ENODATA, "Could not load.", src)
        self.capture.set(cv2.CAP_PROP_POS_FRAMES, 0)

        self.frame_count = self.capture.get(cv2.CAP_PROP_FRAME_COUNT)
        self.fps = self.capture.get(cv2.CAP_PROP_FPS)

        self.width = self.capture.get(cv2.CAP_PROP_FRAME_WIDTH)
        self.height = self.capture.get(cv2.CAP_PROP_FRAME_HEIGHT)

        self.full_path = os.path.realpath(src)

    def extract_frames(self, max_frames, max_pixels):
        """
        Extract the required number of frames and save them as image files.
        """
        self.validate_max_frames(max_frames)

        dst_folder = os.path.join(self.get_input_dir(), self.get_input_name())
        max_pixels = evaluate(max_pixels)
        video_pixel_count = self.height * self.width

        if not os.path.exists(dst_folder):
            os.makedirs(dst_folder)

        frames_count = self.get_number_of_frames_to_extract(max_frames)
        width, height = self.get_size(max_pixels)
        for frame_number in range(frames_count):
            ret, frame = self.capture.read()
            if not ret:
                break
            if max_pixels < video_pixel_count:
                frame = cv2.resize(frame, (int(width), int(height)), interpolation=cv2.INTER_AREA)
            im = cv2.imwrite(os.path.join(dst_folder, 'frame_{:05d}.png'.format(frame_number)), frame)
            if not im:
                raise IPOLConvertInputError('Conversion error, frame could not be written to the file')

    def create_avi(self, max_frames, max_pixels):
        """
        Create AVI video file
        """
        self.validate_max_frames(max_frames)

        ffmpeg_command = "avconv -y -i {} -c:v huffyuv -pix_fmt rgb24 ".format(self.full_path)
        max_pixels = evaluate(max_pixels)
        ffmpeg_command += self.get_ffmpeg_options(max_pixels, max_frames)

        processed_video = os.path.join(self.get_input_dir(), self.get_input_name() + ".avi")
        convert_proc = Popen([ffmpeg_command + " " + processed_video], shell=True)
        convert_proc.wait()

        if convert_proc.returncode != 0:
            raise IPOLConvertInputError('Conversion error: video could not be converted to AVI')

    def get_time_for_frames(self, max_frames):
        """
        Get the time interval according to the maximum number of frames allowed.
        """
        video_duration = self.frame_count / self.fps
        required_time = max_frames / self.fps
        from_time = video_duration / 2.0 - required_time / 2.0
        to_time = video_duration / 2.0 + required_time / 2.0

        frame_time = required_time / max_frames
        from_frame = from_time * max_frames / required_time
        to_frame = to_time * max_frames / required_time

        if to_frame - from_frame + 1 > max_frames:
            to_time = to_time - frame_time

        return from_time, to_time

    def get_ffmpeg_options(self, max_pixels, max_frames):
        """
        Get ffmpeg options if needed.
        """
        options = ""
        if max_frames < self.frame_count:
            from_time, to_time = self.get_time_for_frames(max_frames)
            options += "-ss {} -to {}".format(\
              str(datetime.timedelta(seconds=from_time)), \
              str(datetime.timedelta(seconds=to_time)))

        width, height = self.get_size(max_pixels)
        if self.width != width or self.height != height:
            options += " -vf scale={}:{}".format(width, height)

        return options

    def get_size(self, max_pixels):
        """
        Get frame size after being eventually rescaled to max_pixels. It keeps the aspect ratio.
        """
        if max_pixels < self.height * self.width:
            scaling_factor = self.get_scaling_factor(max_pixels)
            return np.floor(scaling_factor * self.width), np.floor(scaling_factor * self.height)
        return self.width, self.height

    def get_scaling_factor(self, max_pixels):
        """
        Compute the scaling factor to reduce the image keeping its aspect ratio.
        """
        return math.sqrt(max_pixels / (self.height * self.width))

    def get_number_of_frames_to_extract(self, max_frames):
        """
        Get number of frames of the final input.
        """
        if max_frames < self.frame_count:
            self.set_capture_pos(max_frames)
            return max_frames
        return self.frame_count

    def set_capture_pos(self, max_frames):
        """
        Set capture pos based on frame count and max_frames.
        """
        first_frame = int(self.frame_count / 2) - int(max_frames / 2)
        self.capture.set(cv2.CAP_PROP_POS_FRAMES, first_frame)

    def get_input_dir(self):
        """
        Get input directory from full path.
        """
        return os.path.split(self.full_path)[0]

    def get_input_name(self):
        """
        Get input name from full path.
        """
        return os.path.splitext(os.path.split(self.full_path)[1])[0]

    @staticmethod
    def validate_max_frames(max_frames):
        """
        Check max_frames range and type
        """
        if not isinstance(max_frames, int):
            raise IPOLConvertInputError('Type error: max_frames must be an integer')
        if max_frames < 1:
            raise IPOLConvertInputError('Range error: max_frames must be positive')

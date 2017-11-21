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
Image, multipe formats handling
"""

from __future__ import print_function
import os
import sys
import time

import cv2
import numpy as np
import errno


class IPOLImage(object):
    '''
    Generic image class, dealing with the best python libraries for performances, and formats.
    Actually : OpenCV.
    Operations are done on a numpy matrix.
    Load : jpeg (uint8), png (uint8, uint16; alpha; colormap), tiff (uint8, uint16)
    Writes : jpeg (uint8), png (uint8, uint16; alpha), tiff (uint8, uint16)
    '''
    # don’t forget :
    # ICC profile
    # EXIF ?
    # to test float32)
    def __init__(self, src_file, uint8=False, gray=False):
        '''
        Load image data by path.
        '''
        if not os.path.isfile(src_file):
            raise OSError(errno.ENOENT, "File not found", src_file)
        self.src_file = src_file
        pars = 0
        if gray:
            pars |= cv2.IMREAD_GRAYSCALE
        if not uint8:
            pars |= cv2.IMREAD_UNCHANGED
        self.data = cv2.imread(self.src_file, pars)

    def paths(self):
        '''
        Build and store different paths, used for saving dest file.
        '''
        self.src_path = os.path.realpath(self.src_file)
        self.src_dir, self.src_basename = os.path.split(self.src_path)
        self.src_name, self.src_ext = os.path.splitext(self.src_basename)

    def blend_alpha(self, back_color=(255, 255, 255)):
        '''
        if data loaded has an alpha layer, blend it with a bgcolor
        '''
        data = self.data
        # 1 channel, Gray, do nothing
        if len(data.shape) == 2 or data.shape[2] == 1:
            return
        # 2 channels, Gray with alpha
        elif data.shape[2] == 2:
            # convert back_color to a grey luminosity
            back_gray = 0.21 * back_color[0] + 0.72 * back_color[1] + 0.07 * back_color[2]
            alpha_mask = data[:, :, 3].astype(float)
            if data.dtype == 'uint8':
                alpha_mask = alpha_mask / 255
            elif data.dtype == 'uint16':
                alpha_mask = alpha_mask / 65535
                back_gray = back_gray * 257.0
            elif data.dtype == 'uint32':
                alpha_mask = alpha_mask / ((1 << 32) - 1)
                back_gray = back_gray * 16843009.0
            else: # float
                back_gray = back_gray / 255.0
            # build a background matrix as float
            back_mat = np.zeros((data.shape[0], data.shape[1], 1), float)
            # fill it with background color
            back_mat[:] = back_gray
            # apply inverse mask to background
            back_mat = cv2.multiply(1.0 - alpha_mask, back_mat)
            # apply mask to foregroung
            fore_mat = cv2.multiply(alpha_mask, data[:, :, 0].astype(float))
            # merge back and fore
            self.data = cv2.add(back_mat, fore_mat)
            return
        # 3 channels, BGR, do nothing
        elif data.shape[2] == 3:
            return
        # 4 channels, BGRA, blend
        elif data.shape[2] == 4:
            # convert back_color to BGR (OpenCV format)
            back_color = tuple(reversed(back_color))
            # build an alpha_mask, convert to float [0, 1], according to dtype
            alpha_mask = cv2.cvtColor(data[:, :, 3], cv2.COLOR_GRAY2BGR).astype(float)
            if data.dtype == 'uint8':
                alpha_mask = alpha_mask / 255
            elif data.dtype == 'uint16':
                alpha_mask = alpha_mask / 65535
                back_color = (back_color[0] * 257.0, back_color[1] * 257.0, back_color[2] * 257.0)
            elif data.dtype == 'uint32':
                alpha_mask = alpha_mask / ((1 << 32) - 1)
                back_color = (back_color[0] * 16843009.0, back_color[1] * 16843009.0, back_color[2] * 16843009.0)
            else: # float
                back_color = (back_color[0] / 255.0, back_color[1] / 255.0, back_color[2] / 255.0)

            # build a background matrix as float
            back_mat = np.zeros((data.shape[0], data.shape[1], 3), float)
            # fill it with background color
            back_mat[:] = back_color
            # apply inverse mask to background
            back_mat = cv2.multiply(1.0 - alpha_mask, back_mat)
            # apply mask to foregroung
            fore_mat = cv2.multiply(alpha_mask, data[:, :, :3].astype(float))
            # merge back and fore
            self.data = cv2.add(back_mat, fore_mat)

    def save(self, dest_file, **kwargs):
        '''
        Choose the save method according to extension
        '''
        ext = os.path.splitext(dest_file)[1]
        if ext == '.png':
            return self._save_png(dest_file, **kwargs)
        elif ext == '.tiff' or ext == '.tif':
            return self._save_tiff(dest_file, **kwargs)
        elif ext == '.jpg' or ext == '.jpeg':
            return self._save_jpeg(dest_file, **kwargs)
        else:
            raise ValueError("Extension {}, is not supported.".format(ext))

    def _save_jpeg(self, dest_file, optimize=True, progressive=True, quality=80):
        '''
        Save data as jpeg
        '''
        self.blend_alpha()
        # not found in OpenCV API subsampling, ex: '4:4:4'
        pars = []
        if optimize:
            pars.extend([cv2.IMWRITE_JPEG_OPTIMIZE, 1])
        if progressive:
            pars.extend([cv2.IMWRITE_JPEG_PROGRESSIVE, 1])
        if quality >= 0 and quality <= 100:
            pars.extend([cv2.IMWRITE_JPEG_QUALITY, quality])
        return cv2.imwrite(dest_file, self.data, pars)

    def _save_png(self, dest_file, compression=9):
        '''
        Save data as png
        '''
        # no optimise flag found in OpenCV API
        pars = []
        if compression >= 0 and compression <= 9:
            pars.extend([cv2.IMWRITE_PNG_COMPRESSION, compression])
        return cv2.imwrite(dest_file, self.data, pars)


    def _save_tiff(self, dest_file):
        '''
        Save data as tiff
        '''
        return cv2.imwrite(dest_file, self.data)

    def resize(self, preserve_ratio=True, width=None, height=None, zoom=None, interpolation=None):
        '''
        Smart resize, according to different parameters
        '''
        src_height, src_width = self.data.shape[:2]
        dest_width, dest_height = width, height
        if interpolation: # keep requested interpolation
            pass
        elif (dest_width > src_width) or (dest_height > src_height) or zoom > 1: # augmentation, pixelise
            interpolation = cv2.INTER_NEAREST
        else: # diminution, for thumbnail, some interpolation
            interpolation = cv2.INTER_AREA

        if zoom:
            self.data = cv2.resize(self.data, None, fx=zoom, fy=zoom, interpolation=interpolation)
            return
        # problem
        if not width > 0 and not height > 0:
            raise ValueError("Bad arguments, at least zoom or (width and/or height)")
        # containing box
        if dest_width > 0 and dest_height > 0:
            if preserve_ratio:
                ratio_width = float(dest_width) / src_width
                ratio_height = float(dest_height) / src_height
                if ratio_width < ratio_height:
                    dest_height *= ratio_width
                else:
                    dest_width *= ratio_height
        # forced height
        elif dest_height > 0:
            max_width = 2*dest_height # avoid extreme ratio
            # if src image is for example a line of 1 pixel height, keep original height
            if src_height < 10:
                dest_height = src_height
            dest_width = int(round(float(src_width * dest_height) / src_height))
            dest_width = min(dest_width, src_width, max_width)
            if dest_width <= 0:
                dest_width = src_width
        # forced width
        elif dest_width > 0:
            max_height = 2*dest_width # avoid extreme ratio
            # if src image is for example a line of 1 pixel width, keep original width
            if src_width < 10:
                dest_width = src_width
            dest_height = int(round(float(src_height * dest_width) / src_width))
            dest_height = min(dest_height, src_height, max_height)
            if dest_height <= 0:
                dest_height = src_height
        # dtype of matrix is still kept
        self.data = cv2.resize(self.data, (dest_width, dest_height), interpolation=interpolation)

    def crop(self, box):
        '''
        Crop data according to a 4-tuple rectangle (left, upper, right, lower)
        '''
        # TODO = self.data[280:340, 330:390]
        pass

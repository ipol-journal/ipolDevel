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
Image wrapper for conversion, resizing, reencode.
"""

from __future__ import print_function
import errno
import mimetypes
import os

import cv2
import numpy as np

class Image(object):
    '''
    Generic image class, dealing with the best python libraries for performances, and formats (currently : OpenCV).
    '''

    @staticmethod
    def load(src, flags=cv2.IMREAD_UNCHANGED):
        '''
        Factory, returns an image object build from file.
        '''
        if not os.path.isfile(src):
            raise OSError(errno.ENOENT, "File not found", src)
        im = Image()
        im.data = cv2.imread(src, flags)
        if im.data is None:
            raise OSError(errno.ENODATA, "No data read. For supported image formats, see doc OpenCV imread", src)
        im.src_file = src
        im.src_path = os.path.realpath(src)
        im.src_dir, im.src_basename = os.path.split(im.src_path)
        im.src_name, im.src_ext = os.path.splitext(im.src_basename)
        return im

    @staticmethod
    def decode(buf, flags=cv2.IMREAD_UNCHANGED):
        '''
        Factory, returns an image object build from a string of bytes.
        '''
        # OpenCV loads bytes as one dimension numpy vector of uint8 numbers.
        buf = np.fromstring(buf, dtype=np.uint8)
        im = Image()
        im.data = cv2.imdecode(buf, flags)
        if im.data is None:
            raise RuntimeError(errno.ENODATA, "No data read. For supported image formats, see doc OpenCV imread")
        return im

    @staticmethod
    def data(data):
        '''
        Factory, return am image object build with the data matrix.
        '''
        im = Image()
        im.data = data
        return im

    @staticmethod
    def video_frame(video_file, pos_ratio=0.5, pos_max=7500):
        '''
        From a video, returns a significative frame as an image object
        '''
        cap = cv2.VideoCapture(video_file)
        pos_frame = int(cap.get(cv2.CAP_PROP_FRAME_COUNT) * pos_ratio)
        pos_frame = min(pos_frame, pos_max)
        for _ in range(1, pos_frame):
            cap.read()
        _, frame = cap.read()
        # When everything done, release the capture
        cap.release()
        im = Image()
        im.data = frame
        return im

    def width(self):
        '''
        Returns width of image.
        '''
        return self.data.shape[1]

    def height(self):
        '''
        Returns height of image.
        '''
        return self.data.shape[0]

    def dtype(self):
        '''
        Returns data type of image matrix.
        '''
        return self.data.dtype

    def write(self, dst_file, **kwargs):
        '''
        Save image matrix to destination file, encoded according to file extension.
        '''
        # warning, cv2.imwrite will not create subdirectories and silently fail
        dst_dir = os.path.dirname(dst_file)
        if dst_dir and not os.path.exists(dst_dir):
            os.makedirs(dst_dir)
        data, pars = self._4ser(dst_file, **kwargs)
        cv2.imwrite(dst_file, data, pars)

    def encode(self, ext, **kwargs):
        '''
        Return image matrix as encoded bytes, format according to a file extension.
        '''
        data, pars = self._4ser('dummy.' + ext.lstrip('.'), **kwargs)
        ext = '.' + ext.lstrip('.')
        _, buf = cv2.imencode(ext, data, pars)
        return buf.tostring()

    def _4ser(self, path, **kwargs):
        '''
        Return data and parameters prepared for serialization (memory or file).
        '''
        # See _4{ext} for available options for each image encoding formats.
        mime_type, _ = mimetypes.guess_type(path)
        if mime_type == 'image/jpeg':
            return self._4jpeg(**kwargs)
        elif mime_type == 'image/png':
            return self._4png(**kwargs)
        elif mime_type == 'image/tiff':
            return self._4tiff(**kwargs)
        return self.data, []


    def _4jpeg(self, optimize=True, progressive=True, quality=80):
        '''
        Prepare data for JPEG, before saving to file or return bytes (blend alpha, 8 bits).
        '''
        data = self._blend_alpha(self.data)
        data, _ = self._convert_depth(data, '8i')
        # not found in OpenCV API subsampling, ex: '4:4:4'
        pars = []
        if optimize:
            pars.extend([cv2.IMWRITE_JPEG_OPTIMIZE, 1])
        if progressive:
            pars.extend([cv2.IMWRITE_JPEG_PROGRESSIVE, 1])
        if quality >= 0 and quality <= 100:
            pars.extend([cv2.IMWRITE_JPEG_QUALITY, quality])
        return data, pars

    def _4png(self, compression=9):
        '''
        Prepare data for PNG, before saving to file or return bytes.
        '''
        # no optimise flag found in OpenCV API
        pars = []
        data = self.data
        if data.dtype != np.uint8 and data.dtype != np.uint16:
            data, _ = self._convert_depth(data, '16i')
        if compression >= 0 and compression <= 9:
            pars.extend([cv2.IMWRITE_PNG_COMPRESSION, compression])
        return data, pars


    def _4tiff(self):
        '''
        Prepare data for TIFF, before saving to file or return bytes (blend alpha).
        '''
        data = self._blend_alpha(self.data) # assume that tiff do not support alpha
        pars = []
        return data, pars

    @staticmethod
    def valid_numeric(name, value, amax=None, amin=None):
        """
        Validate values
        """
        if value is None:
            return value
        if value > amax:
            raise ValueError("{}={} > max={}".format(name, value, amax))
        if value < amin:
            raise ValueError("{}={} < min={}".format(name, value, amin))
        return value

    def resize(self, width=None, height=None, fx=None, fy=None,
               preserve_ratio=True, interpolation=None, max_width=5000, max_height=5000):
        '''
        Resize image data.
        '''
        src_height, src_width = self.data.shape[:2]
        width = self.valid_numeric('width', width, amax=max_width, amin=1)
        height = self.valid_numeric('height', height, amax=max_height, amin=1)
        fx = self.valid_numeric('fx', fx, amax=float(max_width)/src_width, amin=1.0/src_width)
        fy = self.valid_numeric('fy', fy, amax=float(max_height)/src_height, amin=1.0/src_height)
        if fx or fy:
            if not fx:
                fx = fy
            if not fy:
                fy = fx
            if interpolation: # keep requested interpolation
                pass
            elif fx > 0 and fy > 0: # augmentation, pixelise
                interpolation = cv2.INTER_NEAREST
            else: # diminution, for thumbnail, some interpolation
                interpolation = cv2.INTER_AREA
            self.data = cv2.resize(self.data, None, fx=float(fx), fy=float(fy), interpolation=interpolation)
            return self

        dst_width = width
        dst_height = height

        # containing box
        if dst_width > 0 and dst_height > 0:
            if preserve_ratio:
                ratio_width = float(dst_width) / src_width
                ratio_height = float(dst_height) / src_height
                if ratio_width < ratio_height:
                    dst_height = float(src_height) * ratio_width
                else:
                    dst_width = float(src_width) * ratio_height
        # forced height
        elif dst_height > 0:
            max_width = 3*dst_height # avoid extreme ratio
            # if src image is for example a line of 1 pixel height, keep original height
            if src_height < 10:
                dst_height = src_height
            dst_width = int(round(float(src_width * dst_height) / src_height))
            dst_width = min(dst_width, max_width)
            if dst_width <= 0:
                dst_width = src_width
        # forced width
        elif dst_width > 0:
            max_height = 2*dst_width # avoid extreme ratio
            # if src image is for example a line of 1 pixel width, keep original width
            if src_width < 10:
                dst_width = src_width
            dst_height = int(round(float(src_height * dst_width) / src_width))
            dst_height = min(dst_height, max_height)
            if dst_height <= 0:
                dst_height = src_height
        else:
            raise ValueError("Image.resize(), not enough parameters to resize image.")
        # dtype of matrix is still kept
        if interpolation: # keep requested interpolation
            pass
        elif (dst_width > src_width) or (dst_height > src_height): # augmentation, pixelise
            interpolation = cv2.INTER_NEAREST
        else: # diminution, for thumbnail, some interpolation
            interpolation = cv2.INTER_AREA
        self.data = cv2.resize(self.data, (int(dst_width), int(dst_height)), interpolation=interpolation)
        return self

    def crop(self, x=0, y=0, width=0, height=0):
        '''
        Crop data according to a 4-tuple rectangle (left, upper, right, lower)
        '''
        if width <= 0 or height <= 0 or x < 0 or y < 0:
            raise ValueError("Crop, bad arguments x={}, y={}, x+width={}, y+height={} outside image ({}, {})".format(x, y, x+width, y+height, self.width, self.height))
        if x + width > self.width or y + height > self.height:
            raise ValueError("Crop, bad arguments x={}, y={}, x+width={}, y+height={} outside image ({}, {})".format(x, y, x+width, y+height, self.width, self.height))
        self.data = self.data[y:y+height, x:x+width]

    def convert(self, mode):
        '''
        Converts data of the image according to a mode (number of channels and depth).
        '''
        # ret = True, if data have been modified. This flag allow to rewite an image with no modification.
        # mode: 1x8i, 3x8i, 1x16i, 3x16i, 1x32i, 3x32i
        channels, depth = mode.split('x')
        data = self.data
        data, ret1 = self._convert_channels(data, int(channels))
        data, ret2 = self._convert_depth(data, depth)
        self.data = data
        return ret1 | ret2

    def convert_channels(self, channels):
        '''
        Converts image data to grey=1 or color=3.
        '''
        self.data, ret = self._convert_channels(self.data, int(channels))
        return ret

    def convert_depth(self, depth):
        '''
        Converts image data color depth.
        '''
        self.data, ret = self._convert_depth(self.data, depth)
        return ret

    @staticmethod
    def _convert_channels(data, dst_channels):
        '''
        Converts the number of channels of an image matrix.
        '''
        if not dst_channels:
            return data, False
        dst_channels = int(dst_channels)
        # always blend alpha
        data = Image._blend_alpha(data)
        if len(data.shape) == 2:
            data.shape = [data.shape[0], data.shape[1], 1]
        src_channels = data.shape[2]
        if src_channels == dst_channels:
            return data, False
        if src_channels == 3 and dst_channels == 1:
            data = cv2.cvtColor(data, cv2.COLOR_BGR2GRAY)
        elif src_channels == 1 and dst_channels == 3:
            data = cv2.cvtColor(data, cv2.COLOR_GRAY2BGR)
        else: # unknown number of channels
            raise ValueError("Convert channels '{}', number of channels not yet supported.".format(dst_channels))
        return data, True

    @staticmethod
    def _convert_depth(data, dst_depth):
        '''
        Converts the depth of an image matrix.
        '''
        if not dst_depth:
            return data, False
        supported_dtypes = ['uint8', 'uint16', 'uint32', 'float16', 'float32']
        depth_dtypes = {'8i': 'uint8', '8': 'uint8', '16i': 'uint16', '16': 'uint16', '32i': 'uint32',
                        '32': 'uint32', '16f': 'float16', '32f': 'float32'}
        src_dtype = data.dtype
        # normalisation of requested depth as a dtype
        if dst_depth in depth_dtypes:
            dst_dtype = depth_dtypes[dst_depth]
        else:
            dst_dtype = dst_depth
        # same source and destination dtype, do nothing
        if src_dtype == dst_dtype:
            return data, False

        if dst_dtype not in supported_dtypes:
            raise ValueError("Destination depth '{}' not suppported for conversion.".format(dst_depth))
        if src_dtype not in supported_dtypes:
            raise ValueError("Source dtype '{}' not suppported for depth conversion.".format(src_dtype))

        # Source is float
        if src_dtype == 'float32' or src_dtype == 'float16':
            # casting float
            if dst_dtype == 'float32':
                return data.astype(np.float32, copy=False), True
            if dst_dtype == 'float16':
                return data.astype(np.float16, copy=False), True
            # float to int
            src_min = np.nanmin(data) # matrix may contain NaN
            src_max = np.nanmax(data)
            # reduce matrix between 0 to 1
            # min and max are close to the dtype limits, divide to have place for calculation
            if src_max - src_min >= np.finfo(src_dtype).max:
                data = (data/2 - src_min/2) / (src_max/2 - src_min/2)
            else:
                data = (data - src_min) / (src_max - src_min)
            if dst_dtype == 'uint8':
                data = data * 255 # 2^8 - 1
                data = data.astype(np.uint8, copy=False)
            elif dst_dtype == 'uint16':
                data = data * 65535 # 2^16 - 1
                data = data.astype(np.uint16, copy=False)
            elif dst_dtype == 'uint32':
                data = data * 4294967295 # 2^32 - 1
                data = data.astype(np.uint32, copy=False)
            return data, True

        # Source is integer

        # to 8 bits
        if dst_dtype == 'uint8':
            if src_dtype == 'uint16':
                data = data >> 8 # exact and faster than / 257.0
            elif src_dtype == 'uint32':
                data = data >> 16
            # cast at the end
            data = data.astype(np.uint8, copy=False)
            return data, True
        # to 16 bits
        elif dst_dtype == 'uint16':
            if src_dtype == 'uint8':
                data = data.astype(np.uint16, copy=False) # cast before to give place
                data = data * 257.0 # (2^16 - 1)/(2^8 - 1), bitshift is unprecise
            elif src_dtype == 'uint32':
                data = data >> 8
                data = data.astype(np.uint16, copy=False) # cast after
            return data, True
        # to 32 bits
        elif dst_dtype == 'uint32':
            data = data.astype(np.uint32, copy=False) # cast before calculations
            if src_dtype == 'uint8':
                data = data * 16843009.0 # (2^32 - 1)/(2^8 - 1)
            elif src_dtype == 'uint16':
                data = data * 65537.0 # (2^32 - 1)/(2^16 - 1)
            return data, True
        # int to float, just a cast
        elif dst_depth == '16f':
            return data.astype(np.float16, copy=False), True
        # int to float, just a cast
        elif dst_depth == '32f':
            return data.astype(np.float32, copy=False), True
        # should not arrive
        else:
            raise ValueError("Conversion from '{}' to '{}', not yet supported.".format(src_dtype, dst_depth))

    @staticmethod
    def _blend_alpha(data, back_color=(255, 255, 255)):
        '''
        If an image matrix has an alpha layer, blend it with a background color
        '''
        if len(data.shape) == 2:
            data.shape = [data.shape[0], data.shape[1], 1]
        # 1 channel, Gray, do nothing
        if data.shape[2] == 1:
            return data
        # 3 channels, BGR, do nothing
        elif data.shape[2] == 3:
            return data
        # 2 channels, Gray with alpha
        elif data.shape[2] == 2:
            # check if alpha is just a 100% layer
            if np.unique(data[:, :, 1]).size == 1:
                return data[:, :, 0]
            orig_dtype = data.dtype
            # convert back_color to a grey luminosity
            back_gray = 0.21 * back_color[0] + 0.72 * back_color[1] + 0.07 * back_color[2]
            # build a float matrix from the alpha layer, convert it to [0,1]
            alpha_mask = data[:, :, 1].astype(np.float64)
            if data.dtype == 'uint8':
                alpha_mask = alpha_mask / 255.0 # 2^8 - 1
            elif data.dtype == 'uint16':
                alpha_mask = alpha_mask / 65535.0 # 2^16 - 1
                back_gray = back_gray * 257.0 # (2^16 - 1) / (2^8 - 1)
            elif data.dtype == 'uint32':
                alpha_mask = alpha_mask / ((1 << 32) - 1) # 2^32 - 1
                back_gray = back_gray * 16843009.0 # (2^32 - 1) / (2^8 - 1)
            else: # float
                alpha_min = np.nanmin(alpha_mask) # matrix may contain NaN
                alpha_max = np.nanmax(alpha_mask)
                alpha_mask = (alpha_mask - alpha_min) / (alpha_max - alpha_min)
                # convert desired background according to min and max of the
                data_min = np.nanmin(data[:, :, 0])
                data_max = np.nanmax(data[:, :, 0])
                back_gray = back_gray / 255.0 * (data_max - data_min) + data_min
            # build a background matrix as float
            back_mat = np.zeros((data.shape[0], data.shape[1], 1), np.float64)
            # fill it with background color
            back_mat[:] = back_gray
            # apply inverse mask to background
            back_mat = cv2.multiply(1.0 - alpha_mask, back_mat)
            # apply mask to foregroung
            fore_mat = cv2.multiply(alpha_mask, data[:, :, 0].astype(np.float64))
            # merge back and fore
            data = cv2.add(back_mat, fore_mat)
            # restore original dtype
            data = data.astype(orig_dtype, copy=False)
            return data
        # 4 channels, BGRA, blend
        elif data.shape[2] == 4:
            # check if alpha is just a 100% layer
            if np.unique(data[:, :, 3]).size == 1:
                return data[:, :, :3]
            orig_dtype = data.dtype
            # convert back_color to BGR (OpenCV format)
            back_color = tuple(reversed(back_color))
            # build an alpha_mask, convert to float [0, 1], according to dtype
            alpha_mask = cv2.cvtColor(data[:, :, 3], cv2.COLOR_GRAY2BGR).astype(np.float64)
            if data.dtype == 'uint8':
                alpha_mask = alpha_mask / 255.0 # 2^8 - 1
            elif data.dtype == 'uint16':
                alpha_mask = alpha_mask / 65535.0 # 2^16 - 1
                back_color = (back_color[0] * 257.0, back_color[1] * 257.0, back_color[2] * 257.0)
            elif data.dtype == 'uint32':
                alpha_mask = alpha_mask / ((1 << 32) - 1) # 2^32 - 1
                back_color = (back_color[0] * 16843009.0, back_color[1] * 16843009.0, back_color[2] * 16843009.0)
            else: # float
                alpha_min = np.nanmin(alpha_mask) # matrix may contain NaN
                alpha_max = np.nanmax(alpha_mask)
                alpha_mask = (alpha_mask - alpha_min) / (alpha_max - alpha_min)
                data_min = np.nanmin(data[:, :, :3])
                data_max = np.nanmax(data[:, :, :3])
                back_color = (
                    back_color[0] / 255.0 * (data_max - data_min) + data_min,
                    back_color[1] / 255.0 * (data_max - data_min) + data_min,
                    back_color[2] / 255.0 * (data_max - data_min) + data_min
                )
            # build a background matrix as float
            back_mat = np.zeros((data.shape[0], data.shape[1], 3), np.float64)
            # fill it with background color
            back_mat[:] = back_color
            # apply inverse mask to background
            back_mat = cv2.multiply(1.0 - alpha_mask, back_mat)
            # apply mask to foregroung
            fore_mat = cv2.multiply(alpha_mask, data[:, :, :3].astype(np.float64))
            # merge back and fore
            data = cv2.add(back_mat, fore_mat)
            # restore original dtype
            data = data.astype(orig_dtype, copy=False)
            return data
        else: # unknown format
            return data

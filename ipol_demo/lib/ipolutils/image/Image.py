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
import tifffile

class Image(object):
    '''
    Generic image class, dealing with the best python libraries for performances, and formats (currently : OpenCV).
    '''
    DEPTH_DTYPE = {'8i': np.uint8, '8': np.uint8, '16i': np.uint16, '16': np.uint16, '32i': np.uint32,
                   '32': np.uint32, '16f': np.float16, '32f': np.float32}

    @staticmethod
    def load(src, flags=cv2.IMREAD_UNCHANGED):
        '''
        Factory, returns an image object build from file.
        '''
        if not os.path.isfile(src):
            raise OSError(errno.ENOENT, "File not found", src)
        im = Image()

        mime_type, _ = mimetypes.guess_type(src)

        if mime_type == 'image/tiff': # use tifffile
            im.data = tifffile.imread(src)
            if len(im.data.shape) < 3:
                pass
            elif im.data.shape[2] > 3: # RGBA > BGRA
                im.data = im.data[..., [2, 1, 0, 3]]
            elif im.data.shape[2] == 3: # RGB > BGR
                im.data = im.data[..., [2, 1, 0]]
        else:
            im.data = cv2.imread(src, flags)
        if type(im.data).__module__ != np.__name__:
            raise OSError(errno.ENODATA, "No data read. For supported image formats, see doc OpenCV imread", src)
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
        Factory, returns an image object build with the data matrix.
        '''
        im = Image()
        im.data = data
        return im

    @staticmethod
    def video_frame(video_file, pos_ratio=0.3):
        '''
        From a video, returns a significative frame as an image object.
        '''
        cap = cv2.VideoCapture(video_file)
        pos_frame = int(cap.get(cv2.CAP_PROP_FRAME_COUNT) * pos_ratio)
        cap.set(cv2.CAP_PROP_POS_FRAMES, pos_frame)
        _, frame = cap.read()
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
        mime_type, _ = mimetypes.guess_type(dst_file)
        if mime_type == 'image/tiff': # use tifffile
            data = self.data
            if len(data.shape) < 3:
                pass
            elif data.shape[2] > 3: # BGRA > RGBA
                data = data[..., [2, 1, 0, 3]]
            elif data.shape[2] == 3: # BGR > RGB
                data = data[..., [2, 1, 0]]
            tifffile.imsave(dst_file, data)
        else:
            data, pars = self._4ser(dst_file, **kwargs)
            if not cv2.imwrite(dst_file, data, pars):
                raise OSError(errno.EBADFD, "OpenCV imwrite error", dst_file)

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


    def _4jpeg(self, optimize=True, progressive=True, quality=92):
        '''
        Prepare data for JPEG, before saving to file or return bytes (blend alpha, 8 bits).
        '''
        data = self.blend_alpha_static(self.data)
        data = self.convert_depth_static(data, '8i')
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
            data = self.convert_depth_static(data, '16i')
        if compression >= 0 and compression <= 9:
            pars.extend([cv2.IMWRITE_PNG_COMPRESSION, compression])
        return data, pars

    def _4tiff(self):
        '''
        Prepare data for TIFF, before saving to file or return bytes (blend alpha).
        '''
        data = self.blend_alpha_static(self.data) # assume that tiff do not support alpha
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

    def get_channels(self):
        """
        Returns the number of channels of the image data loaded.
        """
        # impossible to keep self.data.shape[2] = 1 for gray image, is deleted by cv2 ops.
        if len(self.data.shape) < 3:
            return 1
        return self.data.shape[2]

    def check_channels(self, channels):
        '''
        Returns true if number of channels of the image is equals to the int parameter.
        '''
        return channels == self.get_channels()

    def convert_channels(self, dst_channels):
        '''
        Converts the number of channels of an image matrix.
        '''
        if not dst_channels:
            return False
        dst_channels = int(dst_channels)
        src_channels = self.get_channels()
        # if alpha, blend it, and retake the src channels
        if src_channels == 2 or src_channels == 4:
            self.data = self.blend_alpha_static(self.data)
            src_channels = self.get_channels()
        if src_channels == dst_channels:
            return False
        if src_channels == 3 and dst_channels == 1:
            self.data = cv2.cvtColor(self.data, cv2.COLOR_BGR2GRAY)
        elif src_channels == 1 and dst_channels == 3:
            self.data = cv2.cvtColor(self.data, cv2.COLOR_GRAY2BGR)
        else: # unknown number of channels
            raise ValueError("Channel conversion, {} > {} not yet supported.".format(src_channels, dst_channels))
        return True

    def check_depth(self, depth):
        '''
        Tests if the depth is equal to the matrix dtype.
        '''
        dtype = self.DEPTH_DTYPE[depth]
        return self.data.dtype == dtype

    def convert_depth(self, dst_depth):
        """
        Converts the depth of image data.
        """
        self.data = self.convert_depth_static(self.data, dst_depth)

    @staticmethod
    def convert_depth_static(data, dst_depth):
        """
        Converts the depth of an image matrix.
        Used as a static method, before saving as jpeg, without affecting underlaying data.
        """
        if not dst_depth in Image.DEPTH_DTYPE:
            raise ValueError("Destination depth '{}' not suppported for conversion.".format(dst_depth))
        src_dtype = data.dtype
        dst_dtype = Image.DEPTH_DTYPE[dst_depth]


        # same source and destination dtype, do nothing
        if src_dtype == dst_dtype:
            return data

        # Source is float
        if np.issubdtype(src_dtype, np.floating):
            # float -> float
            if np.issubdtype(dst_dtype, np.floating):
                data = data.astype(dst_dtype, copy=False)
            # float -> int
            else:
                src_min, src_max = np.min(data), np.max(data)
                # normalize to range [0, 1] and multiply to max for int format
                data = (data - src_min) / float(src_max - src_min) * np.iinfo(dst_dtype).max
                data = data.astype(dst_dtype, copy=False)
            return data

        # int -> int
        elif np.issubdtype(dst_dtype, np.integer): #check condition
            dst_max = np.iinfo(dst_dtype).max
            src_max = np.iinfo(src_dtype).max
            if dst_max < src_max: # Reduce bits, cast after
                k = src_max / dst_max
                data = data / k
                data = data.astype(dst_dtype, copy=False)
            else: # Increase bits, cast before to have place for max value
                data = data.astype(dst_dtype, copy=False)
                k = dst_max / src_max # keep k as int, if k is float (data * k) will become float
                data = data * k
            return data

        # int -> float
        elif np.issubdtype(dst_dtype, np.floating):
            data = data.astype(dst_dtype, copy=False), True
            return data

        raise ValueError("Conversion from '{}' to '{}', not yet supported.".format(src_dtype, dst_depth))

    @staticmethod
    def blend_alpha_static(data, back_color=(255, 255, 255)):
        '''
        If an image matrix has an alpha layer, blend it with a background color.
        Used as a static method, before saving as tiff or jpeg, without affecting underlaying data.
        '''
        if len(data.shape) < 3 or data.shape[2] not in [2, 4]:
            return data
        # check if alpha is just a 100% layer
        if np.unique(data[:, :, -1]).size == 1:
            return data[:, :, 0:-1]
        orig_dtype = data.dtype # keep original depth
        # 2 channels, Gray with alpha
        if data.shape[2] == 2:
            channels = 1
            # convert back_color to a grey luminosity
            back_color = 0.21 * back_color[0] + 0.72 * back_color[1] + 0.07 * back_color[2]
            alpha_mask = data[:, :, 1].astype(np.float64)
        # 4 channels, BGRA
        elif data.shape[2] == 4:
            channels = 3
            # convert back_color to BGR (OpenCV format)
            back_color = np.array(tuple(reversed(back_color)))
            # convert alpha mask to a 3 chanels gray
            alpha_mask = cv2.cvtColor(data[:, :, 3], cv2.COLOR_GRAY2BGR).astype(np.float64)
        # convert alphamask as float [0, 1]
        if  np.issubdtype(orig_dtype, np.integer):
            alpha_min = data_min = 0
            alpha_max = data_max = np.iinfo(orig_dtype).max
        else: # float
            alpha_min = np.nanmin(alpha_mask) # matrix may contain NaN
            alpha_max = np.nanmax(alpha_mask)
            data_min = np.nanmin(data[:, :, -1])
            data_max = np.nanmax(data[:, :, -1])
        alpha_mask = (alpha_mask - alpha_min) / float(alpha_max - alpha_min)
        back_color = back_color / 255.0 * (data_max - data_min) + data_min

        # build a background matrix as float
        back_mat = np.zeros((data.shape[0], data.shape[1], channels), np.float64)
        # fill it with background color
        back_mat[:] = back_color
        # apply inverse mask to background
        back_mat = cv2.multiply(1.0 - alpha_mask, back_mat)
        # apply mask to foregroung
        fore_mat = cv2.multiply(alpha_mask, data[:, :, :-1].astype(np.float64))
        # merge back and fore
        data = cv2.add(back_mat, fore_mat)
        # restore original dtype
        data = data.astype(orig_dtype, copy=False)
        return data

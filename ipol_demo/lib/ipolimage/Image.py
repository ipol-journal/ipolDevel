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
from contextlib import contextmanager
import errno
import os
import sys

import cv2
import numpy as np

@contextmanager
def redirector(out=open(os.devnull, 'w')):
    '''
    Stderr redirector for external C libraries.
    '''
    # https://stackoverflow.com/questions/5081657/
    fd = sys.stderr.fileno()
    def _redirect(fileno):
        sys.stderr.close() # + implicit flush()
        os.dup2(fileno, fd) # fd writes to 'to' file
        sys.stderr = os.fdopen(fd, 'w') # Python writes to fd

    with os.fdopen(os.dup(fd), 'w') as old_stdout:
        _redirect(out.fileno())
        try:
            yield # allow code to be run with the redirected stdout
        finally:
            _redirect(old_stdout.fileno()) # restore stdout.

class Image(object):
    '''
    Generic image class, dealing with the best python libraries for performances, and formats.
    Actually : OpenCV.
    Operations are done on a numpy matrix.
    Load : jpeg (uint8), png (uint8, uint16; alpha; colormap), tiff (uint8, uint16)
    Writes : jpeg (uint8), png (uint8, uint16; alpha), tiff (uint8, uint16)
    '''
    dtype = None
    width = None
    height = None
    channels = None
    # don’t forget: ICC profile?, EXIF?
    def __init__(self, src):
        '''
        Construct an image object, load data according to src type when possible.
        None: set data later, see IPOLImage.load(file_path), IPOLImage.decode(string_bytes)
        numpy.ndarray: matrix like internal CV image
        str, unicode: file_path
        '''
        # Object build without file, data may be loaded by decode (low typing, no good test)
        if src is None:
            return
        # source is a data matrix
        if isinstance(src, np.ndarray):
            self.data = src
            return
        # source seems a file
        self.load(src)

    def load(self, path, flags=cv2.IMREAD_UNCHANGED):
        '''
        Load image data as a file
        '''
        if not os.path.isfile(path):
            raise OSError(errno.ENOENT, "File not found", path)
        # OpenCV C do not resend the warnings to Python see https://stackoverflow.com/questions/9131992
        # with redirector():
        # default flag to IMREAD_UNCHANGED, option to keep alpha or uint16
        self.data = cv2.imread(path, flags)
        if self.data is None:
            raise OSError(errno.ENODATA, "No data read. For supported image formats, see doc OpenCV imread", path)
        self.src_file = path
        self.src_path = os.path.realpath(self.src_file)
        self.src_dir, self.src_basename = os.path.split(self.src_path)
        self.src_name, self.src_ext = os.path.splitext(self.src_basename)
        self._props()

    def decode(self, buf, flags=cv2.IMREAD_UNCHANGED):
        '''
        Load image data as a string of bytes
        '''
        buf = np.fromstring(buf, dtype=np.uint8)
        # Are they problems with warnings ?
        self.data = cv2.imdecode(buf, flags)
        if self.data is None:
            raise RuntimeError(errno.ENODATA, "No data read. For supported image formats, see doc OpenCV imread")
        self._props()

    def _props(self):
        '''
        Set properties from data like width or height, updated after each changes.
        '''
        if len(self.data.shape) == 2:
            self.height, self.width = self.data.shape
            self.channels = 1
        else: # let exception shout if it is not like that
            self.height, self.width, self.channels = self.data.shape
        self.dtype = self.data.dtype

    @staticmethod
    def blend_alpha(data, back_color=(255, 255, 255)):
        '''
        Take a CV numpy matrix, blend with back_color if there is an alpha layer.
        Return the resulting matrix. Do not affect the field of data.
        '''
        # 1 channel, Gray, do nothing
        if len(data.shape) == 2 or data.shape[2] == 1:
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
            alpha_mask = data[:, :, 3].astype(float)
            if data.dtype == 'uint8':
                alpha_mask = alpha_mask / 255.0
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
            alpha_mask = cv2.cvtColor(data[:, :, 3], cv2.COLOR_GRAY2BGR).astype(float)
            if data.dtype == 'uint8':
                alpha_mask = alpha_mask / 255.0
            elif data.dtype == 'uint16':
                alpha_mask = alpha_mask / 65535.0
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
            data = cv2.add(back_mat, fore_mat)
            # restore original dtype
            data = data.astype(orig_dtype, copy=False)
            return data
        else: # unknown format
            return data


    def write(self, dst_file, force=False, **kwargs):
        '''
        Save image matrix to destination file, format according to file extension.
        See _4ser for available extensions and formats.
        '''
        # ? concurrency conflict
        if os.path.exists(dst_file) and not force:
            raise OSError(errno.EEXIST, "Destination file already exists, use force=True kwarg to overwrite", dst_file)
        # caution, cv2.imwrite will not create subdirectories and silently fail
        dst_dir = os.path.dirname(dst_file)
        if dst_dir and not os.path.exists(dst_dir):
            os.makedirs(dst_dir)
        ext = os.path.splitext(dst_file)[1]
        data, pars = self._4ser(ext, **kwargs)
        cv2.imwrite(dst_file, data, pars)

    def encode(self, ext, **kwargs):
        '''
        Return image matrix as encoded bytes, format according to a file extension.
        See _4ser for available extensions and formats.
        '''
        data, pars = self._4ser(ext, **kwargs)
        ext = '.' + ext.lstrip('.')
        _, buf = cv2.imencode(ext, data, pars)
        return buf.tostring()

    def _4ser(self, ext, **kwargs):
        '''
        Return data and parameters prepared for serialization (memory or file)
        Available extensions.
        jpeg, jpg
        png
        tif, tiff
        See _4{ext} for available options for each image encoding formats.
        '''
        ext = ext.lstrip('.') # strip leading dot
        if ext == 'jpg' or ext == 'jpeg':
            return self._4jpeg(**kwargs)
        elif ext == 'png':
            return self._4png(**kwargs)
        elif ext == 'tiff' or ext == 'tif':
            return self._4tiff(**kwargs)
        else:
            raise ValueError("Extension {}, is not supported.".format(ext))


    def _4jpeg(self, optimize=True, progressive=True, quality=80):
        '''
        Prepare data for jpeg, before saving to file or return bytes.
            optimize=True (True|False)
            progressive=True (True|False)
            quality=80 (0—100)
        '''
        data = self.blend_alpha(self.data)
        data, _ = self.convert_matrix(data, 'x8i')
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
        Prepare data for png, before saving to file or return bytes.
            compression=9 (0-9)
        '''
        # no optimise flag found in OpenCV API
        pars = []
        if compression >= 0 and compression <= 9:
            pars.extend([cv2.IMWRITE_PNG_COMPRESSION, compression])
        return self.data, pars


    def _4tiff(self):
        '''
        Prepare data for tiff, before saving to file or return bytes.
        '''
        data = self.blend_alpha(self.data) # assume that tiff do not support alpha
        pars = []
        return data, pars

    def resize(self, preserve_ratio=True, width=None, height=None, fx=None, fy=None, interpolation=None):
        '''
        Smart resize, according to different parameters
        '''

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
            self.data = cv2.resize(self.data, None, fx=fx, fy=fy, interpolation=interpolation)
            self._props()
            return

        src_height, src_width = self.data.shape[:2]
        dst_width, dst_height = width, height
        # problem
        if not width > 0 and not height > 0:
            raise ValueError("Bad arguments, at least zoom or (width and/or height)")

        # containing box
        if dst_width > 0 and dst_height > 0:
            if preserve_ratio:
                ratio_width = float(dst_width) / src_width
                ratio_height = float(dst_height) / src_height
                if ratio_width < ratio_height:
                    dst_height = float(src_height) * ratio_width
                else:
                    dst_width =  float(src_width) * ratio_height
        # forced height
        elif dst_height > 0:
            max_width = 2*dst_height # avoid extreme ratio
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
        # dtype of matrix is still kept
        if interpolation: # keep requested interpolation
            pass
        elif (dst_width > src_width) or (dst_height > src_height): # augmentation, pixelise
            interpolation = cv2.INTER_NEAREST
        else: # diminution, for thumbnail, some interpolation
            interpolation = cv2.INTER_AREA
        self.data = cv2.resize(self.data, (int(dst_width), int(dst_height)), interpolation=interpolation)
        self._props()

    def crop(self, x=0, y=0, width=0, height=0):
        '''
        Crop data according to a 4-tuple rectangle (left, upper, right, lower)
        '''
        if width <= 0 or height <= 0 or x < 0 or y < 0:
            raise ValueError("Crop, bad arguments x={}, y={}, x+width={}, y+height={} outside image ({}, {})".format(x, y, x+width, y+height, self.width, self.height))
        if x + width > self.width or y + height > self.height:
            raise ValueError("Crop, bad arguments x={}, y={}, x+width={}, y+height={} outside image ({}, {})".format(x, y, x+width, y+height, self.width, self.height))
        self.data = self.data[y:y+height, x:x+width]
        self._props()

    def convert(self, mode):
        '''
        Convert data accordind to mode. See convert_matrix for values impleéented.
        Return True if a modification have been done
        '''
        self.data, ret = self.convert_matrix(self.data, mode)
        self._props()
        return ret

    @staticmethod
    def video_frame(video_file, pos_ratio=0.5, pos_max=7500):
        '''
        From a video, returns a significative frame as an image object
        '''
        cap = cv2.VideoCapture(video_file)
        pos_frame = int(cap.get(cv2.CAP_PROP_FRAME_COUNT) * pos_ratio)
        pos_frame = min(pos_frame, pos_max)
        for i in range(1, pos_frame):
            cap.read()
        ret, frame = cap.read()
        # When everything done, release the capture
        cap.release()
        return Image(frame)

    @staticmethod
    def convert_matrix(data, mode):
        '''
        Convert number of channels and dtype of a CV image matrix.
        Static method allow to modify data for saving (ex: 8 bits for jpeg)
        without
        Return: a tuple (data, modification) where data is the resulting data
            and modification is a flag with value None: no modification, True: modified
        data: a CV numpy matrix
        mode: 1x8i, 3x8i, 1x16i, 3x16i, 1x32i, 3x32i
        '''
        # TODO 1x1i, nx16f, nx32f

        if not mode:
            return data, None
        ret = None # default return value


        if mode[0] != 'x': # channel modification requested
            dst_channels = int(mode[0])
            if len(data.shape) == 2:
                src_channels = 1
            else:
                src_channels = data.shape[2]
            # always blend alpha for 1 or 3 channels
            if src_channels == 2 or src_channels == 4:
                data = Image.blend_alpha(data)
                ret = True
            if dst_channels == 1:
                if src_channels == 3:
                    data = cv2.cvtColor(data, cv2.COLOR_BGR2GRAY)
                    ret = True
            elif dst_channels == 3:
                if src_channels == 1:
                    data = cv2.cvtColor(data, cv2.COLOR_GRAY2BGR)
                    ret = True
            else: # unknown number of channels
                raise ValueError("Convert matrix, mode={}, number of channels not yet supported.".format(mode))

        if 'x' in mode: # dtype modification requested
            dst_depth = mode[mode.index('x')+1:]
            src_dtype = data.dtype
            if dst_depth == '8i' or dst_depth == '8':
                if src_dtype == 'uint8': # OK, do nothing
                    pass
                elif src_dtype == 'uint16':
                    data = data >> 8 # faster than data = data / 256
                    data = data.astype(np.uint8, copy=False) # just a cast
                    ret = True
                elif src_dtype == 'uint32':
                    data = data >> 16
                    data = data.astype(np.uint8, copy=False)
                    ret = True
                elif src_dtype == 'float32' or src_dtype == 'float16':
                    src_min = np.amin(data)
                    src_max = np.amax(data)
                else:
                    raise ValueError("Convert matrix, source dtype={} not yet supported for '{}' mode conversion.".format(src_dtype, dst_depth))
            elif dst_depth == '16i' or dst_depth == '16':
                if src_dtype == 'uint16': # OK, do nothing
                    pass
                elif src_dtype == 'uint8':
                    data = data.astype(np.uint16, copy=False)
                    data = data << 8
                    ret = True
                elif src_dtype == 'uint32':
                    data = data >> 8
                    data = data.astype(np.uint16, copy=False)
                    ret = True
                else:
                    raise ValueError("Convert matrix, source dtype={} not yet supported  for '{}' mode conversion.".format(src_dtype, dst_depth))
            else:
                raise ValueError("Convert matrix, mode={} not yet supported.".format(mode))
        return data, ret

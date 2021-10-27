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
Image operations wrapper.
"""
import errno
import mimetypes
import os

import cv2
import imageio
import numpy as np
import tifffile
from ipolutils.errors import IPOLImageReadError


class Image(object):
    '''
    Image container object.
    '''
    DEPTH_DTYPE = {'8i': np.uint8, '8': np.uint8, '16i': np.uint16, '16': np.uint16, '32i': np.uint32,
                   '32': np.uint32, '16f': np.float16, '32f': np.float32}

    def __init__(self, data=None, buf=None, src=None):
        '''
        Constructor
        '''
        if np.count_nonzero(list(v is not None for v in (data, buf, src))) != 1:
            raise Exception("You should specify only one origin (data, buf, or src)")

        if data is not None:
            self.data = data
        elif buf:
            buf = np.frombuffer(buf, dtype=np.uint8)
            self.data = cv2.imdecode(buf, cv2.IMREAD_UNCHANGED)
        elif src:
            if not os.path.isfile(src):
                raise OSError(errno.ENOENT, "File not found", src)
            mime_type, _ = mimetypes.guess_type(src)
            if mime_type == 'image/tiff':
                self.data = tifffile.imread(src)
                self.is_tiff = True
                self.ensure_data_shape()
                if self.is_tiff_image():
                    self.data = self.reverse_channels_order() # tifffile reads as RGB, OpenCV need BGR
            elif mime_type == 'image/jpeg':
                # cv2.IMREAD_COLOR will take care of the orientation flag in the EXIF.
                # As a collateral effect it'll drop the alpha channel and reduce the color depth to 8 bits, which
                # is convenient since we're encoding to JPEG.
                self.data = cv2.imread(src, cv2.IMREAD_COLOR)
            elif mime_type == 'image/gif':
                im = imageio.get_reader(src, '.gif')
                for frame in im:
                    self.data = frame
                    break
            else:
                self.data = cv2.imread(src, cv2.IMREAD_UNCHANGED)

        if self.data is None:
            raise IPOLImageReadError(f'Image read error, data={data} buf={buf}, src={src}')
        self.ensure_data_shape()

    def is_tiff_image(self):
        '''
        Check if the given TIFF is an image (less or equal to 4 channels and uint8/uint16 depth).
        '''
        return self.get_channels() <= 4 and self.data.dtype in (np.uint8, np.uint16)

    @staticmethod
    def video_frame(video_file, pos_ratio=0.3):
        '''
        Extract a representative frame from a video (for example to be used as a thumbnail).
        '''
        cap = cv2.VideoCapture(video_file)
        pos_frame = int(cap.get(cv2.CAP_PROP_FRAME_COUNT) * pos_ratio)
        cap.set(cv2.CAP_PROP_POS_FRAMES, pos_frame)
        _, frame = cap.read()
        cap.release()
        return Image(data=frame)

    def reverse_channels_order(self):
        """
        Reverse the channels order (RGB > BGR), for compatibility among libraries.
        """
        if self.data.shape[2] == 4: # BGRA > RGBA or RGBA > BGRA 
            return self.data[..., [2, 1, 0, 3]]
        elif self.data.shape[2] == 3: # BGR > RGB or RGB > BGR
            return self.data[..., [2, 1, 0]]
        return self.data

    def width(self):
        '''
        Returns the width.
        '''
        return self.data.shape[1]

    def height(self):
        '''
        Returns the height.
        '''
        return self.data.shape[0]

    def write(self, dst_file, **kwargs):
        """
        Save the image matrix into the destination file, encoded according to the file extension.
        """
        # warning, cv2.imwrite will not create subdirectories and silently fail
        dst_dir = os.path.dirname(dst_file)
        if not os.path.exists(dst_dir):
             raise OSError(errno.ENOENT, "Folder not found", dst_dir)
        mime_type, _ = mimetypes.guess_type(dst_file)
        if mime_type == 'image/tiff':
            tifffile.imsave(dst_file,
                self.reverse_channels_order() if self.is_tiff_image() else self.data)
        else:
            pars = self.prepare_for_save(dst_file, **kwargs)
            if not cv2.imwrite(dst_file, self.data, pars):
                raise Exception("OpenCV imwrite error", dst_file)

    def encode(self, ext, **kwargs):
        '''
        Convert according to the given extension, as bytes.
        '''
        pars = self.prepare_for_save('dummy{}'.format(ext), **kwargs)
        _, buf = cv2.imencode(ext, self.data, pars)
        return buf

    def prepare_for_save(self, path, **kwargs):
        '''
        Return data and parameters for serialization.
        '''
        # See prepare_for_{ext} for available options for each image encoding formats.
        mime_type, _ = mimetypes.guess_type(path)
        if mime_type == 'image/jpeg':
            return self.prepare_for_jpeg(**kwargs)
        elif mime_type == 'image/png':
            return self.prepare_for_png(**kwargs)
        return []

    def prepare_for_jpeg(self, optimize=True, progressive=True, quality=92):
        '''
        Prepare data for JPEG.
        '''
        if self.has_alpha():
            self.data = self.remove_alpha(self.data)
        self.convert_depth('8i')
        # not found in OpenCV API subsampling, ex: '4:4:4'
        pars = []
        if optimize:
            pars.extend([cv2.IMWRITE_JPEG_OPTIMIZE, 1])
        if progressive:
            pars.extend([cv2.IMWRITE_JPEG_PROGRESSIVE, 1]) 
        pars.extend([cv2.IMWRITE_JPEG_QUALITY, quality])
        return pars

    def prepare_for_png(self, compression=9):
        '''
        Prepare data for PNG.
        '''
        # no optimize flag found in OpenCV API
        pars = []
        pars.extend([cv2.IMWRITE_PNG_COMPRESSION, compression])
        return pars

    def resize(self, width=None, height=None, interpolation=None):
        '''
        Resize image data.
        '''
        src_height, src_width = self.data.shape[:2]
        # forced width*height (aspect ratio modified)
        if width and height:
            pass
        # forced height
        elif height:
            width = int(round(float(src_width * height) / src_height))
        # forced width
        elif width:
            height = int(round(float(src_height * width) / src_width))
        else:
            raise ValueError("Image.resize(), not enough parameters to resize image.")
        # dtype of matrix is kept
        if interpolation: # keep requested interpolation
            pass
        elif (width > src_width) or (height > src_height): # enlarge
            interpolation = cv2.INTER_NEAREST # Nearest neighbors
        else: # shrink, for thumbnail, some interpolation
            interpolation = cv2.INTER_AREA
        self.cv2_resize(int(width), int(height), interpolation)

    def crop(self, x=0, y=0, width=0, height=0):
        '''
        Rectangular crop.
        '''
        if width <= 0 or height <= 0 or x < 0 or y < 0:
            raise ValueError("Crop, bad arguments x={}, y={}, x+width={}, y+height={} outside image ({}, {})".format(x, y, x+width, y+height, self.width(), self.height()))
        if x + width > self.width() or y + height > self.height():
            raise ValueError("Crop, bad arguments x={}, y={}, x+width={}, y+height={} outside image ({}, {})".format(x, y, x+width, y+height, self.width(), self.height()))
        self.data = self.data[y:y+height, x:x+width]

    def get_channels(self):
        """
        Get the number of channels.
        """
        return self.data.shape[2]

    def convert_channels(self, dst_channels):
        '''
        Converts the number of channels.
        '''
        dst_channels = int(dst_channels)
        src_channels = self.get_channels()
        # if alpha, blend it, and retake the src channels
        if self.has_alpha():
            self.data = self.remove_alpha(self.data)
            src_channels = self.get_channels()
        if src_channels == dst_channels:
            return
        if src_channels == 3 and dst_channels == 1:
            self.cv2_cvtColorToGray()
        elif src_channels == 1 and dst_channels == 3:
            self.data = cv2.cvtColor(self.data, cv2.COLOR_GRAY2BGR)
        else:
            raise ValueError("Channel conversion, {} > {} not yet supported.".format(src_channels, dst_channels))

    def convert_depth(self, dst_depth):
        """
        Converts the depth.
        """
        dst_dtype = Image.DEPTH_DTYPE[dst_depth]
        if not dst_dtype:
            raise ValueError("Destination depth '{}' not suppported for conversion.".format(dst_depth))
        src_dtype = self.data.dtype

        if src_dtype == dst_dtype:
            return

        # Source is float 
        if np.issubdtype(src_dtype, np.floating):
            # float -> float
            if np.issubdtype(dst_dtype, np.floating):
                self.data = self.data.astype(dst_dtype, copy=False)
            # float -> int
            else:
                src_min, src_max = np.min(self.data), np.max(self.data)
                # normalize to range [0, 1] and multiply to max for int format
                self.data = (self.data - src_min) / float(src_max - src_min) * np.iinfo(dst_dtype).max
                self.data = self.data.astype(dst_dtype, copy=False)

        # int -> int
        elif np.issubdtype(dst_dtype, np.integer): #check condition
            dst_max = np.iinfo(dst_dtype).max
            src_max = np.iinfo(src_dtype).max
            if dst_max < src_max: # Reduce bits, cast after
                k = src_max / dst_max
                self.data = self.data / k
                self.data = self.data.astype(dst_dtype, copy=False)
            else: # Increase bits
                self.data = self.data.astype(dst_dtype, copy=False)
                k = int(dst_max / src_max)
                self.data = self.data * k

        # int -> float
        elif np.issubdtype(dst_dtype, np.floating):
            self.data = self.data.astype(dst_dtype, copy=False), True

        else:
            raise ValueError("Conversion from '{}' to '{}', not supported.".format(src_dtype, dst_depth))

    def has_alpha(self):
        '''
        Check if the given image has an alpha channel. 
        '''
        return self.data.shape[2] in (2, 4) and self.data.dtype in (np.uint8, np.uint16)

    @staticmethod
    def remove_alpha(data):
        '''
        If an image has an alpha layer, blend it with a background color.
        '''
        back_color = (0, 0, 0) # The inpainting demos expect black 
        # check if alpha is just a 100% layer
        if np.unique(data[:, :, -1]).size == 1:
            return data[:, :, 0:-1]
        orig_dtype = data.dtype # keep original depth
        num_channels = data.shape[2]
        # 2 channels, gray with alpha
        if num_channels == 2:
            channels = 1
            # convert back_color to gray
            back_color = 0.21 * back_color[0] + 0.72 * back_color[1] + 0.07 * back_color[2]
            alpha_mask = data[:, :, 1].astype(np.float64)
        # 4 channels, BGRA
        elif num_channels == 4:
            channels = 3
            # convert back_color to BGR (OpenCV format)
            back_color = np.array(tuple(reversed(back_color)))
            # convert alpha mask to a 3 channels gray
            alpha_mask = Image(data=data[:, :, 3])
            alpha_mask.data = cv2.cvtColor(alpha_mask.data, cv2.COLOR_GRAY2BGR)
            alpha_mask = alpha_mask.data.astype(np.float64)
        # convert alphamask as float [0, 1]
        if  np.issubdtype(orig_dtype, np.integer):
            alpha_min = data_min = 0
            alpha_max = data_max = np.iinfo(orig_dtype).max
        else: # float
            alpha_min = np.min(alpha_mask)
            alpha_max = np.max(alpha_mask)
            data_min = np.min(data[:, :, -1])
            data_max = np.max(data[:, :, -1])
        alpha_mask = (alpha_mask - alpha_min) / float(alpha_max - alpha_min)
        back_color = back_color / 255.0 * (data_max - data_min) + data_min

        # build a background matrix of floats
        back_mat = np.zeros((data.shape[0], data.shape[1], channels), np.float64)
        # fill it with a background color
        back_mat[:] = back_color
        # apply inverse mask to background
        back_mat = cv2.multiply(1.0 - alpha_mask, back_mat)
        # apply mask to foreground
        fore_mat = cv2.multiply(alpha_mask, data[:, :, :-1].astype(np.float64))
        # merge back and foreground
        data = cv2.add(back_mat, fore_mat)
        # restore original dtype
        data = data.astype(orig_dtype, copy=False)
        return data

    def ensure_data_shape(self):
        '''
        Ensure that the data shape contains the number of channels.
        '''
        if len(self.data.shape) != 3:
            self.data.shape = self.data.shape + (1,)

    ###################
    # CV2 WRAPPER. 
    # Needed because the operations below remove the channels dimension when it's 1.
    ###################

    def cv2_cvtColorToGray(self):
        '''
        CV2 cvtColor wrapper to convert from color to gray.
        '''
        self.data = cv2.cvtColor(self.data, cv2.COLOR_BGR2GRAY)
        self.ensure_data_shape()

    def cv2_resize(self, width, height, interpolation):
        '''
        CV2 resize wrapper.
        '''
        self.data = cv2.resize(self.data, (width, height), interpolation=interpolation)
        self.ensure_data_shape()

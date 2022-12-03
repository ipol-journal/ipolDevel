"""
IPOL Conversion module, services to convert blobs.
"""

import base64
import binascii
from dataclasses import dataclass
from enum import Enum
import errno
import glob
import logging
import math
import mimetypes
import os
from typing import Optional
from result import Ok, Err, Result

import numpy as np
from conversion.errors import IPOLConvertInputError, IPOLCropInputError
from ipolutils.errors import IPOLImageReadError
from ipolutils.evaluator.evaluator import evaluate
from ipolutils.image.Image import Image
from ipolutils.video.Video import Video


class ConversionStatus(Enum):
    Error = -1
    NotNeededOrWithoutLoss = 0
    Done = 1
    NeededButForbidden = 2

@dataclass
class ConversionInfo:
    code: ConversionStatus
    modifications: list[str]
    error: Optional[str]


class Converter():

    def __init__(self):
        self.logger = init_logging()

    def convert(self, work_dir: str, input_list, crop_info) -> Result[dict[int,ConversionInfo], str]:
        """
        Pre-process the input data in their working directory, according to the DDL specs and optional crop.
        """
        def hide_workdir(message):
            return message.replace(work_dir, '<work_dir>')

        info = {}

        for i, input_desc in enumerate(input_list):
            assert 'type' in input_desc

            # before transformation success, default return code is failure
            code = ConversionStatus.Error
            error = None
            modifications = []

            # Search for a file for this input
            pattern = os.path.join(work_dir, 'input_{}'.format(i)) + '.*'
            input_files = glob.glob(pattern)

            # no file found, is this input optional?
            if not input_files:
                if not input_desc.get('required', True):
                    # input[i] not present but not required, do nothing
                    continue

                # An input is required and is absent, warn but no exception
                error = f"Input required, but file not found in: {pattern}"

            else:
                input_file = input_files[0]

                # Is file too large for expected input in DDL?
                if input_desc.get('max_weight') and os.path.getsize(input_file) > evaluate(input_desc.get('max_weight')):
                    error = f"File too large: {input_file}"

                # convert the file
                else:
                    result = self._convert_file(input_desc, input_file, crop_info)

                    if isinstance(result, Ok):
                        code, modifications = result.value
                    else:
                        # exit early, critical issue with the conversion
                        message = hide_workdir(result.unwrap_err())
                        return Err(f"Input {i}: {message}")

            info[i] = ConversionInfo(
                code=code,
                modifications=modifications,
                error=error,
            )

        # globally OK (no exception), but for some input, a return code could be -1
        return Ok(info)

    def _convert_file(self, input_desc, input_file, crop_info) -> Result[tuple[ConversionStatus,list[str]], str]:
        input_type = input_desc['type']
        try:
            if input_type == 'image':
                code, modifications = self._convert_image(input_file, input_desc, crop_info)
            elif input_type == "data":
                code = self._add_ext_to_data(input_file, input_desc)
                modifications = []
            elif input_type == "video":
                code, modifications = self._convert_video(input_file, input_desc)
            else:
                return Err(f"{input_type}: unknown input type")

        except (IPOLConvertInputError, IPOLCropInputError) as ex:
            self.logger.exception(ex)
            return Err(repr(ex))
        except (IPOLImageReadError) as ex:
            return Err(repr(ex))
        except OSError as ex:
            # Do not log if it's an unsupported file format
            if ex.errno != errno.ENODATA or 'imread' not in ex.strerror:
                self.logger.exception(ex)
            return Err(repr(ex))
        except RuntimeError as ex:
            self.logger.exception(ex)
            return Err(repr(ex))
        except Exception as ex:
            self.logger.exception(ex)
            return Err(repr(ex))

        else:
            return Ok((code, modifications))

    @staticmethod
    def _convert_image(input_file, input_desc, crop_info=None) -> tuple[ConversionStatus, list[str]]:
        """
        Convert image if needed
        """
        # Image has to be always loaded to test width and size
        im = Image(src=input_file)
        dst_file = os.path.splitext(input_file)[0] + input_desc.get('ext')

        program = [
            # Color conversion
            ConverterChannels(input_desc, im),
            # Depth conversion
            ConverterDepth(input_desc, im),
            # Crop before reducing image to max_pixels (or the crop box will be outside of scope)
            ConverterCrop(input_desc, im, crop_info),
            # Resize image if bigger than a max.
            ConverterMaxPixels(input_desc, im),
            # Re-encoding (ex: jpg > png)
            ConverterEncoding(input_desc, input_file, dst_file),
        ]
        messages = []
        lossy_modification = False
        modification = False

        for task in program:
            if not task.need_conversion():
                continue
            if not task.can_convert():
                return ConversionStatus.NeededButForbidden, []

            info_loss = task.information_loss()
            message = task.convert()
            modification = True
            if info_loss:
                messages.append(message)
                lossy_modification = True

        # something have been done, write file
        if modification:
            im.write(dst_file)
        # Nothing done, ensure expected extension (.jpe > .jpeg; .tif > .tiff)
        elif input_file != dst_file:
            os.rename(input_file, dst_file)
        if lossy_modification:
            return ConversionStatus.Done, messages
        return ConversionStatus.NotNeededOrWithoutLoss, []

    @staticmethod
    def _convert_video(input_file, input_desc) -> tuple[ConversionStatus, list[str]]:
        """
        Convert video
        """
        modifications = []
        video = Video(input_file)
        as_frames = input_desc.get('as_frames', None)
        max_frames = int(evaluate(input_desc.get('max_frames')))
        max_pixels = int(evaluate(input_desc.get('max_pixels')))
        if as_frames:
            result = video.extract_frames(max_frames=max_frames, max_pixels=max_pixels)
            if result == 1:
                code = ConversionStatus.Done
            elif result == 0:
                code = ConversionStatus.NotNeededOrWithoutLoss
            else:
                assert False
            modifications.append('extracted to frames')
        else:
            result = video.create_avi(max_frames=max_frames, max_pixels=max_pixels)
            if result == 1:
                code = ConversionStatus.Done
            elif result == 0:
                code = ConversionStatus.NotNeededOrWithoutLoss
            else:
                assert False
            modifications.append('AVI created')
            modifications.append('huffman encoded')

        return code, modifications

    @staticmethod
    def _add_ext_to_data(input_file, input_desc) -> ConversionStatus:
        """
        Add the specified extension to the data file
        """
        ext = input_desc.get('ext')
        if ext is None:
            raise IPOLConvertInputError('No format extension given')
        filename_no_ext, _ = os.path.splitext(input_file)
        input_with_extension = filename_no_ext + ext
        os.rename(input_file, input_with_extension)
        return ConversionStatus.NotNeededOrWithoutLoss

    def convert_tiff_to_png(self, img):
        """
        Converts the input TIFF to PNG.
        This is used by the web interface for visualization purposes
        """
        data = {"status": "KO"}
        try:
            buf = base64.b64decode(img)
            # cv2.IMREAD_ANYCOLOR option try to convert to uint8, 7x faster than matrix conversion
            # but fails with some tiff formats (float)
            im = Image(buf=buf)
            im.convert_depth('8i')
            buf = im.encode('.png')
            data["img"] = binascii.b2a_base64(buf).decode() # re-encode bytes
            data["status"] = "OK"
        except Exception:
            message = "TIFF to PNG for client, conversion failure."
            self.logger.exception(message)
        return data

class ConverterImage():
    """
    Base class for a conversion task
    """

    def __init__(self, input_desc, im):
        self.forbid_preprocess = input_desc.get("forbid_preprocess", False)
        self.im = im

    def information_loss(self):
        """
        Checks if the conversion may lose information
        """
        raise NotImplementedError

    def can_convert(self):
        """
        Checks if the conversion is allowed
        """
        return not self.forbid_preprocess or not self.information_loss()

    def need_conversion(self):
        """
        Checks if the conversion is needed
        """
        raise NotImplementedError

    def convert(self):
        """
        Performs conversion on image data, returns label with the exact parameters if the action was performed
        """
        raise NotImplementedError

class ConverterDepth(ConverterImage):
    """
    Converts pixel depth (ex: '8i' for uint8 = int 8 bits)
    """

    def __init__(self, input_desc, im):
        super(ConverterDepth, self).__init__(input_desc, im)
        dtype = input_desc.get('dtype', None)
        _, self.dst_depth = dtype.split('x')
        self.dst_dtype = None
        if self.dst_depth:
            self.dst_dtype = np.dtype(Image.DEPTH_DTYPE[self.dst_depth])

    def information_loss(self):
        if not self.dst_dtype:
            return False

        info_level = {
            np.dtype(np.uint8): 1,
            np.dtype(np.uint16): 2,
            np.dtype(np.uint32): 3,
            np.dtype(np.float16): 4,
            np.dtype(np.float32): 5
        }

        in_level = info_level.get(self.im.data.dtype)
        out_level = info_level[self.dst_dtype]

        if not in_level:
            return True

        return in_level > out_level

    def need_conversion(self):
        if not self.dst_dtype:
            return False
        return self.dst_dtype != self.im.data.dtype

    def convert(self):
        src_dtype = self.im.data.dtype
        self.im.convert_depth(self.dst_depth)
        return "depth {} --> {}".format(src_dtype, self.im.data.dtype)

class ConverterChannels(ConverterImage):
    """
    Converts number of channels of an image (ex: color to gray)
    """

    def __init__(self, input_desc, im):
        super(ConverterChannels, self).__init__(input_desc, im)
        dtype = input_desc.get('dtype', None)
        self.dst_channels, _ = dtype.split('x')
        if self.dst_channels:
            self.dst_channels = int(self.dst_channels)

    def information_loss(self):
        return self.im.get_channels() > self.dst_channels

    def need_conversion(self):
        return self.dst_channels and self.im.get_channels() != self.dst_channels

    def convert(self):
        src_channels = self.im.get_channels()
        self.im.convert_channels(self.dst_channels)
        return "#channels: {} --> {}".format(src_channels, self.dst_channels)

class ConverterCrop(ConverterImage):
    """
    Crops the image.
    """

    def __init__(self, input_desc, im, crop_info):
        super(ConverterCrop, self).__init__(input_desc, im)
        if not crop_info:
            self.x = -1
            return
        self.x = int(round(crop_info.get('x', -1)))
        self.y = int(round(crop_info.get('y', -1)))
        self.width = int(round(crop_info.get('width', -1)))
        self.height = int(round(crop_info.get('height', -1)))

    def information_loss(self):
        return (
            self.x > 0 and self.y > 0 and self.width >= 0 and self.height >= 0
            and self.x + self.width < self.im.width() and self.y + self.height < self.im.height()
        )

    def need_conversion(self):
        return self.information_loss()

    def convert(self):
        self.im.crop(x=self.x, y=self.y, width=self.width, height=self.height)
        return "crop at [{}, {}]".format(self.x, self.y)

class ConverterMaxPixels(ConverterImage):
    """
    Resizes the image if it's larger than max_pixels.
    """

    def __init__(self, input_desc, im):
        super(ConverterMaxPixels, self).__init__(input_desc, im)
        self.max_pixels = int(evaluate(input_desc.get('max_pixels')))

    def information_loss(self):
        return self.im.width() * self.im.height() > self.max_pixels

    def need_conversion(self):
        return self.information_loss()

    def convert(self):
        scaling_factor = self.max_pixels / (self.im.width() * self.im.height())
        dst_width = np.floor(math.sqrt(scaling_factor) * self.im.width())
        dst_height = np.floor(math.sqrt(scaling_factor) * self.im.height())
        self.im.resize(width=dst_width, height=dst_height)
        return "resized {0:.2f}%".format(scaling_factor * 100)

class ConverterEncoding(ConverterImage):
    """
    Changes the image encoding on save.
    """

    def __init__(self, input_desc, src_file, dst_file):
        super(ConverterEncoding, self).__init__(input_desc, None)
        self.src_type, _ = mimetypes.guess_type(src_file)
        self.dst_type, _ = mimetypes.guess_type(dst_file)

    def information_loss(self):
        return self.dst_type == 'image/jpeg'

    def need_conversion(self):
        return self.src_type != self.dst_type

    def convert(self):
        # nothing to do here, will be done when saving the image
        return "encoding: {} --> {}".format(self.src_type.split('/')[1], self.dst_type.split('/')[1])


def init_logging():
    """
    Initialize the error logs of the module.
    """
    logger = logging.getLogger("dispatcher")

    logger.setLevel(logging.DEBUG)
    handler = logging.StreamHandler()
    formatter = logging.Formatter(
        '%(asctime)s; [%(filename)s:%(lineno)s - %(funcName)20s() ] %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S')
    handler.setFormatter(formatter)

    logger.addHandler(handler)
    return logger

#!/usr/bin/python
# -*- coding:utf-8 -*-
"""
IPOL Conversion module, services to convert blobs.
"""

import logging
import os
import glob
import json
import sys
import math
import ConfigParser
import re
import base64
import mimetypes

import cherrypy
import numpy as np
from ipolutils.image.Image import Image
from ipolutils.video.Video import Video
from ipolutils.evaluator.evaluator import evaluate
from ipolutils.errors import IPOLTypeError
from errors import IPOLConvertInputError
from errors import IPOLCropInputError


def authenticate(func):
    """
    Wrapper to authenticate before using an exposed function
    """

    def authenticate_and_call(*args, **kwargs):
        """
        Invokes the wrapped function if authenticated
        """
        if not is_authorized_ip(cherrypy.request.remote.ip) and not (\
                        "X-Real-IP" in cherrypy.request.headers and is_authorized_ip(\
                    cherrypy.request.headers["X-Real-IP"])):
            error = {'status': 'KO', 'error': "Authentication Failed"}
            return json.dumps(error, indent=4)
        return func(*args, **kwargs)

    def is_authorized_ip(ip):
        """
        Validates the given IP
        """
        conversion = Conversion.get_instance()
        patterns = []
        # Creates the patterns  with regular expressions
        for authorized_pattern in conversion.authorized_patterns:
            patterns.append(re.compile(authorized_pattern.replace(".", r"\.").replace("*", "[0-9]*")))
        # Compare the IP with the patterns
        for pattern in patterns:
            if pattern.match(ip) is not None:
                return True
        return False

    return authenticate_and_call


class Conversion(object):
    """
    The Conversion module
    """

    instance = None

    @staticmethod
    def get_instance():
        """
        Singleton pattern
        """
        if Conversion.instance is None:
            Conversion.instance = Conversion()
        return Conversion.instance

    def __init__(self):
        """
        Constructor.
        """
        self.base_directory = os.getcwd()
        self.logs_dir = cherrypy.config.get("logs_dir")
        self.host_name = cherrypy.config.get("server.socket_host")
        self.config_common_dir = cherrypy.config.get("config_common_dir")
        # the run directory in shared_folder, realpath ensure normalization (security tests)
        self.run_dir = os.path.realpath(cherrypy.config.get("run_dir"))

        # Logs
        try:
            if not os.path.exists(self.logs_dir):
                os.makedirs(self.logs_dir)
            self.logger = self.init_logging()
        except Exception as ex:
            self.logger.exception("Failed to create log dir (using file dir). {}: {}".format(type(ex).__name__, str(ex)))

        # Security: authorized IPs
        self.authorized_patterns = self.read_authorized_patterns()

    def read_authorized_patterns(self):
        """
        Read from the IPs conf file
        """
        # Check if the config file exists
        authorized_patterns_path = os.path.join(self.config_common_dir, "authorized_patterns.conf")
        if not os.path.isfile(authorized_patterns_path):
            self.logger.error("read_authorized_patterns: Can't open {}".format(authorized_patterns_path))
            return []

        # Read config file
        try:
            cfg = ConfigParser.ConfigParser()
            cfg.read([authorized_patterns_path])
            patterns = []
            for item in cfg.items('Patterns'):
                patterns.append(item[1])
            return patterns
        except ConfigParser.Error:
            self.logger.exception("Bad format in {}".format(authorized_patterns_path))
            return []

    def init_logging(self):
        """
        Initialize the error logs of the module.
        """
        logger = logging.getLogger("conversion_log")

        logger.setLevel(logging.DEBUG)
        handler = logging.FileHandler(os.path.join(self.logs_dir, 'error.log'))
        formatter = logging.Formatter(
            '%(asctime)s; [%(filename)s:%(lineno)s - %(funcName)20s() ] %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S')
        handler.setFormatter(formatter)

        logger.addHandler(handler)
        return logger

    @staticmethod
    @cherrypy.expose
    def index():
        """
        Index page of the module.
        """
        return "Conversion module"

    @staticmethod
    @cherrypy.expose
    def default(attr):
        """
        Default method invoked when asked for non-existing service.
        """
        data = {'status': 'KO', "message": "Unknown service '{}'".format(attr)}
        return json.dumps(data)

    @staticmethod
    @cherrypy.expose
    def ping():
        """
        Ping service: answer with a PONG.
        """
        data = {'status': 'OK', "ping": "pong"}
        return json.dumps(data)

    @cherrypy.expose
    @authenticate
    def shutdown(self):
        """
        Shutdown the module.
        """
        data = {'status': 'KO'}
        try:
            cherrypy.engine.exit()
            data['status'] = 'OK'
        except Exception as ex:
            self.logger.exception("Failed to shutdown. {}: {}".format(type(ex).__name__, str(ex)))
            sys.exit(1)
        return json.dumps(data)

    @cherrypy.expose
    def convert(self, work_dir, inputs_description, crop_info=None):
        """
        Pre-process the input data in their working directory, according to the DDL specs and optional crop.
        """
        # For each file processed, return a code
        # -1: exception, response KO
        # 0:  No conversion needed or converted without loosing information
        # 1:  Conversion with information loss performed (ex: image resizing)
        # 2:  Conversion is not authorized by DDL
        # Info is a dictionary for each input, with return code and possible error
        info = {}
        # Global try, will stop at first exception in an input
        try:
            input_list = json.loads(inputs_description)
            if crop_info is not None:
                crop_info = json.loads(crop_info)

            for i, input_desc in enumerate(input_list):
                # before transformation success, default return code is failure
                info[i] = {'code': -1}
                # Search for a file for this input
                pattern = os.path.join(work_dir, 'input_{}'.format(i)) + '.*'
                input_files = glob.glob(pattern)
                # no file found, is this input optional?
                if len(input_files) < 1:
                    # optional is said by {"required": False}, absence of required field means: required
                    if not input_desc.get('required', True):
                        del info[i] # input[i] not present but not required, say nothing
                        continue
                    # An input is required and is absent, warn but no exception
                    info[i]['error'] = "Input required, but file not found in: {}".format(pattern)
                    continue
                input_file = input_files[0]
                # Is file too large for expected input in DDL?
                if input_desc.get('max_weight') and os.path.getsize(input_file) > input_desc.get('max_weight'):
                    info[i]['error'] = "File too large: {}".format(input_file)
                    continue
                # check input type
                input_type = input_desc['type']
                if input_desc.get('type') == 'image':
                    info[i]['code'], info[i]['modifications'] = self.convert_image(input_file, input_desc, crop_info)
                elif input_desc.get('type') == "data":
                    info[i]['code'] = self.add_ext_to_data(input_file, input_desc)
                elif input_desc.get('type') == "video":
                    info[i]['code'] = self.convert_video(input_file, input_desc)
                else:
                    info[i]['error'] = "{}: unknown input type".format(input_type)

        except (IPOLConvertInputError, IPOLCropInputError) as ex:
            self.logger.exception(ex)
            message = "Input #{}. {}".format(i, str(ex))
            return self.make_KO_response(message, work_dir)
        except IPOLTypeError as ex:
            message = "Input #{}. {}".format(i, str(ex))
            return self.make_KO_response(message, work_dir)
        except (OSError, IOError, RuntimeError) as ex:
            self.logger.exception(ex)
            message = "Input #{}. {}: {}".format(i, type(ex).__name__, str(ex))
            return self.make_KO_response(message, work_dir)
        except Exception as ex:
            self.logger.exception(ex)
            message = "Input #{}, unexpected error. {}: {}. file: {}".format(i, type(ex).__name__, str(ex), input_file)
            return self.make_KO_response(message, work_dir)
        # globally OK (no exception), but for some input, a return code could be -1
        return json.dumps({'status': 'OK', 'info': info})

    @staticmethod
    def make_KO_response(message, work_dir):
        """
        Return a JSON KO response with an error message.
        """
        response = {'status':'KO'}
        # do not send full path to client
        response['error'] = message.replace(work_dir, '<work_dir>')
        return json.dumps(response, indent=4)

    @staticmethod
    def convert_image(input_file, input_desc, crop_info=None):
        """
        Convert image if needed
        """
        # Image has to be always loaded to test width and size
        im = Image.load(input_file)
        dst_file = os.path.splitext(input_file)[0] + input_desc.get('ext')

        program = [
            # Color conversion, usually reducing to gray, sooner is better
            ConverterChannels(input_desc, im),
            # Depth conversion, usually reducing to 8 bits, sooner is better
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
                return 2, [] # Conversion needed but forbidden

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
            return 1, messages
        return 0, []

    @staticmethod
    def convert_video(input_file, input_desc):
        """
        Convert video
        """
        code = 0 # default return code, video not modified
        modifications = []
        video = Video(input_file)
        as_frames = input_desc.get('as_frames', None)
        max_frames = input_desc.get('max_frames')
        max_pixels = evaluate(input_desc.get('max_pixels'))
        if as_frames:
            code = video.extract_frames(max_frames=max_frames, max_pixels=max_pixels)
            modifications.append('extracted to frames')
        else:
            code = video.create_avi(max_frames=max_frames, max_pixels=max_pixels)
            modifications.append('AVI created')
            modifications.append('huffman encoded')

        return code, modifications

    @staticmethod
    def add_ext_to_data(input_file, input_desc):
        """
        Add the specified extension to the data file
        """
        ext = input_desc.get('ext')
        if ext is None:
            raise IPOLConvertInputError('DDL Error, missing extension field (to convert the input in the expected format by demo)')
        filename_no_ext, _ = os.path.splitext(input_file)
        input_with_extension = filename_no_ext + ext
        os.rename(input_file, input_with_extension)
        return 0 # return code

    @cherrypy.expose
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
            im = Image.decode(buf)
            im.convert_depth('8i')
            buf = im.encode('.png')
            data["img"] = base64.b64encode(buf) # reencode bytes
            data["status"] = "OK"
        except Exception:
            message = "TIFF to PNG for client, conversion failure."
            self.logger.exception(message)
        return json.dumps(data, indent=4)

class ConverterImage(object):
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
            self.dst_dtype = Image.get_dtype_by_depth(self.dst_depth)

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
        return info_level.get(self.im.dtype()) > info_level.get(self.dst_dtype)

    def need_conversion(self):
        if not self.dst_dtype:
            return False
        return self.dst_dtype != self.im.dtype()

    def convert(self):
        src_dtype = self.im.dtype()
        self.im.convert_depth(self.dst_depth)
        return "depth {} -> {}".format(src_dtype, self.im.dtype())

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
        return "#channels: {} -> {}".format(src_channels, self.dst_channels)

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
        self.max_pixels = int(evaluate(input_desc.get('max_pixels', -1)))

    def information_loss(self):
        return self.max_pixels > 0 and self.im.width() * self.im.height() > self.max_pixels

    def need_conversion(self):
        return self.information_loss()

    def convert(self):
        scaling_factor = self.max_pixels / float(self.im.width() * self.im.height())
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
        return "encoding: {} -> {}".format(self.src_type.split('/')[1], self.dst_type.split('/')[1])

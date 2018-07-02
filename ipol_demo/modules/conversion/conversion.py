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
import traceback

import cherrypy
from ipolutils.image.Image import Image
from ipolutils.video.Video import Video
from ipolutils.evaluator.evaluator import evaluate

from errors import IPOLConvertInputError
from errors import IPOLCropInputError
from ipolutils.errors import IPOLTypeError


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
        Consructor.
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
        # -1: exception, response KO.
        # 0:  No conversion needed.
        # 1:  Conversion performed (ex: image resizing).
        # 2:  Conversion is not authorized by DDL.
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
            ConverterChannels(im, input_desc),
            # Depth conversion, usually reducing to 8 bits, sooner is better
            ConverterDepth(im, input_desc),
            # Crop before reducing image to max_pixels (or the crop box will be outside of scope)
            ConverterCrop(im, crop_info),
            # Resize image if bigger than a max.
            ConverterMaxpixels(im, input_desc),
            # Re-encoding (ex: jpg > png)
            ConverterExtension(input_file, dst_file),
        ]
        # Is there an operation to do ?
        todo = False
        for task in program:
            if task.todo:
                todo = True
        # Nothing to do, ensure expected extension (.jpe > .jpeg; .tif > .tiff)
        if not todo:
            if input_file != dst_file:
                os.rename(input_file, dst_file)
            return 0, []
        # Something to do, but forbidden, ensure expected extension
        if input_desc.get("forbid_preprocess", False):
            if input_file != dst_file:
                os.rename(input_file, dst_file)
            return 2, [] # Conversion needed but forbidden
        # do work
        modifications = []
        for task in program:
            if task.todo:
                task.do_convert()
                modifications.append(task.label)
        # do not forget to write modifications
        im.write(dst_file)
        return 1, modifications

    @staticmethod
    def convert_video(input_file, input_desc):
        """
        Convert video according to DDL specification
        """
        code = 0 # default return code, video not modified
        modifications = []
        video = Video(input_file)
        as_frames = input_desc.get('as_frames', None)
        max_frames = input_desc.get('max_frames')
        max_pixels = evaluate(input_desc.get('max_pixels'))
        if as_frames:
            video.extract_frames(max_frames=max_frames, max_pixels=max_pixels)
            code = 1
            modifications.append('extracted to frames')
        else:
            video.create_avi(max_frames=max_frames, max_pixels=max_pixels)
            code = 1
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
            print message
            print traceback.format_exc()
            self.logger.exception(message)
        return json.dumps(data, indent=4)

class ConverterImage(object):
    """
    Interface of a conversion task for an image.
    """
    todo = False
    done = False
    def _do(self):
        """
        The specific action of the converter, with parameters prepared by the constructor.
        """
        raise NotImplementedError
    def do_convert(self):
        """
        Do conversion if allowed.
        """
        if not self.todo:
            return self.done
        self._do()
        self.done = True
        return self.done

class ConverterDepth(ConverterImage):
    """
    Converts image depth by pixel (ex: 'i8' for uint8, int 8 bits)
    """
    label = "depth"
    def __init__(self, im, input_desc):
        dtype = input_desc.get('dtype')
        if not dtype:
            return
        _, depth = dtype.split('x')
        if im.check_depth(depth):
            return
        self.im = im
        self.depth = depth
        self.todo = True
    def _do(self):
        self.im.convert_depth(self.depth)

class ConverterChannels(ConverterImage):
    """
    Converts number of channels of an image (ex: color to gray)
    """
    label = "colors"
    def __init__(self, im, input_desc):
        dtype = input_desc.get('dtype')
        if not dtype:
            return
        channels, _ = dtype.split('x')
        if im.check_channels(channels):
            return
        self.im = im
        self.channels = channels
        self.todo = True
    def _do(self):
        self.im.convert_channels(self.channels)

class ConverterCrop(ConverterImage):
    """
    Crops an image according to a json specification.
    """
    label = "crop"
    def __init__(self, im, crop_info):
        if crop_info is None:
            return
        self.im = im
        self.x = int(round(crop_info.get('x')))
        self.y = int(round(crop_info.get('y')))
        self.width = int(round(crop_info.get('width')))
        self.height = int(round(crop_info.get('height')))
        self.todo = True
    def _do(self):
        self.im.crop(x=self.x, y=self.y, width=self.width, height=self.height)

class ConverterMaxpixels(ConverterImage):
    """
    Resizes image if bigger than max_pixels.
    """
    label = "resize"
    def __init__(self, im, input_desc):
        max_pixels = input_desc.get('max_pixels')
        if max_pixels is None:
            return
        max_pixels = evaluate(max_pixels)
        if max_pixels <= 0:
            return
        input_pixels = im.width() * im.height()
        if input_pixels < max_pixels:
            return
        self.im = im
        self.fxy = math.sqrt(float(max_pixels - 1) / float(input_pixels))
        self.todo = True
    def _do(self):
        self.im.resize(fx=self.fxy, fy=self.fxy)

class ConverterExtension(ConverterImage):
    """
    Change extension
    """
    label = "extension"
    def __init__(self, src_file, dst_file):
        src_type, _ = mimetypes.guess_type(src_file)
        dst_type, _ = mimetypes.guess_type(dst_file)
        if src_type == dst_type:
            return
        self.todo = True
    def _do(self):
        # new encoding needed (ex: jpeg > png), according to the input and destination extension
        # nothing to do here, will be done by aving image
        pass

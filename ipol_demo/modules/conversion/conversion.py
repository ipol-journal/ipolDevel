#!/usr/bin/python
# -*- coding:utf-8 -*-
"""
Conversion: perform any conversions needed (or leave the data as it is, if not needed)

All exposed WS return JSON with a status OK/KO, along with an error
description if that's the case.
"""

import logging
import os
import glob
import json
import sys
import math
import ConfigParser
import re
import tempfile
import base64
import mimetypes
from libtiff import TIFF
import png
from PIL import Image
import cherrypy
from Tools.evaluator import evaluate
from errors import IPOLConvertInputError
from errors import IPOLCropInputError

sys.path.append(os.path.join(os.path.dirname(__file__), 'lib'))
from IPOLImage import IPOLImage


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
            return json.dumps(error)
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
        Initialize Conversion class
        """
        self.base_directory = os.getcwd()
        self.logs_dir = cherrypy.config.get("logs_dir")
        self.host_name = cherrypy.config.get("server.socket_host")
        self.config_common_dir = cherrypy.config.get("config_common_dir")

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
            self.error_log("read_authorized_patterns",
                           "Can't open {}".format(authorized_patterns_path))
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

    def error_log(self, function_name, error):
        """
        Write an error log in the logs_dir defined in archive.conf
        """
        error_string = function_name + ": " + error
        self.logger.error(error_string)

    @staticmethod
    @cherrypy.expose
    def index():
        """
        index of the module.
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
        # inputs_desc seems more consistent accross modules, should be changed here and in core.py and test.py
        """
        Pre-process the input data in their working directory, according to the DDL specs and optional crop.
        For each file processed, return a code
        -1: exception, response KO
        0:  No conversion needed, returned by convert_image()
        1:  Conversion performed (ex: image resizing), returned by convert_image()
        2:  Conversion is not authorized by ddl, returned by convert_image()
        """
        # Info is a dictionary for each input, with return code and possible error
        info = {}
        # Global try, will stop at first exception in an input
        try:
            inputs_desc = json.loads(inputs_description)
            if crop_info is not None:
                crop_info = json.loads(crop_info)
            # loop on ddl inputs
            inputs_len = len(inputs_desc)
            for i in range(inputs_len):
                input_desc = inputs_desc[i]
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
                if input_type not in ['image', 'data', 'video']:
                    info[i]['error'] = "{}: unknown input type".format(input_type)
                    continue
                # do conversion
                if input_desc.get('type') == 'image':
                    info[i]['code'] = self.convert_image(input_file, input_desc, crop_info)
                elif input_desc.get('type') == "data":
                    info[i]['code'] = self.add_ext_to_data(input_file, input_desc)
                elif input_desc.get('type') == "video":
                    info[i]['code'] = 1

        except IPOLConvertInputError as ex:
            message = "Input #{}. {}".format(i, str(ex))
            return self.make_KO_response(message, work_dir)
        except IPOLCropInputError as ex:
            message = "Input #{}. {}".format(i, str(ex))
            return self.make_KO_response(message, work_dir)
        except (OSError, IOError) as ex:
            message = "Input #{}. {}: {}".format(i, type(ex).__name__, str(ex))
            return self.make_KO_response(message, work_dir)
        except Exception as ex:
            message = "Input #{}, unexpected error. {}: {}. file: {}".format(i, type(ex).__name__, str(ex), input_file)
            return self.make_KO_response(message, work_dir)
        # globally OK (no exception), but for some input, a return code could be -1
        return json.dumps({'status': 'OK', 'info': info})

    def make_KO_response(self, message, work_dir):
        """
        Return a JSON KO response with an error message.
        """
        response = {'status':'KO'}
        self.logger.exception(message)
        # do not send full path to client
        response['error'] = message.replace(work_dir, '<work_dir>')
        print json.dumps(response, indent=2, ensure_ascii=False)
        print message
        return json.dumps(response)

    def convert_image(self, input_file, input_desc, crop_info=None):
        """
        Convert image if needed
        """
        code = 0
        im = Image.open(input_file)
        input_file_type, _ = mimetypes.guess_type(input_file)
        input_desc_type, _ = mimetypes.guess_type("dummy" + input_desc.get('ext'))
        if input_file_type != input_desc_type:
            # Change ext needed
            self.change_image_ext(input_file, input_desc.get('ext'))
            input_file = os.path.splitext(input_file)[0] + input_desc.get('ext')
            code = 1

        if crop_info is not None:
            # Crop is needed
            self.crop_image(input_file, crop_info)
            im = Image.open(input_file)
            code = 1

        if im.size[0] * im.size[1] > evaluate(input_desc.get('max_pixels')):
            # Resize needed
            if input_desc.get("forbid_preprocess", False):
                return 2 # Conversion needed but forbidden
            self.resize_image(input_file, evaluate(input_desc.get('max_pixels')))
            code = 1

        if self.needs_dtype_convert(im, input_desc):
            self.change_image_dtype(input_file, input_desc.get('dtype'))
            code = 1
        return code

    @staticmethod
    def add_ext_to_data(input_file, input_desc):
        """
        Add the specified extension to the data file
        """
        ext = input_desc.get('ext')
        if ext is None: # Why not an IPOLDDL error or something like that ?
            raise IPOLConvertInputError('DDL Error, missing extension field (to convert the input in the expected format by demo)')
        filename_no_ext, _ = os.path.splitext(input_file)
        input_with_extension = filename_no_ext + ext
        os.rename(input_file, input_with_extension)
        return 0

    @staticmethod
    def change_image_ext(input_file, ext):
        """
        Convert the image to the required extension
        """
        try:
            im = Image.open(input_file)
            im.save(os.path.splitext(input_file)[0] + ext)
        except Exception as ex:
            # the exceptions will always provide full path of the file, no need to repeat
            raise IPOLConvertInputError("Image format conversion error. {}: {}".format(type(ex).__name__, str(ex)))

    @staticmethod
    def crop_image(input_file, crop_info):
        """
        Crop an image with info provide by client
        """
        try:
            x0 = int(round(crop_info.get('x')))
            y0 = int(round(crop_info.get('y')))
            x1 = int(round(crop_info.get('x') + crop_info.get('width')))
            y1 = int(round(crop_info.get('y') + crop_info.get('height')))
            im = Image.open(input_file)
            im.crop((x0, y0, x1, y1)).save(input_file)
        except Exception as ex:
            raise IPOLCropInputError("Image crop error. {}: {}".format(type(ex).__name__, str(ex)))

    @staticmethod
    def resize_image(input_file, max_pixels):
        """
        Resize the image
        """
        try:
            im = Image.open(input_file)
            scale_factor = math.sqrt(im.size[0] * im.size[1] / max_pixels)
            new_width = int(round(im.width / scale_factor))
            new_height = int(round(im.height / scale_factor))
            im.resize((new_width, new_height), Image.ANTIALIAS).save(input_file)
        except Exception as ex:
            # Pillow will always provide a full path of the file
            print ex
            raise IPOLConvertInputError('Image resize error. {}: {}'.format(type(ex).__name__, str(ex)))


    @staticmethod
    def needs_dtype_convert(im, input_info):
        """
        checks if input image needs conversion
        """
        mode_kw = {'1x1i': '1',
                   '1x1': '1',
                   '1x8i': 'L',
                   '1x8': 'L',
                   '3x8i': 'RGB',
                   '3x8': 'RGB'}
        # check mode
        if not input_info.get('dtype'):
            return False

        return im.mode != mode_kw.get(input_info.get('dtype'))

    @staticmethod
    def change_image_dtype(input_file, mode):
        """
        Convert the image pixel array to another numeric type
        """
        im = Image.open(input_file)
        try:
            print mode
            # TODO handle other modes (binary, 16bits, 32bits int/float)
            mode_kw = {'1x1i': '1',
                       '1x1': '1',
                       '1x8i': 'L',
                       '1x8': 'L',
                       '3x8i': 'RGB',
                       '3x8': 'RGB'}[mode]
        except KeyError:
            raise KeyError('Invalid mode {}'.format(mode))
        if im.mode != mode_kw:
            im.convert(mode_kw).save(input_file)

    @cherrypy.expose
    def convert_tiff_to_png(self, img):
        """
        Converts the input TIFF to PNG.
        This is used by the web interface for visualization purposes
        """
        data = {"status": "KO"}
        try:
            im = IPOLImage(None) # create encoder without file
            im.decode(base64.b64decode(img)) # load data in OpenCV
            data["img"] = base64.b64encode(im.bytes('png')) # get encoded bytes
            data["status"] = "OK"
        except Exception as ex:
            print "Failed to convert image from TIFF to PNG", ex
            self.logger.exception("Failed to convert image from TIFF to PNG")
        return json.dumps(data)

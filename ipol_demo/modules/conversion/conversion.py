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
import base64
import mimetypes
import traceback
import cherrypy
import cv2
import numpy as np
from ipolimage import Image
from ipolevaluator import evaluate

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
            return self.make_KO_response(message, work_dir, ex)
        except IPOLCropInputError as ex:
            message = "Input #{}. {}".format(i, str(ex))
            return self.make_KO_response(message, work_dir, ex)
        except (OSError, IOError) as ex:
            message = "Input #{}. {}: {}".format(i, type(ex).__name__, str(ex))
            return self.make_KO_response(message, work_dir, ex)
        except Exception as ex:
            message = "Input #{}, unexpected error. {}: {}. file: {}".format(i, type(ex).__name__, str(ex), input_file)
            return self.make_KO_response(message, work_dir, ex)
        # globally OK (no exception), but for some input, a return code could be -1
        return json.dumps({'status': 'OK', 'info': info})

    def make_KO_response(self, message, work_dir, ex):
        """
        Return a JSON KO response with an error message.
        """
        response = {'status':'KO'}
        self.logger.exception(message)
        # do not send full path to client
        response['error'] = message.replace(work_dir, '<work_dir>')
        print(traceback.format_exc())
        print json.dumps(response, indent=2, ensure_ascii=False)
        print message
        return json.dumps(response)

    def convert_image(self, input_file, input_desc, crop_info=None):
        """
        Convert image if needed
        """
        # Method could be a function (no-self-use)
        code = 0
        # Image has to be always loaded to test width and size
        im = Image(input_file)
        # convert image matrix if needed (before resize)
        if im.convert(input_desc.get('dtype')):
            code = 1

        # crop before reducing image to max_pixels (or the crop box will be outside of scope)
        if crop_info is not None:
            # Crop is needed
            x = int(round(crop_info.get('x')))
            y = int(round(crop_info.get('y')))
            width = int(round(crop_info.get('width')))
            height = int(round(crop_info.get('height')))
            im.crop(x=x, y=y, width=width, height=height)
            code = 1

        max_pixels = evaluate(input_desc.get('max_pixels'))
        input_pixels = im.width * im.height
        if input_pixels > max_pixels:
            fxy = math.sqrt(float(max_pixels - 1) / float(input_pixels))
            im.resize(fx=fxy, fy=fxy)
            code = 1

        input_file_type, _ = mimetypes.guess_type(input_file)
        input_desc_type, _ = mimetypes.guess_type("dummy" + input_desc.get('ext'))
        input_path, input_ext = os.path.splitext(input_file)
        dst_file = input_path + input_desc.get('ext')
        # new encoding needed, according to the input and destination extension
        if input_file_type != input_desc_type:
            # will be done by im.write() below
            code = 1
        # same encoding,
        elif code == 1:
            pass
        # no conversion needed but not the expected extension (.jpe > .jpeg; .tif > .tiff)
        else:
            os.rename(input_file, dst_file)
        if code == 1: # image data have been modified, save it
            if input_desc.get("forbid_preprocess", False):
                return 2 # Conversion needed but forbidden
            im.write(dst_file, force=True) # force overwrites if needed
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
            cvim = cv2.imdecode(np.fromstring(buf, dtype=np.uint8), cv2.IMREAD_ANYCOLOR)
            if False and cvim is not None:
                _, buf = cv2.imencode(".png", cvim) # [cv2.IMWRITE_PNG_COMPRESSION, 9]
            else:
                ipim = Image(None)
                ipim.decode(buf)
                ipim.convert("x8i")
                buf = ipim.encode('.png')
            data["img"] = base64.b64encode(buf) # reencode bytes
            data["status"] = "OK"
        except Exception as ex:
            mess = "TIFF to PNG for client, conversion failure."
            print mess
            print(traceback.format_exc())
            self.logger.exception(mess)
        return json.dumps(data)

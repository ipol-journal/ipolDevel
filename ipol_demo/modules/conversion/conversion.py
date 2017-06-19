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
import shutil
import sys
import math
import ConfigParser
import re
from PIL import Image
import cherrypy
from Tools.evaluator import evaluate
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
        if not is_authorized_ip(cherrypy.request.remote.ip) and not (
                "X-Real-IP" in cherrypy.request.headers and is_authorized_ip(cherrypy.request.headers["X-Real-IP"])):
            error = {"status": "KO", "error": "Authentication Failed"}
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
        except Exception as e:
            self.logger.exception("Failed to create log dir (using file dir) : {}".format(e))

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
        data = {"status": "KO", "message": "Unknown service '{}'".format(attr)}
        return json.dumps(data)

    @staticmethod
    @cherrypy.expose
    def ping():
        """
        Ping pong.
        """
        data = {"status": "OK", "ping": "pong"}
        return json.dumps(data)

    @cherrypy.expose
    @authenticate
    def shutdown(self):
        """
        Shutdown the module.
        """
        data = {"status": "KO"}
        try:
            cherrypy.engine.exit()
            data["status"] = "OK"
        except Exception as ex:
            self.logger.error("Failed to shutdown : {}".format(ex))
            sys.exit(1)
        return json.dumps(data)

    @cherrypy.expose
    def convert(self, work_dir, inputs_description, crop_info=None):
        """
        pre-process the input data
        -1: error
        0:  No conversion needed
        1:  Conversion performed (ex: image resizing)
        2:  Conversion is not authorized
        """
        # [TODO] Check if conversion is authorized (not yet in the DDL)
        data = {"status": "OK"}
        input_files = None
        try:
            inputs_description = json.loads(inputs_description)

            if crop_info is not None:
                crop_info = json.loads(crop_info)

            for i in range(len(inputs_description)):
                input_desc = inputs_description[i]
                input_name = os.path.join(work_dir, 'input_{}'.format(i))
                input_files = glob.glob(input_name + '.*')

                if len(input_files) != 1:
                    if input_desc.get('required'):
                        # Problem here.
                        data['status'] = 'KO'
                        data['error'] = "Wrong number of inputs for an image"
                        data['code'] = -1
                        return json.dumps(data)
                    else:
                        # Optional input missing, end of inputs
                        data['status'] = 'OK'
                        data['code'] = 0
                        return json.dumps(data)
                if os.path.getsize(input_files[0]) > input_desc.get('max_weight'):
                    # Input is too large
                    data['status'] = 'KO'
                    data['error'] = "File too large"
                    data['code'] = -1
                    return json.dumps(data)

                if input_desc.get('type') == 'image':
                    code = self.convert_image(input_files[0], input_desc,crop_info)
                    data['status'] = 'OK'
                    data['code'] = code
                    return json.dumps(data)

                elif input_desc.get('type') != "data":
                    code = self.convert_data()
                    data['status'] = 'OK'
                    data['code'] = code
                    return json.dumps(data)

                else:
                    # [todo] Add more types
                    data['status'] = 'KO'
                    data['code'] = -1
                    data['error'] = "Unknown input type"
                    return json.dumps(data)

        except IOError as ex:
            error_msg = "Failed to read input {}. Error: {}".format(input_files[0], str(ex))
            self.logger.error(error_msg)
            print error_msg
            data['status'] = 'KO'
            data['code'] = -1
            data['error'] = error_msg
            return json.dumps(data)
        except IPOLConvertInputError as ex:
            error_msg = "Failed to convert the input {}. Error: {}".format(input_files[0], str(ex))
            self.logger.error(error_msg)
            print error_msg
            data['status'] = 'KO'
            data['code'] = -1
            data['error'] = error_msg
            return json.dumps(data)
        except IPOLCropInputError as ex:
            error_msg = "Failed to crop the input {}. Error: {}".format(input_files[0], str(ex))
            self.logger.error(error_msg)
            print error_msg
            data['status'] = 'KO'
            data['code'] = -1
            data['error'] = error_msg
            return json.dumps(data)
        except Exception as ex:
            error_msg = "Unhandled exception in the convert. Error: {}".format(str(ex))
            self.logger.error(error_msg)
            print error_msg
            data['status'] = 'KO'
            data['code'] = -1
            data['error'] = error_msg
            return json.dumps(data)

    def convert_image(self, input_file, input_desc, crop_info=None):
        """
        Convert image if needed
        """
        code = 0
        im = Image.open(input_file)
        if os.path.splitext(input_file)[1] != input_desc.get('ext'):
            # Change ext needed
            self.change_ext(input_file, input_desc.get('ext'))
            code = 1
        if im.size[0] * im.size[1] > evaluate(input_desc.get('max_pixels')):
            # Resize needed
            self.resize_image(input_file, evaluate(input_desc.get('max_pixels')))
            code = 1
        if crop_info is not None:
            # Crop is needed
            self.crop_image(input_file, crop_info)
            code = 1
        return code

    def convert_data(self):
        """
        Convert data if needed
        """
        # [TODO] is really needed to convert data?
        return 0

    @staticmethod
    def change_ext(input_file, ext):
        """
        Convert the image to the required extension
        """
        try:
            im = Image.open(input_file)
            im.save(os.path.splitext(input_file)[0] + ext)
        except Exception as ex:
            raise IPOLConvertInputError(ex)

    @staticmethod
    def crop_image(input_file, crop_info):
        """
        Crop the image
        """
        try:
            x0 = int(round(crop_info['x']))
            y0 = int(round(crop_info['y']))
            x1 = int(round(crop_info['x'] + crop_info['w']))
            y1 = int(round(crop_info['y'] + crop_info['h']))
            im = Image.open(input_file)
            im.crop((x0, y0, x1, y1)).save(input_file)
        except Exception as ex:
            raise IPOLCropInputError(ex)

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
            print ex
            raise IPOLConvertInputError(ex)

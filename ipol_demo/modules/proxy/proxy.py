#!/usr/bin/python
# -*- coding:utf-8 -*-

# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.


"""
This module is a proxy for the other modules
"""

import sys
import errno
import logging
import json
import cherrypy
import os
import os.path
import urllib
import xml.etree.ElementTree as ET

class Proxy(object):
    """
    This class implements a proxy for the other modules.
    """
            
#####
# initialization and static methods.
#####
    @staticmethod
    def mkdir_p(path):
        """
        Implement the UNIX shell command "mkdir -p"
        with given path as parameter.
        """
        try:
            os.makedirs(path)
        except OSError as exc:
            if exc.errno == errno.EEXIST and os.path.isdir(path):
                pass
            else:
                raise
                
                
    @staticmethod
    def get_dict_modules():
        """
        Return a dictionary of the differents IPOL modules as keys, and
        another dictionary as value, containing several keys: a url,
        the server where the module is, the directory of the module on the
        server, and a list of strings representing the commands available
        to the module.
        """
        dict_modules = {}
        tree = ET.parse('../config_common/modules.xml')
        root = tree.getroot()
        
        for module in root.findall('module'):
            dict_tmp = {}
            list_tmp = []

            for command in module.findall('command'):
                list_tmp.append(command.text)

            list_tmp.append("info")
            dict_tmp["url"] = module.find('url').text
            dict_tmp["server"] = module.find('server').text
            dict_tmp["path"] = module.find('path').text
            dict_tmp["commands"] = list_tmp
            dict_modules[module.get('name')] = dict_tmp
            
        return dict_modules
    
    def init_logging(self):
        """
        Initialize the error logs of the module.
        """
        logger = logging.getLogger("archive_log")
        logger.setLevel(logging.ERROR)
        handler = logging.FileHandler(os.path.join(self.logs_dir,
                                                   'error.log'))
        formatter = logging.Formatter('%(asctime)s ERROR in %(message)s',
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
        
        
    def __init__(self, option):
        cherrypy.config.update("./proxy.conf")
        self.logs_dir = cherrypy.config.get("logs_dir")
        self.mkdir_p(self.logs_dir)
        self.logger = self.init_logging()
        self.dict_modules = self.get_dict_modules()

#####
# web utilities
#####

    @cherrypy.expose
    def ping(self):
        """
        Ping pong.
        :rtype: JSON formatted string
        """
        data = {}
        data["status"] = "OK"
        data["ping"] = "pong"
        return json.dumps(data)

    @cherrypy.expose
    def shutdown(self):
        """
        Shutdown the module.
        """
        data = {}
        data["status"] = "KO"
        try:
            cherrypy.engine.exit()
            data["status"] = "OK"
        except Exception as ex:
            self.error_log("shutdown", str(ex))
        return json.dumps(data)
      
    @cherrypy.expose
    def index(self, **kwargs):
        """
        Index for the archive. Dispatch a request to the corresponding module
        """
        url=kwargs.copy()
        error = {}
        error["status"] = "KO"
        error_message="ERROR "
        
        url_size = len(url)
        error['url_parameters'] = url_size
        
        # Check Url Parameters
        if url_size == 0:
            ex = "url without any parameters"
            self.error_log("index", ex)
            return json.dumps(error)
        
        # Check if module is specified
        if 'module' not in url:
           error["code"] = -1
           ex = "url without module"
           self.error_log("index", ex)
           return json.dumps(error)

        module = url['module']
        
        # Check if module is valid
        if module not in self.dict_modules.keys():
            error["code"] = -2
            if module == "":
               ex = " module in url is empty"
            else:
               ex = module + " does not appear in the XML file in the proxy "
            
            self.error_log("index", ex)
            return json.dumps(error)
        
        del url['module']
        
        # Check if service is specified
        if 'service' not in url:
            error["code"] = -3
            ex = "Not WS in the url"
            self.error_log("index", ex)
            return json.dumps(error)
		
        service=url['service']
        
        del url['service']
        
        # Build request URL
        params=""
        if len(url) > 0:
           params = "?" + urllib.urlencode(url)
        
        # Request module for service   
        try:
            call_service = urllib.urlopen(self.dict_modules[module]["url"] + service + params).read()
        except Exception as ex:
            error["code"] = -4
            self.error_log("index", "Module '" + module + "' communication error; " + str(ex))
            return json.dumps(error)
        
        # Return module response
        try:
            return json.dumps(json.loads(call_service))
        except Exception as ex:
            error["code"] = -5
            self.error_log("index", str(ex))
            return json.dumps(error)
        
        

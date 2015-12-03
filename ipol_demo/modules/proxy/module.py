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
This module is a proxy for the modules
"""

import sys
import errno
import logging
import json
import cherrypy
import os
import os.path
import urllib
import urllib2

import xml.etree.ElementTree as ET

class Proxy(object):
    """
    This class implement a proxy for the modules.
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
        
    def root_index(name):
        return "Hello, %s!" % name


    @cherrypy.expose
    def index(self, **kwargs):
        """
        Index for the archive. Redirect a petition for the correct module (if it is found)
        """
        url=kwargs.copy()
        error = {}
        error["status"] = "KO"
        error_message="ERROR "
        
        url_size = len(url)
        error['url_parameters'] = url_size
        
        if url_size == 0:
		   ex = "url without any information"
		   print (error_message + ex)
		   self.error_log("index", ex)
		   return json.dumps(error)
        
        if 'module' not in url:
           error["cout"] = "0"
           ex = "url without module"
           print (error_message + ex)
           self.error_log("index", ex)
           return json.dumps(error)
		
        module=url['module']
        
        if module not in self.dict_modules.keys():
            error["cout"] = "1"
            if module == "":
               ex = " module in url is empty"
            else:
               ex = module + " does not appear in the XML file in the proxy "
            
            print (error_message + ex)
            self.error_log("index", ex)
            return json.dumps(error)
        
        del url['module']
        
        if 'service' not in url:
            error["cout"] = "2"
            ex = "Not WS in the url"
            print (error_message + ex)
            self.error_log("index", ex)
            return json.dumps(error)
		
        service=url['service']
        
        del url['service']
        
        params=""
        if len(url) > 0:
           params = "?" + urllib.urlencode(url)
           
        call_service = urllib.urlopen(self.dict_modules[module]["url"] + service + params).read()
        print call_service
        
        try:
            return json.dumps(json.loads(call_service))
        except Exception as ex:
            error["cout"] = "3"
            self.error_log("index", str(ex))
            return json.dumps(error)
        
        

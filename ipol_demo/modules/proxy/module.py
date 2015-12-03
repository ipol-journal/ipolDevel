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

    def __init__(self, option):
        self.dict_modules = self.get_dict_modules()

    def root_index(name):
        return "Hello, %s!" % name

    @cherrypy.expose
    def index(self):
        """
        Index for the archive.
        """
        return json.dumps(self.dict_modules)

    def check_parameter_input(self, module, args_array):
        """
        """  
        data={}
        data['fail'] = "TRUE"
        array_size = len(args_array)
        data['n_parameters'] = array_size
        
        if array_size == 0:
		   print "There is not parameters"
		   return data
        elif module not in self.dict_modules.keys():
             data['module'] = "No module"
             print "MODULE: " + module + " does not appear in proxy xml file"
             return data
        elif 'service' not in args_array:
             data['param_setting'] = 'Bad parameter setting'
             return data
        
        service=args_array['service']
        if service not in self.dict_modules[module]["commands"]:
           data['WS'] = service + " unavailable"
           print ("WS " + service + " unavailable for module" + module)
           return data
        
        return service
        
    def execute_service(self, module, kwargs):
        """
        """
        service = self.check_parameter_input(module , kwargs)
        
        if 'fail' in service:
            return service
            
        url = self.dict_modules[module]["url"]
        call_service = urllib.urlopen(url + service).read()
        return json.loads(call_service)
        
    @cherrypy.expose
    def archive(self, **kwargs):
        """
        Execute service in archive module
        """
        module="archive"
        return json.dumps(self.execute_service(module, kwargs))        
    
    @cherrypy.expose
    def blobs(self, **kwargs):
        """
        Execute service in blobs module
        """
        module="blobs"
        return json.dumps(self.execute_service(module, kwargs))        
    
    @cherrypy.expose
    def demoinfo(self, **kwargs):
        """
        Execute service in blobs module
        """
        module="demoinfo"
        return json.dumps(self.execute_service(module, kwargs))

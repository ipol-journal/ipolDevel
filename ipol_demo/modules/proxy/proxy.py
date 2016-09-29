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

import requests


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
        logger = logging.getLogger("proxy_log")
        logger.setLevel(logging.ERROR)
        handler = logging.FileHandler(os.path.join(self.logs_dir, 'error.log'))
        formatter = logging.Formatter('%(asctime)s ERROR in %(message)s', datefmt='%Y-%m-%d %H:%M:%S')
        handler.setFormatter(formatter)
        logger.addHandler(handler)
        return logger

    def error_log(self, function_name, error):
        """
        Write an error log in the logs_dir defined in proxy.conf
        """
        error_string = function_name + ": " + error
        self.logger.error(error_string)


    def __init__(self):
        self.logs_dir = cherrypy.config.get("logs_dir")
        self.mkdir_p(self.logs_dir)
        self.logger = self.init_logging()
        self.dict_modules = self.get_dict_modules()
    
    
    @cherrypy.expose
    def default(self, attr):
        """
        Default method invoked when asked for non-existing service.
        """
        data = {}
        data["status"] = "KO"
        data["message"] = "Unknown service '{}'".format(attr)
        return json.dumps(data)


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
        Index for the proxy. Dispatch a request to the corresponding module
        """
        url=kwargs.copy()
        error = {}
        error["status"] = "KO"
        error_message="ERROR "

        url_size = len(url)
        error['url_parameters'] = url_size

        # Check Url Parameters
        if url_size == 0:
            error["code"] = -1
            ex = "url without any parameters"
            self.error_log("index", ex)
            return json.dumps(error)

        # Check if module is specified
        if 'module' not in url:
            error["code"] = -2
            ex = "url without module"
            self.error_log("index", ex)
            return json.dumps(error)

        module = url['module']

        # Check if module is valid
        if module not in self.dict_modules.keys():
            error["code"] = -3
            if module == "":
                ex = " module in url is empty"
            else:
                ex = module + " does not appear in the XML file in the proxy "

            self.error_log("index", ex)
            return json.dumps(error)

        del url['module']

        # Check if service is specified
        if 'service' not in url:
            error["code"] = -4
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
            error["code"] = -5
            self.error_log("index", "Module '" + module + "' communication error; " + str(ex))
            return json.dumps(error)

        # Return module response
        try:
            return json.dumps(json.loads(call_service))
        except Exception as ex:
            error["code"] = -6
            self.error_log("index", str(ex))
            return json.dumps(error)


    @cherrypy.expose
    def proxy_service_call(self, module, service, servicehttpmethod=None, 
                           params=None, jsonparam=None):
        """

        I need to be able to call proxy in POST, and get it to call the WS depending
        of an htlm method arg (get,post...)

        this function must be transparent, so it will return the WS result as it is or an  error_json {status, code}

        this function uses requests to execute WS calls
        http://docs.python-requests.org/en/latest/user/quickstart/
        Instead of encoding the dict yourself, you can also pass it directly using the json parameter (added in version 2.4.2) and it will be encoded automatically:
        """
        error_json = {}
        error_json["status"] = "KO"
                
        #validate params and set default params
        try:

            if module is None:
                error_json["code"] = -2
                self.error_log(proxy_service_call,"no module")
                return json.dumps(error_json)
            else:
                # Check if module is valid
                if module not in self.dict_modules.keys():
                    error_json["code"] = -3
                    if module == "":
                        error_msg = " module in url is empty"
                    else:
                        error_msg = module + " does not appear in the XML file in the proxy "

                    self.error_log("proxy_service_call", error_msg)
                    return json.dumps(error_json)

            if service is None:
                error_json["code"] = -4
                error_msg = "Not WS in the url"
                self.error_log("proxy_service_call", error_msg)
                return json.dumps(error_json)


            if servicehttpmethod is None:
                servicehttpmethod='GET'

            if params:
                #request call needs a dict for params
                try:
                    params=json.loads(params)
                except Exception:
                    error_msg=" Cannot recover params to dict for request call"
                    print error_msg
                    error_json["code"] = -3
                    self.error_log("proxy_service_call", error_msg)
                    return json.dumps(error_json)

        except Exception as e:
            error_msg="no params e: {0}".format(e)
            self.logger.exception(error_msg)
            error_json["code"] = -1
            return json.dumps(error_json)

        #build WS url
        ws_url= self.dict_modules[module]["url"]+ service

        # WS call
        try:
            if servicehttpmethod == 'GET':

                response = requests.get(ws_url, params = params)

            elif servicehttpmethod =='POST':

                response = requests.post(   ws_url, 
                                            params = params, 
                                            json = jsonparam)
            else:

                error_msg = " Invalid servicehttpmethod, only GET and POST allowed at the present moment"
                print error_msg
                error_json["code"] = -3
                self.error_log("proxy_service_call", error_msg)
                return json.dumps(error_json)

            result = response.content
            
            # validate that json returned by WS is valid
            try:
                json_object = json.loads(result)
            except Exception:
                error_msg=" Invalid JSON returned"
                print error_msg
                error_json["code"] = -6
                self.error_log("proxy_service_call", error_msg)
                return json.dumps(error_json)

        except Exception as e:
            error_json["code"] = -5
            self.error_log("proxy_service_call", "Module '" + module + \
                            "' communication error; " + str(e))
            print error_json
            return json.dumps(error_json)

        return result



    @cherrypy.expose
    def proxy_post(self, module, service,**kwargs):
        """
        Designed for proxy posts
        files are send using file_0:blob, file_1:blob, etc ...
        from the javascript FormData post

        this function uses requests to execute WS calls
        http://docs.python-requests.org/en/latest/user/quickstart/
        Instead of encoding the dict yourself, you can also pass it directly using the json parameter (added in version 2.4.2) and it will be encoded automatically:
        """
        error_json = {}
        error_json["status"] = "KO"
        #validate params and set default params
        
        if module is None:
            error_json["code"] = -2
            self.error_log(proxy_service_call,"no module")
            return json.dumps(error_json)
        else:
            # Check if module is valid
            if module not in self.dict_modules.keys():
                error_json["code"] = -3
                if module == "":
                    error_msg = " module in url is empty"
                else:
                    error_msg = module + \
                        " does not appear in the XML file in the proxy "

                self.error_log("proxy_service_call", error_msg)
                return json.dumps(error_json)

        if service is None:
            error_json["code"] = -4
            error_msg = "Not WS in the url"
            self.error_log("proxy_service_call", error_msg)
            return json.dumps(error_json)

        #build WS url
        ws_url= self.dict_modules[module]["url"]+ service

        # WS call
        try:
            print "sending with data = ",kwargs
            p = kwargs.copy()
            filelist={}
            i=0
            while "file_{0}".format(i) in p:
                fname="file_{0}".format(i)
                filelist[fname]=p[fname].file
                p.pop(fname)
                i+=1
            response = requests.post(ws_url, params=p, files=filelist)

            result = response.content
            # validate that json returned by WS is valid
            try:
                json_object = json.loads(result)
            except Exception:
                error_msg=" Invalid JSON returned"
                print error_msg
                error_json["code"] = -6
                self.error_log("proxy_service_call", error_msg)
                return json.dumps(error_json)

        except Exception as e:
            error_json["code"] = -5
            self.logger.exception(  "Module '" + module + \
                                    "' communication error; " + str(e))
            return json.dumps(error_json)

        return json.dumps(result)



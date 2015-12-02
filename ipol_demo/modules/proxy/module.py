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


    def __init__(self, option):
        """
        """
        pass

    def root_index(name):
        return "Hello, %s!" % name

    @cherrypy.expose
    def index(self):
        """
        Small index for the archive.
        """
        #print etree.tostring(doc,pretty_print=True ,xml_declaration=True, encoding="utf-8")
        
        doc = ET.parse('modules.xml')
        root=doc.getroot()
        message_for_the_screen='Welcome to the IPOL proxy module: <br><br>'
        message_for_the_screen += 'You have ' + str(len(root)) + ' modules for connecting <br><br>'
        
        index_module = 1

        for module in root.findall('module'):
            
            message_for_the_screen += str(index_module) + "." + module.get('name')
            index_module=index_module+1
            
            message_for_the_screen += " | List of commands = {"
            for command in module.findall('command'):
                message_for_the_screen += command.text + ","
               
            
            message_for_the_screen =  message_for_the_screen[:-1] + "}<br>"
           
        return message_for_the_screen


#def branch_leaf(size):
#    return str(int(size) + 3)

#mappings = [
#    (r'^/([^/]+)$', root_index),
#    (r'^/branch/leaf/(\d+)$', branch_leaf),
#    ]

    
    
    @cherrypy.expose
    def archive(self, **kwargs):
        """
        """

        #urls_values = urllib.urlencode(data, True)
        #url = cherrypy.server.base() + req + '?' + urls_values
        print "HOLA PIVE"
        return "Nelson mola"
        res = urllib2.urlopen("http://boucantrin.ovh.hw.ipol.im:9000/ping")
        res = urllib2.urlopen("http://boucantrin.ovh.hw.ipol.im:9000/ping")
        tmp = res.read()
        print tmp
        qqq = json.loads(tmp)
        print type(qqq)

        #print kwargs

        #status = {"kwargs" : str(kwargs)}
        return json.dumps(qqq)



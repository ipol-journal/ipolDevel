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

# Module written by Alexis Mongin. Contact : alexis.mongin #~AT~# outlook.com

"""
Main function.
"""

import os
import cherrypy
import sys
from archive import Archive

def CORS():
    cherrypy.response.headers["Access-Control-Allow-Origin"] = "*"

if __name__ == '__main__':
    
    cherrypy.tools.CORS = cherrypy.Tool('before_handler', CORS)
    
    if len(sys.argv) == 2 and os.path.isfile(sys.argv[1]):
        VALUE = sys.argv[1]
    else:
        VALUE="archive.conf"
    BASE_DIR = os.path.dirname(os.path.abspath(__file__))
    CONF_FILE = os.path.join(BASE_DIR, VALUE)
    
    #if "--test" in sys.argv:
        #cherrypy.quickstart(Archive('test',CONF_FILE), config=CONF_FILE)
    #cherrypy.quickstart(Archive(None,CONF_FILE), config=CONF_FILE)

    cherrypy.config.update(CONF_FILE)
    
    CONF = {
        '/' : {
            'tools.staticdir.root': os.getcwd(),
            'tools.CORS.on': True
        },
        '/blobs_thumbs': {
            'tools.staticdir.on': True,
            'tools.staticdir.dir': "blobs_thumbs"
        },
        '/blobs': {
            'tools.staticdir.on': True,
            'tools.staticdir.dir': "blobs"
        }
    }

    APP = cherrypy.tree.mount(Archive(None,CONF_FILE), '/', CONF)
    APP.merge(CONF_FILE)
    
    cherrypy.engine.start()
    cherrypy.engine.block()

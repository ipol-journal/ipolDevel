#!/usr/bin/env python
# -*- coding:utf-8 -*-

"""
Main function
Load from the blobs configuration file
Create the cherrypy server
"""

import os
import os.path
import sys
import cherrypy
from blobs import Blobs

def CORS():
    """
    This function enable CORS (cross origin resource sharing)
    more info at : http://blog.edutoolbox.de/?p=114
    """
    cherrypy.response.headers["Access-Control-Allow-Origin"] = "*" # mean: CORS to

if __name__ == '__main__':

    cherrypy.tools.CORS = cherrypy.Tool('before_handler', CORS)

    if len(sys.argv) == 2 and os.path.isfile(sys.argv[1]):
        VALUE = sys.argv[1]
    else:
        VALUE = "blobs.conf"

    BASE_DIR = os.path.dirname(os.path.abspath(__file__))
    CONF_FILE = os.path.join(BASE_DIR, VALUE)

    cherrypy.config.update(CONF_FILE)

    FINAL = cherrypy.config['final.dir']
    THUMB = cherrypy.config['thumbnail.dir']

    CONF = {
        '/' : {
            'tools.staticdir.root': os.getcwd(),
        },
        '/blob_directory': {
            'tools.staticdir.on': True,
            'tools.staticdir.dir': FINAL
        },
        '/thumbnail': {
            'tools.staticdir.on': True,
            'tools.staticdir.dir': THUMB
        }

    }

    cherrypy.config.update(CONF)

    APP = cherrypy.tree.mount(Blobs.get_instance(), '/', CONF)
    APP.merge(CONF_FILE)

    if hasattr(cherrypy.engine, "signal_handler"):
        cherrypy.engine.signal_handler.subscribe()
    if hasattr(cherrypy.engine, "console_control_handler"):
        cherrypy.engine.console_control_handler.subscribe()
    cherrypy.engine.start()
    cherrypy.engine.block()

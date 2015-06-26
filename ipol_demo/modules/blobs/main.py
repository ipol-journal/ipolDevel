#!/usr/bin/env python
# -*- coding:utf-8 -*-

"""
Main function
Load from the blobs configuration file
Create the cherrypy server
"""

import cherrypy
import os
import os.path
import sys
from module import Blob
from error import print_usage_function

if __name__ == '__main__':
    if len(sys.argv) != 2 or not os.path.isfile(sys.argv[1]):
        print_usage_function(sys.argv[0])
        sys.exit(1)

    BASE_DIR = os.path.dirname(os.path.abspath(__file__))
    CONF_FILE = os.path.join(BASE_DIR, sys.argv[1])

    cherrypy.config.update(CONF_FILE)

    FINAL = cherrypy.config['final.dir']

    conf = {
        '/' : {
            'tools.staticdir.root': os.getcwd(),
        },
        '/blob_directory': {
            'tools.staticdir.on': True,
            'tools.staticdir.dir': FINAL
        }
    }

    cherrypy.config.update(conf)

    app = cherrypy.tree.mount(Blob(), '/', conf)
    app.merge(CONF_FILE)

    if hasattr(cherrypy.engine, "signal_handler"):
        cherrypy.engine.signal_handler.subscribe()
    if hasattr(cherrypy.engine, "console_control_handler"):
        cherrypy.engine.console_control_handler.subscribe()
    cherrypy.engine.start()
    cherrypy.engine.block()




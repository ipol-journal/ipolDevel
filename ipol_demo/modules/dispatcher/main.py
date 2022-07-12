#!/usr/bin/env python3
# -*- coding:utf-8 -*-

"""
Main function
Load from the dispatcher configuration file
Create the cherrypy server
"""


import os
import sys

import cherrypy

from dispatcher import Dispatcher


def CORS():
    """
    CORS
    """
    cherrypy.response.headers["Access-Control-Allow-Origin"] = "*"

if __name__ == '__main__':

    cherrypy.tools.CORS = cherrypy.Tool('before_handler', CORS)

    CONF_FILE_REL = sys.argv[1] if len(sys.argv) == 2 and os.path.isfile(sys.argv[1]) else "dispatcher.conf"

    BASE_DIR = os.path.dirname(os.path.abspath(__file__))
    CONF_FILE_ABS = os.path.join(BASE_DIR, CONF_FILE_REL)

    cherrypy.config.update(CONF_FILE_ABS)
    cherrypy.log.error_log.setLevel('ERROR')
    cherrypy.quickstart(Dispatcher.get_instance(), config=CONF_FILE_ABS)

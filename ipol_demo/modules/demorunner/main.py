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
from demorunner import DemoRunner


def CORS(): 
  cherrypy.response.headers["Access-Control-Allow-Origin"] = "*" # mean: CORS to 

if __name__ == '__main__':

    cherrypy.tools.CORS = cherrypy.Tool('before_handler', CORS) 

    CONF_FILE_REL = sys.argv[1] if len(sys.argv) == 2 and os.path.isfile(sys.argv[1]) else "demorunner.conf"

    BASE_DIR      = os.path.dirname(os.path.abspath(__file__))
    CONF_FILE_ABS = os.path.join(BASE_DIR, CONF_FILE_REL)
    
    cherrypy.config.update(CONF_FILE_ABS)    
    cherrypy.tools.CORS = cherrypy.Tool('before_handler', CORS) 
    cherrypy.quickstart(DemoRunner(), config=CONF_FILE_ABS)


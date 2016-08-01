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

    if len(sys.argv) == 2 and os.path.isfile(sys.argv[1]):
        conf_file = sys.argv[1]
    else:
        conf_file ="demorunner.conf"

    cherrypy.config.update(conf_file)    
    cherrypy.tools.CORS = cherrypy.Tool('before_handler', CORS) 
    cherrypy.quickstart(DemoRunner(), config=conf_file)


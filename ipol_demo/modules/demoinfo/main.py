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

# Module written by Jose Arrecio Kubon josearrecio@gmail.com

"""
Main function.
"""
import sys
import os
import cherrypy
from demoinfo import DemoInfo

def CORS():
    """
    This function enable CORS (cross origin resource sharing)
    more info at : http://blog.edutoolbox.de/?p=114
    """
    cherrypy.response.headers["Access-Control-Allow-Origin"] = "*"


if __name__ == '__main__':

    CONF_FILE_REL = sys.argv[1] if len(sys.argv) == 2 and os.path.isfile(sys.argv[1]) else "demoinfo.conf"

    BASE_DIR = os.path.dirname(os.path.abspath(__file__))
    CONF_FILE_ABS = os.path.join(BASE_DIR, CONF_FILE_REL)

    cherrypy.tools.CORS = cherrypy.Tool('before_handler', CORS)
    cherrypy.quickstart(DemoInfo(CONF_FILE_ABS), '', config=CONF_FILE_ABS)

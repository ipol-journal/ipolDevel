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

    CONF_FILE_REL = sys.argv[1] if len(sys.argv) == 2 and os.path.isfile(sys.argv[1]) else "archive.conf"

    BASE_DIR      = os.path.dirname(os.path.abspath(__file__))
    CONF_FILE_ABS = os.path.join(BASE_DIR, CONF_FILE_REL)
    cherrypy.log.error_log.setLevel('ERROR')
    cherrypy.config.update(CONF_FILE_ABS)
    cherrypy.quickstart(Archive.get_instance(), config=CONF_FILE_ABS)

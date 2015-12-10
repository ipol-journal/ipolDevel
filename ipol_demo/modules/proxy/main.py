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
Main function.
"""

import cherrypy
import sys, os
from proxy import Proxy

def CORS(): 
  cherrypy.response.headers["Access-Control-Allow-Origin"] = "*" # mean: CORS to 

if __name__ == '__main__':

    if len(sys.argv) == 2 and os.path.isfile(sys.argv[1]):
        conf_file = sys.argv[1]
    else:
        conf_file = "proxy.conf"

    cherrypy.tools.CORS = cherrypy.Tool('before_handler', CORS) 
    cherrypy.quickstart(Proxy(None), config=conf_file)

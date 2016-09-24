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
from core import demo_index


#-------------------------------------------------------------------------------
def CORS(): 
  cherrypy.response.headers["Access-Control-Allow-Origin"] = "*" # mean: CORS to 

#-------------------------------------------------------------------------------
def err_tb():
    """
    replace the default error response
    with an cgitb HTML traceback
    """
    import cgitb, sys
    tb = cgitb.html(sys.exc_info())
    def set_tb():
        """ set the traceback output """
        cherrypy.response.body = tb
        cherrypy.response.headers['Content-Length'] = None
    cherrypy.request.hooks.attach('after_error_response', set_tb)


if __name__ == '__main__':

    cherrypy.tools.CORS = cherrypy.Tool('before_handler', CORS) 

    ## config file and location settings
    base_dir = os.path.dirname(os.path.abspath(__file__))
    cherrypy.log("app base_dir: %s" % base_dir,
                 context='SETUP', traceback=False)
    
    if len(sys.argv) == 2 and os.path.isfile(sys.argv[1]):
        conf_file = sys.argv[1]
    else:
        conf_file = "core.conf"
    
    if not os.path.isfile(conf_file):
        cherrypy.log("warning: the conf file is missing, " \
                         "copying the example conf",
                     context='SETUP', traceback=False)
    
    cherrypy.config.update(conf_file)
    cherrypy.tools.cgitb = cherrypy.Tool('before_error_response', err_tb)
    cherrypy.quickstart(demo_index(), config=conf_file)
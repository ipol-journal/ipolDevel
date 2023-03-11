#!/usr/bin/env python3
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

import os
import sys

import cherrypy
from core import Core


# -------------------------------------------------------------------------------
def CORS():
    """
    CORS
    """
    cherrypy.response.headers["Access-Control-Allow-Origin"] = "*"  # mean: CORS to


# -------------------------------------------------------------------------------
def err_tb():
    """
    replace the default error response
    with an cgitb HTML traceback
    """
    import cgitb

    tb = cgitb.html(sys.exc_info())

    def set_tb():
        """set the traceback output"""
        cherrypy.response.body = tb
        cherrypy.response.headers["Content-Length"] = None

    cherrypy.request.hooks.attach("after_error_response", set_tb)


if __name__ == "__main__":
    cherrypy.tools.CORS = cherrypy.Tool("before_handler", CORS)

    ## config file and location settings

    CONF_FILE_REL = (
        sys.argv[1]
        if len(sys.argv) == 2 and os.path.isfile(sys.argv[1])
        else "core.conf"
    )
    LOCAL_CONF_REL = "local.conf"

    BASE_DIR = os.path.dirname(os.path.abspath(__file__))
    CONF_FILE_ABS = os.path.join(BASE_DIR, CONF_FILE_REL)
    LOCAL_CONF_FILE = os.path.join(BASE_DIR, LOCAL_CONF_REL)

    if not os.path.isfile(LOCAL_CONF_FILE):
        print("Error: the conf file is missing, ")
        sys.exit(-1)
    if not os.path.isfile(CONF_FILE_ABS):
        print("Error: the conf file is missing, ")
        sys.exit(-1)
    cherrypy.config.update(CONF_FILE_ABS)
    cherrypy.config.update(LOCAL_CONF_FILE)
    cherrypy.log.error_log.setLevel("ERROR")
    cherrypy.tools.cgitb = cherrypy.Tool("before_error_response", err_tb)

    core = Core.get_instance()
    cherrypy.tree.mount(
        core.get_dispatcher_api(), "/api/dispatcher", config=CONF_FILE_ABS
    )
    cherrypy.tree.mount(
        core.get_conversion_api(), "/api/conversion", config=CONF_FILE_ABS
    )
    cherrypy.tree.mount(core.get_demoinfo_api(), "/api/demoinfo", config=CONF_FILE_ABS)
    cherrypy.quickstart(core, config=CONF_FILE_ABS)

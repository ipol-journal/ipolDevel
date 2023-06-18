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

    import argparse

    parser = argparse.ArgumentParser()
    parser.add_argument("config", help="path to core.conf file")
    args = parser.parse_args()
    config_file = args.config

    if not os.path.isfile(config_file):
        print("Error: the conf file is missing")
        sys.exit(-1)

    cherrypy.config.update(config_file)
    cherrypy.log.error_log.setLevel("ERROR")
    cherrypy.tools.cgitb = cherrypy.Tool("before_error_response", err_tb)

    core = Core.get_instance()
    cherrypy.tree.mount(
        core.get_dispatcher_api(), "/api/dispatcher", config=config_file
    )
    cherrypy.tree.mount(
        core.get_conversion_api(), "/api/conversion", config=config_file
    )
    cherrypy.tree.mount(core.get_demoinfo_api(), "/api/demoinfo", config=config_file)
    cherrypy.quickstart(core, config=config_file)

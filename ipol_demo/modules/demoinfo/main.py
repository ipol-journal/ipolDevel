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

import cherrypy
from module import DemoInfo

#todo This should not be hardcoded
CONFIGFILE = "./demoinfo.conf"

if __name__ == '__main__':

	cherrypy.quickstart(DemoInfo(CONFIGFILE), '', config="demoinfo.conf")


	# cherrypy.tree.mount(DemoInfo(None), '/', config="demoinfo.conf")
	# cherrypy.engine.start()
	# cherrypy.engine.block()










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

import cherrypy
import sys
from archive import Archive

if __name__ == '__main__':
    if "--test" in sys.argv:
        cherrypy.quickstart(Archive('test'), config="archive.conf")
    cherrypy.quickstart(Archive(None), config="archive.conf")

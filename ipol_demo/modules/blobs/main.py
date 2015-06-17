#!/usr/bin/env python
# -*- coding:utf-8 -*-

"""
Main function
Load from the blobs configuration file
Create the cherrypy server
"""

import cherrypy
import os, os.path
from module import Blob

if __name__ == '__main__':
    base_dir = os.path.dirname(os.path.abspath(__file__))
    conf_file = os.path.join(base_dir, 'blobs.conf')

    cherrypy.config.update(conf_file)

    tmp = cherrypy.config['tmp.dir']
    final = cherrypy.config['final.dir']
    html = cherrypy.config['html.dir']

    cherrypy.quickstart(Blob(tmp, final, html))

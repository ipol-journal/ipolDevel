"""
IPOL demo app collection
"""

import os
from lib import base_app

base_dir = os.path.dirname(os.path.abspath(__file__))

# (id:app) demo dict
demo_dict = {}
for demo_id in os.listdir(base_dir):
  demo_path = os.path.join(base_dir, demo_id)
  if os.path.isdir(demo_path):
    demo_dict[demo_id] = demo_path
    #try:
        ## use function version of `from demo_id import app as _.app`
        #demo_dict[demo_id] = __import__(demo_id, globals(), locals(),
                                        #['app'], -1).app
    #except ImportError, e:
        #print "ERROR: Import error in app %s: %s" % (demo_id, e)
        #print "ERROR: App not loaded."
    #except SyntaxError, e:
        #print "ERROR: Syntax error in app %s: %s" % (demo_id, e)
        #print "ERROR: App not loaded."
    #except StandardError, e:
        #print "ERROR: Unspecified error in app %s: %s" % (demo_id, e)
        #print "ERROR: App not loaded."

#! /usr/bin/python
"""
base cherrypy launcher for the IPOL demo app
"""

#TODO: blacklist from config file

import cherrypy
from mako.lookup import TemplateLookup

import os
import shutil
from lib import build_demo_base
from lib import base_app
#import json
import simplejson as json

def CORS(): 
  cherrypy.response.headers["Access-Control-Allow-Origin"] = "*" # mean: CORS to 



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


class demo_index(object):
    """
    simplistic demo index used as the root app
    """

    def __init__(self, indexd, demo_desc):
        """
        initialize with demo_dict for indexing
        """
        self.indexd    = indexd
        self.demo_desc = demo_desc

    @cherrypy.expose
    def index(self):
        """
        simple demo index page
        """
        tmpl_dir = os.path.join(os.path.dirname(__file__),
                                'lib', 'template')
        tmpl_lookup = TemplateLookup(directories=[tmpl_dir],
                                     input_encoding='utf-8',
                                     output_encoding='utf-8',
                                     encoding_errors='replace')
        return tmpl_lookup.get_template('index.html')\
            .render(indexd=self.demo_desc,
                    title="Demonstrations",
                    description="")

def do_build(demo_dict,clean):
    """
    build/update the demo programs
    """
    print "do_build"
    for (demo_id, demo_path) in demo_dict.items():
      print "\n---- demo: ",demo_id
      # get demo dir
      current_dir = os.path.dirname(os.path.abspath(__file__))
      demo_dir = os.path.join(current_dir,"app",demo_id)
      # read JSON file
      # update the demo apps programs
      demo = base_app(demo_path)
      
      # we should have a dict or a list of dict
      if isinstance(demo.demo_description['build'],dict):
        builds = [ demo.demo_description['build'] ]
      else:
        builds = demo.demo_description['build']
      
      first_build = True
      for build_params in builds:
        bd = build_demo_base.BuildDemoBase( demo_dir)
        bd.set_params(build_params)
        
        cherrypy.log("building", context='SETUP/%s' % demo_id,
                      traceback=False)
        try:
          if clean:
            bd.clean()
          else:
            bd.make(first_build)
            first_build=False
        except Exception as e:
          print "Build failed with exception ",e
          cherrypy.log("build failed (see the build log)",
                        context='SETUP/%s' % demo_id,
                        traceback=False)
    return

def do_run(demo_dict, demo_desc):
    """
    run the demo app server
    """
    for (demo_id, demo_path) in demo_dict.items():
        # mount the demo apps
        try:
          demo = base_app(demo_path)
          cherrypy.log("loading", context='SETUP/%s' % demo_id,
                      traceback=False)
          cherrypy.tree.mount(demo, script_name='/%s' % demo_id)
        except Exception as inst:
          print "failed to start demo ", inst
          cherrypy.log("starting failed (see the log)",
                        context='SETUP/%s' % demo_id,
                        traceback=True)
          
    # cgitb error handling config
    cherrypy.tools.cgitb = cherrypy.Tool('before_error_response', err_tb)
    print demo_dict
    # start the server
    cherrypy.quickstart(demo_index(demo_dict,demo_desc), config=conf_file)
    return

def get_values_of_o_arguments(argv):
    """
    return the -o options on the argument list, and remove them
    """
    r = []
    n = len(argv)
    for j in range(n):
        i = n-j-1
        if i > 1 and argv[i-1] == "-o":
            r.append(argv[i])
            del argv[i]
            del argv[i-1]
    return r

def CheckDemoDescription(desc):
  # check the general section
  ok = True
  required_keys = set([ "general", "inputs", "params", "results", "archive", "build", "run" ])
  if not required_keys.issubset(desc.keys()):
    print "missing sections in JSON file: ", required_keys.difference(desc.keys())
    return False

  # general section
  required_keys = set([ "demo_title", "input_description", "param_description", "is_test", "xlink_article" ])
  if not required_keys.issubset(desc['general'].keys()):
    mess =  "missing keys in 'general' secton of JSON file: {0}".format(required_keys.difference(desc['general'].keys()))
    print mess
    cherrypy.log(mess, context='SETUP', traceback=False)
    return False
  return ok

if __name__ == '__main__':

    cherrypy.tools.CORS = cherrypy.Tool('before_handler', CORS) 

    import sys

    # config file and location settings
    base_dir = os.path.dirname(os.path.abspath(__file__))
    conf_file = os.path.join(base_dir, 'demo.conf')
    conf_file_example = os.path.join(base_dir, 'demo.conf.example')
    cherrypy.log("app base_dir: %s" % base_dir,
                 context='SETUP', traceback=False)

    if not os.path.isfile(conf_file):
        cherrypy.log("warning: the conf file is missing, " \
                         "copying the example conf",
                     context='SETUP', traceback=False)
        shutil.copy(conf_file_example, conf_file)

    cherrypy.config.update(conf_file)

    # load the demo collection
    from app import demo_dict

    demo_desc = {}
    # check for json files
    for (demo_id, demo_app) in demo_dict.items():
      jsonpath = os.path.join(base_dir, "static/JSON/{0}.json".format(demo_id))
      try:
        print " reading description of demo ",demo_id
        demo_file = open(jsonpath)
        demo_description = json.load(demo_file)
        if CheckDemoDescription(demo_description):
          demo_desc[demo_id] = demo_description
          print "OK"
        else:
          demo_dict.pop(demo_id)
          print "FAILED"
        demo_file.close()
      except ValueError as e:
        print "EXCEPTION: ", e
        cherrypy.log("failed to read JSON demo description")
        demo_dict.pop(demo_id)
        
    #print demo_dict
    #print demo_desc

    # filter out test demos
    if cherrypy.config['server.environment'] == 'production':
      for (demo_id, demo_app) in demo_dict.items():
        print "is_test:", demo_desc[demo_id]["is_test"]
        if demo_desc[demo_id]["is_test"]:
            demo_dict.pop(demo_id)

    # if there is any "-o" command line option, keep only the mentioned demos
    demo_only_ids = get_values_of_o_arguments(sys.argv)
    if len(demo_only_ids) > 0:
      for demo_id in demo_dict.keys():
          if not demo_id in demo_only_ids:
              demo_dict.pop(demo_id)

    # now handle the remaining command-line options
    # default action is "run"
    if len(sys.argv) == 1:
        sys.argv += ["run"]
    for arg in sys.argv[1:]:
        if "build" == arg:
            do_build(demo_dict,False)
        elif "clean" == arg:
            do_build(demo_dict,True)
        elif "run" == arg:
            do_run(demo_dict, demo_desc)
        else:
            print """
usage: %(argv0)s [action]

actions:
* run     launch the web service (default)
* build   build/update the compiled programs
""" % {'argv0' : sys.argv[0]}

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
from sets import Set
import re

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


#-------------------------------------------------------------------------------
#-------------------------------------------------------------------------------
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

#-------------------------------------------------------------------------------
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

#-------------------------------------------------------------------------------
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

#-------------------------------------------------------------------------------
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

#-------------------------------------------------------------------------------
def CheckDemoDescription(desc):
  # check the general section
  ok = True
  required_keys = set([ "general", "build", "inputs", "params", "run", "archive", "results"  ])
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


#-------------------------------------------------------------------------------
def UpdateCounters(_dict,_list):
  for l in _list:
    if l in _dict:
      _dict[l] += 1
    else:
      _dict[l] = 1

#-------------------------------------------------------------------------------
def WriteDDLOptions(sn,section_types,section_keys,latex_section):
  """
    sn: section name
    section_keys: dict containing the keys for each section
    latex_section: corresponding text of the latex file
    return string containing the processed json code
  """

  max_count = 0
  for t in section_keys[sn]:
    max_count = max(max_count,section_keys[sn][t])

  res = ''
  indent=''
  
  # only list possible type if it is not an list element
  if ':' not in sn:
    res +=  indent+' "{0}_types": '.format(sn)
    res +=  '[ '
    index=0
    for t in section_types[sn]:
      counter = section_types[sn][t]
      if t.startswith('<type'): 
        if index>0:  res +=  ', '
        res +=  '"{0} ({1})"'.format(t[7:-2],counter)
        index+=1
      if t.startswith('list_elt:<type'): 
        if index>0:  res +=  ', '
        res +=  '"list:{0} ({1})"'.format(t[16:-2],counter)
        index+=1
    res +=  '],\n'
    res +=  indent+' "{0}": \n'.format(sn)
  else:
    indent = '  '
    res +=  indent+' "{0} ({1})": \n'.format(sn[sn.find(':')+1:],max_count)
  res +=  indent+'    {\n'
  
  for t in section_keys[sn]:
    counter = section_keys[sn][t]
    res +=  indent+'    "{0} ({1})":'.format(t,counter)
    # try to find the associated doc
    latex_section = re.sub(r'\\-','',latex_section)
    doc = re.search(r"^[^&]*{0}[^&]*&([^&]*)&([^\\]*)\\".format(t.replace('_','\\\\_')),
                    latex_section,re.MULTILINE)
    if doc:
      res_string = doc.group(1)
      # get rid of newlines and white spaces
      res_string = re.sub(r'\s+',' ',res_string)
      res_string = re.sub(r'\n',' ',res_string)
      res_string = re.sub(r'\\-','',res_string)
      res_string = re.sub(r'\\{','{',res_string)
      res_string = re.sub(r'\\}','}',res_string)
      res_string = res_string.strip()
      res +=  '"'+res_string+'",\n'
    else:
      res +=  '"*** doc not found ***",\n'
  res +=  indent+'    },\n'
  return (res,max_count)
  

#-------------------------------------------------------------------------------
#-------------------------------------------------------------------------------
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

    section_names = Set()
    section_keys  = dict()
    section_types = dict()

    demo_desc = {}
    demo_count=0
    # check for json files
    for (demo_id, demo_app) in demo_dict.items():
      jsonpath = os.path.join(base_dir, "static/JSON/{0}.json".format(demo_id))
      try:
        demo_count += 1
        print " ",demo_count,"\treading json ",demo_id,
        demo_file = open(jsonpath)
        demo_description = json.load(demo_file)
        if CheckDemoDescription(demo_description):
          demo_desc[demo_id] = demo_description
          print " --> OK "
          # save all keys
          section_names.update(demo_description.keys())
          for k in demo_description.keys():
            if k not in section_keys:
              section_keys[k]=dict()
              section_types[k]=dict()
            UpdateCounters(section_types[k],[repr(type(demo_description[k]))])
            if type(demo_description[k])==dict:
              UpdateCounters(section_keys[k],demo_description[k].keys())
            if type(demo_description[k])==list:
              # create a dict per type
              for elt in demo_description[k]:
                if (type(elt)==dict):
                  new_key=''
                  if 'type' in elt:
                    new_key = k+":"+elt['type'].lower()
                  if k+'_type' in elt:
                    new_key = k+":"+elt[k+'_type'].lower()
                  if new_key!='':
                    if new_key not in section_keys:
                      section_keys[new_key]=dict()
                      print "adding key:",new_key, " with ", elt.keys()
                    UpdateCounters(section_keys[new_key],elt.keys())
                  else:
                    UpdateCounters(section_keys[k],elt.keys())
                else:
                  UpdateCounters(section_keys[k],['list_elt:'+repr(type(elt))])
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
      elif arg == "jsoninfo":
        # read latex file to get more info 
        ddl_tex = open("../doc/ddl/ddl.tex")
        # order sections by their position in the latex file
        ordered_sections = []
        latex_section=dict()
        for l in ddl_tex:
          if '\subsection' in l:
            for sn in section_names:
              if sn in l:
                ordered_sections.append(sn)
                current_subsection=sn
                latex_section[current_subsection] = ''
          if '\section' in l:
            current_subsection=""
          if current_subsection!="":
            latex_section[current_subsection] += l
        for sn in section_names:
          if sn not in ordered_sections:
            ordered_sections.append(sn)
        
        print "All demo sections are "
        #print "Latex code"
        #for sn in ordered_sections:
          #if sn in latex_section:
            #print latex_section[sn]
        
        print "JSON help file: see ddl_help.json"
        dllf = open("ddl_help.json","w")
        dllf.write( "{")
        for os in ordered_sections:
          if os+':' in section_keys.keys(): 
            dllf.write(' "{0}":\n'.format(os))
            dllf.write('   {\n')
          else:
            doc = WriteDDLOptions(os,section_types,
                            section_keys,latex_section[os])
            dllf.write(doc[0])
          list_res=[]
          for sn in section_keys.keys():
            if sn.startswith(os+":"):
              res = WriteDDLOptions(sn,section_types,
                              section_keys,latex_section[os])
              list_res.append(res)
          # sort by counters
          list_res.sort(key=lambda res: res[1],reverse=True)
          if list_res:
            for lr in list_res:
              dllf.write(lr[0])
          if os+':' in section_keys.keys(): 
            dllf.write('   },\n')
        dllf.write( "}\n")
        dllf.close()
      else:
          print """
usage: %(argv0)s [action]

actions:
* run     launch the web service (default)
* build   build/update the compiled programs
""" % {'argv0' : sys.argv[0]}

      
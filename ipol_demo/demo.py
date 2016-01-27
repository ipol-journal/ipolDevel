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
#import simplejson as json
import json
# json schema validation
from jsonschema import validate
from jsonschema import Draft4Validator
from jsonschema import ValidationError

from sets import Set
import re
import urllib2

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

    def __init__(self, dlist):
        """
        initialize
        """
        self.dlist    = dlist

    @cherrypy.expose
    def index(self):
        """
        simple demo index page
        """
        self.dlist.do_reload()
        tmpl_dir = os.path.join(os.path.dirname(__file__),
                                'lib', 'template')
        tmpl_lookup = TemplateLookup(directories=[tmpl_dir],
                                     input_encoding='utf-8',
                                     output_encoding='utf-8',
                                     encoding_errors='replace')
        return tmpl_lookup.get_template('index.html')\
            .render(indexd=self.dlist.demo_desc,
                    proxy_server=self.dlist.proxy_server,
                    title="Demonstrations",
                    description="")

#-------------------------------------------------------------------------------
#-------------------------------------------------------------------------------
class DemoLog(object):
    
    def __init__(self,logmess):
        self.logmess = logmess
    
    @cherrypy.expose
    def index(self):
        print "DemoLog index"
        return self.logmess

#-------------------------------------------------------------------------------
def ParseLatex(section_names,section_keys,latex_sections,ordered_sections):
    """
        fills dictionary latex_sections and list ordered_sections
        latex_sections   contains all the latex code of a subsection related to
                        a DDL section. If the section is a list with different
                        types, then each subsubsection part and the common
                        part are saved.
        ordered_sections contains the sections in the order of their appearance
                        in latex
    """
    # read latex file to get more info 
    ddl_tex = open("../doc/ddl/ddl.tex")
    for l in ddl_tex:
        if '\subsection' in l:
            for sn in section_names:
                if sn.replace('_','\_')  in l:
                    ordered_sections.append(sn)
                    current_subsection    = sn
                    current_subsubsection = ""
                    # all possible list element types
                    current_elttypes=[]
                    # list possible elements types from section_keys
                    for st in section_keys.keys():
                        if st.startswith(sn+':'):
                            elttype=st[st.find(':')+1:]
                            current_elttypes.append(elttype)
                            latex_sections[current_subsection+':'+elttype] = ''
                    latex_sections[current_subsection] = ''
        if '\section' in l:
            current_subsection=""
            current_subsubsection=""
        if current_subsection:
            if ('\subsubsection' in l) and current_elttypes:
                current_subsubsection = ""
                for t in current_elttypes:
                    if '{'+t.replace('_','\_')+'}' in l:
                        current_subsubsection = t
            if current_subsubsection:
                latex_sections[current_subsection+':'+current_subsubsection] += l
            else:
                latex_sections[current_subsection] += l
    # adding remaining (not found) sections
    for sn in section_names:
        if sn not in ordered_sections:
            ordered_sections.append(sn)

#-------------------------------------------------------------------------------
def WriteDDLOptions(sn,section_types,section_keys,latex_sections):
    """
        sn: section name
        section_keys: dict containing the keys for each section
        latex_sections: corresponding text of the latex file
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
    
    keys_doc = []
    for t in section_keys[sn]:
        counter = section_keys[sn][t]
        keydoc =  indent+'    "{0} ({1})":'.format(t,counter)
        # try to find the associated doc
        latex_section = re.sub(r'\\-','',latex_sections[sn])
        doc = re.search(r"^[\s]*{0}[\s]*&([^&]*)&([^\\]*)\\".format(t.replace('_','\\\\_')),
                        latex_section,re.MULTILINE)
        if doc:
            res_string = doc.group(1)
            keypos = doc.span()[0]
            # get rid of newlines and white spaces
            res_string = re.sub(r'\s+',' ',res_string)
            res_string = re.sub(r'\n',' ',res_string)
            res_string = re.sub(r'\\-','',res_string)
            res_string = re.sub(r'\\{','{',res_string)
            res_string = re.sub(r'\\}','}',res_string)
            res_string = res_string.replace('\_','_')
            res_string = res_string.strip()
            keydoc +=  '"'+res_string+'",\n'
        else:
            keydoc +=  '"*** doc not found ***",\n'
            keypos=0
        keys_doc.append((keypos,keydoc))
            
    # sort keys by their latex position
    keys_doc.sort(key=lambda res: res[0])
    for docs in keys_doc:
        res += docs[1]
    res +=  indent+'    },\n'
    return (res,max_count)
  

#-------------------------------------------------------------------------------
#-------------------------------------------------------------------------------

class ListDemos:
    """
        List all demos using demoinfo module through the proxy module
        Check each demo DDL scheme
    """
    
    #---------------------------------------------------------------------------
    def __init__(self):
        """
        initialize class members
        """
        self.reset_members()
        self.proxy_server     = cherrypy.config['demo.proxy_server']
        self.demoinfo_service = self.proxy_server+'/?module=demoinfo&service='
        self.CURRENT_DIR      = os.path.dirname(os.path.abspath(__file__))
        self.checked_demos    = dict()  # don't recheck already checked demos
                                        # based on their creation date/time
                                        # key: internal id of demoinfo
                                        # value: creation time


    #---------------------------------------------------------------------------
    def reset_members(self):
        """
            demo_dict       : dict  key   : demo id as string, 
                                    value : demo disk path
            internalid_dict : dict  key   : demo id as string, 
                                    value : demoinfo internal id as string
            demo_desc       : dict  key   : demo id as string
                                    value : demo DDL (json format)
        """
        self.demo_dict         = dict()
        self.internalid_dict   = dict()
        self.modification_dict = dict()
        self.demo_desc         = dict()
        self.demo_logs         = dict()
        # variables for parsing latex documentation, doing statistics
        # about DDL sections/properties usage and generating a help JSON file 
        
        # all the names of main sections in DDL files
        self.section_names = Set()
        # Dictionary of dictionaries, for each section k, section_keys[k] contains
        # a dictionary of (key,counter) pairs that counts the number of occurences
        # of each key. 
        # ex: section_names['general']['demo_title'] is the number of occurences
        # of 'demo_title' in 'general' section for all valid json files
        # if a section is of type list, it may contain a list of dictionaries
        # with types refered by its 'type' or 'section_type' key, then we create
        # a dictionary per type in the form:
        # section_names['build:make']['flags'] which counts the number of occurences
        # of the flags key in elements of type 'make' within 'build' sections for 
        # all the valid json files.
        self.section_keys  = dict()
        # Dictionary of dictionaries that counts the number of occurences of 
        # each type for each section 
        self.section_types = dict()

    #---------------------------------------------------------------------------
    def update_counters(self,_dict,_list):
        """
        _dict is a dictionary that counts the occurences of each key
        increment by one the occurences of each element of the given _list
        """
        for l in _list:
            if l in _dict:
                _dict[l] += 1
            else:
                _dict[l] = 1

    #---------------------------------------------------------------------------
    def update_demo_stats(self,demo_description):
        """
        input: demo_description: dictionary from json file
        updated:
        section_names
                set of all the names of main sections in DDL files
        section_keys
            Dictionary of dictionaries, for each section k, section_keys[k] contains
            a dictionary of (key,counter) pairs that counts the number of occurences
            of each key. 
            ex: section_names['general']['demo_title'] is the number of occurences
            of 'demo_title' in 'general' section for all valid json files
            if a section is of type list, it may contain a list of dictionaries
            with types refered by its 'type' or 'section_type' key, then we create
            a dictionary per type in the form:
            section_names['build:make']['flags'] which counts the number of occurences
            of the flags key in elements of type 'make' within 'build' sections for 
            all the valid json files.
        section_types 
            Dictionary of dictionaries that counts the number of occurences of 
            each type for each section 
        """
        # save all keys
        self.section_names.update(demo_description.keys())
        for k in demo_description.keys():
            if k not in self.section_keys:
                self.section_keys[k]=dict()
                self.section_types[k]=dict()
            self.update_counters(self.section_types[k],[repr(type(demo_description[k]))])
            if type(demo_description[k])==dict:
                self.update_counters(self.section_keys[k],demo_description[k].keys())
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
                            if new_key not in self.section_keys:
                                self.section_keys[new_key]=dict()
                                #print "adding key:",new_key, " with ", elt.keys()
                            self.update_counters(self.section_keys[new_key],elt.keys())
                        else:
                            self.update_counters(self.section_keys[k],elt.keys())
                    else:
                        self.update_counters(self.section_keys[k],['list_elt:'+repr(type(elt))])
            
    #---------------------------------------------------------------------------
    def ensure_dir(self,f):
        """
        """
        d = os.path.dirname(f)
        if not os.path.exists(d):
            os.makedirs(d)

    #---------------------------------------------------------------------------
    def get_demo_list(self):
        """
        using demoinfo module to create demo_dict ...
        use proxy
        """
        get_demolist_url = self.demoinfo_service+'demo_list'
        res = urllib2.urlopen(get_demolist_url)
        resjson = json.loads(res.read())
        if resjson['status']=="OK":
            for d in resjson['demo_list']:
                id_str = str(d['editorsdemoid'])
                #print id_str
                self.demo_dict[id_str]=self.CURRENT_DIR+'/app_new/'+str(d['editorsdemoid'])
                self.internalid_dict[id_str]  =d['id']
                self.modification_dict[id_str]=d['modification']
                self.ensure_dir(self.demo_dict[id_str])


    #-------------------------------------------------------------------------------
    def check_DDL(self,desc,demo_id):
        """
            Check the demo description based on the json schema
        """
        ddl_schema = json.load(open("modules/config_common/ddl_schema.json"))
        #print "****"
        #print ddl_schema
        #print "****"
        try:
            validate(desc,ddl_schema)
        except ValidationError as e:
            print e.message
            self.demo_log(demo_id,"check_DDL Error: {0} \n".format(e.message))
            return False
        return True

    #---------------------------------------------------------------------------
    def demo_log(self, demo_id, mess):
        if demo_id in self.demo_logs:
            self.demo_logs[demo_id] = self.demo_logs[demo_id]+mess
        else:
            self.demo_logs[demo_id] = mess

    #---------------------------------------------------------------------------
    def check_demos(self, getstats=True):
        """
            needs values in self.demo_dict (obtained from calling get_demo_list)
        """
        # check for json files
        for (demo_id, demo_app) in self.demo_dict.items():
            print "---- Checking DDL {0:10}".format(demo_id),
            self.demo_log(demo_id,"<p> Checking of demo description {0} </p>\n".format(demo_id))
            try:
                internal_id       = str(self.internalid_dict[demo_id])
                modification_date = self.modification_dict[demo_id]
                # read demo descriptions
                res1 = urllib2.urlopen(self.demoinfo_service+\
                            "read_last_demodescription_from_demo"+\
                            "&demo_id="+internal_id+\
                            "&returnjsons=True" )
                res1json = json.loads(res1.read())
                if res1json['status'] == 'OK':
                    ddl_info = res1json['last_demodescription']
                    if ddl_info:
                        ddl = ddl_info['json']
                        demo_description = json.loads(ddl)
                        demo_description = json.loads(demo_description)
                        if  internal_id not in self.checked_demos or \
                            modification_date>self.checked_demos[internal_id]:
                                
                            if self.check_DDL(demo_description,demo_id):
                                print " --> OK "
                                self.demo_desc[demo_id] = demo_description
                                if getstats: self.update_demo_stats(demo_description)
                                self.checked_demos[internal_id] = modification_date
                            else:
                                print "FAILED"
                                self.demo_log(demo_id,"Failed to check demo description\n")
                                self.demo_dict.pop(demo_id)
                        else:
                            print " --> OK (already checked)"
                            self.demo_desc[demo_id] = demo_description
                            if getstats: self.update_demo_stats(demo_description)
                    else:
                        print "FAILED, no DDL found"
                        self.demo_log(demo_id,"no DDL found\n")
                        self.demo_dict.pop(demo_id)
                else:
                    print "FAILED, status not OK"
                    self.demo_dict.pop(demo_id)
            except ValueError as e:
                print "EXCEPTION: ", e
                self.demo_log(demo_id,"EXCEPTION: {0}\n".format(e))
                cherrypy.log("failed to read JSON demo description")
                self.demo_dict.pop(demo_id)

    #---------------------------------------------------------------------------
    def filter_production_demos(self):
        """
            filter out test demos
        """
        if cherrypy.config['server.environment'] == 'production':
            for (demo_id, demo_app) in self.demo_dict.items():
                if 'general' in self.demo_desc[demo_id] and \
                    self.demo_desc[demo_id]['general']["is_test"]:
                    self.demo_dict.pop(demo_id)

    #---------------------------------------------------------------------------
    def get_values_of_o_arguments(self,argv):
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

    #---------------------------------------------------------------------------
    def filter_arguments(self,argv):
        """
            if there is any "-o" command line option, keep only the mentioned demos
        """
        demo_only_ids = self.get_values_of_o_arguments(argv)
        if len(demo_only_ids) > 0:
            for demo_id in self.demo_dict.keys():
                if not demo_id in demo_only_ids:
                    self.demo_dict.pop(demo_id)

    #---------------------------------------------------------------------------
    def do_build(self, clean):
        """
        build/update the demo programs
        """
        print "\n===== Build demos source code ====="
        for (demo_id, demo_path) in self.demo_dict.items():
            print "---- demo: {0:10}".format(demo_id),
            # get demo dir
            current_dir = os.path.dirname(os.path.abspath(__file__))
            # read JSON file
            # update the demo apps programs
            demo = base_app(demo_path, self.demo_desc[demo_id])
            # we should have a dict or a list of dict
            if isinstance(demo.demo_description['build'],dict):
                builds = [ demo.demo_description['build'] ]
            else:
                builds = demo.demo_description['build']
            first_build = True
            for build_params in builds:
                bd = build_demo_base.BuildDemoBase( demo_path)
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
            print ""
        return

    #---------------------------------------------------------------------------
    def do_mount(self):
        """
        mount all demos in cherrypy 
        """
        print "do_mount begin"
        for (demo_id, demo_path) in self.demo_dict.items():
            # mount the demo apps
            try:
                demo = base_app(demo_path,self.demo_desc[demo_id])
                cherrypy.log("loading", context='SETUP/%s' % demo_id,
                            traceback=False)
                cherrypy.tree.mount(demo, script_name='/%s' % demo_id)
            except Exception as inst:
                print "failed to start demo ", inst
                cherrypy.log("starting failed (see the log)",
                                context='SETUP/%s' % demo_id,
                                traceback=True)
        print "do_mount end"
        
        # Display logs for other demos
        for (demo_id,demo_log) in self.demo_logs.items():
            if demo_id not in self.demo_dict:
                cherrypy.tree.mount(DemoLog(demo_log), script_name='/%s' % demo_id)

    #---------------------------------------------------------------------------
    def do_run(self):
        """
        run the demo app server
        """
        # cgitb error handling config
        cherrypy.tools.cgitb = cherrypy.Tool('before_error_response', err_tb)
        # start the server
        # give to demo_index the current object (self)
        cherrypy.quickstart(demo_index(self), config=conf_file)
        return

    #---------------------------------------------------------------------------
    def do_reload(self):
        """
        rerun the demo app server
        """

        # 1. copy dict and modification dates
        # this will also to speed-up reload process --> still need to be done
        demo_dict_bak         = self.demo_dict.copy()
        modification_dict_bak = self.modification_dict.copy()
        demo_desc_bak         = self.demo_desc.copy()

        # 2. recreate demo list
        self.reset_members()
        self.get_demo_list()
        
        # 3.
        self.check_demos(getstats=False)
        self.filter_production_demos()
        
        # 4. remount demos 
        for (demo_id, demo_path) in demo_dict_bak.items():
            path='/%s' % demo_id
            if path in cherrypy.tree.apps:
                print "CheeryPy unmounting ", path
                del cherrypy.tree.apps[path]
        self.do_mount()

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

    dlist = ListDemos()
    dlist.get_demo_list()
    dlist.check_demos(getstats=True)
    dlist.filter_production_demos()
    dlist.filter_arguments(sys.argv)

    # now handle the remaining command-line options
    # default action is "run"
    if len(sys.argv) == 1:
        sys.argv += ["run"]
    for arg in sys.argv[1:]:
      if "build" == arg:
        dlist.do_build( False)
      elif "clean" == arg:
        dlist.do_build( True)
      elif "run" == arg:
        dlist.do_run()
      elif arg == "jsoninfo":
        # order sections by their position in the latex file
        ordered_sections = []
        latex_sections=dict()
        ParseLatex(dlist.section_names,
                   dlist.section_keys,
                   latex_sections,
                   ordered_sections)
        
        #print "All demo sections are "
        #print "Latex code"
        #for sn in latex_sections:
            #if "repeat" in sn:
                #print
                #print "---------------- ",sn,"--------------"
                #print latex_sections[sn]
        
        print "JSON help file: see ddl_help.json"
        dllf = open("ddl_help.json","w")
        dllf.write( "{")
        for os in ordered_sections:
          if os+':' in section_keys.keys(): 
            dllf.write(' "{0}":\n'.format(os))
            dllf.write('   {\n')
          else:
            doc = WriteDDLOptions(os,
                                  dlist.section_types,
                                  dlist.section_keys,
                                  latex_sections)
            dllf.write(doc[0])
          list_res=[]
          for sn in dlist.section_keys.keys():
            if sn.startswith(os+":"):
              res = WriteDDLOptions(sn,
                                    dlist.section_types,
                                    dlist.section_keys,
                                    latex_sections)
              list_res.append(res)
          # sort by counters
          list_res.sort(key=lambda res: res[1],reverse=True)
          if list_res:
            for lr in list_res:
              dllf.write(lr[0])
          if os+':' in dlist.section_keys.keys(): 
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

      
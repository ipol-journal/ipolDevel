#! /usr/bin/python
"""
base cherrypy launcher for the IPOL demo app
"""

#TODO: blacklist from config file

import cherrypy
import sys


import shutil
#from lib import build_demo_base
from lib import base_app

import json     

#from sets import Set
#import re
#import urllib2

import errno
import logging
import os
import os.path

import urllib
import requests

import hashlib
from   datetime import datetime
from   random   import random
import glob

#from   image    import thumbnail, image
#from   misc     import prod
import PIL.ImageDraw

from PIL import Image


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
    demo index used as the root app
    """
    def init_logging(self):
        """
        Initialize the error logs of the module.
        """
        logger = logging.getLogger("core_log")
        logger.setLevel(logging.ERROR)
        handler = logging.FileHandler(os.path.join(self.logs_dir, self.logs_name))
        formatter = logging.Formatter('%(asctime)s ERROR in %(message)s', datefmt='%Y-%m-%d %H:%M:%S')
        handler.setFormatter(formatter)
        logger.addHandler(handler)
        return logger

    def error_log(self, function_name, error):
        """
        Write an error log in the logs_dir defined in demo.conf
        """
        error_string = function_name + ": " + error
        self.logger.error(error_string)
    
    def __init__(self):
        
        try:
            self.logs_dir = cherrypy.config.get("logs.dir")
            self.logs_name = cherrypy.config.get("logs.name")
            self.share_run_dir = cherrypy.config.get("running.dir")
            self.current_directory = os.getcwd()
            self.proxy_server = cherrypy.config.get("demo.proxy_server")
            
            self.mkdir_p(self.logs_dir)
            self.mkdir_p(self.share_run_dir)
            self.logger = self.init_logging()
            print "IPOL Core system Initialized"
        
        except Exception as ex:
            self.error_log("__init__", str(ex))
        
    @staticmethod
    def mkdir_p(path):
        """
        Implement the UNIX shell command "mkdir -p"
        with given path as parameter.
        """
        created = 'false'
        try:
            os.makedirs(path)
            created = 'true'
        except OSError as exc:
            if exc.errno == errno.EEXIST and os.path.isdir(path):
                pass
            else:
                raise
        
        return created

    @cherrypy.expose
    def index(self):
        """
        Small index for the demorunner.
        """
        return ("Welcome to IPOL Core !")

    @cherrypy.expose
    def ping(self):
        """
        Ping pong.
        :rtype: JSON formatted string
        """
        data = {}
        data["status"] = "OK"
        data["ping"] = "pong"
        return json.dumps(data)

    @cherrypy.expose
    def shutdown(self):
        """
        Shutdown the module.
        """
        data = {}
        data["status"] = "KO"
        try:
            cherrypy.engine.exit()
            data["status"] = "OK"
        except Exception as ex:
            self.error_log("shutdown", str(ex))
        return json.dumps(data)

    @cherrypy.expose
    def default(self, attr):
        """
        Default method invoked when asked for non-existing service.
        """
        data = {}
        data["status"] = "KO"
        data["message"] = "Unknown service '{}'".format(attr)
        return json.dumps(data)
    
    def get_new_key(self, demo_id, key=None):
        """
        create a key if needed, and the key-related attributes
        """
        if key is None:
            keygen = hashlib.md5()
            seeds = [cherrypy.request.remote.ip,
                     # use port to improve discrimination
                     # for proxied or NAT clients
                     cherrypy.request.remote.port,
                     datetime.now(),
                     random()]
            
            for seed in seeds:
                keygen.update(str(seed))
            key = keygen.hexdigest().upper()

        # check key
        if not (key and key.isalnum()):
            # HTTP Bad Request
            raise cherrypy.HTTPError(400, "The key is invalid")

        ## reload demo description
        #work_dir = self.WorkDir(demo_id,key)
        #if not os.path.isdir(work_dir):
            #os.makedirs(work_dir)

        return key

    def create_run_dir(self, demo_id, run_folder):
        """
        If it not exist, create a run_dir for a demo
        then, create a folder for the execution
        :param demo_id:   id demo
        :param run_folder: key 
        """
        demo_path = os.path.join(self.current_directory,\
                                 self.share_run_dir,\
                                 demo_id,\
                                 run_folder)
        self.mkdir_p(demo_path)
        
        return demo_path
    
    def process_inputs(self, work_dir, inputs_desc, crop_info):
        """
        pre-process the input data
        we suppose that config has been initialized, and save the dimensions
        of each converted image in self.cfg['meta']['input$i_size_{x,y}']
        """
        msg = ""
        max_width = 0
        max_height = 0
        nb_inputs = len(inputs_desc)
        
        for i in range(nb_inputs):
            input_msg = ""
            # check the input type
            input_desc = inputs_desc[i]
            # find files starting with input_%i
            print input_desc
            input_files = glob.glob(os.path.join(work_dir,'input_%i' % i+'.*'))
          
            if input_desc['type']=='image':
                ## we deal with an image, go on ...
                if len(input_files) != 1:
                    ## problem here
                    raise cherrypy.HTTPError(400, "Wrong number of inputs for an image")
                else:
                    ## open the file as an image
                    try:
                        #im = image(input_files[0])
                        print "HOLA AQUI DEBERIA IR IM = IMAGE(....)"
                    except IOError:
                        raise cherrypy.HTTPError(400, "Bad input file")
            
             ##-----------------------------
             ## Save the original file as PNG
             ## todo: why save original image as PNG??
             ##
             ## Do a check before security attempting copy.
             ## If the check fails, do a save instead
             #if im.im.format != "PNG" or \
                #im.size[0] > 20000 or im.size[1] > 20000 or \
                #len(im.im.getbands()) > 4:
              ## Save as PNG (slow)
              #self.save_image(im, os.path.join(work_dir,'input_%i.orig.png' % i))
              ## delete the original
              #os.remove(input_files[0])
            #else:
              ## Move file (fast)
              #shutil.move(input_files[0],
                          #os.path.join(work_dir,'input_%i.orig.png' % i))

            
            ##-----------------------------
            ## convert to the expected input format: TODO: do it if needed ...
            
            ## crop first if available
            #if crop_info!=None:
                #crop_res = self.crop_input(im, i, demo_id, key, inputs_desc, crop_info)
                #res_data['info'] += crop_res['info']
                #if crop_res['status']=="OK":
                    #im_converted = image(crop_res['filename'])
                    #im_converted_filename = 'input_%i.crop.png' % i
                #else:
                    #im_converted = im.clone()
                    #im_converted_filename = 'input_%i.orig.png' % i
            #else:
                #im_converted = im.clone()
                #im_converted_filename = 'input_%i.orig.png' % i
            
            #if self.need_convert_or_resize(im_converted,input_desc):
                #print "need convertion or resize, input description: ", input_desc
                #output_msg = self.convert_and_resize(im_converted,input_desc)
                #input_msg += " Input {0}:".format(i)+output_msg+" "
                ## save a web viewable copy
                #im_converted.save(os.path.join(work_dir,'input_%i.png' % i),
                                  #compresslevel=self.png_compresslevel)
            #else:
                ## just create a symbolic link  
                #os.symlink(im_converted_filename,\
                           #os.path.join(work_dir,'input_%i.png' % i))
                
            #ext = input_desc['ext']
            ## why saving a copy of the converted image in non-png format ?
            ### save a working copy:
            ##if ext != ".png":
                ### Problem with PIL or our image class: this call seems to be
                ### problematic when saving PGM files. Not reentrant?? In any
                ### case, avoid calling it from a thread.
                ###threads.append(threading.Thread(target=self.save_image,
                ###               args = (im_converted, self.work_dir + 'input_%i' % i + ext))
                ##self.save_image(im_converted, self.work_dir + 'input_%i' % i + ext)


            #if im.size != im_converted.size:
                #input_msg += " {0} --> {1} ".format(im.size,im_converted.size)
                #print "The image has been resized for a reduced computation time ",
                #print  "({0} --> {1})".format(im.size,im_converted.size)
            ## update maximal dimensions information
            #max_width  = max(max_width,im_converted.size[0])
            #max_height = max(max_height,im_converted.size[1])
            ##self.cfg['meta']['input%i_size_x'%i] = im_converted.size[0]
            ##self.cfg['meta']['input%i_size_y'%i] = im_converted.size[1]
            #if input_msg!="":
                ## next line in html
                #msg += input_msg+"<br/>\n"
            ## end if type is image
          #else:
            ## check if we have a representing image to display
            #if len(input_files)>1:
              ## the number of input files should be 2...
              ## for the moment, only check for png file
              #png_file = os.path.join(work_dir,'input_%i.png' % i)
              ##if png_file in input_files:
                ### save in configuration the information to allow its display
                ##self.cfg['meta']['input%i_has_image'%i] = True
        ## end for i in range(nb_inputs)
        
        ## for compatibility with previous system, create input_0.sel.png
        ## as symbolic link
        #os.symlink('input_0.png', os.path.join(work_dir,'input_0.sel.png'))
        
        #res_data["info"] += " process_inputs() took: {0} sec.;".format(end-start)
        #res_data["max_width"]  = max_width
        #res_data["max_height"] = max_height
        
        return msg

    
    def copy_blobs(self, run_path, blobs_info):
        """
        copy the blobs in the run path. 
        The blobs can be uploaded by post method or a blobs from blob module
        """
        inputs_desc = blobs_info['ddl_inputs']
        crop_info   = blobs_info['crop_info']
        blob_url    = blobs_info['url']
        
        del blobs_info['ddl_inputs']
        del blobs_info['crop_info']
        del blobs_info['url']
        
        inputs_desc = json.loads(inputs_desc)
        crop_info   = json.loads(crop_info)
        nb_inputs = len(inputs_desc)
        
        blobfile = urllib.URLopener()
        for inputinfo in blobs_info.keys():
            # 1. retreive index
            posstart=inputinfo.index(':')
            idx = int(inputinfo[:posstart])
            #print inputs_desc[idx]
            inputinfo = inputinfo[posstart+1:]
            
            if ',' in inputinfo:
                # what should we do ? we should have two files here...
                inputfiles = inputinfo.split(',')
            else:
                inputfiles = [ inputinfo ]
            # extract input files to work dir as input_%i.ext
            for inputfile in inputfiles:
                basename  = inputfile[:inputfile.index('.')]
                ext       = inputfile[inputfile.index('.'):]
                blob_link =  blob_url +'/'+ basename + ext
                blobfile.retrieve(blob_link, os.path.join(run_path,'input_{0}{1}'.format(idx,ext)))
            
        msg = self.process_inputs(run_path, inputs_desc, crop_info)
        
        return 1

    
    @cherrypy.expose
    def run(self, demo_id, internal_demo_id,  **kwargs):
        """
        Check if a demo is already compiled, if not compiles it
        :param demo_id:   id demo
        :param ddl_build: build section of the ddl json 
        """
        print "### RUN in CORE ####"
        key = self.get_new_key(demo_id) 
        
        run_path = self.create_run_dir(demo_id, key)
        print "Run path is ",run_path
        
        blobs_info = kwargs.copy()
        self.copy_blobs(run_path, blobs_info)
        
        request = '?module=demoinfo&service=read_demo_description&demodescriptionID=' + internal_demo_id
        print self.proxy_server + request
        json_response = urllib.urlopen(self.proxy_server + request).read()
        response = json.loads(json_response)
        demo_description = json.loads(response['demo_description'])
        print "\n\n---"
        print demo_description['build']
        
        
        
        ###   ESTO TIRA BIEN PARA AHORA NO LO QUIERO!!
        #dr_winner = 'demorunner2'
        #request = '?module='+ dr_winner +'&service=ensure_compilation&demo_id=' + demo_id + '&ddl_build=' + ddl_build
        #print self.proxy_server + request
        #json_response = urllib.urlopen(self.proxy_server + request).read()
        
        #print "response ="
        #response = json.loads(json_response)
        #print response
        #status = response['status']
        
        response = {}
        response['status'] = 'KO' # Quiero que falle
        
        return json.dumps(response)



#-------------------------------------------------------------------------------
if __name__ == '__main__':

    cherrypy.tools.CORS = cherrypy.Tool('before_handler', CORS) 

    # config file and location settings
    base_dir = os.path.dirname(os.path.abspath(__file__))
    conf_file = os.path.join(base_dir, 'demo.conf')
    #conf_file_example = os.path.join(base_dir, 'demo.conf.example')
    cherrypy.log("app base_dir: %s" % base_dir,
                 context='SETUP', traceback=False)

    if not os.path.isfile(conf_file):
        cherrypy.log("warning: the conf file is missing, " \
                         "copying the example conf",
                     context='SETUP', traceback=False)
    
    cherrypy.config.update(conf_file)
    cherrypy.tools.cgitb = cherrypy.Tool('before_error_response', err_tb)
    # start the server give to demo_index the current object (self)
    cherrypy.quickstart(demo_index(), config=conf_file)
    
      
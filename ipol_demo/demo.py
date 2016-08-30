#! /usr/bin/python
"""
base cherrypy launcher for the IPOL demo app
"""

#TODO: blacklist from config file

import cherrypy
import sys


import shutil
from lib import base_app

import json     

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

from   misc     import prod
from image import thumbnail, image
import magic
from PIL import Image,ImageDraw
import mimetypes

import time
from   timeit   import default_timer as timer

from sendarchive import SendArchive

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
            self.server_address=  'http://{0}:{1}'.format(
                                  cherrypy.config['server.socket_host'],
                                  cherrypy.config['server.socket_port'])
            
            self.logs_dir = cherrypy.config.get("logs.dir")
            self.logs_name = cherrypy.config.get("logs.name")
            self.share_run_dir = cherrypy.config.get("running.dir")
            self.current_directory = os.getcwd()
            self.proxy_server = cherrypy.config.get("demo.proxy_server")
            
            self.mkdir_p(self.logs_dir)
            self.mkdir_p(self.share_run_dir)
            self.logger = self.init_logging()
            
            self.png_compresslevel=1
            
            self.stack_depth = 0 ### Maybe we should quit this. It's for JQuery Message I think....
            
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
    
    #---------------------------------------------------------------------------
    # INPUT HANDLING TOOLS (OLD with a few modifications)
    #---------------------------------------------------------------------------
    def save_image(self, im, fullpath):
        '''
        Save image object given full path
        '''
        self.stack_depth+=1
        start = timer()
        im.save(fullpath, compresslevel=self.png_compresslevel)
        end=timer()
        self.stack_depth-=1
        

    #---------------------------------------------------------------------------
    def need_convert(self, im, input_info):
        '''
        check if input image needs convertion
        '''
        mode_kw = {'1x8i' : 'L',
                    '3x8i' : 'RGB'}
        # check max size
        return  im.im.mode != mode_kw[input_info['dtype']]
            
    #---------------------------------------------------------------------------
    def need_convert_or_resize(self, im, input_info):
        '''
        Convert and resize an image object
        '''
        # check max size
        max_pixels = eval(str(input_info['max_pixels']))
        return  self.need_convert(im,input_info) or \
                prod(im.size) > max_pixels

    #---------------------------------------------------------------------------
    def convert_and_resize(self, im, input_info):
        '''
        Convert and resize an image object
        '''
        msg=""
        self.stack_depth+=1
        start = timer()
        if self.need_convert(im,input_info):
            im.convert(input_info['dtype'])
            msg += " converted to '{0}' ".format(input_info['dtype'])
        # check max size
        max_pixels = eval(str(input_info['max_pixels']))
        resize = prod(im.size) > max_pixels
        
        if resize:
            cherrypy.log("input resize")
            im.resize(max_pixels)
            if msg!= "":
                msg += "&"
            msg += " resized to {0}px ".format(max_pixels)
            print "msg",msg
        
        end=timer()
        self.stack_depth-=1
        
        return msg
    ###--------------------------------------------------------------------------
    ##          END BLOCK OF INPUT TOOLS
    ###--------------------------------------------------------------------------
    
    ##----------------------------
    #   OLD FUNCTIONS  - In the future, they should be refactored
    ##-----------------------------
    def crop_input(self, img, idx, work_dir, inputs_desc, crop_info):
        """
        Crop input if selected
            img: input image to crop
            idx: input position
            work_dir
            inputs_desc
            crop_info
        """
        print "#### crop_input ####"
        # for the moment, we can only crop the first image
        self.stack_depth += 1
        crop_start = timer()
        res_data = {}
        res_data['info'] = ""
        
        if idx!=0:
            res_data["status"] = "KO"
            return res_data
        
        cropped_filename = os.path.join(work_dir,'input_{0}.crop.png'.format(idx))
        res_data['filename'] = cropped_filename

        print "crop_info = {0}".format(crop_info)
        crop_info = json.loads(crop_info)
        
        if crop_info["enabled"]:
            # define x0,y0,x1,y1
            x0 = int(round(crop_info['x']))
            y0 = int(round(crop_info['y']))
            x1 = int(round(crop_info['x']+crop_info['w']))
            y1 = int(round(crop_info['y']+crop_info['h']))
            #save parameters
            try:
                ## TODO: get rid of eval()
                max_pixels  = eval(str(inputs_desc[0]['max_pixels']))
                # Karl: here different from base_app approach
                # crop coordinates are on original image size
                start=timer()
                img.crop((x0, y0, x1, y1))
                print " img.crop took: {0} seconds;".format(timer()-start)
                # resize if cropped image is too big
                if max_pixels and prod(img.size) > max_pixels:
                    start=timer()
                    img.resize(max_pixels, method="antialias")
                # save result
                self.save_image(img,cropped_filename)

            except ValueError as e:
                traceback.print_exc()
                res_data["status"] = "KO"
                res_data['info'] += " cropping failed with exception;"
                # TODO deal with errors in a clean way
                raise cherrypy.HTTPError(400, # Bad Request
                                            "Incorrect parameters, " +
                                            "image cropping failed.")
                return res_data
        else:
            res_data["status"]  = "KO"
            res_data['info'] += " no cropping area selected;"
            self.stack_depth -= 1
            return res_data
        
        res_data["status"] = "OK"
        end=timer()
        res_data["info"]   += " crop_input took: {0} seconds;".format(end-crop_start)
        print " crop_input took: {0} seconds;".format(end-crop_start)
        self.stack_depth -= 1
        
        return res_data

    
    def process_inputs(self, work_dir, inputs_desc, crop_info=None, res_data=None):
        """
        pre-process the input data
        we suppose that config has been initialized, and save the dimensions
        of each converted image in self.cfg['meta']['input$i_size_{x,y}']
        """
        print "#####  Entering process_inputs...  #####"
        self.stack_depth += 1
        start = timer()
        msg = ""
        max_width = 0
        max_height = 0
        nb_inputs = len(inputs_desc)
        
        for i in range(nb_inputs):
          input_msg = ""
          # check the input type
          input_desc = inputs_desc[i]
          # find files starting with input_%
          input_files = glob.glob(os.path.join(work_dir,'input_%i' % i+'.*'))
          if input_desc['type']=='image':
            # we deal with an image, go on ...
            print "Processing input {0}".format(i)
            if len(input_files)!=1:
                if  ('required' in inputs_desc[i].keys()) and \
                    inputs_desc[i]['required']:
                    # problem here
                    raise cherrypy.HTTPError(400, "Wrong number of inputs for an image")
                else:
                    # optional input missing, end of inputs
                    break
            else:
              # open the file as an image
              try:
                  im = image(input_files[0])
              except IOError:
                print "failed to read image " + input_files[0]
                raise cherrypy.HTTPError(400, # Bad Request
                                         "Bad input file")

            ##-----------------------------
            ## Save the original file as PNG
            ## todo: why save original image as PNG??
            ##
            ## Do a check before security attempting copy.
            ## If the check fails, do a save instead
            if  im.im.format != "PNG" or \
                im.size[0] > 20000 or im.size[1] > 20000 or \
                len(im.im.getbands()) > 4:
              # Save as PNG (slow)
              self.save_image(im, os.path.join(work_dir,'input_%i.orig.png' % i))
              # delete the original
              os.remove(input_files[0])
            else:
              # Move file (fast)
              shutil.move(input_files[0],
                          os.path.join(work_dir,'input_%i.orig.png' % i))

            ##-----------------------------
            ## convert to the expected input format: TODO: do it if needed ...
            if crop_info!=None:
                crop_res = self.crop_input(im, i, work_dir, inputs_desc, crop_info)
                res_data['info'] += crop_res['info']
                
                if crop_res['status']=="OK":
                    im_converted = image(crop_res['filename'])
                    im_converted_filename = 'input_%i.crop.png' % i
                else:
                    im_converted = im.clone()
                    im_converted_filename = 'input_%i.orig.png' % i
            else:
                im_converted = im.clone()
                im_converted_filename = 'input_%i.orig.png' % i
            
            if self.need_convert_or_resize(im_converted,input_desc):
                print "need convertion or resize, input description: ", input_desc
                output_msg = self.convert_and_resize(im_converted,input_desc)
                input_msg += " Input {0}:".format(i)+output_msg+" "
                # save a web viewable copy
                im_converted.save(os.path.join(work_dir,'input_%i.png' % i),
                                  compresslevel=self.png_compresslevel)
            else:
                # just create a symbolic link  
                os.symlink(im_converted_filename,\
                           os.path.join(work_dir,'input_%i.png' % i))
                
            ext = input_desc['ext']
            
            if im.size != im_converted.size:
                input_msg += " {0} --> {1} ".format(im.size,im_converted.size)
                print "The image has been resized for a reduced computation time ",
                print  "({0} --> {1})".format(im.size,im_converted.size)
            # update maximal dimensions information
            max_width  = max(max_width,im_converted.size[0])
            max_height = max(max_height,im_converted.size[1])
            if input_msg!="":
                # next line in html
                msg += input_msg+"<br/>\n"
            # end if type is image
          else:
            # check if we have a representing image to display
            if len(input_files)>1:
              # the number of input files should be 2...
              # for the moment, only check for png file
              png_file = os.path.join(work_dir,'input_%i.png' % i)
              
        
        # for compatibility with previous system, create input_0.sel.png
        # as symbolic link
        os.symlink('input_0.png', os.path.join(work_dir,'input_0.sel.png'))
        res_data["info"] += " process_inputs() "
        
        res_data["max_width"]  = max_width
        res_data["max_height"] = max_height
        
        return msg

    
    def input_upload(self, work_dir, blobs, inputs_desc, crop_info=None, **kwargs):
        """
        use the uploaded input files
        file_0, file_1, ... are the input files
        ddl_input is the input section of the demo description
        """
        print "#### input_upload ####"
        res_data = {}
        res_data['info'] = ''
        
        print "inputs_desc = ",inputs_desc
        nb_inputs = len(inputs_desc)
        
        
        for i in range(nb_inputs):
          file_up = blobs.pop('file_%i' % i,None)
          
          if file_up==None or file_up.filename == '':
            if  not('required' in inputs_desc[i].keys()) or \
                inputs_desc[i]['required']:
              ## missing file
              raise cherrypy.HTTPError(400, # Bad Request
                                       "Missing input file number {0}".format(i))
            else:
                # skip this input
                continue

          ## suppose than the file is in the correct format for its extension
          ext = inputs_desc[i]['ext']
          file_save = file(os.path.join(work_dir,'input_%i' % i + ext), 'wb')

          size = 0
          while True:
            ## TODO larger data size
            data = file_up.file.read(128)
            if not data:
                break
            size += len(data)
            if 'max_weight' in inputs_desc[i] and size > eval(str(inputs_desc[i]['max_weight'])):
                # file too heavy
                res_data['status'] = 'KO'
                res_data['info'] = "File too large, resize or use better compression"
                raise cherrypy.HTTPError(400, # Bad Request
                                          "File too large, " +
                                          "resize or use better compression")
                return res_data
            
            file_save.write(data)
          file_save.close()
        
        res_data['status'] = 'OK'
        
        return res_data
    
    def input_select_and_crop(self, work_dir, blob_url, blobs, crop_info=None):
        """
        use the selected available input images
        input parameters:
        returns:
        """
        print "#### input_select_and_crop begin ####"
        start = timer()
        self.stack_depth=0
        self.stack_depth+=1
        
        res_data = {}
        res_data['info'] = ''
        nb_inputs = len(blobs)
        
        # copy to work_dir
        blobfile = urllib.URLopener()
        print blobs
        for index,blob in blobs.items():
            print blob[0]
            extension = blob[0].split('.')
            blob_link =  blob_url +'/'+ blob[0]
            print blob_link
            blobfile.retrieve(blob_link, os.path.join(work_dir,'input_{0}.{1}'.format(index,extension[1])))
        
        return res_data

    ##---------------
    ### OLD FUNCTIONS BLOCK END -- Need a refactoring :)
    #--------------
    
    def copy_blobs(self, work_dir, input_type, blobs, ddl_inputs, crop_info=None):
        """
        copy the blobs in the run path. 
        The blobs can be uploaded by post method or a blobs from blob module
        """
        print "### Entering copy_blobs...  ###"
        res_data = {}
        
        if input_type == 'upload':
            res_data = self.input_upload(work_dir, blobs, ddl_inputs, crop_info) 
            
            if res_data['status'] == 'KO':
                return res_data

        elif input_type == 'blobset':
            blob_url = blobs['url']
            del blobs['url']
            res_data = self.input_select_and_crop(work_dir, blob_url, blobs, crop_info)
        
        msg = self.process_inputs(work_dir, ddl_inputs, crop_info, res_data)
        res_data["status"]  = "OK"
        res_data["message"] = "input files copied to the local path"
        res_data['process_inputs_msg'] = msg
        
        return res_data
    
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

        return key

    def create_run_dir(self, demo_id, key):
        """
        If it not exist, create a run_dir for a demo
        then, create a folder for the execution
        :param demo_id:   id demo
        :param run_folder: key 
        """
        demo_path = os.path.join(self.current_directory,\
                                 self.share_run_dir,\
                                 demo_id,\
                                  key)
        self.mkdir_p(demo_path)
        
        return demo_path
    
    @cherrypy.expose
    def run(self, demo_id, internal_demoid,  **kwargs):
        """
        Check if a demo is already compiled, if not compiles it
        :param demo_id:   id demo
        :param ddl_build: build section of the ddl json 
        """
        print "### RUN in CORE ####"
        print "demo_id =",demo_id, " internal_demoid=", internal_demoid
        print "kwargs=",kwargs
        
        if 'input_type' in kwargs:
            input_type = kwargs['input_type']
        
        if 'params' in kwargs:
            params = kwargs['params']
        
        if 'original' in kwargs:
            original_exp = kwargs['original']
        
        if 'crop_info' in kwargs:
            crop_info = kwargs['crop_info']
        else:
            crop_info=None
        
        if 'meta' in kwargs:
            meta = kwargs['meta']
        else:
            meta = {}
        
        blobs = {}
        if input_type == 'upload':
            i = 0
            while "file_{0}".format(i) in kwargs:
                fname="file_{0}".format(i)                
                blobs[fname] = kwargs[fname]
                i+=1
        
        elif input_type == 'blobset':
            blobs = json.loads(kwargs['blobs']) 
        
        try:
            request = '?module=demoinfo&service=read_last_demodescription_from_demo&demo_id=' + internal_demoid + '&returnjsons=True'
            json_response = urllib.urlopen(self.proxy_server + request).read()
            response = json.loads(json_response)
            last_demodescription = response['last_demodescription']
            
            ddl_json    = json.loads(json.loads(last_demodescription['json']))
            
            if 'build' in ddl_json:
                ddl_build   = ddl_json['build']
            if 'inputs' in ddl_json:
                ddl_inputs  = ddl_json['inputs']
            
        except Exception as ex:
            print "FAIL in DDL"
            self.logger.exception("The DDL from demoinfo has fail")
            res_data = {}
            res_data['info'] = 'The DDL from demoinfo has fail in the CORE'
            res_data['status'] = 'KO'
            return json.dump(res_data)
            
        
        ## End block for obtain DDL
        key = self.get_new_key(demo_id)
        work_dir = self.create_run_dir(demo_id, key)
        print "Run path is ",work_dir
        
        if input_type != 'noinputs':
            try:
                res_data = self.copy_blobs(work_dir, input_type, blobs, ddl_inputs, crop_info)
                
                if res_data["process_inputs_msg"] != "":
                     meta["process_inputs_msg"] = res_data["process_inputs_msg"]
                meta["max_width"]  = res_data["max_width"]
                meta["max_height"] = res_data["max_height"]
                meta["nb_inputs"]  = len(blobs)
                meta["original"]   = original_exp
                
            except Exception as ex:
                print "FAILURE IN COPY_BLOBS"
                print str(ex)
                self.logger.exception("Failure in copy_blobs")
                return json.dumps(res_data)
        else:
            res_data = {}
            res_data['info'] = ''
            res_data["status"]  = "OK"
        
        
        #try:
            #request = '?module=demodispatcher&service=wait_demoRunner&demo_id=' + str(demo_id) 
            #print self.proxy_server + request
            #json_response = urllib.urlopen(self.proxy_server + request).read()
            #response = json.loads(json_response)
            #dr_winner = response['url_of_selected_dr']
        #except Exception as ex:
                #pass
            
        dr_winner = 'demorunner' ## In the future, the demo_dispatcher request will be included here.
                        
        try:
            print "Entering dr.ensure_compilation()"
            
            userdata = {"module":dr_winner, "service":"ensure_compilation", "demo_id":demo_id, "ddl_build":json.dumps(ddl_build)}
            resp = requests.post(self.proxy_server, data=userdata)
            json_response = resp.json() 
            
            status = json_response['status']
            
            print "ensure_compilation response --> " + status
            
            if status == 'OK':
                print "dr.exec_and_wait()"
                
                userdata = {"module":dr_winner, "service":"exec_and_wait", "demo_id":demo_id, "key":key, "params":params }
                
                if 'run' in ddl_json:
                    userdata['ddl_run'] = json.dumps(ddl_json['run'])
                            
                if 'config' in ddl_json:
                    userdata['ddl_config'] = json.dumps(ddl_json['config'])
                
                userdata['meta'] = json.dumps(meta)
                
                resp = requests.post(self.proxy_server, data=userdata)
                
                json_response = resp.json() 
                json_response['work_url'] =  os.path.join(self.server_address,\
                                                            self.share_run_dir,\
                                                            demo_id,\
                                                            key) + '/'
                print "resp ",json_response
                
                # save res_data as a results.json file
                try:
                    with open(os.path.join(work_dir,"results.json"),"w") as resfile:
                        json.dump(json_response,resfile)
                except Exception:
                    print "Failed to save results.json file"
                    self.logger.exception("Failed to save results.json file")
                    return json.dumps(json_response)
                
                
                status = json_response['status']
                
                if status == 'OK':
                    print "archive.store_experiment()"
                    if original_exp == 'true':
                        ddl_archive = ddl_json['archive']
                        print ddl_archive
                        result_archive = SendArchive.prepare_archive(demo_id, work_dir, ddl_archive, json_response, self.proxy_server)
                else:
                    print "FAIL RUNNING"
                    self.logger.exception("Failed running in the demorunner")
                    return json.dumps(json_response)

            else:
                print "FAILURE IN THE COMPILATION"
                return json.dumps(json_response)
                
        except Exception as ex:
                print "Failure in the run function of the CORE"
                print str(ex)
                res_data['info'] = 'Failure in the run function of the CORE using ' + dr_winner + ' module'
                res_data["status"]  = "KO"
                return json.dumps(json_response)
            
        return json.dumps(json_response)



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
    
      
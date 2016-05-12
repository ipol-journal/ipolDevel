#!/usr/bin/env python
# -*- coding:utf-8 -*-

"""
This file implements the demo runner module,
which takes care of running an IPOL demo using web services
"""

# add lib path for import
import os.path, sys
sys.path.append(os.path.join(os.path.dirname(os.path.realpath(__file__)), "../../lib"))
sys.path.append(os.path.join(os.path.dirname(os.path.realpath(__file__)), "../.."))


import hashlib
from   datetime import datetime
from   random   import random
import urllib
from   timeit   import default_timer as timer
from   image    import thumbnail, image
from   misc     import prod
import PIL.ImageDraw

import threading
import cherrypy
import build_demo_base
import os
import json
import glob
import shutil
import time

import  run_demo_base
from    run_demo_base import RunDemoBase
from    run_demo_base import IPOLTimeoutError

import traceback

from sendarchive import SendArchive

class DemoRunner(object):
    """
    This class implements Web services to run IPOL demos
    """
    def __init__(self):
        """
        Initialize DemoRunner
        """
        self.running_dir = cherrypy.config['running.dir']
        self.current_directory = os.getcwd()
        self.server_address=  'http://{0}:{1}'.format(
                                  cherrypy.config['server.socket_host'],
                                  cherrypy.config['server.socket_port'])
        self.png_compresslevel=1
        self.stack_depth = 0

    #---------------------------------------------------------------------------
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
    @cherrypy.expose
    def init_demo(self, demo_id, ddl_build):
        """
        Check if a demo is already compiled, if not compiles it
        :param demo_id:   id demo
        :param ddl_build: build section of the ddl json 
        """
        print "#### init_demo ####"
        result = self.check_build(demo_id,ddl_build)
        print "result is ",result
        return json.dumps(result)

    #---------------------------------------------------------------------------
    def check_build(self, demo_id, ddl_build):
        """
            rebuild demo from source code if required
        """

        res_data = {}

        # reload demo description
        demo_path = os.path.join(self.current_directory,\
                                 self.running_dir,\
                                 demo_id)
        
        # parse stringified json
        ddl_build = json.loads(ddl_build)
        print "ddl_build = ", ddl_build

        print "---- check_build demo: {0:10}".format(demo_id),
        # we should have a dict or a list of dict
        if isinstance(ddl_build,dict):
            builds = [ ddl_build ]
        else:
            builds = ddl_build
        first_build = True
        for build_params in builds:
            bd = build_demo_base.BuildDemoBase( demo_path)
            bd.set_params(build_params)
            cherrypy.log("building", context='SETUP/%s' % demo_id,
                        traceback=False)
            try:
                make_info = bd.make(first_build)
                first_build=False
                res_data["status"]  = "OK"
                res_data["message"] = "Build for demo {0} checked".format(demo_id)
                res_data["info"]    = make_info
            except Exception as e:
                print "Build failed with exception ",e
                cherrypy.log("build failed (see the build log)",
                                context='SETUP/%s' % demo_id,
                                traceback=False)
                res_data["status"] = "KO"
                res_data["message"] = "Build for demo {0} failed".format(demo_id)
                return res_data
            
        print ""
        return res_data

    #---------------------------------------------------------------------------
    def WorkDir(self,demo_id,key):
        return os.path.join(    self.current_directory,\
                                self.running_dir,\
                                demo_id,\
                                'tmp',\
                                key+'/')

    #---------------------------------------------------------------------------
    def WorkUrl(self,demo_id,key):
        return os.path.join(    self.server_address,\
                                self.running_dir,\
                                demo_id,\
                                'tmp',\
                                key+'/')

    #---------------------------------------------------------------------------
    def BaseDir(self,demo_id,key):
        return os.path.join(    self.current_directory,\
                                self.running_dir,\
                                demo_id+'/')

    #---------------------------------------------------------------------------
    #
    # KEY MANAGEMENT
    #
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

        # reload demo description
        work_dir = self.WorkDir(demo_id,key)
        if not os.path.isdir(work_dir):
            os.makedirs(work_dir)

        return key
    

    #
    # INPUT HANDLING TOOLS
    #

    #---------------------------------------------------------------------------
    def save_image(self, im, fullpath):
        '''
        Save image object given full path
        '''
        self.stack_depth+=1
        start = timer()
        im.save(fullpath, compresslevel=self.png_compresslevel)
        end=timer()
        self.output( "save_image {0} took {1} sec".format(fullpath,end-start))
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
        self.output( "im.im.mode = {0}".format(im.im.mode))
        # check max size
        max_pixels = eval(str(input_info['max_pixels']))
        resize = prod(im.size) > max_pixels
        if resize:
            cherrypy.log("input resize")
            im.resize(max_pixels)
            if msg!= "":
                msg += "&"
            msg += " resized to {0}px ".format(max_pixels)
        end=timer()
        self.output( "convert_and_resize took {0} sec".format(end-start))
        self.stack_depth-=1
        return msg

    #---------------------------------------------------------------------------
    def process_inputs(self, demo_id, key, inputs_desc, crop_info, res_data):
        """
        pre-process the input data
        we suppose that config has been initialized, and save the dimensions
        of each converted image in self.cfg['meta']['input$i_size_{x,y}']
        """
        self.stack_depth += 1
        self.output("#### process_inputs ####")
        start = timer()
        msg = ""
        max_width = 0
        max_height = 0
        nb_inputs = len(inputs_desc)
        work_dir = self.WorkDir(demo_id,key)
        
        for i in range(nb_inputs):
          input_msg = ""
          # check the input type
          input_desc = inputs_desc[i]
          # find files starting with input_%i
          input_files = glob.glob(os.path.join(work_dir,'input_%i' % i+'.*'))
          
          if input_desc['type']=='image':
            # we deal with an image, go on ...
            self.output( "Processing input {0}".format(i))
            if len(input_files)!=1:
              # problem here
              raise cherrypy.HTTPError(400, "Wrong number of inputs for an image")
            else:
              # open the file as an image
              try:
                  im = image(input_files[0])
              except IOError:
                self.output( "failed to read image " + input_files[0])
                raise cherrypy.HTTPError(400, # Bad Request
                                         "Bad input file")

            
            #-----------------------------
            # Save the original file as PNG
            # todo: why save original image as PNG??
            #
            # Do a check before security attempting copy.
            # If the check fails, do a save instead
            if  im.im.format != "PNG" or \
                im.size[0] > 20000 or im.size[1] > 20000 or \
                len(im.im.getbands()) > 4:
              # Save as PNG (slow)
              self.output( "calling self.save_image()")
              self.save_image(im, os.path.join(work_dir,'input_%i.orig.png' % i))
              # delete the original
              os.remove(input_files[0])
            else:
              # Move file (fast)
              shutil.move(input_files[0],
                          os.path.join(work_dir,'input_%i.orig.png' % i))

            
            #-----------------------------
            # convert to the expected input format: TODO: do it if needed ...
            
            # crop first if available
            if crop_info!=None:
                crop_res = self.crop_input(im, i, demo_id, key, inputs_desc, crop_info)
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
            # why saving a copy of the converted image in non-png format ?
            ## save a working copy:
            #if ext != ".png":
                ## Problem with PIL or our image class: this call seems to be
                ## problematic when saving PGM files. Not reentrant?? In any
                ## case, avoid calling it from a thread.
                ##threads.append(threading.Thread(target=self.save_image,
                ##               args = (im_converted, self.work_dir + 'input_%i' % i + ext))
                #self.save_image(im_converted, self.work_dir + 'input_%i' % i + ext)


            if im.size != im_converted.size:
                input_msg += " {0} --> {1} ".format(im.size,im_converted.size)
                print "The image has been resized for a reduced computation time ",
                print  "({0} --> {1})".format(im.size,im_converted.size)
            # update maximal dimensions information
            max_width  = max(max_width,im_converted.size[0])
            max_height = max(max_height,im_converted.size[1])
            #self.cfg['meta']['input%i_size_x'%i] = im_converted.size[0]
            #self.cfg['meta']['input%i_size_y'%i] = im_converted.size[1]
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
              #if png_file in input_files:
                ## save in configuration the information to allow its display
                #self.cfg['meta']['input%i_has_image'%i] = True
        # end for i in range(nb_inputs)
        
        # for compatibility with previous system, create input_0.sel.png
        # as symbolic link
        os.symlink('input_0.png', os.path.join(work_dir,'input_0.sel.png'))
        
        end=timer()
        self.output( " process_inputs() took: {0} sec.;".format(end-start))
        res_data["info"] += " process_inputs() took: {0} sec.;".format(end-start)
        res_data["max_width"]  = max_width
        res_data["max_height"] = max_height
        
        self.stack_depth -= 1
        self.output("#### process_inputs end ####")
        return msg


    #---------------------------------------------------------------------------
    @cherrypy.expose
    def input_upload(self, **kwargs):
        """
        use the uploaded input files
        file_0, file_1, ... are the input files
        demo_id   id of the current demo
        ddl_input is the input section of the demo description
        """
        
        print "#### input_upload ####"
        print "args:", kwargs
        res_data = {}
        res_data['info'] = ''
        # we need a unique key for the execution
        demo_id = kwargs['demo_id']
        print "demo_id=",demo_id
        key = self.get_new_key(demo_id)
        res_data["key"]     = key
        work_dir = self.WorkDir(demo_id,key)
        print "ddl_inputs = ",kwargs['ddl_inputs']
        inputs_desc = json.loads(kwargs['ddl_inputs'])
        nb_inputs = len(inputs_desc)
        
        for i in range(nb_inputs):
          file_up = kwargs['file_%i' % i]
          
          if file_up.filename == '':
            if  not('required' in inputs_desc[i].keys()) or \
                inputs_desc[i]['required']:
              # missing file
              raise cherrypy.HTTPError(400, # Bad Request
                                       "Missing input file number {0}".format(i))
            else:
                # skip this input
                continue

          # suppose than the file is in the correct format for its extension
          ext = inputs_desc[i]['ext']
          file_save = file(os.path.join(work_dir,'input_%i' % i + ext), 'wb')

          size = 0
          while True:
            # TODO larger data size
            data = file_up.file.read(128)
            if not data:
                break
            size += len(data)
            if 'max_weight' in inputs_desc[i] and size > eval(str(inputs_desc[i]['max_weight'])):
                # file too heavy
                raise cherrypy.HTTPError(400, # Bad Request
                                          "File too large, " +
                                          "resize or use better compression")
            file_save.write(data)
          file_save.close()

        crop_info=None
        msg = self.process_inputs(demo_id, key, inputs_desc, crop_info, res_data)
        
        #msg = self.process_inputs()
        #self.log("input uploaded")
        #self.cfg['meta']['original'] = True
        #self.cfg['meta']['max_width']  = self.max_width;
        #self.cfg['meta']['max_height'] = self.max_height;
        #self.cfg.save()

        res_data['status'] = "OK"
        if msg!="":
            res_data['process_inputs_msg'] = msg
        print "upload res_data=",res_data
        return json.dumps(res_data)


    #---------------------------------------------------------------------------
    def crop_input(self, img, idx, demo_id, key, inputs_desc, crop_info):
        """
        Crop input if selected
            img: input image to crop
            idx: input position
            demo_id
            key
            inputs_desc
            crop_info
        """

        self.stack_depth += 1
        self.output("#### crop_input ####")
        crop_start = timer()
        res_data = {}
        res_data['info'] = ""
        # for the moment, we can only crop the first image
        if idx!=0:
            res_data["status"] = "KO"
            return res_data
            
        work_dir = self.WorkDir(demo_id,key)
        #initial_filename = os.path.join(work_dir,'input_{0}.orig.png'.format(idx))
        cropped_filename = os.path.join(work_dir,'input_{0}.crop.png'.format(idx))
        res_data['filename'] = cropped_filename
        self.output( "crop_info = {0}".format(crop_info))
        
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
                # ----- this code is not used anymore since
                #       uploaded images are sent after crop
                #       we will also save the crop information in archive
                #       to be able to reload the experiment from archive in the 
                #       future
                ##
                ## cut subimage from original image
                ##
                ## draw selected rectangle on the image
                #imgS        = image(initial_filename)
                #self.output("imgS mode = {0}".format(imgS.im.mode))
                ## need to convert image to RGB mode before drawing ...
                #start=timer()
                #imgS.convert('3x8i')
                #self.output(" imgS.convert('3x8i') took: {0} seconds;".format(timer()-start))
                #start=timer()
                ##imgS.draw_line([(x0, y0), (x1, y0), (x1, y1), (x0, y1), (x0, y0)],
                                ##color="red")
                ##imgS.draw_line([(x0+1, y0+1), (x1-1, y0+1), (x1-1, y1-1),
                                ##(x0+1, y1-1), (x0+1, y0+1)], color="white")
                #self.output(" draw_lines took: {0} seconds;".format(timer()-start))
                #self.save_image(imgS,os.path.join(work_dir,'input_{0}s.png'.format(idx)))
                
                # Karl: here different from base_app approach
                # crop coordinates are on original image size

                #start=timer()
                #img = image(initial_filename)
                #self.output(" read image took: {0} seconds;".format(timer()-start))
                start=timer()
                img.crop((x0, y0, x1, y1))
                self.output(" img.crop took: {0} seconds;".format(timer()-start))
                # resize if cropped image is too big
                if max_pixels and prod(img.size) > max_pixels:
                    start=timer()
                    img.resize(max_pixels, method="antialias")
                    self.output(" img.resize took: {0} seconds;".format(timer()-start))
                # save result
                self.save_image(img,cropped_filename)

            except ValueError as e:
                self.output("crop failed with exception : {0}".format(e))
                traceback.print_exc()
                res_data["status"] = "KO"
                res_data['info'] += " cropping failed with exception;"
                # TODO deal with errors in a clean way
                raise cherrypy.HTTPError(400, # Bad Request
                                            "Incorrect parameters, " +
                                            "image cropping failed.")
                self.stack_depth -= 1
                return res_data
        else:
            res_data["status"]  = "KO"
            res_data['info'] += " no cropping area selected;"
            self.stack_depth -= 1
            return res_data

        res_data["status"]  = "OK"
        end=timer()
        res_data["info"]    += " crop_input took: {0} seconds;".format(end-crop_start)
        self.output(" crop_input took: {0} seconds;".format(end-crop_start))
        self.stack_depth -= 1
        return res_data


    def output(self, mess):
        print "  "*self.stack_depth+mess

    #---------------------------------------------------------------------------
    @cherrypy.expose
    def input_select_and_crop(self, **kwargs):
        """
        use the selected available input images
        input parameters:
            demo_id
            ddl_inputs
            url
            list of inputs
        returns:
            { key, status, message }
        """
        start = timer()
        self.stack_depth=0
        self.output("#### input_select_and_crop begin ####")
        self.stack_depth+=1
        res_data = {}
        res_data['info'] = ''
        # we need a unique key for the execution
        demo_id = kwargs.pop('demo_id',None)
        key = self.get_new_key(demo_id)
        res_data["key"]     = key
        work_dir = self.WorkDir(demo_id,key)
        inputs_desc = kwargs.pop('ddl_inputs',None)
        inputs_desc = json.loads(inputs_desc)

        crop_info   = kwargs.pop('crop_info',None)
        crop_info   = json.loads(crop_info)

        nb_inputs = len(inputs_desc)

        blob_url = kwargs.pop('url',None)
        self.output("blob_url: {0}".format(blob_url))
        self.output("kwargs: {0}".format(kwargs))
        
        self.output("\n-----\ninput_select : {0}".format(kwargs.keys()))
        # copy to work_dir
        blobfile = urllib.URLopener()
        for inputinfo in kwargs.keys():
          self.output("\n**\n")
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
          self.output("inputfiles: {0}".format(inputfiles))
          for inputfile in inputfiles:
            start=timer()
            self.output( "---- inputfile: '{0}'".format(inputfile))
            self.output( "{0}".format(type(inputfile)))
            basename  = inputfile[:inputfile.index('.')]
            ext       = inputfile[inputfile.index('.'):]
            self.output( "basename : {0}".format(basename))
            blob_link =  blob_url +'/'+ basename + ext
            self.output("blob_link = {0}".format(blob_link))
            blobfile.retrieve(blob_link, 
                              os.path.join(work_dir,'input_{0}{1}'.format(idx,ext)))
            end=timer()
            self.output("---- retrieving file took {0} seconds".format(end-start))
        
        msg = self.process_inputs(demo_id, key, inputs_desc,crop_info, res_data)
        ##self2.log("input selected : %s" % kwargs.keys()[0])
        #self.cfg['meta']['original'] = False
        #self.cfg['meta']['max_width']  = self.max_width;
        #self.cfg['meta']['max_height'] = self.max_height;
        #self.cfg.save()

        # Let users copy non-standard input into the work dir
        # don't have fnames here
        #self2.input_select_callback(fnames)

        ## jump to the params page
        #return self.params(msg=msg, key=self2.key)
        
        res_data["status"]  = "OK"
        res_data["message"] = "input files copied to the local path"
        if msg!="":
            res_data['process_inputs_msg'] = msg
        self.stack_depth-=1
        self.output("#### input_select_and_crop:{0} sec.".format(timer()-start))
        return json.dumps(res_data)


    #---------------------------------------------------------------------------
    @cherrypy.expose
    def run_demo(self, demo_id, key, ddl_json, params, meta):
        
        res_data = {}
        res_data["key"] = key
        print "#### run demo ####"
        print "demo_id = ",demo_id
        print "key = ",key
        ddl_json = json.loads(ddl_json)
        ddl_run = ddl_json['run']
        print "ddl_run = ",ddl_run
        params  = json.loads(params)
        print "params = ",params
        res_data["work_url"] = self.WorkUrl(demo_id,key)
        res_data['params']   = params
        res_data['algo_info'] = {}
        res_data['algo_meta'] = json.loads(meta)
        
        # run the algorithm
        try:
            run_time = time.time()
            #self.cfg.save()
            self.run_algo(demo_id,key,ddl_run, params, res_data)
            #self.cfg.Reload()
            ## re-read the config in case it changed during the execution
            res_data['algo_info']['run_time'] = time.time() - run_time
            res_data['status'] = 'OK'
        except IPOLTimeoutError:
            res_data['status'] = 'KO'
            res_data['error'] = 'timeout'
        except RuntimeError as e:
            #print "self.show_results_on_error =", self.show_results_on_error
            #if not(self.show_results_on_error):
                #return self.error(errcode='runtime',errmsg=str(e))
            #else:
                #self.cfg['info']['run_time'] = time.time() - run_time
                #self.cfg['info']['status']   = 'failure'
                #self.cfg['info']['error']    = str(e)
                #self.cfg.save()
                #pass
            res_data['algo_info']['status']   = 'failure'
            res_data['algo_info']['run_time'] = time.time() - run_time
            res_data['status']   = 'KO'
            res_data['error']    = str(e)
            
        # check if new config fields
        if 'config' in ddl_json.keys():
            ddl_config = ddl_json['config']
            if 'info_from_file' in ddl_config.keys():
                for info in ddl_config['info_from_file']:
                    print "*** ",info
                    filename = ddl_config['info_from_file'][info]
                    try:
                        work_dir = self.WorkDir(demo_id,key)
                        f = open( os.path.join(work_dir,filename))
                        print "open ok"
                        file_lines = f.read().splitlines()
                        print file_lines
                        # remove empty lines and replace new lines with ' | '
                        new_string = " | ".join([ll.rstrip() for ll in file_lines if ll.strip()])
                        print new_string
                        res_data['algo_info'][info] = new_string
                        f.close()
                    except Exception as e:
                        print "failed to get info ",  info, " from file ", os.path.join(work_dir,filename)
                        print "Exception ",e

        # Files must be stored by the archive module
        if (len(ddl_json['inputs'])==0) or \
            res_data['algo_meta']['original']:
            work_dir = self.WorkDir(demo_id,key)
            SendArchive.prepare_archive(work_dir,ddl_json['archive'],res_data)
            res_data["send_archive"]=True
        else:
            res_data["send_archive"]=False

        return json.dumps(res_data)
        
        
    #---------------------------------------------------------------------------
    # Core algorithm runner
    #---------------------------------------------------------------------------
    def run_algo(self,demo_id,key,ddl_run,params, res_data):
        """
        the core algo runner
        """
        
        # refresh demo description ??
        print "----- run_algo begin -----"
        work_dir = self.WorkDir(demo_id,key)
        base_dir = self.BaseDir(demo_id,key)
        rd = run_demo_base.RunDemoBase(base_dir, work_dir)
        rd.set_logger(cherrypy.log)
        #if 'demo.extra_path' in cherrypy.config:
            #rd.set_extra_path(cherrypy.config['demo.extra_path'])
        rd.set_algo_params(params)
        rd.set_algo_info  (res_data['algo_info'])
        rd.set_algo_meta  (res_data['algo_meta'])
        #rd.set_MATLAB_path(self.get_MATLAB_path())
        rd.set_demo_id(demo_id)
        rd.set_commands(ddl_run)
        print "--"
        rd.run_algo()
        print "--"
        ## take into account possible changes in parameters
        res_data['params']      = rd.get_algo_params()
        res_data['algo_info']   = rd.get_algo_info()
        res_data['algo_meta']   = rd.get_algo_meta()
        #print "self.cgf['param']=",self.cfg['param']
        print "----- run_algo end -----"
        return

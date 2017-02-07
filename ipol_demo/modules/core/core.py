#!/usr/bin/python

"""
IPOL Core module
"""

import base64
import tempfile
import sys
import os

# To send emails
import smtplib
from email.mime.text import MIMEText
from email.mime.application import MIMEApplication
from email.mime.multipart import MIMEMultipart

import xml.etree.ElementTree as ET

# [ToDo] [Miguel] Change this by a normal import!
sys.path.append(os.path.join(\
    os.path.dirname(os.path.realpath(__file__)), "Tools"))
#
from misc import prod
from image import image
from sendarchive import SendArchive



import sys
import shutil
import json

import errno
import logging
import os
import os.path

import urllib

import hashlib
from   datetime import datetime
from   random   import random
import glob
import time

import tarfile
import zipfile

import socket

from libtiff import TIFF
import png

import requests
import cherrypy


#-------------------------------------------------------------------------------
class Core(object):
    """
    Core index used as the root app
    """

    def init_logging(self):
        """
        Initialize the error logs of the module.
        """
        logs_dir_abs = os.path.join(os.path.dirname(os.path.realpath(__file__)), self.logs_dir_rel)
        self.mkdir_p(logs_dir_abs)
        logger = logging.getLogger(logs_dir_abs)
        logger.setLevel(logging.ERROR)
        handler = logging.FileHandler(os.path.join(logs_dir_abs, self.logs_name))
        formatter = logging.Formatter(\
          '%(asctime)s ERROR in %(message)s',\
          datefmt='%Y-%m-%d %H:%M:%S')
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
            self.host_name = cherrypy.config['server.socket_host']


            # Read configuration file
            self.serverEnvironment = cherrypy.config.get("server.environment").lower()

            self.demorunners_file = cherrypy.config.get("demorunners_file")
            self.logs_dir_rel = cherrypy.config.get("logs.dir")
            self.logs_name = cherrypy.config.get("logs.name")
            self.logger = self.init_logging()

            self.project_folder = cherrypy.config.get("project_folder")
            self.blobs_folder = cherrypy.config.get("blobs_folder")
            self.demoExtrasFilename = cherrypy.config.get("demoExtrasFilename")

            self.shared_folder_rel = cherrypy.config.get("shared_folder")
            self.shared_folder_abs = os.path.join(self.project_folder, self.shared_folder_rel)
            self.demoExtrasMainDir = os.path.join(\
              self.shared_folder_abs, \
              cherrypy.config.get("demoExtrasDir"))
            self.dl_extras_dir = os.path.join(self.shared_folder_abs, \
              cherrypy.config.get("dl_extras_dir"))
            self.share_run_dir_rel = cherrypy.config.get("running.dir")
            self.share_run_dir_abs = os.path.join(\
              self.shared_folder_abs, self.share_run_dir_rel)

            self.load_demorunners()

            #Create shared folder if not exist
            self.mkdir_p(self.shared_folder_abs)

            #create running dir and demoextras dirs
            self.mkdir_p(self.share_run_dir_abs)
            self.mkdir_p(self.dl_extras_dir)
            self.mkdir_p(self.demoExtrasMainDir)
            #return to core

            # Configure
            self.png_compresslevel = 1

            print "IPOL Core module started"

        except Exception as ex:
            self.logger.exception("__init__", str(ex))

    def load_demorunners(self):
        """
        Read demorunners xml
        """
        dict_demorunners = {}
        tree = ET.parse(self.demorunners_file)
        root = tree.getroot()

        for demorunner in root.findall('demorunner'):
            dict_tmp = {}
            list_tmp = []

            for capability in demorunner.findall('capability'):
                list_tmp.append(capability.text)

            dict_tmp["server"] = demorunner.find('server').text
            dict_tmp["serverSSH"] = demorunner.find('serverSSH').text
            dict_tmp["capability"] = list_tmp

            dict_demorunners[demorunner.get('name')] = dict_tmp

        self.demorunners = dict_demorunners

    @cherrypy.expose
    def refresh_demorunners(self):
        '''
        refresh demorunners information and alert the dispatcher module
        '''
        data = {}
        data["status"] = "OK"

        try:
            # Reload DRs config
            self.load_demorunners()

            # Ask Dispatcher to reload too
            self.post(self.host_name, "dispatcher", "refresh_demorunners")
        except Exception as ex:
            print ex
            self.logger.exception("refresh_demorunners")
            data["status"] = "KO"
            data["message"] = "Can not load demorunners.xml"

        return json.dumps(data)

    @cherrypy.expose
    def get_demorunners(self):
        '''
        Get the information of the demorunners
        '''
        data = {}
        data["status"] = "OK"
        try:
            data["demorunners"] = str(self.demorunners)
        except Exception as ex:
            print ex
            self.logger.exception("get_demorunners")
            data["status"] = "KO"
            data["message"] = "Can not get demorunners"

        return json.dumps(data)

    def demorunners_workload(self):
        """
        Get the workload of each DR
        """
        dr_wl = {}
        for dr_name in self.demorunners:
            try:
                resp = self.post(self.demorunners[dr_name]['server'],\
                  'demorunner', 'get_workload')
                response = resp.json()
                if response['status'] == 'OK':
                    dr_wl[dr_name] = response['workload']
                else:
                    self.error_log("demorunners_workload", \
                      "get_workload returned KO for DR='{}'".\
                      format(dr_name))
                    dr_wl[dr_name] = 100.0
            except Exception as ex:
                s = "Error when trying to obtain the \
workload of '{}'".format(dr_name)
                self.logger.exception(s)
                print "Error when trying to obtain the workload of '{}' - {}".format(dr_name, ex)
        return dr_wl

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
            # Better safe than sorry
            if exc.errno == errno.EEXIST and os.path.isdir(path):
                pass
            else:
                raise

        return created

    @cherrypy.expose
    def index(self):
        """
        Index page
        """

        resp = self.post(self.host_name, 'demoinfo', 'demo_list')
        response = resp.json()
        status = response['status']

        cherrypy.response.headers['Content-Type'] = 'text/html'
        if status == 'KO':
            string = """
                 <!DOCTYPE html>
                 <html lang="en">
                 <head>
                 <meta charset="utf-8">
                 <title>IPOL demos</title>
                 </head>
                 <body>
                 <h2>IPOL internal error: demoInfo module returned KO</h2><br>
                 </body>
                 </html>
                 """
            return string

        demo_list = response['demo_list']
        
        # Get all publication states
        demos_by_state = dict()
        for demo in demo_list:
            publication_state = demo["state"]
            if publication_state not in demos_by_state:
                demos_by_state[publication_state] = []
            
            demos_by_state[publication_state].append( {\
              'editorsdemoid': demo['editorsdemoid'], \
              'editorsdemoid': demo['editorsdemoid'], \
              'title': demo['title'] \
            })

        demos_string = ""
        
        # Show demos according to their state
        for publication_state in demos_by_state.keys():
            demos_string += "<h2>{}</h2>".format(publication_state)
            
            for demo_data in demos_by_state[publication_state]:
                demos_string += "Demo #{}: <a href='/demo/clientApp/demo.html?id={}'>{}</a><br>".format(
                    demo_data['editorsdemoid'], demo_data['editorsdemoid'], demo_data['title'])

        string = """
                 <!DOCTYPE html>
                 <html lang="en">
                 <head>
                 <meta charset="utf-8">
                 <title>IPOL demos</title>
                 </head>
                 <body>
                 <h1>List of demos</h1>
                 <h3>The demos whose ID begins with 77777 are workshops and those with 55555 are tests.</h3><br>
                 {}
                 </body>
                 </html>
                 """.format(demos_string)

        return string

    @cherrypy.expose
    def demo(self):
        '''
        Return a HTML page with the list of demos.
        '''
        return self.index()


    @staticmethod
    @cherrypy.expose
    def ping():
        """
        Ping service: answer with a PONG.
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
        except Exception:
            self.logger.exception("shutdown")
        return json.dumps(data)

    @staticmethod
    @cherrypy.expose
    def default(attr):
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
        # [Miguel] It's not clear to me what stack_depth is used for.
        # In any case, it seems that probably we have here a typical race condition.
        im.save(fullpath, compresslevel=self.png_compresslevel)


    #---------------------------------------------------------------------------
    @staticmethod
    def needs_convert(im, input_info):
        '''
        checks if input image needs convertion
        '''
        mode_kw = {'1x8i' : 'L',\
                   '3x8i' : 'RGB'}
        # check max size
        return  im.im.mode != mode_kw[input_info['dtype']]

    #---------------------------------------------------------------------------
    def needs_convert_or_resize(self, im, input_info):
        '''
        Convert and resize an image object
        '''
        # check max size
        max_pixels = eval(str(input_info['max_pixels']))
        return self.needs_convert(im, input_info) or \
               prod(im.size) > max_pixels

    #---------------------------------------------------------------------------
    def convert_and_resize(self, im, input_info):
        '''
        Convert and resize an image object
        '''
        msg = ""
        if self.needs_convert(im, input_info):
            im.convert(input_info['dtype'])
            msg += " converted to '{0}' ".format(input_info['dtype'])
        # check max size
        max_pixels = eval(str(input_info['max_pixels']))
        resize = prod(im.size) > max_pixels

        if resize:
            im.resize(max_pixels)
            if msg != "":
                msg += "&"
            msg += " resized to {0}px ".format(max_pixels)
            print "msg", msg
        return msg

    @cherrypy.expose
    def convert_tiff_to_png(self, img):
        '''
        Converts the input TIFF to PNG.
        This is used by the web interface for visualization purposes
        '''
        data = {}
        data["status"] = "KO"
        try:
            temp_file = tempfile.NamedTemporaryFile()
            temp_file.write(base64.b64decode(img))
            temp_file.seek(0)

            tiffFile = TIFF.open(temp_file.name, mode='r')
            tiffImage = tiffFile.read_image()
            # Get number of rows, columns, and channels
            Nrow, Ncolumn, _ = tiffImage.shape

            pixelMatrix = tiffImage[:, :, 0:3].reshape(\
              (Nrow, Ncolumn * 3), order='C').astype(tiffImage.dtype)
            tmp_file = tempfile.SpooledTemporaryFile()

            bitdepth = int(tiffImage.dtype.name.split("uint")[1])
            writer = png.Writer(Ncolumn, Nrow, \
              bitdepth=bitdepth, greyscale=False)

            writer.write(tmp_file, pixelMatrix)
            tmp_file.seek(0)
            encoded_string = base64.b64encode(tmp_file.read())

            data["img"] = encoded_string
            data["status"] = "OK"
        except Exception as ex:
            print "Failed to convert image from tiff to png", ex
            self.logger.exception("Failed to convert image from tiff to png")
        return json.dumps(data)


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

        if idx != 0:
            return False, None

        filename = os.path.join(work_dir, \
          'input_{0}.crop.png'.format(idx))

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
                ## [Miguel][ToDo]
                ## TODO: get rid of ALL eval/exec!!!
                max_pixels = eval(str(inputs_desc[0]['max_pixels']))
                # Karl: here different from base_app approach
                # crop coordinates are on original image size
                img.crop((x0, y0, x1, y1))
                # resize if cropped image is too big
                if max_pixels and prod(img.size) > max_pixels:
                    img.resize(max_pixels, method="antialias")
                # save result
                self.save_image(img, filename)
            except ValueError:
                return False, None

        else:
            return False, None

        return True, filename


    def process_inputs(self, work_dir, inputs_desc, crop_info=None):
        """
        pre-process the input data
        """
        print "#####  Entering process_inputs...  #####"
        msg = ""
        max_width = 0
        max_height = 0
        nb_inputs = len(inputs_desc)

        for i in range(nb_inputs):
            input_msg = ""
            # check the input type
            input_desc = inputs_desc[i]
            # find files starting with input_%
            input_files = glob.glob(os.path.join(work_dir, \
              'input_%i' % i+'.*'))
            if input_desc['type'] == 'image':
            # we deal with an image, go on ...
                print "Processing input {0}".format(i)
                if len(input_files) != 1:
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
                ##
                ## Do a check before security attempting copy.
                ## If the check fails, do a save instead
                if  im.im.format != "PNG" or \
                    im.size[0] > 20000 or im.size[1] > 20000 or \
                    len(im.im.getbands()) > 4:
                    # Save as PNG (slow)
                    self.save_image(im, os.path.join(work_dir, \
                      'input_%i.orig.png' % i))
                    # delete the original
                    os.remove(input_files[0])
                else:
                    # Move file (fast)
                    shutil.move(input_files[0], \
                      os.path.join(work_dir, 'input_%i.orig.png' % i))

                ##-----------------------------
                ## convert to the expected input format. TODO: do it if needed ...
                if crop_info is not None:
                    status, filename = self.crop_input(im, i, work_dir, inputs_desc, crop_info)

                    if status:
                        im_converted = image(filename)
                        im_converted_filename = 'input_%i.crop.png' % i
                    else:
                        im_converted = im.clone()
                        im_converted_filename = 'input_%i.orig.png' % i
                else:
                    im_converted = im.clone()
                    im_converted_filename = 'input_%i.orig.png' % i

                if self.needs_convert_or_resize(im_converted, input_desc):
                    print "need convertion or resize, input description: ", input_desc
                    output_msg = self.convert_and_resize(im_converted,\
                      input_desc)
                    input_msg += " Input {0}:".format(i)+output_msg+" "
                    # save a web viewable copy
                    im_converted.save(os.path.join(work_dir,\
                      'input_%i.png' % i), \
                      compresslevel=self.png_compresslevel)
                else:
                    # just create a symbolic link
                    os.symlink(im_converted_filename,\
                      os.path.join(work_dir, 'input_%i.png' % i))

                if im.size != im_converted.size:
                    input_msg += " {0} --> {1} ".\
                      format(im.size, im_converted.size)
                    print "The image has been resized for a reduced computation time ",
                    print  "({0} --> {1})".\
                      format(im.size, im_converted.size)
                # update maximal dimensions information
                max_width = max(max_width, im_converted.size[0])
                max_height = max(max_height, im_converted.size[1])
                if input_msg != "":
                    # next line in html
                    msg += input_msg + "<br/>\n"
                # end if type is image
            else:
                # check if we have a representing image to display
                if len(input_files) > 1:
                    # the number of input files should be 2...
                    # for the moment, only check for png file

                    # [ToDo] [Miguel] This png_file variable is
                    # never used!!!
                    png_file = os.path.join(work_dir,\
                      'input_%i.png' % i)


    @staticmethod
    def input_upload(work_dir, blobs, inputs_desc):
        """
        use the uploaded input files
        file_0, file_1, ... are the input files
        ddl_input is the input section of the demo description
        """
        print "#### input_upload ####"

        print "inputs_desc = ", inputs_desc
        nb_inputs = len(inputs_desc)


        for i in range(nb_inputs):
            file_up = blobs.pop('file_%i' % i, None)

            if file_up is None or file_up.filename == '':
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
            file_save = file(os.path.join(\
              work_dir, 'input_%i' % i + ext), 'wb')

            size = 0
            while True:
                ## TODO larger data size
                data = file_up.file.read(128)
                if not data:
                    break
                size += len(data)
                if 'max_weight' in inputs_desc[i] and\
                  size > eval(str(inputs_desc[i]['max_weight'])):
                    # file too heavy
                    # Bad Request
                    raise cherrypy.HTTPError(400, \
                      "File too large, " + \
                       "resize or compress more")

                file_save.write(data)
            file_save.close()


    def copy_blobset_from_physical_location(self, work_dir, blobs):
        """
        use the selected available input images
        input parameters:
        returns:
        """
        print "#### input_select_and_crop begin ####"

        blob_physical_location = blobs['physical_location']
        del blobs['physical_location']
        del blobs['url']

        # copy to work_dir
        for index, blob in blobs.items():
            original_blob_path = os.path.join(self.blobs_folder,\
              blob_physical_location, blob[0])
            extension = blob[0].split('.')
            try:
                shutil.copy(original_blob_path, os.path.join(\
                  work_dir, 'input_{0}.{1}'.\
                  format(index, extension[1])))
            except Exception as ex:
                s = "Copy blobs to physical location, \
work_dir={}, original_blob_path={}".\
format(work_dir, original_blob_path)
                self.logger.exception(s)
                print ex

    ##---------------
    ### OLD FUNCTIONS BLOCK END -- Need a refactoring :)
    #--------------


    @staticmethod
    def download(url_file, filename):
        """
        Download a file from the network
        @param url: source url
        @param fname: destination file name

        @return: successfull process
        """

        try:
            url_handle = urllib.urlopen(url_file)
            file_handle = open(filename, 'w')
            file_handle.write(url_handle.read())
            file_handle.close()
            success = 0
        except Exception:
            success = 1

        return success

    @staticmethod
    def extract(filename, target):
        """
        extract tar, tgz, tbz and zip archives

        @param filename: archive file name
        @param target: target extraction directory

        @return: the archive content
        """
        try:
            # start with tar
            ar = tarfile.open(filename)
            content = ar.getnames()
        except tarfile.ReadError:
            # retry with zip
            ar = zipfile.ZipFile(filename)
            content = ar.namelist()

        # no absolute file name
        assert not any([os.path.isabs(f) for f in content])
        # no .. in file name
        assert not any([(".." in f) for f in content])

        try:
            ar.extractall(target)
        except (IOError, AttributeError):
        # DUE TO SOME ODD BEHAVIOR OF extractall IN Pthon 2.6.1 (OSX 10.6.8)
        # BEFORE TGZ EXTRACT FAILS INSIDE THE TARGET DIRECTORY A FILE
        # IS CREATED, ONE WITH THE NAME OF THE PACKAGE
        # SO WE HAVE TO CLEAN IT BEFORE STARTING OVER WITH ZIP
        # cleanup/create the target dir
            if os.path.isdir(target):
                shutil.rmtree(target)
            os.mkdir(target)

            # zipfile module < 2.6
            for member in content:
                if member.endswith(os.path.sep):
                    os.mkdir(os.path.join(target, member))
                else:
                    f = open(os.path.join(target, member), 'wb')
                    f.write(ar.read(member))
                    f.close()

        return content

    
    def download_demo_extra(self, source, target, first_download):
        """
        Download a demoextras for a given demo
        inputs: source from demoinfo, target in core, first_download (true or false)
        return: success or not
        """
        if not first_download:
            try:
                os.remove(target)
            except OSError as ex: 
                error_message = "Failure removing the demoextra {}.\
Error: {} ".format(target,ex)
                self.logger.error(error_message)
                return False
            
        print "Downloading  {} ...".format(source)
        if self.download(source, target) == 1:
            error_message = "Failure downloading the demoextra {}".format(source)
            self.logger.error(error_message)
            return False
        
        return True
    
    def extract_demo_extra(self, demo_id, compressed_file):
        """
        Extract a demo extra...
        input: demo_id and compressed file for the extraction
        return: success or not 
        """
        demoExtrasFolder = os.path.join(self.demoExtrasMainDir, demo_id)

        try:        
            if os.path.isdir(demoExtrasFolder):
                print "Cleaning the original {} ".format(demoExtrasFolder)
                shutil.rmtree(demoExtrasFolder)                        
            
            self.mkdir_p(demoExtrasFolder)
            print "Extracting {} ...".format(compressed_file)
            self.extract(compressed_file, demoExtrasFolder)
            success = True
        
        except Exception as ex:
            error_message="Extraction failed for demo {}. \
Exception {} ".format(demo_id, ex)
            self.logger.exception(error_message)
            success = False
        
        return success



    def ensure_extras_updated(self, demo_id):
        """
        Ensure that the demo extras of a given demo are updated respect to demoinfo information.
        and exists in the core folder.
        """
        print "### Ensuring demo extras... ##"

        ddl_extras_folder = os.path.join(self.dl_extras_dir, demo_id)
        compressed_file = os.path.join(ddl_extras_folder, \
          self.demoExtrasFilename)

        self.mkdir_p(ddl_extras_folder)
        
        userdata = {"demo_id":demo_id}
        
        if not os.path.isfile(compressed_file):
            
            first_download=True
            code_message="First download with code "
            
            resp = self.post(self.host_name, 'demoinfo', \
                   'get_compressed_file_url_ws', userdata)
                    
        else:
            ## If the file already exists, we must compare the dates
            first_download=False
            code_message="Is the file in the core newer? (2 = no, 0 = yes)"
            
            file_state = os.stat(compressed_file)
            userdata["time_of_file_in_core"] = str(file_state.st_ctime)
            userdata["size_of_file_in_core"] = str(file_state.st_size)
            
            resp = self.post(self.host_name, 'demoinfo', \
               'get_file_updated_state', userdata)
        
        response = resp.json()
        status = response['status']
        code = response['code']

        if status == "OK":
            
            print code_message, code
            if code == "2":
                file_from_demoinfo = response['url_compressed_file']            
                self.download_demo_extra(file_from_demoinfo, compressed_file, first_download)
                
                if not self.extract_demo_extra(demo_id, compressed_file):            
                    raise
        else:
            error_message = "KO downloading a demoextras. \
Demoinfo code = {}".format(response['code'])
            self.logger.exception(error_message)
            print error_message
            raise
        
        return response
        

    def copy_blobs(self, work_dir, input_type, blobs, ddl_inputs):
        """
        copy the blobs in the run path.
        The blobs can be uploaded by post method or a blobs from blob module
        """
        print "### Entering copy_blobs...  ###"

        if input_type == 'upload':
            self.input_upload(work_dir, blobs, ddl_inputs)
        elif input_type == 'blobset':
            self.copy_blobset_from_physical_location(work_dir, blobs)



    @staticmethod
    def create_new_execution_key():
        """
        create a new experiment identifier
        """
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
            self.logger.exception("create_new_execution_key()")
            return None

        return key

    def create_run_dir(self, demo_id, key):
        """
        If it not exist, create a run_dir for a demo
        then, create a folder for the execution
        :param demo_id:   id demo
        :param run_folder: key
        """
        demo_path = os.path.join(self.shared_folder_abs, \
                                 self.share_run_dir_abs, \
                                 demo_id, \
                                 key)
        self.mkdir_p(demo_path)
        return demo_path


    def get_demo_metadata(self, demo_id):
        '''
        Gets demo meta data given its editor's ID
        '''
        userdata = {"demoid": demo_id}
        resp = self.post(self.host_name, 'demoinfo', \
          'read_demo_metainfo', userdata)
        return resp.json()



    def get_demo_editor_list(self, demo_id):
        '''
        Get the list of active editors of the given demo
        '''
        # Get the list of editors of the demo
        # userdata = {"module":"demoinfo", "service":"demo_get_editors_list"}
        userdata = {"demo_id": demo_id}
        resp = self.post(self.host_name, 'demoinfo', \
          'demo_get_editors_list', userdata)
        response = resp.json()
        status = response['status']

        if status != 'OK':
            # [ToDo]: log this error!
            return ()

        editor_list = response['editor_list']

        if len(editor_list) == 0:
            return () # No editors given

        # Get the names and emails of the active editors
        emails = []
        for entry in editor_list:
            if entry['active'] == 1:
                emails.append((entry['name'], entry['mail']))

        return emails

    @staticmethod
    def send_email(subject, text, emails, zip_filename=None):
        '''
        Send an email to the given recipients
        '''
        emails_list = [entry[1] for entry in emails]
        emails_str = ", ".join(emails_list)

        msg = MIMEMultipart()

        msg['Subject'] = subject
        # [ToDo] Move this to the core.conf
        msg['From'] = "IPOL Core <nor" + "eply" + "@cml" + "a.ens" + "-cac" + "han.fr>"
        msg['To'] = emails_str # Must pass only a comma-separated string here
        msg.preamble = text

        if zip_filename is not None:
            with open(zip_filename) as fp:
                zip_data = MIMEApplication(fp.read())
                zip_data.add_header('Content-Disposition', 'attachment', filename="experiment.zip")
            msg.attach(zip_data)

        text_data = MIMEText(text)
        msg.attach(text_data)

        s = smtplib.SMTP('localhost')

         # Must pass only a list here
        s.sendmail(msg['From'], emails_list, msg.as_string())
        s.quit()

    def get_build_log_text(self, demo_id):
        '''
        Returns the contents of the build log file
        '''
        # [ToDo] Use the shared folder to access a DR!
        buildLog_filename = "{}/../ipol_demo/modules/demorunner/binaries/{}/build.log".\
          format(self.shared_folder_abs, demo_id)
        if not os.path.isfile(buildLog_filename):
            return ""

        fp = open(buildLog_filename, 'rb')
        text = "Compilation of demo #{} failed:\n\n{}".format(demo_id, fp.read())
        fp.close()

        return text


    def send_compilation_error_email(self, demo_id):
        ''' Send email to editor when compilation fails '''
        print "send_compilation_error_email"

        emails = self.get_demo_editor_list(demo_id)

        demo_state = self.get_demo_metadata(demo_id)["state"].lower()
        
        # Add Tech and Edit only if this is the production server and
        # the demo has been published        
        if self.serverEnvironment == 'production' and \
          demo_state == "published":
            emails.append(('IPOL Tech', "te" + "ch" + "@ip" + "ol.im"))
            emails.append(('IPOL Edit', "ed" + "it" + "@ip" + "ol.im"))

        if len(emails) == 0:
            return

        # Send the email
        # [ToDo] Use the shared folder to access a DR!
        text = self.get_build_log_text(demo_id)
        subject = 'Compilation of demo #{} failed'.format(demo_id)
        self.send_email(subject, text, emails)

    # From http://stackoverflow.com/questions/1855095/how-to-create-a-zip-archive-of-a-directory
    @staticmethod
    def zipdir(path, ziph):
        ''' Zip a directory '''
        # ziph is zipfile handle
        for root, _, files in os.walk(path):
            for f in files:
                ziph.write(os.path.join(root, f))

    def send_runtime_error_email(self, demo_id, key):
        ''' Send email to editor when the execution fails '''
        emails = self.get_demo_editor_list(demo_id)

        demo_state = self.get_demo_metadata(demo_id)["state"].lower()
        
        # Add Tech and Edit only if this is the production server and
        # the demo has been published        
        if self.serverEnvironment == 'production' and \
          demo_state == "published":
            emails.append(('IPOL Tech', "te" + "ch" + "@ip" + "ol.im"))
            emails.append(('IPOL Edit', "ed" + "it" + "@ip" + "ol.im"))

        if len(emails) == 0:
            return

        # Attach experiment in zip file and send the email
        hostname = socket.gethostname()
        hostbyname = socket.gethostbyname(hostname)
        text = "This is the IPOL Core machine ({}, {}).\n\n\
The execution with key={} of demo #{} has failed.\nPlease find \
attached the failed experiment data.".\
format(hostname, hostbyname, key, demo_id)

        subject = '[IPOL Core] Demo #{} execution failure'.format(demo_id)

        # Zip the contents of the tmp/ directory of the failed experiment
        zip_filename = '/tmp/{}.zip'.format(key)
        zipf = zipfile.ZipFile(zip_filename, 'w', zipfile.ZIP_DEFLATED)
        self.zipdir("{}/run/{}/{}".format(self.shared_folder_abs, demo_id, key), zipf)
        zipf.close()

        self.send_email(subject, text, emails, zip_filename=zip_filename)

    def send_demorunner_unresponsive_email(self, \
      unresponsive_demorunners):
        '''
        Send email to editor when the demorruner is down
        '''
        emails = []
        if self.serverEnvironment == 'production':
            emails.append(('IPOL Tech', "te" + "ch" + "@ip" + "ol.im"))
        if len(emails) == 0:
            return

        hostname = socket.gethostname()
        hostbyname = socket.gethostbyname(hostname)

        unresponsive_demorunners_list = ",".\
          join(unresponsive_demorunners)

        text = "This is the IPOL Core machine ({}, {}).\n\nThe list \
of demorunners unresponsive is: {}.".format(\
hostname, hostbyname, unresponsive_demorunners_list)
        print text
        subject = '[IPOL Core] Demorunner unresponsive'
        self.send_email(subject, text, emails)

    @cherrypy.expose
    def run(self, demo_id, **kwargs):
        """
        Run a demo. The presentation layer requests the Core to
        execute a demo.
        """
        print "### RUN in CORE ####"
        print "demo_id =", demo_id
        print "kwargs=", kwargs

        if 'input_type' in kwargs:
            input_type = kwargs.get('input_type', None)
        else:
            response = {}
            response["status"] = "KO"
            self.error_log("run", \
              "There is not input_type in run function.")
            return json.dumps(response)


        if 'params' in kwargs:
            params = kwargs.get('params', None)

        if 'original' in kwargs:
            original_exp = kwargs.get('original', None)

        if 'crop_info' in kwargs:
            crop_info = kwargs.get('crop_info', None)
        else:
            crop_info = None

        blobs = {}
        if input_type == 'upload':
            i = 0
            while "file_{0}".format(i) in kwargs:
                fname = "file_{0}".format(i)
                blobs[fname] = kwargs[fname]
                i += 1
        elif input_type == 'blobset':
            blobs = json.loads(kwargs['blobs'])
        elif input_type == 'noinputs':
            pass

        ## Start of block to obtain the DDL
        try:
            userdata = {"demo_id": demo_id, "returnjsons": 'True'}
            resp = self.post(self.host_name, 'demoinfo', \
              'read_last_demodescription_from_demo', userdata)
            response = resp.json()
            last_demodescription = response['last_demodescription']
            ddl_json = json.loads(last_demodescription['json'])
            if 'build' in ddl_json:
                ddl_build = ddl_json['build']
            if 'inputs' in ddl_json:
                ddl_inputs = ddl_json['inputs']

        except Exception as ex:
            print "Failed to obtain the DDL of demo {}".format(demo_id)
            s = "Failed to obtain the DDL of demo {}".format(demo_id)
            self.logger.exception(s)
            res_data = {}
            res_data['info'] = 'DDL read demoInfo failed in the Core'
            res_data['status'] = 'KO'
            return json.dump(res_data)
        ## End block to obtain the DDL

        # Create a new execution key
        key = self.create_new_execution_key()
        if key is None:
            res_data = {}
            res_data['info'] = 'Failed to create a valid key'
            res_data['status'] = 'KO'
            self.logger.exception("Failed to create a valid key")
            return json.dumps(res_data)

        work_dir = self.create_run_dir(demo_id, key)
        print "Run path is ", work_dir

        # Copy input blobs
        if input_type != 'noinputs':
            try:
                self.copy_blobs(work_dir, input_type, blobs, ddl_inputs)
                self.process_inputs(work_dir, ddl_inputs, crop_info)

            except Exception as ex:
                print "FAILURE in copy_blobs/process_inputs. \
demo_id = ", demo_id
                res_data = {}
                res_data['info'] = 'Failure in copy_blobs/process_inputs in CORE'
                res_data['status'] = 'KO'
                self.logger.exception("copy_blobs/process_inputs FAILED")
                return json.dumps(res_data)


        try:
            # Find a DR with satisfies the requirements
            requirements = ddl_json['general']['requirements'] \
                if 'general' in ddl_json and 'requirements' in ddl_json['general'] else None

            dr = self.get_demorunner(self.demorunners_workload(), \
              requirements)

            print "Entering dr.ensure_compilation()"
            userdata = {"demo_id": demo_id, "ddl_build": json.dumps(ddl_build)}
            resp = self.post(dr, 'demorunner', 'ensure_compilation', userdata)
            demorunner_response = resp.json()
            status = demorunner_response['status']
            print "ensure_compilation response --> " + status + " in demo = " + demo_id

            if status != 'OK':
                print "FAILURE IN THE COMPILATION in demo = ", demo_id
                self.error_log("ensure_compilation()", \
"ensure_compilation functions returns KO in the demorunner: " + \
dr + " module")

                # Send compilation message to the editors
                self.send_compilation_error_email(demo_id)
                text = self.get_build_log_text(demo_id)

                # Message for the web interface
                demorunner_response["error"] = \
                  " --- Compilation error. --- {} - {}".\
                  format(demorunner_response["message"], text)

                return json.dumps(demorunner_response)

            print "Entering ensure_extras_updated()"
            data = self.ensure_extras_updated(demo_id)
            print "Result in ensure_extras_updated : ", data

            print "dr.exec_and_wait()"

            userdata = {"demo_id": demo_id, "key": key, "params": params}

            if 'run' in ddl_json:
                userdata['ddl_run'] = json.dumps(ddl_json['run'])

            if 'config' in ddl_json:
                userdata['ddl_config'] = json.dumps(ddl_json['config'])

            if 'general' in ddl_json and 'timeout' in ddl_json['general']:
                userdata['timeout'] = ddl_json['general']['timeout']


            resp = self.post(dr, 'demorunner', 'exec_and_wait', userdata)

            demorunner_response = resp.json()
            print userdata
            print demorunner_response

            if demorunner_response['status'] != 'OK':
                print "DR answered KO for demo #{}".format(demo_id)
                self.error_log("dr.exec_and_wait()", "DR returned KO")

                # Message for the web interface
                demorunner_response["error"] = format(demorunner_response["algo_info"]["status"])

                # Send email to the editors
                self.send_runtime_error_email(demo_id, key)
                return json.dumps(demorunner_response)

            demorunner_response['work_url'] = os.path.join(\
                   "http://{}/api/core/".format(self.host_name), \
                                        self.shared_folder_rel, \
                                        self.share_run_dir_rel, \
                                        demo_id, \
                                        key) + '/'

            print "resp ", demorunner_response

            # Archive the experiment, if the 'archive' section
            # exists in the DDL
            print "archive.store_experiment()"
            if original_exp == 'true' and 'archive' in ddl_json:
                ddl_archive = ddl_json['archive']
                print ddl_archive
                SendArchive.prepare_archive(demo_id, \
                  work_dir, ddl_archive, demorunner_response, self.host_name)

        except Exception as ex:
            s = "Failure in the run function of the \
CORE in demo #{}".format(demo_id)
            self.logger.exception(s)
            print "Failure in the run function of the CORE in \
demo #{} - {}".format(demo_id, str(ex))
            core_response = {}
            core_response["status"] = "KO"
            core_response["error"] = "{}".format(ex)
            return json.dumps(core_response)

        dic = self.read_algo_info(work_dir)
        for name in dic:
            demorunner_response["algo_info"][name] = dic[name]

        print "Run successful in demo = ", demo_id
        print json.dumps(demorunner_response)
        return json.dumps(demorunner_response)

    def read_algo_info(self, work_dir):
        '''
        Read the file algo_info.txt to make available in the system
        variables created or modified by the algorithm
        '''
        file_name = os.path.join(work_dir, "algo_info.txt")

        if not os.path.isfile(file_name):
            return {} # The algorithm didn't create the file

        dic = {}
        f = open(file_name, "r")
        lines = f.readlines()
        #
        for line in lines:
            # Read with format A = B, where B can contain the '=' sign
            if len(line.split("=", 1)) < 2 or \
                   line.split("=", 1)[0].strip() == "":
                print "incorrect format in algo_info.txt, in line {}".format(line)
                self.error_log("run", "incorrect format in algo_info.txt, at line {}".format(line))
                continue

            # Add name and assigned value to the output dict
            name, value = line.split("=", 1)
            name = name.strip()
            dic[name] = value

        f.close()
        return dic


    def get_demorunner(self, demorunners_workload, requirements=None):
        '''
        Return an active demorunner for the requirements
        '''
        demorunner_data = {\
          "demorunners_workload": str(demorunners_workload),\
          "requirements":requirements}
        unresponsive_demorunners = set()
        # Try twice the length of the DR list before raising an exception
        for i in range(len(self.demorunners)*2):
            # Get a demorunner for the requirements
            dispatcher_response = self.post(self.host_name, \
              'dispatcher', 'get_demorunner', demorunner_data)
            if not dispatcher_response.ok:
                raise Exception("Dispatcher unresponsive")

            # Check if there is a DR for the requirements
            if dispatcher_response.json()['status'] != 'OK':
                raise Exception(dispatcher_response.json()['message'])

            dr_name = dispatcher_response.json()['name']
            dr_server = self.demorunners[dr_name]['server']

            # Check if the DR is up. Otherwise add it to the
            # list of unresponsive DRs
            demorunner_response = self.post(dr_server, \
              'demorunner', 'ping')
            if demorunner_response.ok:
                if len(unresponsive_demorunners) > 0:
                    self.send_demorunner_unresponsive_email(unresponsive_demorunners)
                return dr_server
            else:
                self.error_log("get_demorunner", \
                  "Module {} unresponsive".format(dr_name))
                print "Module {} unresponsive".format(dr_name)
                unresponsive_demorunners.add(dr_name)

            # At half of the tries wait 5 secs and try again
            if i == len(self.demorunners)-1:
                time.sleep(5)

        # If there is no demorrunner active send an email with all the unresponsive DRs
        self.send_demorunner_unresponsive_email(unresponsive_demorunners)
        raise Exception("No DR available after many tries")




    def post(self, host, module, service, data=None):
        """
        Do a POST via api
        """
        try:
            url = 'http://{0}/api/{1}/{2}'.format(
                host,
                module,
                service)
            return requests.post(url, data=data)
        except Exception as ex:
            print "Failure in the post function of the CORE in the call \
              to {} module - {}".format(module, str(ex))
            self.logger.exception(\
              "Failure in the post function of the CORE")

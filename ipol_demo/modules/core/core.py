#!/usr/bin/python

"""
IPOL Core module
"""

import base64
import tempfile
import re
# To send emails
import smtplib
from email.mime.text import MIMEText
from email.mime.application import MIMEApplication
from email.mime.multipart import MIMEMultipart

import xml.etree.ElementTree as ET

import shutil
import json
import ConfigParser

import errno
import logging
import os
import os.path
import traceback

import urllib

import hashlib
from datetime import datetime
from random import random
import glob
import time

import tarfile
import zipfile

import socket

import mimetypes

from libtiff import TIFF
import png

import requests
import cherrypy
import magic



from Tools.misc import prod
from Tools.image import image
from Tools.sendarchive import SendArchive
from Tools.evaluator import IPOLEvaluateError
from Tools.evaluator import evaluate
from errors import IPOLDemoExtrasError
from errors import IPOLExtractError
from errors import IPOLInputUploadError
from errors import IPOLCopyBlobsError
from errors import IPOLProcessInputsError


def authenticate(func):
    """
    Wrapper to authenticate before using an exposed function
    """

    def authenticate_and_call(*args, **kwargs):
        """
        Invokes the wrapped function if authenticated
        """
        if not is_authorized_ip(cherrypy.request.remote.ip) \
                and not ("X-Real-IP" in cherrypy.request.headers
                         and is_authorized_ip(cherrypy.request.headers["X-Real-IP"])):
            error = {"status": "KO", "error": "Authentication Failed"}
            return json.dumps(error)
        return func(*args, **kwargs)

    def is_authorized_ip(ip):
        """
        Validates the given IP
        """
        core = Core.get_instance()
        patterns = []
        # Creates the patterns  with regular expressions
        for authorized_pattern in core.authorized_patterns:
            patterns.append(re.compile(authorized_pattern.replace(".", "\\.").replace("*", "[0-9]*")))
        # Compare the IP with the patterns
        for pattern in patterns:
            if pattern.match(ip) is not None:
                return True
        return False

    return authenticate_and_call


# -------------------------------------------------------------------------------
class Core(object):
    """
    Core index used as the root app
    """
    instance = None

    @staticmethod
    def get_instance():
        """
        Singleton pattern
        """
        if Core.instance is None:
            Core.instance = Core()
        return Core.instance

    def init_logging(self):
        """
        Initialize the error logs of the module.
        """
        logs_dir_abs = os.path.join(os.path.dirname(os.path.realpath(__file__)), self.logs_dir_rel)
        self.mkdir_p(logs_dir_abs)
        logger = logging.getLogger(logs_dir_abs)
        logger.setLevel(logging.ERROR)
        handler = logging.FileHandler(os.path.join(logs_dir_abs, self.logs_name))
        formatter = logging.Formatter(
            '%(asctime)s ERROR in %(message)s',
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
        """
        Constructor
        """
        try:
            self.host_name = cherrypy.config['server.socket_host']

            # Read configuration file
            self.serverEnvironment = cherrypy.config.get("server.environment").lower()

            self.demorunners_file = cherrypy.config.get("demorunners_file")
            self.demorunners = {}

            self.logs_dir_rel = cherrypy.config.get("logs.dir")
            self.logs_name = cherrypy.config.get("logs.name")
            self.logger = self.init_logging()
            self.common_config_dir = cherrypy.config.get("config_common_dir")
            self.project_folder = cherrypy.config.get("project_folder")
            self.blobs_folder = cherrypy.config.get("blobs_folder")
            self.demoExtrasFilename = cherrypy.config.get("demoExtrasFilename")

            self.shared_folder_rel = cherrypy.config.get("shared_folder")
            self.shared_folder_abs = os.path.join(self.project_folder, self.shared_folder_rel)
            self.demoExtrasMainDir = os.path.join(
                self.shared_folder_abs,
                cherrypy.config.get("demoExtrasDir"))
            self.dl_extras_dir = os.path.join(self.shared_folder_abs,
                                              cherrypy.config.get("dl_extras_dir"))
            self.share_run_dir_rel = cherrypy.config.get("running.dir")
            self.share_run_dir_abs = os.path.join(
                self.shared_folder_abs, self.share_run_dir_rel)

            self.load_demorunners()

            # Security: authorized IPs
            self.authorized_patterns = self.read_authorized_patterns()

            # Create shared folder if not exist
            self.mkdir_p(self.shared_folder_abs)

            # create running dir and demoextras dirs
            self.mkdir_p(self.share_run_dir_abs)
            self.mkdir_p(self.dl_extras_dir)
            self.mkdir_p(self.demoExtrasMainDir)
            # return to core

            # Configure
            self.png_compresslevel = 1

        except Exception as ex:
            self.logger.exception("__init__", str(ex))

    def read_authorized_patterns(self):
        """
        Read from the IPs conf file
        """
        # Check if the config file exists
        authorized_patterns_path = os.path.join(self.common_config_dir, "authorized_patterns.conf")
        if not os.path.isfile(authorized_patterns_path):
            self.error_log("read_authorized_patterns",
                           "Can't open {}".format(authorized_patterns_path))
            return []

        # Read config file
        try:
            cfg = ConfigParser.ConfigParser()
            cfg.read([authorized_patterns_path])
            patterns = []
            for item in cfg.items('Patterns'):
                patterns.append(item[1])
            return patterns
        except ConfigParser.Error:
            self.logger.exception("Bad format in {}".format(authorized_patterns_path))
            return []

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
        """
        refresh demorunners information and alert the dispatcher module
        """
        data = {"status": "KO"}

        try:
            # Reload DRs config
            self.load_demorunners()

            demorunners = {"demorunners": json.dumps(self.demorunners)}
            response = self.post(self.host_name, "dispatcher", "set_demorunners", data=demorunners)
            if response.json().get('status') == "OK":
                data['status'] = 'OK'

        except Exception as ex:
            print ex
            self.logger.exception("refresh_demorunners")
            data["error"] = "Can not refresh demorunners"

        return json.dumps(data)

    @cherrypy.expose
    def get_demorunners(self):
        """
        Get the information of the demorunners
        """
        data = {"status": "OK"}
        try:
            data["demorunners"] = str(self.demorunners)
        except Exception as ex:
            print ex
            self.logger.exception("get_demorunners")
            data["status"] = "KO"
            data["message"] = "Can't get demorunners"

        return json.dumps(data)

    @cherrypy.expose
    def get_demorunners_stats(self):
        """
        Get stats of all the demorunners to be used by the external tools like the CP
        """
        response = {}
        demorunners = []
        #
        for dr in self.demorunners:
            try:
                response = self.post(self.demorunners[dr].get('server'), 'demorunner', 'get_workload')
                if not response.ok:
                    demorunners.append({'name': dr, 'status': 'KO'})
                    continue

                json_response = response.json()
                if json_response.get('status') == 'OK':
                    demorunners.append({'name': dr,
                                        'status': 'OK',
                                        'workload': float('%.2f' % (json_response.get('workload')))})
                else:
                    demorunners.append({'name': dr, 'status': 'KO'})

            except ConnectionError:
                self.logger.exception("Couldn't get DR={} workload".format(dr.get("name", "<?>")))
                demorunners.append({'name': dr, 'status': 'KO'})
                continue
            except Exception as ex:
                print ex
                message = "Couldn't get the DRs workload"
                self.logger.exception(message)
                response["status"] = "KO"
                response["message"] = message

        # Return the DRs in the response
        response["demorunners"] = demorunners
        response["status"] = "OK"
        return json.dumps(response)

    def demorunners_workload(self):
        """
        Get the workload of each DR
        """
        dr_workload = {}
        for dr_name in self.demorunners:
            try:
                resp = self.post(self.demorunners[dr_name]['server'], 'demorunner', 'get_workload')
                if not resp.ok:
                    self.error_log("demorunners_workload", "Bad post response from DR='{}'".format(dr_name))
                    continue

                response = resp.json()
                if response.get('status', '') == 'OK':
                    dr_workload[dr_name] = response.get('workload')
                else:
                    self.error_log("demorunners_workload", "get_workload KO response for DR='{}'".format(dr_name))
                    dr_workload[dr_name] = 100.0
            except ConnectionError:
                self.error_log("demorunners_workload", "get_workload ConnectionError for DR='{}'".format(dr_name))
                continue
            except Exception:
                s = "Error when obtaining the workload of '{}'".format(dr_name)
                self.logger.exception(s)
                dr_workload[dr_name] = 100.0
                print s
                continue

        return dr_workload

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
            self.send_internal_error_email("Unable to get the list of demos")
            string = """
                 <!DOCTYPE html>
                 <html lang="en">
                 <head>
                 <meta charset="utf-8">
                 <title>IPOL demos</title>
                 </head>
                 <body>
                 <h2>IPOL internal error: unable to get the list of demos</h2><br>
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

            demos_by_state[publication_state].append({
                'editorsdemoid': demo['editorsdemoid'],
                'title': demo['title']
            })

        demos_string = ""

        # Show demos according to their state
        for publication_state in demos_by_state:
            # Sort demo list by demo ID
            demos_by_state[publication_state] = sorted(demos_by_state[publication_state], key=lambda(d): (d['editorsdemoid']), reverse=True)

            demos_string += "<h2>{}</h2>".format(publication_state)

            for demo_data in demos_by_state[publication_state]:
                editorsdemoid = str(demo_data['editorsdemoid'])

                demos_string += "Demo #{} {}: <a href='/demo/clientApp/demo.html?id={}'>{}</a><br>".format(
                    editorsdemoid,
                    "(private)" if editorsdemoid.startswith("33333") else "",
                    editorsdemoid, demo_data['title'].encode('utf-8'))

        string = """
                 <!DOCTYPE html>
                 <html lang="en">
                 <head>
                 <meta charset="utf-8">
                 <title>IPOL demos</title>
                 </head>
                 <body>
                 <h1>List of demos</h1>
                 <h3>The demos whose ID begins with '77777' are public workshops and those with '33333' are private.
                 Test demos begin with '55555'.</h3><br>
                 {}
                 </body>
                 </html>
                 """.format(demos_string)

        return string

    @cherrypy.expose
    def demo(self):
        """
        Return a HTML page with the list of demos.
        """
        return self.index()

    @staticmethod
    @cherrypy.expose
    def ping():
        """
        Ping service: answer with a PONG.
        """
        data = {"status": "OK", "ping": "pong"}
        return json.dumps(data)

    @cherrypy.expose
    @authenticate
    def shutdown(self):
        """
        Shutdown the module.
        """
        data = {"status": "KO"}
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
        data = {"status": "KO", "message": "Unknown service '{}'".format(attr)}
        return json.dumps(data)

    # ---------------------------------------------------------------------------
    # INPUT HANDLING TOOLS (OLD with a few modifications)
    # [Miguel] They're absolutely deprecated and need a full refactoring
    # in the Conversion module.
    # ---------------------------------------------------------------------------
    def save_image(self, im, fullpath):
        """
        Save image object given full path
        """
        im.save(fullpath, compresslevel=self.png_compresslevel)


    @cherrypy.expose
    def convert_tiff_to_png(self, img):
        """
        Converts the input TIFF to PNG.
        This is used by the web interface for visualization purposes
        """
        data = {"status": "KO"}
        try:
            temp_file = tempfile.NamedTemporaryFile()
            temp_file.write(base64.b64decode(img))
            temp_file.seek(0)

            tiff_file = TIFF.open(temp_file.name, mode='r')
            tiff_image = tiff_file.read_image()

            # Check if the image can be converted
            if not ("uint" in tiff_image.dtype.name or "int" in tiff_image.dtype.name):
                path = os.path.join(self.project_folder, "ipol_demo", "modules", "core", "static",
                                    "demo", "clientApp", "images", "non_viewable_data.png")
                with open(path, "rb") as im:
                    data["img"] = base64.b64encode(im.read())
                data["status"] = "OK"
                return json.dumps(data)
            # Get number of rows, columns, and channels
            nrow, ncolumn, _ = tiff_image.shape

            pixel_matrix = tiff_image[:, :, 0:3].reshape(
                (nrow, ncolumn * 3), order='C').astype(tiff_image.dtype)
            tmp_file = tempfile.SpooledTemporaryFile()

            bitdepth = int(tiff_image.dtype.name.split("uint")[1])
            writer = png.Writer(ncolumn, nrow,
                                bitdepth=bitdepth, greyscale=False)

            writer.write(tmp_file, pixel_matrix)
            tmp_file.seek(0)
            encoded_string = base64.b64encode(tmp_file.read())

            data["img"] = encoded_string
            data["status"] = "OK"
        except Exception as ex:
            print "Failed to convert image from TIFF to PNG", ex
            self.logger.exception("Failed to convert image from TIFF to PNG")
        return json.dumps(data)

    # --------------------------------------------------------------------------
    #           END BLOCK OF INPUT TOOLS
    # --------------------------------------------------------------------------

    @staticmethod
    def process_input_data(filename, input_desc):
        '''
        Process input of type 'data'
        '''
        if 'ext' not in input_desc:
            raise IPOLProcessInputsError("The DDL does not have an 'ext' (extension) field")
        ext = input_desc['ext']

        input_first_part, input_ext = os.path.splitext(filename)
        if input_ext != ext:
            os.rename(filename, input_first_part + ext)

    def process_input_image(self, filename, work_dir, input_desc, crop_info):
        '''
        Process input of type 'image'
        '''
        mode_kw = {'1x1i': '1',
                   '1x1': '1',
                   '1x8i': 'L',
                   '1x8': 'L',
                   '3x8i': 'RGB',
                   '3x8': 'RGB'}
        ddl_mode = mode_kw[input_desc['dtype']]

        # Read the image
        im = image(filename)

        json_crop_info = json.loads(crop_info) if crop_info else None
        crop_enabled = json_crop_info and json_crop_info['enabled']

        # Get the expected extension for the file
        if 'ext' not in input_desc:
            raise IPOLProcessInputsError("The DDL does not have a 'ext' (extension) field")
        ext = input_desc['ext']

        # Check if the size and the format are OK
        max_pixels = evaluate(input_desc['max_pixels'])
        size_ok = prod(im.size) <= max_pixels
        format_ok = mimetypes.guess_type(filename)[0] == mimetypes.guess_type("dummy" + ext)[0]
        mode_ok = ddl_mode == im.im.mode

        input_first_part, input_ext = os.path.splitext(filename)

        if not crop_enabled and size_ok and format_ok and mode_ok:
            # This is the most favorable case.
            # There is no crop and both the size and everything else
            # is the same.

            # If the extension also coincides, everything is done
            if input_ext == ext:
                return

            # If not, just change the extension and we're done
            os.rename(filename, input_first_part + ext)
            return


        # From now on, a conversion is needed
        # Perform crop if needed
        if crop_enabled:
            x0 = int(round(json_crop_info['x']))
            y0 = int(round(json_crop_info['y']))
            x1 = int(round(json_crop_info['x'] + json_crop_info['w']))
            y1 = int(round(json_crop_info['y'] + json_crop_info['h']))
            im.crop((x0, y0, x1, y1))

        # Set the mode
        if not mode_ok:
            im.im = im.im.convert(ddl_mode)

        # resize if the (eventually) cropped image is too big
        if max_pixels and prod(im.size) > max_pixels:
            im.resize(int(max_pixels), method="antialias")

        # Finally, save the processed image
        self.save_image(im, os.path.join(work_dir, input_first_part + ext))

    def process_inputs(self, work_dir, inputs_desc, crop_info=None):
        '''
        Process the inputs
        '''
        nb_inputs = len(inputs_desc)

        for i in range(nb_inputs):
            # check the input type
            input_desc = inputs_desc[i]
            # find files starting with input_%
            input_files = glob.glob(os.path.join(work_dir, 'input_{}.*'.format(i)))

            if len(input_files) != 1:
                if 'required' in inputs_desc[i] and inputs_desc[i]['required']:
                    # problem here
                    raise cherrypy.HTTPError(400, "Wrong number of inputs for an image")
                else:
                    # optional input missing, end of inputs
                    break

            input_filename = input_files[0]

            if input_desc['type'] == 'image':
                self.process_input_image(input_filename, work_dir, inputs_desc[i], crop_info)
            elif input_desc['type'] == 'data':
                self.process_input_data(input_filename, inputs_desc[i])
            else:
                raise ValueError("Unknown input type '{}'".format(input_desc['type']))



    @staticmethod
    def input_upload(work_dir, blobs, inputs_desc):
        """
        use the uploaded input files
        file_0, file_1, ... are the input files
        ddl_input is the input section of the demo description
        """
        nb_inputs = len(inputs_desc)

        for i in range(nb_inputs):
            file_up = blobs.pop('file_%i' % i, None)

            if file_up is None or file_up.filename == '':
                if 'required' not in inputs_desc[i].keys() or \
                        inputs_desc[i]['required']:
                    # missing file
                    raise cherrypy.HTTPError(400, "Missing input file number {0}".format(i))
                else:
                    # skip this input
                    continue

            mime = magic.Magic(mime=True)
            file_up.file.seek(0)
            mime_uploaded_blob = mime.from_buffer(file_up.file.read())
            type_of_uploaded_blob, _ = mime_uploaded_blob.split('/')
            ext_of_uploaded_blob = mimetypes.guess_extension(mime_uploaded_blob)

            if 'ext' not in inputs_desc[i]:
                raise IPOLInputUploadError("The DDL doesn't have a 'ext' (extension) field")

            if 'type' not in inputs_desc[i]:
                raise IPOLInputUploadError("The DDL doesn't have a 'type' field")

            if inputs_desc[i]['type'] != type_of_uploaded_blob and inputs_desc[i]['type'] != "data":
                raise IPOLInputUploadError("The DDL type doesn't match the uploaded file")

            # We keep the file according it was uploaded
            # process_inputs will make the possible modifications
            file_save = file(os.path.join(work_dir, 'input_%i' % i + ext_of_uploaded_blob), 'wb')

            size = 0
            file_up.file.seek(0)
            while True:
                data = file_up.file.read(128)
                if not data:
                    break
                size += len(data)
                if 'max_weight' in inputs_desc[i] and size > evaluate(inputs_desc[i]['max_weight']):
                    # file too heavy
                    # Bad Request
                    raise cherrypy.HTTPError(400, "File too large, resize or compress more")

                file_save.write(data)
            file_save.close()

    def copy_blobset_from_physical_location(self, work_dir, blobs_id_list):
        """
        use the selected available input images
        input parameters:
        returns:
        """

        resp = self.post(self.host_name, 'blobs', 'get_blobs_location', {'blobs_ids': blobs_id_list})
        response = resp.json()

        if response['status'] == 'OK':
            physical_locations = response['physical_locations']

            index = 0
            for blob_path in physical_locations:
                try:
                    extension = os.path.splitext(blob_path)[1]
                    final_path = os.path.join(work_dir, 'input_{0}{1}'.format(index, extension))
                    shutil.copy(os.path.join(self.blobs_folder, blob_path), final_path)
                except Exception as ex:
                    self.logger.exception("Error copying blob from {} to {}".format(blob_path, final_path))
                    print "Couldn't copy  blobs from {} to {}. Error: {}".format(blob_path, final_path, ex)

                index += 1
        else:
            self.logger.exception("Blobs get_blobs_location returned KO at Core's copy_blobset_from_physical_location")


    def copy_blobs(self, work_dir, input_type, blobs, ddl_inputs):
        """
        Copy the input blobs to the execution folder.
        """
        if input_type == 'upload':
            self.input_upload(work_dir, blobs, ddl_inputs)
        elif input_type == 'blobset':
            if 'id_blobs' not in blobs:
                raise IPOLCopyBlobsError("id_blobs absent")

            blobs_id_list = blobs['id_blobs']
            self.copy_blobset_from_physical_location(work_dir, blobs_id_list)


    @staticmethod
    def download(url_file, filename):
        """
        Downloads a file from its URL
        """
        url_handle = urllib.urlopen(url_file)
        file_handle = open(filename, 'w')
        file_handle.write(url_handle.read())
        file_handle.close()


    @staticmethod
    def get_compressed_file(filename):
        """
        Return the demoExtras file and contained file names
        """
        if tarfile.is_tarfile(filename):
            # start with tar
            ar_tar = tarfile.open(filename)
            content_tar = ar_tar.getnames()
            return ar_tar, content_tar

        elif zipfile.is_zipfile(filename):
            ar_zip = zipfile.ZipFile(filename)
            content_zip = ar_zip.namelist()
            return ar_zip, content_zip
        else:
            raise IPOLExtractError('The file is neither a ZIP nor TAR')

    def extract(self, filename, target):
        """
        extract tar, tgz, tbz and zip archives
        """
        ar, content = self.get_compressed_file(filename)

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

    def extract_demo_extra(self, demo_id, compressed_file):
        """
        Extract a demo extra...
        input: demo_id and compressed file for the extraction
        return: success or not
        """
        try:
            demo_extras_folder = os.path.join(self.demoExtrasMainDir, str(demo_id))
            if os.path.isdir(demo_extras_folder):
                shutil.rmtree(demo_extras_folder)

            self.mkdir_p(demo_extras_folder)
            self.extract(compressed_file, demo_extras_folder)
        except Exception as ex:
            raise IPOLDemoExtrasError(ex)

    def ensure_extras_updated(self, demo_id):
        """
        Ensure that the demo extras of a given demo are updated respect to demoinfo information.
        and exists in the core folder.
        """
        demoextras_compress_dir = os.path.join(self.dl_extras_dir, str(demo_id))

        demoextras_file = os.path.join(demoextras_compress_dir, self.demoExtrasFilename)

        self.mkdir_p(demoextras_compress_dir)

        resp = self.post(self.host_name, 'demoinfo', 'get_demo_extras_info', {"demo_id": demo_id})
        demoinfo_resp = resp.json()

        if demoinfo_resp['status'] != 'OK':
            raise IPOLDemoExtrasError("Demoinfo responds with a KO")

        if not os.path.isfile(demoextras_file):
            if 'url' not in demoinfo_resp:
                return
            # There is a new demoExtras in demoinfo
            self.download(demoinfo_resp['url'], demoextras_file)
            self.extract_demo_extra(demo_id, demoextras_file)
        else:
            if 'url' not in demoinfo_resp:
                # DemoExtras was removed from demoinfo
                shutil.rmtree(demoextras_compress_dir)  # remove compress file
                shutil.rmtree(os.path.join(self.demoExtrasMainDir, str(demo_id)))  # remove demoExtras file
                return

            demoinfo_demoextras_date = demoinfo_resp['date']
            demoinfo_demoextras_size = demoinfo_resp['size']
            core_demoextras_date = os.stat(demoextras_file).st_mtime
            core_demoextras_size = os.stat(demoextras_file).st_size
            if core_demoextras_date <= demoinfo_demoextras_date or core_demoextras_size != demoinfo_demoextras_size:
                # DemoExtras needs an update
                self.download(demoinfo_resp['url'], demoextras_file)
                self.extract_demo_extra(demo_id, demoextras_file)

    @staticmethod
    def create_new_execution_key(logger):
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
            logger.exception("create_new_execution_key()")
            return None

        return key

    def create_run_dir(self, demo_id, key):
        """
        If it not exist, create a run_dir for a demo
        then, create a folder for the execution
        """
        demo_path = os.path.join(self.shared_folder_abs,
                                 self.share_run_dir_abs,
                                 str(demo_id),
                                 key)
        self.mkdir_p(demo_path)
        return demo_path

    def get_demo_metadata(self, demo_id):
        """
        Gets demo meta data given its editor's ID
        """
        userdata = {"demoid": demo_id}
        resp = self.post(self.host_name, 'demoinfo', 'read_demo_metainfo', userdata)
        return resp.json()

    def get_demo_editor_list(self, demo_id):
        """
        Get the list of editors of the given demo
        """
        # Get the list of editors of the demo
        userdata = {"demo_id": demo_id}
        resp = self.post(self.host_name, 'demoinfo',
                         'demo_get_editors_list', userdata)
        response = resp.json()
        status = response['status']

        if status != 'OK':
            # [ToDo]: log this error!
            return ()

        editor_list = response['editor_list']

        if not editor_list:
            return ()  # No editors given

        # Get the names and emails of the editors
        emails = []
        for entry in editor_list:
            emails.append({"name": entry['name'], "email": entry['mail']})

        return emails

    @staticmethod
    def send_email(subject, text, emails, sender, zip_filename=None):
        """
        Send an email to the given recipients
        """
        if text is None:
            text = ""
        emails_str = ", ".join(emails)

        msg = MIMEMultipart()
        msg['Subject'] = subject
        msg['From'] = "{} <{}>".format(sender["name"], sender["email"])
        msg['To'] = emails_str  # Must pass only a comma-separated string here
        msg.preamble = text

        if zip_filename is not None:
            with open(zip_filename) as fp:
                zip_data = MIMEApplication(fp.read())
                zip_data.add_header('Content-Disposition', 'attachment', filename="experiment.zip")
            msg.attach(zip_data)

        text_data = MIMEText(text)
        msg.attach(text_data)
        try:
            s = smtplib.SMTP('localhost')
            # Must pass only a list here
            s.sendmail(msg['From'], emails, msg.as_string())
            s.quit()
        except Exception:
            pass

    def send_compilation_error_email(self, demo_id, text):
        """
        Send email to editor when compilation fails
        """
        emails = []

        demo_state = self.get_demo_metadata(demo_id)["state"].lower()

        # Add Tech and Edit only if this is the production server and
        # the demo has been published

        config_emails = self.read_emails_from_config()
        if not config_emails:
            return

        for editor_mail in self.get_demo_editor_list(demo_id):
            emails.append(editor_mail['email'])

        if self.serverEnvironment == 'production' and demo_state == "published":
            emails += config_emails['tech']['email'].split(",")
            emails += config_emails['edit']['email'].split(",")
        if not emails:
            return

        # Send the email
        subject = 'Compilation of demo #{} failed'.format(demo_id)
        self.send_email(subject, text, emails, config_emails['sender'])

    def send_internal_error_email(self, message):
        """
        Send email to the IPOL team when an Internal Error has been detected
        """
        config_emails = self.read_emails_from_config()
        if not config_emails:
            return

        emails = config_emails['tech']['email'].split(",")
        if not emails:
            return

        # Send the email
        subject = 'IPOL Internal Error'
        text = "An Internal Error has been detected in IPOL.\n\n"
        text += str(message) + "\n"
        text += "Traceback follows:\n"
        text += traceback.format_exc()

        print "**** INTERNAL ERROR!\n\n"
        print text

        self.send_email(subject, text, emails, config_emails['sender'])

    def read_emails_from_config(self):
        """
        Read the list of emails from the configuration file
        """
        try:
            emails_file_path = os.path.join(self.project_folder,
                                            "ipol_demo", "modules", "config_common", "emails.conf")
            cfg = ConfigParser.ConfigParser()
            if not os.path.isfile(emails_file_path):
                self.error_log("read_emails_from_config",
                               "Can't open {}".format(emails_file_path))
                return {}

            emails = {}
            cfg.read([emails_file_path])
            for section in cfg.sections():
                emails[section] = {"name": cfg.get(section, "name"), "email": cfg.get(section, "email")}

            return emails
        except Exception as e:
            self.logger.exception("Can't read emails of journal staff")
            print "Fail reading emails config. Exception:", e

    # From http://stackoverflow.com/questions/1855095/how-to-create-a-zip-archive-of-a-directory
    @staticmethod
    def zipdir(path, ziph):
        """ Zip a directory """
        # ziph is zipfile handle
        for root, _, files in os.walk(path):
            for f in files:
                ziph.write(os.path.join(root, f))

    def send_runtime_error_email(self, demo_id, key, message):
        """
        Send email to editor when the execution fails
        """
        demo_state = self.get_demo_metadata(demo_id)["state"].lower()
        # Add Tech and Edit only if this is the production server and
        # the demo has been published
        emails = []
        config_emails = self.read_emails_from_config()
        if not config_emails:
            return

        for editor in self.get_demo_editor_list(demo_id):
            emails.append(editor['email'])

        if self.serverEnvironment == 'production' and demo_state == "published":
            emails += config_emails['tech']['email'].split(",")
            emails += config_emails['edit']['email'].split(",")

        if not emails:
            return

        # Attach experiment in zip file and send the email
        hostname = socket.gethostname()
        hostbyname = socket.gethostbyname(hostname)
        text = "This is the IPOL Core machine ({}, {}).\n\n\
The execution with key={} of demo #{} has failed.\nProblem: {}.\nPlease find \
attached the failed experiment data.". \
            format(hostname, hostbyname, key, demo_id, message)

        subject = '[IPOL Core] Demo #{} execution failure'.format(demo_id)

        # Zip the contents of the tmp/ directory of the failed experiment
        zip_filename = '/tmp/{}.zip'.format(key)
        zipf = zipfile.ZipFile(zip_filename, 'w', zipfile.ZIP_DEFLATED)
        self.zipdir("{}/run/{}/{}".format(self.shared_folder_abs, demo_id, key), zipf)
        zipf.close()
        self.send_email(subject, text, emails, config_emails['sender'], zip_filename=zip_filename)

    def send_demorunner_unresponsive_email(self,
                                           unresponsive_demorunners):
        """
        Send email to editor when the demorruner is down
        """
        emails = []
        config_emails = self.read_emails_from_config()
        if not config_emails:
            return

        if self.serverEnvironment == 'production':
            emails += config_emails['tech']['email'].split(",")
        if not emails:
            return

        hostname = socket.gethostname()
        hostbyname = socket.gethostbyname(hostname)

        unresponsive_demorunners_list = ",". \
            join(unresponsive_demorunners)

        text = "This is the IPOL Core machine ({}, {}).\n" \
               "\nThe list of demorunners unresponsive is: {}.". \
            format(hostname, hostbyname, unresponsive_demorunners_list)
        subject = '[IPOL Core] Demorunner unresponsive'
        self.send_email(subject, text, emails, config_emails['sender'])

    def send_email_no_DR(self, demo_id):
        """
        Send email to tech when there isn't any suitable demorunner for a published demo
        """
        emails = []
        config_emails = self.read_emails_from_config()
        if not config_emails:
            return

        if self.serverEnvironment != 'production':
            emails += config_emails['tech']['email'].split(",")
        if not emails:
            return

        hostname = socket.gethostname()
        hostbyname = socket.gethostbyname(hostname)

        text = "This is the IPOL Core machine ({}, {}).\n" \
               "\nThere isn't any suitable DR for demo: {}.". \
            format(hostname, hostbyname, demo_id)
        subject = '[IPOL Core] Not suitable DR'
        self.send_email(subject, text, emails, config_emails['sender'])

    @cherrypy.expose
    def run2(self, **kwargs):
        """
        Run a demo. The presentation layer requests the Core to
        execute a demo.
        """
        print 'KWARGS'
        print kwargs

        clientData = kwargs['clientData']
        clientData = json.loads(clientData)

        demo_id = clientData['demo_id']

        origin = clientData.get('origin', None)
        if origin is not None:
            origin = origin.lower()

        params = clientData.get('params', None)
        print params

        crop_info = clientData.get('crop_info', None)

        private_mode = clientData.get('private_mode', None)

        blobs = {}
        if origin == 'upload':
            print "UPLOAD"
            i = 0
            while "file_{0}".format(i) in kwargs:
                fname = "file_{0}".format(i)
                blobs[fname] = kwargs[fname]
                i += 1
        elif origin == 'blobset':
            print "DEMO"
            print clientData
            blobs = clientData['blobs']
        else:
            pass

        # Obtain the DDL
        try:
            demoinfo_resp = self.post(self.host_name, 'demoinfo', 'get_ddl', {"demo_id": demo_id})
            demoinfo_response = demoinfo_resp.json()

            last_demodescription = demoinfo_response['last_demodescription']
            ddl = json.loads(last_demodescription['ddl'])

            if 'build' in ddl:
                ddl_build = ddl['build']
            else:
                return json.dumps({"status": "KO", "error": "no 'build' section found in the DDL"})

            if 'archive' in ddl:
                # The params must be a list
                if 'params' in ddl['archive']:
                    if type(ddl['archive']['params']) != list:
                        message = "Bad DDL archive section: expected list for parameters, but found {}".format(type(ddl['archive']['params']))
                        return json.dumps({"status": "KO", "error": message})
            
            
            ddl_inputs = ddl['inputs']

        except Exception as ex:
            message = "Failed to obtain the DDL of demo {}".format(demo_id)
            print message, ex
            self.logger.exception(message)
            return json.dumps({'error': message, 'status': 'KO'})

        # Create a new execution key
        key = self.create_new_execution_key(self.logger)
        if key is None:
            message = '**INTERNAL ERROR**. Failed to create a valid execution key'
            self.logger.exception(message)
            self.send_internal_error_email(message)
            res_data = {'error': message, 'status': 'KO'}
            return json.dumps(res_data)
        try:
            work_dir = self.create_run_dir(demo_id, key)
        except Exception as ex:
            res_data = {'error': 'Could not create work_dir for demo {}. Error:{}'.format(demo_id, ex),
                        'status': 'KO'}
            self.logger.exception("Could not create work_dir for demo {}".format(demo_id))
            print 'Could not create work_dir for demo {}. Error:{}'.format(demo_id, ex)
            return json.dumps(res_data)

        # Copy input blobs
        if origin is not None:
            try:
                self.copy_blobs(work_dir, origin, blobs, ddl_inputs)
                params_conv = {"work_dir": work_dir, "inputs_description": json.dumps(ddl_inputs), "crop_info": json.dumps(crop_info)}
                resp = self.post(self.host_name, 'conversion', 'convert', params_conv)
                print resp.json()
                conversion_info = json.loads(resp.json()["info"])
                for input_key in conversion_info:
                    if conversion_info[input_key]["code"] == -1: # Conversion error
                        res_data = {'error': 'Input #{}: {}'.format(input_key, conversion_info[input_key]["error"]),
                                    'status': 'KO'}
                        return json.dumps(res_data)
                    elif conversion_info[input_key]["code"] == 2: # Conversion forbidden
                        res_data = {'error': 'Input #{} size too large but conversion forbidden'.format(input_key),
                                    'status': 'KO'}
                        return json.dumps(res_data)

            except IPOLEvaluateError as ex:
                message = 'Invalid expression "{}" found in the DDL of demo {}'.format(ex, demo_id)
                res_data = {'error': message,
                            'status': 'KO'}
                self.logger.exception(message)
                print message
                return json.dumps(res_data)
            except IPOLCopyBlobsError as ex:
                message = '** INTERNAL ERROR **. Error copying blobs of demo {}: {}'.format(demo_id, ex)
                self.logger.exception(message)
                self.send_internal_error_email(message)
                res_data = {'error': message, 'status': 'KO'}
                return json.dumps(res_data)
            except IPOLInputUploadError as ex:
                message = '** INTERNAL ERROR **. Error uploading input of demo {}: {}'.format(demo_id, ex)
                self.logger.exception(message)
                self.send_internal_error_email(message)
                res_data = {'error': message, 'status': 'KO'}
                return json.dumps(res_data)
            except IPOLProcessInputsError as ex:
                message = '** INTERNAL ERROR **. Error processing inputs of demo {}: {}'.format(demo_id, ex)
                self.logger.exception(message)
                self.send_internal_error_email(message)
                res_data = {'error': message, 'status': 'KO'}
                return json.dumps(res_data)
            except IOError as ex:
                message = '** INTERNAL ERROR **. I/O error processing inputs - {}'.format(ex)
                self.logger.exception(message)
                self.send_internal_error_email(message)
                res_data = {'error': message, 'status': 'KO'}
                return json.dumps(res_data)
            except Exception as ex:
                message = '**INTERNAL ERROR**. Blobs operations of demo {} failed - {}'.format(demo_id, ex)
                self.logger.exception(message)
                self.send_internal_error_email(message)
                res_data = {'error': message, 'status': 'KO'}
                return json.dumps(res_data)

        try:
            if 'general' not in ddl:
                response = {"error": "bad DDL syntax: no 'general' section found", "status": "KO"}
                return json.dumps(response)

            # Find a DR that satisfies the requirements
            if 'requirements' in ddl['general']:
                requirements = ddl['general']['requirements']
            else:
                requirements = None

            dr_name, dr_server = self.get_demorunner(
                self.demorunners_workload(), requirements)
            if dr_name is None:
                response = {'status': 'KO', 'error': 'No DR satisfies the requirements: {}'.format(requirements)}
                if self.get_demo_metadata(demo_id)["state"].lower() == "published":
                    self.send_email_no_DR(demo_id)
                return json.dumps(response)

            build_data = {"demo_id": demo_id, "ddl_build": json.dumps(ddl_build)}
            dr_response = self.post(dr_server, 'demorunner', 'ensure_compilation', build_data)

            demorunner_response = dr_response.json()
            status = demorunner_response['status']
            if status != 'OK':
                print "COMPILATION FAILURE in demo = ", demo_id

                # Send compilation message to the editors
                text = "DR={}, {} - {}".format(dr_name, demorunner_response.get("buildlog", "").encode('utf8'),
                                               demorunner_response["message"].encode('utf8'))

                self.send_compilation_error_email(demo_id, text)

                # Message for the web interface
                response = {"error": " --- Compilation error. --- {}".format(text), "status": "KO"}
                return json.dumps(response)

            try:
                self.ensure_extras_updated(demo_id)
            except IPOLDemoExtrasError as ex:
                message = 'Error processing the demoExtras of demo {}: {}'.format(demo_id, ex)
                self.logger.exception(message)
                print message
                response = {'status': 'KO',
                            'error': message}
                return json.dumps(response)

            # save parameters as a params.json file
            try:
                work_dir = os.path.join(self.share_run_dir_abs, str(demo_id), key)
                json_filename = os.path.join(work_dir, "params.json")
                with open(json_filename, "w") as resfile:
                    resfile.write(json.dumps(params))
            except (OSError, IOError) as ex:
                message = "Failed to save {} in demo {}".format(json_filename, demo_id)
                self.logger.exception(message)
                print message
                response = {'status': 'KO', 'error': message}
                return json.dumps(response)

            userdata = {"demo_id": demo_id, "key": key, "params": json.dumps(params)}

            if 'run' not in ddl:
                return json.dumps({"error": "bad DDL syntax: no 'run' section found", "status": "KO"})

            userdata['ddl_run'] = json.dumps(ddl['run'])

            if 'timeout' in ddl['general']:
                userdata['timeout'] = ddl['general']['timeout']

            resp = self.post(dr_server, 'demorunner', 'exec_and_wait', userdata)
            try:
                demorunner_response = resp.json()
            except Exception as ex:
                message = "**INTERNAL ERROR**. Bad format in the response from DR server {} in demo {}. {} - {}".format(dr_server, demo_id, demorunner_response.content, ex)
                self.logger.exception(message)
                self.send_internal_error_email(message)
                core_response = {"status": "KO", "error": "{}".format(message)}
                return json.dumps(core_response)

            if demorunner_response['status'] != 'OK':
                print "DR answered KO for demo #{}".format(demo_id)
                demo_state = self.get_demo_metadata(demo_id)["state"].lower()

                # Message for the web interface
                msg = (demorunner_response["algo_info"]["status"]).encode('utf-8').strip()
                error = demorunner_response.get("error", "").strip()

                # Prepare a message for the website.
                # In case of a timeout, let it be human oriented.
                if error == 'IPOLTimeoutError':
                    website_message = "This execution had to be stopped because of TIMEOUT. Please reduce the size of your input."
                else:
                    website_message = "DR={}, {}".format(dr_name, msg)

                response = {"error": website_message,
                            "status": "KO"}
                # Send email to the editors
                # (unless it's a timeout in a published demo)
                if not (demo_state == 'published' and error == 'IPOLTimeoutError'):
                    self.send_runtime_error_email(demo_id, key, website_message)
                return json.dumps(response)

            demorunner_response['work_url'] = os.path.join(
                "http://{}/api/core/".format(self.host_name),
                self.shared_folder_rel,
                self.share_run_dir_rel,
                str(demo_id),
                key) + '/'

            dic = self.read_algo_info(work_dir)
            for name in dic:
                demorunner_response["algo_info"][name] = dic[name]
            # Archive the experiment, if the 'archive' section
            # exists in the DDL

            if origin != 'blobset'and private_mode is None and 'archive' in ddl:
                ddl_archive = ddl['archive']
                print ddl_archive
                SendArchive.prepare_archive(demo_id, work_dir, ddl_archive,
                                            demorunner_response, self.host_name)

            # Save the execution, so the users can recover it from the URL
            self.save_execution(demo_id, kwargs, demorunner_response, work_dir)

        except Exception as ex:
            message = "**INTERNAL ERROR** in the run function of the Core in demo {}, {}".format(demo_id, ex)
            self.logger.exception(message)
            self.send_internal_error_email(message)
            core_response = {"status": "KO", "error": "{}".format(message)}
            return json.dumps(core_response)

        return json.dumps(demorunner_response)

    @staticmethod
    def save_execution(demo_id, request, response, work_dir):
        """
        Save all needed data to recreate an execution.
        """
        clientData = json.loads(request['clientData'])

        if clientData.get("origin", "") == "upload":
            # Count how many file entries and remove them
            file_keys = [key for key in request if key.startswith("file_")]
            map(request.pop, file_keys)
            clientData["files"] = len(file_keys)

        clientData = json.dumps(clientData)

        execution_json = {}
        execution_json['demo_id'] = demo_id
        execution_json['request'] = clientData
        execution_json['response'] = response

        # Save file
        with open(os.path.join(work_dir, "execution.json"), 'w') as outfile:
            json.dump(execution_json, outfile)

    @cherrypy.expose
    def load_execution(self, demo_id, key):
        """
        Load the data needed to recreate an execution.
        """
        filename = os.path.join(self.share_run_dir_abs, str(demo_id), key, "execution.json")
        if not os.path.isfile(filename):
            message = "Execution with key={} not found".format(key)
            res_data = {'error': message, 'status': 'KO'}
            print message
            return json.dumps(res_data)

        try:
            with open(filename, "r") as f:
                lines = f.read()
        except Exception as ex:
            message = "** INTERNAL ERROR ** while reading execution with key={}: {}".format(key, ex)
            self.logger.exception(message)
            self.send_internal_error_email(message)
            res_data = {'error': message, 'status': 'KO'}
            return json.dumps(res_data)

        return json.dumps({'status': 'OK', 'execution': lines})

    @cherrypy.expose
    def run(self, demo_id, **kwargs):
        """
        Run a demo. The presentation layer requests the Core to
        execute a demo.
        """
        demo_id = int(demo_id)

        if 'input_type' in kwargs:
            input_type = kwargs.get('input_type')
        else:
            response = {"status": "KO"}
            self.error_log("run", "No 'input_type' passed to the run function.")
            return json.dumps(response)

        params = kwargs.get('params')

        original_exp = kwargs.get('original')

        crop_info = kwargs.get('crop_info', None)

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

        # Start of block to obtain the DDL
        try:
            resp = self.post(self.host_name, 'demoinfo',
                             'get_ddl', {"demo_id": demo_id})
            response = resp.json()

            last_demodescription = response['last_demodescription']
            ddl_json = json.loads(last_demodescription['ddl'])

            if 'build' in ddl_json:
                ddl_build = ddl_json['build']
            else:
                response = {"status": "KO", "error": "no 'build' section found in the DDL"}
                return json.dumps(response)
            
            if 'archive' in ddl_json:
                if 'params' in ddl_json['archive']:
                    # The params must be a list
                    if type(ddl_json['archive']['params']) != list:
                        message = "Bad DDL archive section: expected list for parameters, but found {}".format(type(ddl['archive']['params']))
                        return json.dumps({"status": "KO", "error": message})

            ddl_inputs = ddl_json.get('inputs')

        except Exception as ex:
            message = "Failed to obtain the DDL of demo {}".format(demo_id)
            print message, ex
            self.logger.exception(message)
            res_data = {'error': message, 'status': 'KO'}
            return json.dumps(res_data)
        # End block to obtain the DDL

        # Create a new execution key
        key = self.create_new_execution_key(self.logger)
        if key is None:
            message = '**INTERNAL ERROR**. Failed to create a valid execution key'
            self.logger.exception(message)
            self.send_internal_error_email(message)
            res_data = {'error': message, 'status': 'KO'}
            return json.dumps(res_data)
        try:
            work_dir = self.create_run_dir(demo_id, key)
        except Exception as ex:
            res_data = {'error': 'Could not create work_dir for demo {}. Error:{}'.format(demo_id, ex),
                        'status': 'KO'}
            self.logger.exception("Could not create work_dir for demo {}".format(demo_id))
            print 'Could not create work_dir for demo {}. Error:{}'.format(demo_id, ex)
            return json.dumps(res_data)

        # Copy input blobs
        if input_type != 'noinputs':
            try:
                self.copy_blobs(work_dir, input_type, blobs, ddl_inputs)
                self.process_inputs(work_dir, ddl_inputs, crop_info)
            except IPOLEvaluateError as ex:
                message = 'Invalid expression "{}" found in the DDL of demo {}'.format(ex, demo_id)
                res_data = {'error': message,
                            'status': 'KO'}
                self.logger.exception(message)
                print message
                return json.dumps(res_data)
            except IPOLCopyBlobsError as ex:
                message = 'Error copying blobs of demo {}: {}'.format(demo_id, ex)
                res_data = {'error': message,
                            'status': 'KO'}
                self.logger.exception(message)
                print message
                return json.dumps(res_data)
            except IPOLInputUploadError as ex:
                message = 'Error uploading input of demo {}: {}'.format(demo_id, ex)
                res_data = {'error': message,
                            'status': 'KO'}
                self.logger.exception(message)
                print message
                return json.dumps(res_data)
            except IPOLProcessInputsError as ex:
                message = 'Error processing inputs of demo {}: {}'.format(demo_id, ex)
                res_data = {'error': message,
                            'status': 'KO'}
                self.logger.exception(message)
                print message
                return json.dumps(res_data)
            except IOError as ex:
                message = 'I/O error processing inputs - {}'.format(ex)
                res_data = {'error': message,
                            'status': 'KO'}
                self.logger.exception(message)
                print message
                return json.dumps(res_data)
            except Exception as ex:
                # ToDo: send email
                message = '**INTERNAL ERROR**. Blobs operations of demo {} failed - {}'.format(demo_id, ex)
                self.logger.exception(message)
                self.send_internal_error_email(message)
                res_data = {'error': message,
                            'status': 'KO'}
                return json.dumps(res_data)

        try:

            if 'general' not in ddl_json:
                response = {"error": "bad DDL syntax: no 'general' section found", "status": "KO"}
                return json.dumps(response)

            # Find a DR with satisfies the requirements
            requirements = ddl_json['general']['requirements'] \
                if 'requirements' in ddl_json['general'] else None

            dr_name, dr_server = self.get_demorunner(
                self.demorunners_workload(), requirements)
            if dr_name is None:
                response = {'status': 'KO', 'error': 'No DR satisfies the requirements: {}'.format(requirements)}
                if self.get_demo_metadata(demo_id)["state"].lower() == "published":
                    self.send_email_no_DR(demo_id)
                return json.dumps(response)

            userdata = {"demo_id": demo_id, "ddl_build": json.dumps(ddl_build)}
            resp = self.post(dr_server, 'demorunner', 'ensure_compilation', userdata)

            demorunner_response = resp.json()
            status = demorunner_response['status']
            if status != 'OK':
                print "COMPILATION FAILURE in demo = ", demo_id

                # Send compilation message to the editors
                text = "DR={}, {} - {}".format(dr_name, demorunner_response.get("buildlog", "").encode('utf8'),
                                               demorunner_response["message"].encode('utf8'))

                self.send_compilation_error_email(demo_id, text)

                # Message for the web interface
                response = {"error": " --- Compilation error. --- {}".format(text), "status": "KO"}
                return json.dumps(response)

            try:
                self.ensure_extras_updated(demo_id)
            except IPOLDemoExtrasError as ex:
                message = 'Error processing the demoExtras of demo {}: {}'.format(demo_id, ex)
                self.logger.exception(message)
                print message
                response = {'status': 'KO',
                            'error': message}
                return json.dumps(response)

            # save parameters as a params.json file
            try:
                work_dir = os.path.join(self.share_run_dir_abs, str(demo_id), key)
                json_filename = os.path.join(work_dir, "params.json")
                with open(json_filename, "w") as resfile:
                    resfile.write(params)
            except (OSError, IOError) as ex:
                message = "Failed to save {} in demo {}".format(json_filename, demo_id)
                self.logger.exception(message)
                print message
                response = {'status': 'KO', 'error': message}
                return json.dumps(response)

            userdata = {"demo_id": demo_id, "key": key, "params": params}

            if 'run' not in ddl_json:
                return json.dumps({"error": "bad DDL syntax: no 'run' section found", "status": "KO"})

            userdata['ddl_run'] = json.dumps(ddl_json['run'])

            if 'timeout' in ddl_json['general']:
                userdata['timeout'] = ddl_json['general']['timeout']

            resp = self.post(dr_server, 'demorunner', 'exec_and_wait', userdata)
            try:
                demorunner_response = resp.json()
            except Exception as ex:
                message = "**INTERNAL ERROR**. Bad format in the response from DR server {} in demo {}. {}".format(dr_server, demo_id, ex)
                self.logger.exception(message)
                self.send_internal_error_email(message)
                core_response = {"status": "KO", "error": "{}".format(message)}
                return json.dumps(core_response)

            if demorunner_response['status'] != 'OK':
                print "DR answered KO for demo #{}".format(demo_id)
                demo_state = self.get_demo_metadata(demo_id)["state"].lower()

                # Message for the web interface
                msg = (demorunner_response["algo_info"]["status"]).encode('utf-8').strip()
                error = demorunner_response.get("error", "").strip()

                # Prepare a message for the website.
                # In case of a timeout, let it be human oriented.
                if error == 'IPOLTimeoutError':
                    website_message = "This execution had to be stopped because of TIMEOUT. Please reduce the size of your input."
                else:
                    website_message = "DR={}, {}".format(dr_name, msg)

                response = {"error": website_message,
                            "status": "KO"}
                
                # Send email to the editors
                # (unless it's a timeout in a published demo)
                if not (demo_state == 'published' and error == 'IPOLTimeoutError'):
                    self.send_runtime_error_email(demo_id, key, website_message)
                return json.dumps(response)


            demorunner_response['work_url'] = os.path.join(
                "http://{}/api/core/".format(self.host_name),
                self.shared_folder_rel,
                self.share_run_dir_rel,
                str(demo_id),
                key) + '/'

            # Archive the experiment, if the 'archive' section
            # exists in the DDL
            if (original_exp == 'true' or input_type == 'noinputs') and  'archive' in ddl_json:
                ddl_archive = ddl_json['archive']
                print ddl_archive
                SendArchive.prepare_archive(demo_id, work_dir, ddl_archive,
                                            demorunner_response, self.host_name)

        except Exception as ex:
            message = "**INTERNAL ERROR** in the run function of the Core in demo {}, {}".format(demo_id, ex)
            self.logger.exception(message)
            self.send_internal_error_email(message)
            core_response = {"status": "KO", "error": "{}".format(message)}
            return json.dumps(core_response)

        dic = self.read_algo_info(work_dir)
        for name in dic:
            demorunner_response["algo_info"][name] = dic[name]

        return json.dumps(demorunner_response)

    def read_algo_info(self, work_dir):
        """
        Read the file algo_info.txt to make available in the system
        variables created or modified by the algorithm
        """
        file_name = os.path.join(work_dir, "algo_info.txt")

        if not os.path.isfile(file_name):
            return {}  # The algorithm didn't create the file

        dic = {}
        f = open(file_name, "r")
        lines = f.read().splitlines()
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
        """
        Return an active demorunner for the requirements
        """
        demorunner_data = {
            "demorunners_workload": str(demorunners_workload),
            "requirements": requirements
        }
        unresponsive_demorunners = set()
        # Try twice the length of the DR list before raising an exception
        for i in range(len(self.demorunners) * 2):
            # Get a demorunner for the requirements
            try:
                dispatcher_response = self.post(self.host_name, 'dispatcher', 'get_demorunner', demorunner_data)
            except ConnectionError:
                dispatcher_response = None

            if not dispatcher_response or not dispatcher_response.ok:
                raise Exception("Dispatcher unresponsive") # [Miguel] [ToDo] Use an specific exception, not the too-wide Exception

            # Check if there is a DR for the requirements
            if dispatcher_response.json()['status'] != 'OK':
                return None, None

            dr_name = dispatcher_response.json()['name']
            dr_server = self.demorunners[dr_name]['server']

            # Check if the DR is up. Otherwise add it to the
            # list of unresponsive DRs
            demorunner_response = self.post(dr_server, 'demorunner', 'ping')
            if demorunner_response.ok:
                if unresponsive_demorunners:
                    self.send_demorunner_unresponsive_email(unresponsive_demorunners)
                return dr_name, dr_server
            else:
                self.error_log("get_demorunner",
                               "Module {} unresponsive".format(dr_name))
                print "Module {} unresponsive".format(dr_name)
                unresponsive_demorunners.add(dr_name)

            # At half of the tries wait 5 secs and try again
            if i == len(self.demorunners) - 1:
                time.sleep(5)

        # If there is no demorrunner active send an email with all the unresponsive DRs
        self.send_demorunner_unresponsive_email(unresponsive_demorunners)
        raise Exception("No DR available after many tries")  # [Miguel] [ToDo] Use an specific exception, not the too-wide Exception

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
            self.logger.exception("Failure in the post function of the CORE")

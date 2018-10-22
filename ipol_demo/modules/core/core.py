#!/usr/bin/env python3
"""
IPOL Core module
"""
import configparser
import errno
import glob
import hashlib
import json
import logging
import mimetypes
import os
import os.path
import re
import shutil
# To send emails
import smtplib
import socket
import tarfile
import time
import traceback
import urllib.error
import urllib.parse
import urllib.request
import xml.etree.ElementTree as ET
import zipfile
from collections import OrderedDict
from datetime import datetime
from email.mime.application import MIMEApplication
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from random import random

import cherrypy
import magic

import requests
from archive import send_to_archive
from errors import (IPOLCheckDDLError, IPOLConversionError, IPOLCopyBlobsError,
                    IPOLDecodeInterfaceRequestError, IPOLDemoExtrasError,
                    IPOLDemoRunnerResponseError, IPOLEnsureCompilationError,
                    IPOLExecutionError, IPOLExtractError, IPOLFindSuitableDR,
                    IPOLInputUploadError, IPOLInputUploadTooLargeError,
                    IPOLKeyError, IPOLMissingRequiredInputError,
                    IPOLPrepareFolderError, IPOLProcessInputsError,
                    IPOLReadDDLError, IPOLUploadedInputRejectedError,
                    IPOLWorkDirError)
from ipolutils.evaluator.evaluator import IPOLEvaluateError, evaluate
# deprecated, should be droped with old run
from Tools.image import image


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
            return json.dumps(error).encode()
        return func(*args, **kwargs)

    def is_authorized_ip(ip_number):
        """
        Validates the given IP
        """
        core = Core.get_instance()
        patterns = []
        # Creates the patterns  with regular expressions
        for authorized_pattern in core.authorized_patterns:
            result = re.compile(authorized_pattern.replace(".", "\\.").replace("*", "[0-9]*"))
            patterns.append(result)
        # Compare the IP with the patterns
        for pattern in patterns:
            if pattern.match(ip_number) is not None:
                return True
        return False

    return authenticate_and_call


# -------------------------------------------------------------------------------
class Core():
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
            ### Read the configuration file

            # Get the server environment (integration or production)
            hostname = socket.gethostname()
            if hostname == cherrypy.config.get('production_hostname', 'ipolcore'):
                self.server_environment = 'production'
            elif hostname == cherrypy.config.get('integration_hostname', 'integration'):
                self.server_environment = 'integration'
            else:
                self.server_environment = '<unknown>'

            self.demorunners_file = cherrypy.config.get("demorunners_file")
            self.demorunners = {}

            self.logs_dir_rel = cherrypy.config.get("logs.dir")
            self.logs_name = cherrypy.config.get("logs.name")
            self.logger = self.init_logging()
            self.common_config_dir = cherrypy.config.get("config_common_dir")
            self.project_folder = cherrypy.config.get("project_folder")
            self.blobs_folder = cherrypy.config.get("blobs_folder")

            self.shared_folder_rel = cherrypy.config.get("shared_folder")
            self.shared_folder_abs = os.path.join(self.project_folder, self.shared_folder_rel)
            self.demo_extras_main_dir = os.path.join(
                self.shared_folder_abs,
                cherrypy.config.get("demoExtrasDir"))
            self.dl_extras_dir = os.path.join(self.shared_folder_abs,
                                              cherrypy.config.get("dl_extras_dir"))
            self.share_run_dir_rel = cherrypy.config.get("running.dir")
            self.share_run_dir_abs = os.path.join(
                self.shared_folder_abs, self.share_run_dir_rel)

            self.demo_failure_file = cherrypy.config.get("demo_failure_file")

            # Security: authorized IPs
            self.authorized_patterns = self.read_authorized_patterns()

            # create needed directories
            self.mkdir_p(self.share_run_dir_abs)
            self.mkdir_p(self.shared_folder_abs)
            self.mkdir_p(self.dl_extras_dir)
            self.mkdir_p(self.demo_extras_main_dir)

            self.load_demorunners()
        except Exception:
            self.logger.exception("__init__")

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
            cfg = configparser.ConfigParser()
            cfg.read([authorized_patterns_path])
            patterns = []
            for item in cfg.items('Patterns'):
                patterns.append(item[1])
            return patterns
        except configparser.Error:
            self.logger.exception("Bad format in {}".format(authorized_patterns_path))
            return []

    def load_demorunners(self):
        """
        Load the list of DRs from the configuration file
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
        Refresh the information of all DRs and notify Dispatcher to update
        """
        data = {"status": "KO"}

        try:
            # Reload DRs config
            self.load_demorunners()

            demorunners = {"demorunners": json.dumps(self.demorunners)}
            response = self.post('api/dispatcher/set_demorunners', data=demorunners)
            if response.json().get('status') == "OK":
                data['status'] = 'OK'

        except Exception as ex:
            print(ex)
            self.logger.exception("refresh_demorunners")
            data["error"] = "Can not refresh demorunners"

        return json.dumps(data).encode()

    @cherrypy.expose
    def get_demorunners(self):
        """
        Get the information of all demoRunners
        """
        data = {"status": "OK"}
        try:
            data["demorunners"] = str(self.demorunners)
        except Exception as ex:
            print(ex)
            self.logger.exception("get_demorunners")
            data["status"] = "KO"
            data["message"] = "Can't get demorunners"

        return json.dumps(data).encode()

    @cherrypy.expose
    def get_demorunners_stats(self):
        """
        Get statistic information of all DRs.
        This is mainly used by external monitoring tools.
        """
        demorunners = []
        #
        for demorunner in self.demorunners:
            try:
                response = {}
                dr_server = self.demorunners[demorunner].get('server')
                response = self.post('api/demorunner/get_workload', host=dr_server)
                if not response.ok:
                    demorunners.append({'name': demorunner, 'status': 'KO'})
                    continue

                json_response = response.json()
                if json_response.get('status') == 'OK':
                    workload = float('%.2f' % (json_response.get('workload')))
                    demorunners.append({'name': demorunner,
                                        'status': 'OK',
                                        'workload': workload})
                else:
                    demorunners.append({'name': demorunner, 'status': 'KO'})

            except requests.ConnectionError:
                name = demorunner.get("name", "<?>")
                self.logger.exception("Couldn't get DR={} workload".format(name))
                demorunners.append({'name': demorunner, 'status': 'KO'})
                continue
            except Exception as ex:
                message = "Couldn't get the DRs workload. Error = {}".format(ex)
                print(message)
                self.logger.exception(message)
                return json.dumps({'status': 'KO', 'message': message}).encode()

        # Return the DRs in the response
        return json.dumps({'status': 'OK', 'demorunners': demorunners}).encode()

    def demorunners_workload(self):
        """
        Get the workload of each DR
        """
        dr_workload = {}
        for dr_name in self.demorunners:
            try:
                dr_server = self.demorunners[dr_name]['server']
                resp = self.post('api/demorunner/get_workload', host=dr_server)
                if not resp or not resp.ok:
                    error_message = "Bad post response from DR='{}'".format(dr_name)
                    self.error_log("demorunners_workload", error_message)
                    continue

                response = resp.json()
                if response.get('status', '') == 'OK':
                    dr_workload[dr_name] = response.get('workload')
                else:
                    error_message = "get_workload KO response for DR='{}'".format(dr_name)
                    self.error_log("demorunners_workload", error_message)
                    dr_workload[dr_name] = 100.0
            except requests.ConnectionError:
                error_message = "get_workload ConnectionError for DR='{}'".format(dr_name)
                self.error_log("demorunners_workload", error_message)
                continue
            except Exception:
                error_message = "Error when obtaining the workload of '{}'".format(dr_name)
                self.logger.exception(error_message)
                dr_workload[dr_name] = 100.0
                continue

        return dr_workload

    @staticmethod
    def mkdir_p(path):
        """
        Create a directory given a path.
        It's like a "mkdir -p" command.
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
    def index(self, code_starts=None):
        """
        Index page
        """
        resp = self.post('api/demoinfo/demo_list')
        response = resp.json()
        status = response['status']

        cherrypy.response.headers['Content-Type'] = 'text/html'
        if status != 'OK':
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
        demos_by_state = OrderedDict()
        for demo in demo_list:
            editorsdemoid = demo['editorsdemoid']

            # If the user specified a demo code prefix, then ignore the
            # demos which don't start with that prefix.
            if code_starts and not str(editorsdemoid).startswith(code_starts):
                continue

            publication_state = demo["state"]
            if publication_state not in demos_by_state:
                demos_by_state[publication_state] = []

            demos_by_state[publication_state].append({
                'editorsdemoid': editorsdemoid,
                'title': demo['title']
            })

        demos_string = ""

        # Show demos according to their state
        for publication_state in demos_by_state:
            # Sort demo list by demo ID
            demos_by_state[publication_state] = sorted(demos_by_state[publication_state],\
                                                key=lambda d: (d['editorsdemoid']), \
                                                reverse=True)

            if demos_by_state[publication_state]:
                demos_string += "<h2><a id='{}'>{}</a></h2>".format(publication_state, publication_state)
            #
            for demo_data in demos_by_state[publication_state]:
                editorsdemoid = str(demo_data['editorsdemoid'])

                demos_string += "Demo #{} {}: <a href='/demo/clientApp/demo.html?id={}' target='_blank'>{}</a><br>".format(
                    editorsdemoid,
                    "(private)" if editorsdemoid.startswith("33333") else "",
                    editorsdemoid,
                    demo_data['title'])

        string = """
                 <!DOCTYPE html>
                 <html lang="en">
                 <head>
                 <meta charset="utf-8">
                 <title>IPOL demos</title>
                 </head>
                 <body>
                 <h1>List of demos</h1>
                 """
        # Only show the message if the user didn't specify a code start
        if not code_starts:
            string += """
                     <h3>The demos whose ID begins with '77777' are public workshops and those with '33333' are private.
                     Test demos begin with '55555'.</h3><br>
                     """
        string += """
                 {}
                 </body>
                 </html>
                 """.format(demos_string)

        return string

    @cherrypy.expose
    def demo(self, code_starts=None):
        """
        Return an HTML page with the list of demos.
        """
        return self.index(code_starts=code_starts)

    @staticmethod
    @cherrypy.expose
    def ping():
        """
        Ping: answer with a PONG.
        """
        data = {"status": "OK", "ping": "pong"}
        return json.dumps(data).encode()

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
        return json.dumps(data).encode()

    @staticmethod
    @cherrypy.expose
    def default(attr):
        """
        Default method invoked when asked for a non-existing service.
        """
        data = {"status": "KO", "message": "Unknown service '{}'".format(attr)}
        return json.dumps(data).encode()

    # ---------------------------------------------------------------------------
    # INPUT HANDLING TOOLS (OLD with a few modifications)
    # [Miguel] They're absolutely deprecated and need a full refactoring
    # in the Conversion module.
    # ---------------------------------------------------------------------------
    @staticmethod
    def save_image(im, fullpath):
        """
        Save image object given full path
        """
        im.save(fullpath, compresslevel=1)

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
        size_ok = (im.size[0] * im.size[1]) <= max_pixels
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
        if max_pixels and (im.size[0] * im.size[1]) > max_pixels:
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
                if 'required' not in list(inputs_desc[i].keys()) or \
                        inputs_desc[i]['required']:
                    # missing file
                    raise IPOLMissingRequiredInputError(i)
                else:
                    # skip this input
                    continue

            mime = magic.Magic(mime=True)
            file_up.file.seek(0)
            mime_uploaded_blob = mime.from_buffer(file_up.file.read())
            type_of_uploaded_blob, _ = mime_uploaded_blob.split('/')

            # Reject the uploaded file it it doesn't match the type in the DDL
            if inputs_desc[i]['type'] != type_of_uploaded_blob and inputs_desc[i]['type'] != "data":
                message = "The DDL type ({}) doesn't match the uploaded blob ({})".format(inputs_desc[i]['type'], type_of_uploaded_blob)
                raise IPOLUploadedInputRejectedError(message)

            # Reject the uploaded file it's not 'data' and it can't be guessed
            ext_of_uploaded_blob = mimetypes.guess_extension(mime_uploaded_blob)
            if inputs_desc[i]['type'] != "data" and ext_of_uploaded_blob is None:
                error_message = "The type of the uploaded file could not be recognized and it has been rejected"
                raise IPOLUploadedInputRejectedError(error_message)

            # If it's data, we just put the extension given at the DDL
            if inputs_desc[i]['type'] == "data":
                ext_of_uploaded_blob = inputs_desc[i]['ext']

            # Here we save the file with the final extension, regardless
            # the actual content.
            # Later Core will eventually ask the system to convert the
            # data (for example, encode in PNG).
            file_save = open(os.path.join(work_dir, 'input_%i' % i + ext_of_uploaded_blob), 'wb')

            # Read and save the file
            size = 0
            file_up.file.seek(0)
            while True:
                data = file_up.file.read(128)
                if not data:
                    break
                size += len(data)
                if 'max_weight' in inputs_desc[i] and size > evaluate(inputs_desc[i]['max_weight']):
                    # file too heavy
                    raise IPOLInputUploadTooLargeError(i, evaluate(inputs_desc[i]['max_weight']))

                file_save.write(data)
            file_save.close()

    def copy_blobset_from_physical_location(self, work_dir, blobs_id_list):
        """
        use the selected available input images
        input parameters:
        returns:
        """
        resp = self.post('api/blobs/get_blobs_location', data={'blobs_ids': blobs_id_list})
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
                    print("Couldn't copy  blobs from {} to {}. Error: {}".format(blob_path, final_path, ex))

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
    def check_ddl(ddl):
        """
        Check for required DDL fields and their types.
        """
        # Check that all mandatory sections are present
        sections = ('general', 'build', 'run', 'results')
        for section in sections:
            if not section in ddl:
                raise IPOLCheckDDLError("Bad DDL syntax: missing '{}' section.".format(section))

        # Empty run
        if not ddl['run'] or ddl['run'].isspace():
            raise IPOLCheckDDLError("Bad DDL run section: run is empty.")

        if 'inputs' in ddl:
            # Inputs must be a list.
            if not isinstance(ddl['inputs'], list):
                raise IPOLCheckDDLError("Bad DDL inputs section: expected list.")

            required_fields = {\
                'video' : ('max_pixels', 'max_frames'),\
                'image' : ('max_pixels', 'ext', 'dtype'),\
                'data' : ('ext',)\
            }

            # Integer and positive values
            natural_fields = ('max_pixels', 'max_frames')

            for inputs_counter, input_in_ddl in enumerate(ddl['inputs']):

                if 'type' not in input_in_ddl:
                    raise IPOLCheckDDLError("Bad DDL inputs section: missing 'type' field in input #{}.".format(inputs_counter))

                if input_in_ddl['type'] not in required_fields:
                    raise IPOLCheckDDLError("Bad DDL inputs section: unknown input type '{}' in input #{}".format(input_in_ddl['type'], inputs_counter))

                for required_field in required_fields[input_in_ddl['type']]:
                    if required_field not in input_in_ddl:
                        raise IPOLCheckDDLError("Bad DDL inputs section: missing '{}' field in input #{}.".format(required_field, inputs_counter))

                for natural_field in natural_fields:
                    if natural_field in input_in_ddl:
                        try:
                            value = evaluate(input_in_ddl[natural_field])
                        except IPOLEvaluateError as ex:
                            raise IPOLCheckDDLError("Bad DDL inputs section: invalid expression '{}' in '{}' field at input #{}.".format(ex, natural_field, inputs_counter))

                        integer = float(value) == int(value)
                        if value <= 0 or not integer:
                            raise IPOLCheckDDLError("Bad DDL inputs section: '{}' field must be a positive integer value in input #{}.".format(natural_field, inputs_counter))

        # The params must be a list
        if 'archive' in ddl and 'params' in ddl['archive'] and not isinstance(ddl['archive']['params'], list):
            raise IPOLCheckDDLError("Bad DDL archive section: expected list of parameters, but found {}".format(type(ddl['archive']['params']).__name__))

    @staticmethod
    def download(url_file, filename):
        """
        Downloads a file from its URL
        """
        urllib.request.urlretrieve(url_file, filename)


    @staticmethod
    def walk_demoextras_files(filename):
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
        compressed_file, content = self.walk_demoextras_files(filename)

        # no absolute file name
        assert not any([os.path.isabs(f) for f in content])
        # no .. in file name
        assert not any([(".." in f) for f in content])

        try:
            compressed_file.extractall(target)
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
                    open_file = open(os.path.join(target, member), 'wb')
                    open_file.write(compressed_file.read(member))
                    open_file.close()

        return content

    def extract_demo_extras(self, demo_id, compressed_file):
        """
        Extract a demo extra...
        input: demo_id and compressed file for the extraction
        return: success or not
        """
        try:
            demo_extras_folder = os.path.join(self.demo_extras_main_dir, str(demo_id))
            if os.path.isdir(demo_extras_folder):
                shutil.rmtree(demo_extras_folder)

            self.mkdir_p(demo_extras_folder)
            self.extract(compressed_file, demo_extras_folder)
        except Exception as ex:
            raise IPOLDemoExtrasError(ex)

    def ensure_extras_updated(self, demo_id):
        """
        Ensure that the demo extras of a given demo are updated with respect to demoinfo information.
        and exists in the core folder.
        """
        try:
            resp = self.post('api/demoinfo/get_demo_extras_info', data={"demo_id": demo_id})
            demoinfo_resp = resp.json()

            if demoinfo_resp['status'] != 'OK':
                raise IPOLDemoExtrasError("Failed to obtain demoExtras info")

            demoextras_compress_dir = os.path.join(self.dl_extras_dir, str(demo_id))
            self.mkdir_p(demoextras_compress_dir)

            demoextras_file = glob.glob(demoextras_compress_dir+"/*")

            #no demoExtras in the shared folder
            if not demoextras_file:
                if 'url' not in demoinfo_resp:
                    return

                # There is a new demoExtras in demoinfo
                demoextras_name = os.path.basename(demoinfo_resp['url'])
                demoextras_file = os.path.join(demoextras_compress_dir, demoextras_name)
                self.download(demoinfo_resp['url'], demoextras_file)
                self.extract_demo_extras(demo_id, demoextras_file)
            else:
                demoextras_file = demoextras_file[0]

                # DemoExtras was removed from demoInfo
                if 'url' not in demoinfo_resp:
                    shutil.rmtree(demoextras_compress_dir)
                    shutil.rmtree(os.path.join(self.demo_extras_main_dir, str(demo_id)))
                    return

                demoinfo_demoextras_date = demoinfo_resp['date']
                demoinfo_demoextras_size = demoinfo_resp['size']
                extras_stat = os.stat(demoextras_file)
                core_demoextras_date = extras_stat.st_ctime
                core_demoextras_size = extras_stat.st_size
                if (core_demoextras_date <= demoinfo_demoextras_date or
                        core_demoextras_size != demoinfo_demoextras_size):
                    # DemoExtras needs an update
                    self.download(demoinfo_resp['url'], demoextras_file)
                    self.extract_demo_extras(demo_id, demoextras_file)

        except Exception as ex:
            error_message = "Error processing the demoExtras of demo #{}: {}".format(demo_id, ex)
            raise IPOLDemoExtrasError(error_message)

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
            keygen.update(str(seed).encode())
        key = keygen.hexdigest().upper()

        # check key
        if not (key and key.isalnum()):
            logger.exception("create_new_execution_key()")
            return None

        return key

    def create_run_dir(self, demo_id, key):
        """
        Create the directory of the execution.
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
        resp = self.post('api/demoinfo/read_demo_metainfo', data=userdata)
        return resp.json()

    def get_demo_editor_list(self, demo_id):
        """
        Get the list of editors of the given demo
        """
        # Get the list of editors of the demo
        userdata = {"demo_id": demo_id}
        resp = self.post('api/demoinfo/demo_get_editors_list', data=userdata)
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
            with open(zip_filename, 'rb') as open_file:
                zip_data = MIMEApplication(open_file.read())
                zip_data.add_header('Content-Disposition', 'attachment', filename="experiment.zip")
            msg.attach(zip_data)

        text_data = MIMEText(text)
        msg.attach(text_data)
        try:
            email = smtplib.SMTP('localhost')
            # Must pass only a list here
            email.sendmail(msg['From'], emails, msg.as_string())
            email.quit()
        except Exception:
            pass

    def send_compilation_error_email(self, demo_id, text):
        """
        Send email to editor when compilation fails
        """
        emails = []

        try:
            demo_state = self.get_demo_metadata(demo_id)["state"].lower()
        except BrokenPipeError:
            demo_state = '<???>'

        # Add Tech and Edit only if this is the production server and
        # the demo has been published

        config_emails = self.read_emails_from_config()
        if not config_emails:
            return

        for editor_mail in self.get_demo_editor_list(demo_id):
            emails.append(editor_mail['email'])

        if self.server_environment == 'production' and demo_state == "published":
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

        print("**** INTERNAL ERROR!\n\n")
        print(text)

        self.send_email(subject, text, emails, config_emails['sender'])

    def read_emails_from_config(self):
        """
        Read the list of emails from the configuration file
        """
        try:
            emails_file_path = os.path.join(self.project_folder,
                                            "ipol_demo", "modules", "config_common", "emails.conf")
            cfg = configparser.ConfigParser()
            if not os.path.isfile(emails_file_path):
                self.error_log("read_emails_from_config",
                               "Can't open {}".format(emails_file_path))
                return {}

            emails = {}
            cfg.read([emails_file_path])
            for section in cfg.sections():
                name = cfg.get(section, "name")
                email = cfg.get(section, "email")
                emails[section] = {"name": name, "email": email}

            return emails
        except Exception as ex:
            self.logger.exception("Can't read emails of journal staff")
            print("Fail reading emails config. Exception:", ex)

    # From http://stackoverflow.com/questions/1855095/how-to-create-a-zip-archive-of-a-directory
    @staticmethod
    def zipdir(path, ziph):
        """ Zip a directory """
        # ziph is zipfile handle
        for root, _, files in os.walk(path):
            for zip_file in files:
                ziph.write(os.path.join(root, zip_file))

    def send_runtime_error_email(self, demo_id, key, message):
        """
        Send email to editor when the execution fails
        """
        try:
            demo_state = self.get_demo_metadata(demo_id)["state"].lower()
        except BrokenPipeError:
            demo_state = '<???>'

        # Add Tech and Edit only if this is the production server and
        # the demo has been published
        emails = []
        config_emails = self.read_emails_from_config()
        if not config_emails:
            return

        for editor in self.get_demo_editor_list(demo_id):
            emails.append(editor['email'])

        if self.server_environment == 'production' and demo_state == "published":
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
        try:
            os.remove(zip_filename)
        except OSError:
            pass

    def send_demorunner_unresponsive_email(self, unresponsive_demorunners):
        """
        Send email to editor when the demorruner is down
        """
        emails = []
        config_emails = self.read_emails_from_config()
        if not config_emails:
            return

        if self.server_environment == 'production':
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

    def send_email_no_demorunner(self, demo_id):
        """
        Send email to tech when there isn't any suitable DR for a published demo
        """
        emails = []
        config_emails = self.read_emails_from_config()
        if not config_emails:
            return

        if self.server_environment != 'production':
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

    def decode_interface_request(self, interface_arguments):
        """
        Decode the arguments and extract the files send by the web interface
        """
        if 'clientData' not in interface_arguments:
            raise IPOLDecodeInterfaceRequestError("clientData not found.")
        clientdata = json.loads(interface_arguments['clientData'])
        origin = clientdata.get('origin', None)
        if origin is not None:
            origin = origin.lower()

        blobs = {}
        if origin == 'upload':
            i = 0
            while 'file_{0}'.format(i) in interface_arguments:
                fname = 'file_{0}'.format(i)
                blobs[fname] = interface_arguments[fname]
                i += 1
        elif origin == 'blobset':
            blobs = clientdata['blobs']
        elif not origin:
            pass
        else:
            raise IPOLDecodeInterfaceRequestError("Wrong origin value from the interface.")

        return clientdata['demo_id'], origin, clientdata.get('params', None), \
                  clientdata.get('crop_info', None), clientdata.get('private_mode', None), blobs

    def read_ddl(self, demo_id):
        """
        This function returns the DDL after checking its syntax.
        """
        userdata = {'demo_id': demo_id}
        demoinfo_resp = self.post('api/demoinfo/get_ddl', data=userdata)
        demoinfo_response = demoinfo_resp.json()

        if demoinfo_response['status'] != 'OK':
            raise IPOLReadDDLError("Demoinfo answered KO.")

        last_demodescription = demoinfo_response['last_demodescription']
        ddl = json.loads(last_demodescription['ddl'], object_pairs_hook=OrderedDict)
        return ddl

    def find_suitable_demorunner(self, general_info):
        """
        This function returns the demorunner that fits with the requirements of a given demo
        and according to the dispatcher policies
        """
        if 'requirements' in general_info:
            requirements = general_info['requirements']
        else:
            requirements = None

        dr_name, dr_server = self.get_demorunner(self.demorunners_workload(), requirements)
        if not dr_name:
            error_message = "No DR satisfies the requirements: {}".format(requirements)
            raise IPOLFindSuitableDR(error_message)
        return dr_name, dr_server

    @staticmethod
    def get_response_content(response):
        '''
        Reads the response.content taking care that both the response or the
        response.content might not be present
        '''
        if not response:
            return "(no response)"
        try:
            if not response.content:
                return "(no response.content)"
        except Exception as ex:
            return "(no response.content. Ex: {})".format(ex)
        return response.content

    def ensure_compilation(self, dr_server, dr_name, demo_id, ddl_build):
        """
        Ensure that the source codes of the demo are all updated and compiled correctly
        """
        build_data = {'demo_id': demo_id, 'ddl_build': json.dumps(ddl_build)}
        dr_response = self.post('api/demorunner/ensure_compilation', data=build_data, host=dr_server)

        # Read the JSON response from the DR
        try:
            demorunner_response = dr_response.json()
        except Exception as ex:
            dr_response_content = Core.get_response_content(dr_response)
            error_message = "**INTERNAL ERROR**. Bad format in the response \
                        from DR server {} in demo #{}. {} - {}".format(dr_server, demo_id, dr_response_content, ex)
            self.logger.exception(error_message)
            raise IPOLEnsureCompilationError(error_message)

        # Check if the compilation was successful
        if demorunner_response['status'] != 'OK':
            print("Compilation error in demo #{}".format(demo_id))
            # Add the compilation failure info into the exception
            buildlog = demorunner_response.get('buildlog', '')
            demorunner_message = demorunner_response['message']
            error_message = "DR={}, {}  - {}".format(dr_name, buildlog, demorunner_message)
            raise IPOLEnsureCompilationError(error_message)

    def prepare_folder_for_execution(self, demo_id, origin, blobs, ddl_inputs, params, crop_info):
        """
        Creates the working directory for a new execution. Then it copies and
        eventually converts the input blobs
        """
        key = self.create_new_execution_key(self.logger)
        if not key:
            raise IPOLKeyError("**INTERNAL ERROR**. Failed to create a valid execution key")
        try:
            work_dir = self.create_run_dir(demo_id, key)
            # save parameters as a params.json file.
            # Used in failure email or as an input for DemoExtras
            try:
                json_filename = os.path.join(work_dir, 'params.json')
                with open(json_filename, 'w') as resfile:
                    resfile.write(json.dumps(params))
            except (OSError, IOError) as ex:
                error_message = "Failed to save {} in demo {}".format(json_filename, demo_id)
                self.logger.exception(error_message)
        except Exception as ex:
            raise IPOLWorkDirError(ex)

        if not origin:
            return work_dir, key, []
        # Copy input blobs
        try:
            self.copy_blobs(work_dir, origin, blobs, ddl_inputs)
            params_conv = {'work_dir': work_dir}
            params_conv['inputs_description'] = json.dumps(ddl_inputs)
            params_conv['crop_info'] = json.dumps(crop_info)
            resp = self.post('api/conversion/convert', data=params_conv)
            resp = resp.json()
            # something went wrong in conversion module, transmit error
            if resp['status'] != 'OK':
                raise IPOLConversionError(resp['error'])

            conversion_info = resp['info']
            messages = []
            for input_key in conversion_info:
                if conversion_info[input_key]['code'] == -1:# Conversion error
                    error = conversion_info[input_key]['error']
                    error_message = "Input #{}. {}".format(input_key, error)
                    raise IPOLConversionError(error_message)
                elif conversion_info[input_key]['code'] == 2:# Conversion forbidden
                    error_message = "Input #{} size too large but conversion forbidden".format(input_key)
                    raise IPOLConversionError(error_message)
                elif conversion_info[input_key]['code'] == 1:# Conversion done
                    modifications_str = ', '.join(conversion_info[input_key]['modifications'])
                    message = "Input #{} has been preprocessed {{{}}}.".format(input_key, modifications_str)
                    messages.append(message)
            return work_dir, key, messages
        except IPOLConversionError as ex:
            raise IPOLPrepareFolderError(str(ex))
        except IPOLInputUploadTooLargeError as ex:
            error_message = "Uploaded input #{} over the maximum allowed weight {} bytes".format(ex.index, ex.max_weight)
            raise IPOLPrepareFolderError(error_message)
        except IPOLMissingRequiredInputError as ex:
            error_message = "Missing required input #{}".format(ex.index)
            raise IPOLPrepareFolderError(error_message)
        except IPOLEvaluateError as ex:
            error_message = "Invalid expression '{}' found in the DDL of demo {}".format(str(ex), demo_id)
            raise IPOLPrepareFolderError(error_message)
        except IPOLCopyBlobsError as ex:
            error_message = "** INTERNAL ERROR **. Error copying blobs of demo {}: {}".format(demo_id, ex)
            self.logger.exception(error_message)
            raise IPOLPrepareFolderError(error_message, error_message)
        except IPOLInputUploadError as ex:
            error_message = "Error uploading input of demo #{} with key={}: {}".format(demo_id, key, ex)
            self.logger.exception(error_message)
            raise IPOLPrepareFolderError(error_message)
        except IPOLProcessInputsError as ex:
            error_message = "** INTERNAL ERROR **. Error processing inputs of demo {}: {}".format(demo_id, ex)
            self.logger.exception(error_message)
            raise IPOLPrepareFolderError(error_message, error_message)
        except (IOError, OSError) as ex:
            error_message = "** INTERNAL ERROR **. I/O error processing inputs"
            log_message = (error_message+". {}: {}").format(type(ex).__name__, str(ex))
            self.logger.exception(log_message)
            raise IPOLPrepareFolderError(error_message, log_message)
        except Exception as ex:
            error_message = "**INTERNAL ERROR**. Blobs operations of demo {} failed".format(demo_id)
            log_message = (error_message+". {}: {}").format(type(ex).__name__, str(ex))
            self.logger.exception(log_message)
            raise IPOLPrepareFolderError(error_message, log_message)

    def execute_experiment(self, dr_server, dr_name, demo_id, key, params, ddl_run, ddl_general, work_dir):
        """
        Execute the experiment in the given DR.
        """
        userdata = {'demo_id': demo_id, 'key': key, 'params': json.dumps(params), 'ddl_run': json.dumps(ddl_run)}

        if 'timeout' in ddl_general:
            userdata['timeout'] = ddl_general['timeout']

        resp = self.post('api/demorunner/exec_and_wait', data=userdata, host=dr_server)
        try:
            demorunner_response = resp.json()
        except Exception as ex:
            resp_content = Core.get_response_content(resp)
            error_message = "**INTERNAL ERROR**. Bad format in the response \
                        from DR server {} in demo #{}. {} - {}".format(dr_server, demo_id, resp_content, ex)
            self.logger.exception(error_message)
            # nginx timeout
            if resp_content and "Time-out" in resp_content:
                raise IPOLExecutionError('timeout')
            #Anything else
            raise IPOLExecutionError(error_message, error_message)

        if demorunner_response['status'] != 'OK':
            print("DR answered KO for demo #{}".format(demo_id))

            try:
                demo_state = self.get_demo_metadata(demo_id)["state"].lower()
            except BrokenPipeError:
                demo_state = '<???>'

            # Message for the web interface
            error_msg = (demorunner_response['algo_info']['error_message']).strip()
            error = demorunner_response.get('error', '').strip()

            # Prepare a message for the website.
            website_message = "DR={}\n{}".format(dr_name, error_msg)
            # In case of a timeout, send a human-oriented message to the web interface
            if error == 'IPOLTimeoutError':
                website_message = "This execution had to be stopped because of TIMEOUT. \
                                      Please reduce the size of your input."

            raise IPOLDemoRunnerResponseError(website_message, demo_state, key, error)


        # Check if the user created a demo_failure.txt file
        # This is part of the mechanism which allows the user to signal that the execution can't go on,
        # but not necessarily because of a crash or a error return code.
        #
        # Indeed, a script in the demo could check, for example, if the aspect ratio of
        # the image is what the algorithm excepts, and prevent the actual execution.
        # The script would create demo_failure.txt with, say, the text "The algorithm only works with
        # images of aspect ratio 16:9".
        try:
            failure_filepath = os.path.join(work_dir, self.demo_failure_file)
            if os.path.exists(failure_filepath):
                with open(failure_filepath, 'r') as open_file:
                    failure_message = "{}".format(open_file.read())
                raise IPOLExecutionError(failure_message)
        except (OSError, IOError) as ex:
            error_message = "Failed to read {} in demo {}".format(failure_filepath, demo_id)
            self.logger.exception(error_message)
            raise IPOLExecutionError(error_message, error_message)

        algo_info_dic = self.read_algo_info(work_dir)
        for name in algo_info_dic:
            demorunner_response['algo_info'][name] = algo_info_dic[name]

        demorunner_response['work_url'] = os.path.join(
            "/api/core/",
            self.shared_folder_rel,
            self.share_run_dir_rel,
            str(demo_id),
            key) + '/'

        return demorunner_response

    @cherrypy.expose
    def run2(self, **kwargs):
        """
        Run a demo. The presentation layer requests the Core to execute a demo.
        """
        demo_id = None
        try:
            demo_id, origin, params, crop_info, private_mode, blobs = self.decode_interface_request(kwargs)

            ddl = self.read_ddl(demo_id)

            # Check the DDL for missing required sections and their format
            self.check_ddl(ddl)

            # Find a demorunner according the requirements of the demo and the dispatcher policy
            dr_name, dr_server = self.find_suitable_demorunner(ddl['general'])

            # Ensure that the demoExtras are updated
            self.ensure_extras_updated(demo_id)

            # Ensure that the source code is updated
            self.ensure_compilation(dr_server, dr_name, demo_id, ddl['build'])

            ddl_inputs = ddl.get('inputs')
            # Create run directory in the shared folder, copy blobs and delegate in the conversion module
            # the conversion of the input data if it is requested and not forbidden
            work_dir, key, prepare_folder_messages = self.prepare_folder_for_execution(demo_id, origin, blobs, ddl_inputs, params, crop_info)

            # Delegate in the the chosen DR the execution of the experiment in the run folder
            demorunner_response = self.execute_experiment(dr_server, dr_name, demo_id, \
                                    key, params, ddl['run'], ddl['general'], work_dir)

            # Archive the experiment, if the 'archive' section exists in the DDL and it is not a private execution
            # Also check if it is an original uploaded data from the user (origin != 'blobset') or is enabled archive_always
            if not private_mode and 'archive' in ddl and (origin != 'blobset' or ddl['archive'].get('archive_always')):
                try:
                    response = send_to_archive(demo_id, work_dir, kwargs, ddl['archive'], demorunner_response, socket.getfqdn())
                    if not response['status'] == 'OK':
                        id_experiment = response.get('id_experiment', None)
                        message = "KO from archive module when archiving an experiment: demo={}, key={}, id={}."
                        self.logger.exception(message.format(demo_id, key, id_experiment))
                except Exception as ex:
                    message = "Error archiving an experiment: demo={}, key={}. Error: {}."
                    self.logger.exception(message.format(demo_id, key, str(ex)))

            # Save the execution, so the users can recover it from the URL
            self.save_execution(demo_id, kwargs, demorunner_response, work_dir)

            messages = []
            messages.extend(prepare_folder_messages)

            return json.dumps(dict(demorunner_response, **{'messages': messages})).encode()
        except (IPOLDecodeInterfaceRequestError, IPOLUploadedInputRejectedError) as ex:
            return json.dumps({'error': str(ex), 'status': 'KO'}).encode()
        except (IPOLDemoExtrasError, IPOLKeyError) as ex:
            error_message = str(ex)
            self.send_internal_error_email(error_message)
            self.logger.exception(error_message)
            return json.dumps({'error': error_message, 'status': 'KO'}).encode()
        except IPOLEnsureCompilationError as ex:
            error_message = " --- Compilation error. --- {}".format(str(ex))
            self.send_compilation_error_email(demo_id, error_message)
            return json.dumps({'error': str(ex), 'status': 'KO'}).encode()
        except IPOLFindSuitableDR as ex:
            try:
                if self.get_demo_metadata(demo_id)['state'].lower() == 'published':
                    self.send_email_no_demorunner(demo_id)
            except BrokenPipeError:
                pass

            error_message = str(ex)
            self.logger.exception(error_message)
            return json.dumps({'error': error_message, 'status': 'KO'}).encode()
        except IPOLWorkDirError as ex:
            error_message = "Could not create work_dir for demo {}".format(demo_id)
            # do not output full path for public
            internal_error_message = (error_message + ". Error: {}").format(str(ex))
            self.logger.exception(internal_error_message)
            return json.dumps({'error': error_message, 'status': 'KO'}).encode()
        except (IPOLReadDDLError) as ex:
            error_message = "{} Demo #{}".format(str(ex), demo_id)
            self.logger.exception(error_message)
            if ex.email_message:
                self.send_internal_error_email(ex.email_message)
            return json.dumps({'error': error_message, 'status': 'KO'}).encode()
        except (IPOLCheckDDLError) as ex:
            error_message = "{} Demo #{}".format(str(ex), demo_id)
            self.send_runtime_error_email(demo_id, "NA", error_message)
            return json.dumps({'error': error_message, 'status': 'KO'}).encode()
        except IPOLPrepareFolderError as ex:
            # Do not log: function prepare_folder_for_execution will decide when to log
            if ex.email_message:
                self.send_internal_error_email(ex.email_message)
            return json.dumps({'error': ex.interface_message, 'status': 'KO'}).encode()
        except IPOLExecutionError as ex:
            # Do not log: function execute_experiment will decide when to log
            if ex.email_message:
                self.send_internal_error_email(ex.email_message)
            return json.dumps({'error': ex.interface_message, 'status': 'KO'}).encode()
        except IPOLEvaluateError as ex:
            error_message = "IPOLEvaluateError '{}' detected in demo {}".format(str(ex), demo_id)
            self.logger.exception(error_message)
            self.send_internal_error_email(error_message)
            return json.dumps({'error': error_message, 'status': 'KO'}).encode()
        except IPOLDemoRunnerResponseError as ex:
            # Send email to the editors
            # (unless it's a timeout in a published demo)
            if not (ex.demo_state == 'published' and ex.error == 'IPOLTimeoutError'):
                self.send_runtime_error_email(demo_id, ex.key, ex.message)
            return json.dumps({'error': ex.message, 'status': 'KO'}).encode()
        except Exception as ex:
            # We should never get here.
            #
            # If we arrive here it means that we missed to catch and
            # take care of some exception type.
            error_message = "**INTERNAL ERROR** in the run function of the Core in demo {}, {}. Received kwargs: {}".format(demo_id, ex, str(kwargs))
            print(traceback.format_exc())
            self.logger.exception(error_message)
            self.send_internal_error_email(error_message)
            return json.dumps({'status': 'KO', 'error': error_message}).encode()

    @staticmethod
    def save_execution(demo_id, request, response, work_dir):
        """
        Save all needed data to recreate an execution.
        """
        clientdata = json.loads(request['clientData'])

        if clientdata.get("origin", "") == "upload":
            # Count how many file entries and remove them
            file_keys = [key for key in request if key.startswith("file_")]
            list(map(request.pop, file_keys))
            clientdata["files"] = len(file_keys)

        execution_json = {}
        execution_json['demo_id'] = demo_id
        execution_json['request'] = clientdata
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
            print(message)
            return json.dumps(res_data).encode()

        try:
            with open(filename, "r") as open_file:
                lines = open_file.read()
        except Exception as ex:
            message = "** INTERNAL ERROR ** while reading execution with key={}: {}".format(key, ex)
            self.logger.exception(message)
            self.send_internal_error_email(message)
            res_data = {'error': message, 'status': 'KO'}
            return json.dumps(res_data).encode()

        return json.dumps({'status': 'OK', 'execution': lines}).encode()


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
            return json.dumps(response).encode()

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
            resp = self.post('api/demoinfo/get_ddl', data={"demo_id": demo_id})
            response = resp.json()

            last_demodescription = response['last_demodescription']
            ddl = json.loads(last_demodescription['ddl'])

            # Check the DDL for missing required sections and their format
            self.check_ddl(ddl)

            ddl_build = ddl['build']
            ddl_inputs = ddl.get('inputs')

        except Exception as ex:
            message = "Failed to obtain the DDL of demo {}".format(demo_id)
            print(message, ex)
            self.logger.exception(message)
            res_data = {'error': message, 'status': 'KO'}
            return json.dumps(res_data).encode()
        # End block to obtain the DDL

        # Create a new execution key
        key = self.create_new_execution_key(self.logger)
        if key is None:
            message = "**INTERNAL ERROR**. Failed to create a valid execution key"
            self.logger.exception(message)
            self.send_internal_error_email(message)
            res_data = {'error': message, 'status': 'KO'}
            return json.dumps(res_data).encode()

        try:
            work_dir = self.create_run_dir(demo_id, key)
        except Exception as ex:
            res_data = {'error': 'Could not create work_dir for demo {}. Error:{}'.format(demo_id, ex),
                        'status': 'KO'}
            self.logger.exception("Could not create work_dir for demo {}".format(demo_id))
            print('Could not create work_dir for demo {}. Error:{}'.format(demo_id, ex))
            return json.dumps(res_data).encode()

        # Copy input blobs
        if input_type != 'noinputs':
            try:
                self.copy_blobs(work_dir, input_type, blobs, ddl_inputs)
                self.process_inputs(work_dir, ddl_inputs, crop_info)
            except IPOLInputUploadTooLargeError as ex:
                message = 'Uploaded input #{} over the maximum allowed weight {} bytes'.format(ex.index, ex.max_weight)
                res_data = {'error': message,
                            'status': 'KO'}
                return json.dumps(res_data).encode()
            except IPOLMissingRequiredInputError as ex:
                message = 'Missing required input #{}'.format(ex.index)
                res_data = {'error': message,
                            'status': 'KO'}
                return json.dumps(res_data).encode()
            except IPOLEvaluateError as ex:
                message = 'Invalid expression "{}" found in the DDL of demo {}'.format(ex, demo_id)
                res_data = {'error': message,
                            'status': 'KO'}
                self.logger.exception(message)
                print(message)
                return json.dumps(res_data).encode()
            except IPOLCopyBlobsError as ex:
                message = 'Error copying blobs of demo {}: {}'.format(demo_id, ex)
                res_data = {'error': message,
                            'status': 'KO'}
                self.logger.exception(message)
                print(message)
                return json.dumps(res_data).encode()
            except IPOLUploadedInputRejectedError as ex:
                res_data = {'error': str(ex), 'status': 'KO'}
                return json.dumps(res_data).encode()
            except IPOLInputUploadError as ex:
                message = 'Error uploading input of demo {}: {}'.format(demo_id, ex)
                res_data = {'error': message,
                            'status': 'KO'}
                self.logger.exception(message)
                print(message)
                return json.dumps(res_data).encode()
            except IPOLProcessInputsError as ex:
                message = 'Error processing inputs of demo {}: {}'.format(demo_id, ex)
                res_data = {'error': message,
                            'status': 'KO'}
                self.logger.exception(message)
                print(message)
                return json.dumps(res_data).encode()
            except IOError as ex:
                message = 'I/O error processing inputs - {}'.format(ex)
                res_data = {'error': message,
                            'status': 'KO'}
                self.logger.exception(message)
                print(message)
                return json.dumps(res_data).encode()
            except Exception as ex:
                # ToDo: send email
                message = '**INTERNAL ERROR**. Blobs operations of demo {} failed - {}'.format(demo_id, ex)
                self.logger.exception(message)
                self.send_internal_error_email(message)
                res_data = {'error': message,
                            'status': 'KO'}
                return json.dumps(res_data).encode()

        try:
            # Find a DR with satisfies the requirements
            requirements = ddl['general']['requirements'] \
                if 'requirements' in ddl['general'] else None

            dr_name, dr_server = self.get_demorunner(
                self.demorunners_workload(), requirements)
            if dr_name is None:
                response = {'status': 'KO', 'error': 'No DR satisfies the requirements: {}'.format(requirements)}
                try:
                    if self.get_demo_metadata(demo_id)["state"].lower() == "published":
                        self.send_email_no_demorunner(demo_id)
                except BrokenPipeError:
                    pass

                return json.dumps(response).encode()

            # Ensure that the demoExtras are updated
            try:
                self.ensure_extras_updated(demo_id)
            except IPOLDemoExtrasError as ex:
                message = 'Error processing the demoExtras of demo {}: {}'.format(demo_id, ex)
                self.logger.exception(message)
                print(message)
                response = {'status': 'KO', 'error': message}
                return json.dumps(response).encode()

            # Ensure that the source code is updated
            userdata = {"demo_id": demo_id, "ddl_build": json.dumps(ddl_build)}
            resp = self.post('api/demorunner/ensure_compilation', data=userdata, host=dr_server)
            demorunner_response = resp.json()
            status = demorunner_response['status']
            if status != 'OK':
                print("COMPILATION FAILURE in demo = ", demo_id)

                # Send compilation message to the editors
                text = "DR={}, {} - {}".format(dr_name, demorunner_response.get("buildlog", "").encode('utf8'),
                                               demorunner_response["message"].encode('utf8'))

                self.send_compilation_error_email(demo_id, text)

                # Message for the web interface
                response = {"error": " --- Compilation error. --- {}".format(text), "status": "KO"}
                return json.dumps(response).encode()

            # save parameters as a params.json file
            try:
                work_dir = os.path.join(self.share_run_dir_abs, str(demo_id), key)
                json_filename = os.path.join(work_dir, "params.json")
                with open(json_filename, "w") as resfile:
                    resfile.write(params)
            except (OSError, IOError) as ex:
                message = "Failed to save {} in demo {}".format(json_filename, demo_id)
                self.logger.exception(message)
                print(message)
                response = {'status': 'KO', 'error': message}
                return json.dumps(response).encode()

            userdata = {"demo_id": demo_id, "key": key, "params": params}

            userdata['ddl_run'] = json.dumps(ddl['run'])

            if 'timeout' in ddl['general']:
                userdata['timeout'] = ddl['general']['timeout']
            resp = self.post('api/demorunner/exec_and_wait', data=userdata, host=dr_server)
            try:
                demorunner_response = resp.json()
            except Exception as ex:
                message = "**INTERNAL ERROR**. Bad format in the response from DR server {} in demo {}. {}".format(dr_server, demo_id, ex)
                self.logger.exception(message)
                self.send_internal_error_email(message)
                core_response = {"status": "KO", "error": "{}".format(message)}
                return json.dumps(core_response).encode()

            if demorunner_response['status'] != 'OK':
                print("DR answered KO for demo #{}".format(demo_id))
                try:
                    demo_state = self.get_demo_metadata(demo_id)["state"].lower()
                except BrokenPipeError:
                    demo_state = "<???>"

                # Message for the web interface
                error_msg = (demorunner_response['algo_info']['error_message']).encode('utf-8').strip()
                error = demorunner_response.get('error', '').strip()

                # Prepare a message for the website.
                # In case of a timeout, let it be human oriented.
                if error == 'IPOLTimeoutError':
                    website_message = "This execution had to be stopped because of TIMEOUT. Please reduce the size of your input."
                else:
                    website_message = "DR={}, {}".format(dr_name, error_msg)

                response = {"error": website_message,
                            "status": "KO"}

                # Send email to the editors
                # (unless it's a timeout in a published demo)
                if not (demo_state == 'published' and error == 'IPOLTimeoutError'):
                    self.send_runtime_error_email(demo_id, key, website_message)
                return json.dumps(response).encode()

            # Check if the user created a demo_failure.txt file
            # This is part of the mechanism which allows the user to signal that
            # the execution can't go on, but not necessarily because of a crash or a error return code.
            #
            # Indeed, a script in the demo could check, for example, if the aspect ratio of
            # the image is what the algorithm excepts, and prevent the actual execution.
            # The script would create demo_failure.txt with, say, the text "The algorithm only works with
            # images of aspect ratio 16:9".
            try:
                failure_filepath = os.path.join(work_dir, self.demo_failure_file)
                if os.path.exists(failure_filepath):
                    with open(failure_filepath, 'r') as f:
                        failure_message = "A demo failure occurred while executing: \n {}".format(f.read())
                    return failure_message

            except (OSError, IOError) as ex:
                error_message = "Failed to read {} in demo {}".format(failure_filepath, demo_id)
                self.logger.exception(error_message)
                return error_message

            demorunner_response['work_url'] = os.path.join(
                "/api/core/",
                self.shared_folder_rel,
                self.share_run_dir_rel,
                str(demo_id),
                key) + '/'

            # Archive the experiment, if the 'archive' section
            # exists in the DDL
            if (original_exp == 'true' or input_type == 'noinputs') and 'archive' in ddl:
                try:
                    send_to_archive(demo_id, work_dir, None, ddl['archive'], demorunner_response, socket.getfqdn())
                except Exception as ex:
                    message = "Error archiving the experiment with key={} of demo {}, {}".format(key, demo_id, ex)
                    self.logger.exception(message)
                    self.send_internal_error_email(message)

        except Exception as ex:
            message = "**INTERNAL ERROR** in the run function of the Core in demo {}, {}".format(demo_id, ex)
            self.logger.exception(message)
            self.send_internal_error_email(message)
            core_response = {"status": "KO", "error": "{}".format(message)}
            return json.dumps(core_response).encode()

        dic = self.read_algo_info(work_dir)
        for name in dic:
            demorunner_response["algo_info"][name] = dic[name]

        return json.dumps(demorunner_response).encode()

    def read_algo_info(self, work_dir):
        """
        Read the file algo_info.txt to pass user variables to the
        web interface.
        """
        file_name = os.path.join(work_dir, "algo_info.txt")

        if not os.path.isfile(file_name):
            return {}  # The algorithm didn't create the file

        dic = {}
        open_file = open(file_name, "r")
        lines = open_file.read().splitlines()
        #
        for line in lines:
            # Read with format A = B, where B can contain the '=' sign
            if len(line.split("=", 1)) < 2 or \
                            line.split("=", 1)[0].strip() == "":
                print("incorrect format in algo_info.txt, in line {}".format(line))
                self.error_log("run", "incorrect format in algo_info.txt, at line {}".format(line))
                continue

            # Add name and assigned value to the output dict
            name, value = line.split("=", 1)
            name = name.strip()
            dic[name] = value

        open_file.close()
        return dic

    def get_demorunner(self, demorunners_workload, requirements=None):
        """
        Return an active DR which meets the requirements
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
                dispatcher_response = self.post('api/dispatcher/get_demorunner', data=demorunner_data)
            except requests.ConnectionError:
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
            try:
                demorunner_response = self.post('api/demorunner/ping', host=dr_server)
            except Exception:
                demorunner_response = None

            if demorunner_response and demorunner_response.ok:
                if unresponsive_demorunners:
                    self.send_demorunner_unresponsive_email(unresponsive_demorunners)
                return dr_name, dr_server
            else:
                self.error_log("get_demorunner",
                               "Module {} unresponsive".format(dr_name))
                print("Module {} unresponsive".format(dr_name))
                unresponsive_demorunners.add(dr_name)

            # At half of the tries wait 5 secs and try again
            if i == len(self.demorunners) - 1:
                time.sleep(5)

        # If there is no demorrunner active send an email with all the unresponsive DRs
        self.send_demorunner_unresponsive_email(unresponsive_demorunners)
        raise Exception("No DR available after many tries")  # [Miguel] [ToDo] Use an specific exception, not the too-wide Exception

    def post(self, api_url, data=None, host=None):
        """
        Make a POST request via the IPOL API
        """
        try:
            if host is None:
                host = socket.getfqdn()
            url = 'http://{0}/{1}'.format(host, api_url)
            return requests.post(url, data=data)
        except Exception as ex:
            error_message = "Failure in the post function of the CORE using: URL={}, exception={}".format(url, ex)
            print(error_message)
            self.logger.exception(error_message)

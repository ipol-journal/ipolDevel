"""
IPOL Core module
"""
import configparser
import glob
import hashlib
import io
import json
import logging
import mimetypes
import os
import re
import shutil
import smtplib
import socket
import tarfile
import traceback
import urllib.error
import urllib.parse
import urllib.request
import zipfile
from collections import OrderedDict
from dataclasses import dataclass
from datetime import datetime
from email.mime.application import MIMEApplication
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from random import random
from typing import Any

import cherrypy
import magic
import requests
from archive import send_to_archive
from conversion import conversion
from demoinfo import demoinfo
from dispatcher import dispatcher
from errors import (
    IPOLCheckDDLError,
    IPOLConversionError,
    IPOLCopyBlobsError,
    IPOLDecodeInterfaceRequestError,
    IPOLDemoExtrasError,
    IPOLDemoRunnerResponseError,
    IPOLEnsureCompilationError,
    IPOLExecutionError,
    IPOLExtractError,
    IPOLFindSuitableDR,
    IPOLInputUploadError,
    IPOLInputUploadTooLargeError,
    IPOLKeyError,
    IPOLMissingRequiredInputError,
    IPOLPrepareFolderError,
    IPOLProcessInputsError,
    IPOLReadDDLError,
    IPOLUploadedInputRejectedError,
    IPOLWorkDirError,
)
from ipolutils.evaluator.evaluator import IPOLEvaluateError, evaluate
from ipolutils.read_text_file import read_commented_text_file
from result import Err, Ok


def authenticate(func):
    """
    Wrapper to authenticate before using an exposed function
    """

    def authenticate_and_call(*args, **kwargs):
        """
        Invokes the wrapped function if authenticated
        """
        if "X-Real-IP" in cherrypy.request.headers and is_authorized_ip(
            cherrypy.request.headers["X-Real-IP"]
        ):
            return func(*args, **kwargs)
        error = {"status": "KO", "error": "Authentication Failed"}
        return json.dumps(error).encode()

    def is_authorized_ip(ip):
        """
        Validates the given IP
        """
        core = Core.get_instance()
        patterns = []
        # Creates the patterns  with regular expressions
        for authorized_pattern in core.authorized_patterns:
            patterns.append(
                re.compile(
                    authorized_pattern.replace(".", "\\.").replace("*", "[0-9a-zA-Z]+")
                )
            )
        # Compare the IP with the patterns
        for pattern in patterns:
            if pattern.match(ip) is not None:
                return True
        return False

    return authenticate_and_call


@dataclass
class DispatcherAPI:
    dispatcher: dispatcher.Dispatcher

    @cherrypy.expose
    def get_demorunners_stats(self):
        """
        Get workload of all DRs.
        """
        stats = self.dispatcher.get_demorunners_stats()
        return json.dumps({"status": "OK", "demorunners": stats}).encode()


@dataclass
class ConversionAPI:
    converter: conversion.Converter

    @cherrypy.expose
    def convert_tiff_to_png(self, img):
        """
        Converts the input TIFF to PNG.
        This is used by the web interface for visualization purposes
        """
        data = self.converter.convert_tiff_to_png(img)
        return json.dumps(data, indent=4).encode()


@dataclass
class DemoInfoAPI:
    demoinfo: demoinfo.DemoInfo

    @cherrypy.expose
    @authenticate
    def delete_demoextras(self, demo_id):
        result = self.demoinfo.delete_demoextras(demo_id)

        if result.is_ok():
            data = {"status": "OK"}
        else:
            data = {"status": "KO", "error": result.value}
        return json.dumps(data).encode()

    @cherrypy.expose
    @authenticate
    def add_demoextras(self, demo_id, demoextras, demoextras_name):
        demo_id = int(demo_id)
        demoextras = demoextras.file.read()
        result = self.demoinfo.add_demoextras(demo_id, demoextras, demoextras_name)
        if isinstance(result, Ok):
            data = {"status": "OK"}
        else:
            data = {"status": "KO", "error": result.value}
        return json.dumps(data).encode()

    @cherrypy.expose
    def get_demo_extras_info(self, demo_id):
        demo_id = int(demo_id)
        result = self.demoinfo.get_demo_extras_info(demo_id)
        if isinstance(result, Ok):
            data = {"status": "OK"}
            if result.value is not None:
                data.update(**result.value)
        else:
            data = {"status": "KO", "error": result.value}
        return json.dumps(data).encode()

    @cherrypy.expose
    def demo_list(self):
        result = self.demoinfo.demo_list()
        if isinstance(result, Ok):
            data = {
                "demo_list": result.value,
                "status": "OK",
            }
        else:
            data = {"status": "KO", "error": result.value}
        return json.dumps(data).encode()

    @cherrypy.expose
    def demo_list_by_editorid(self, editorid):
        editorid = int(editorid)
        result = self.demoinfo.demo_list_by_editorid(editorid)
        if isinstance(result, Ok):
            data = {
                "demo_list": result.value,
                "status": "OK",
            }
        else:
            data = {"status": "KO", "error": result.value}
        return json.dumps(data).encode()

    @cherrypy.expose
    def demo_list_pagination_and_filter(self, num_elements_page, page, qfilter=None):
        num_elements_page = int(num_elements_page)
        page = int(page)
        result = self.demoinfo.demo_list_pagination_and_filter(
            num_elements_page, page, qfilter
        )
        if isinstance(result, Ok):
            data = {"status": "OK"}
            data.update(**result.value)
        else:
            data = {"status": "KO", "error": result.value}
        return json.dumps(data).encode()

    @cherrypy.expose
    @authenticate
    def demo_get_editors_list(self, demo_id):
        demo_id = int(demo_id)
        result = self.demoinfo.demo_get_editors_list(demo_id)
        if isinstance(result, Ok):
            data = {
                "editor_list": result.value,
                "status": "OK",
            }
        else:
            data = {"status": "KO", "error": result.value}
        return json.dumps(data).encode()

    @cherrypy.expose
    @authenticate
    def demo_get_available_editors_list(self, demo_id):
        demo_id = int(demo_id)
        result = self.demoinfo.demo_get_available_editors_list(demo_id)
        if isinstance(result, Ok):
            data = {
                "editor_list": result.value,
                "status": "OK",
            }
        else:
            data = {"status": "KO", "error": result.value}
        return json.dumps(data).encode()

    @cherrypy.expose
    def read_demo_metainfo(self, demoid):
        demoid = int(demoid)
        result = self.demoinfo.read_demo_metainfo(demoid)
        if isinstance(result, Ok):
            data = {"status": "OK"}
            data.update(**result.value)
        else:
            data = {"status": "KO", "error": result.value}
        return json.dumps(data).encode()

    @cherrypy.expose
    @cherrypy.tools.allow(methods=["POST"])  # allow only post
    @authenticate
    def add_demo(self, demo_id, title, state, ddl=None):
        demo_id = int(demo_id)
        result = self.demoinfo.add_demo(demo_id, title, state, ddl)
        if isinstance(result, Ok):
            data = {"status": "OK", "demo_id": result.value}
        else:
            data = {"status": "KO", "error": result.value}
        return json.dumps(data).encode()

    @cherrypy.expose
    @cherrypy.tools.allow(methods=["POST"])  # allow only post
    @authenticate
    def update_demo(self, demo: str, old_editor_demoid: int):
        old_editor_demoid = int(old_editor_demoid)
        demo_dict = json.loads(demo)
        assert "demo_id" in demo_dict
        assert "title" in demo_dict
        assert "state" in demo_dict
        result = self.demoinfo.update_demo(demo_dict, old_editor_demoid)
        if isinstance(result, Ok):
            data = {"status": "OK"}
        else:
            data = {"status": "KO", "error": result.value}
        return json.dumps(data).encode()

    @cherrypy.expose
    @authenticate
    def editor_list(self):
        result = self.demoinfo.editor_list()
        if isinstance(result, Ok):
            data = {"status": "OK", "editor_list": result.value}
        else:
            data = {"status": "KO", "error": result.value}
        return json.dumps(data).encode()

    @cherrypy.expose
    @authenticate
    def get_editor(self, email):
        result = self.demoinfo.get_editor(email)
        if isinstance(result, Ok):
            data: dict[str, Any] = {"status": "OK"}
            if editor := result.value:
                data["editor"] = editor
        else:
            data = {"status": "KO", "error": result.value}
        return json.dumps(data).encode()

    @cherrypy.expose
    @cherrypy.tools.allow(methods=["POST"])
    @authenticate
    def update_editor_email(self, new_email, old_email, name):
        result = self.demoinfo.update_editor_email(new_email, old_email, name)
        if isinstance(result, Ok):
            data = {"status": "OK"}
            if message := result.value:
                data["message"] = message
        else:
            data = {"status": "KO", "error": result.value}
        return json.dumps(data).encode()

    @cherrypy.expose
    @cherrypy.tools.allow(methods=["POST"])  # allow only post
    @authenticate
    def add_editor(self, name, mail):
        result = self.demoinfo.add_editor(name, mail)
        if isinstance(result, Ok):
            data = {"status": "OK"}
        else:
            data = {"status": "KO", "error": result.value}
        return json.dumps(data).encode()

    @cherrypy.expose
    @cherrypy.tools.allow(methods=["POST"])  # allow only post
    @authenticate
    def add_editor_to_demo(self, demo_id, editor_id):
        demo_id = int(demo_id)
        editor_id = int(editor_id)
        result = self.demoinfo.add_editor_to_demo(demo_id, editor_id)
        if isinstance(result, Ok):
            data = {"status": "OK"}
        else:
            data = {"status": "KO", "error": result.value}
        return json.dumps(data).encode()

    @cherrypy.expose
    @cherrypy.tools.allow(methods=["POST"])  # allow only post
    @authenticate
    def remove_editor_from_demo(self, demo_id, editor_id):
        demo_id = int(demo_id)
        editor_id = int(editor_id)
        result = self.demoinfo.remove_editor_from_demo(demo_id, editor_id)
        if isinstance(result, Ok):
            data = {"status": "OK"}
        else:
            data = {"status": "KO", "error": result.value}
        return json.dumps(data).encode()

    @cherrypy.expose
    @cherrypy.tools.allow(methods=["POST"])  # allow only post
    @authenticate
    def remove_editor(self, editor_id):
        editor_id = int(editor_id)
        result = self.demoinfo.remove_editor(editor_id)
        if isinstance(result, Ok):
            data = {"status": "OK"}
        else:
            data = {"status": "KO", "error": result.value}
        return json.dumps(data).encode()

    @cherrypy.expose
    @authenticate
    def get_ddl_history(self, demo_id):
        demo_id = int(demo_id)
        result = self.demoinfo.get_ddl_history(demo_id)
        if isinstance(result, Ok):
            data = {"status": "OK", "ddl_history": result.value}
        else:
            data = {"status": "KO", "error": result.value}
        return json.dumps(data).encode()

    @cherrypy.expose
    @authenticate
    def get_ddl(self, demo_id):
        demo_id = int(demo_id)
        result = self.demoinfo.get_ddl(demo_id)
        if isinstance(result, Ok):
            data = {
                "status": "OK",
                "last_demodescription": {
                    "ddl": result.value,
                },
            }
        else:
            data = {"status": "KO", "error": result.value}
        return json.dumps(data).encode()

    @cherrypy.expose
    @cherrypy.tools.allow(methods=["POST"])  # allow only post
    @authenticate
    def save_ddl(self, demoid):
        demoid = int(demoid)
        cl = cherrypy.request.headers["Content-Length"]
        ddl = cherrypy.request.body.read(int(cl)).decode()
        result = self.demoinfo.save_ddl(demoid, ddl)
        if isinstance(result, Ok):
            data = {"status": "OK"}
        else:
            data = {"status": "KO", "error": result.value}
        return json.dumps(data).encode()

    @cherrypy.expose
    def get_interface_ddl(self, demo_id, sections=None):
        demo_id = int(demo_id)
        result = self.demoinfo.get_interface_ddl(demo_id, sections)
        if isinstance(result, Ok):
            data = {
                "status": "OK",
                "last_demodescription": {
                    "ddl": result.value,
                },
            }
        else:
            data = {"status": "KO", "error": result.value}
        return json.dumps(data).encode()

    @cherrypy.expose
    @authenticate
    def get_ssh_keys(self, demo_id):
        demo_id = int(demo_id)
        result = self.demoinfo.get_ssh_keys(demo_id)
        if isinstance(result, Ok):
            pubkey, privkey = result.value
            data = {
                "status": "OK",
                "pubkey": pubkey,
                "privkey": privkey,
            }
        else:
            data = {"status": "KO", "error": result.value}
        return json.dumps(data).encode()

    @cherrypy.expose
    @authenticate
    def reset_ssh_keys(self, demo_id):
        demo_id = int(demo_id)
        result = self.demoinfo.reset_ssh_keys(demo_id)
        if isinstance(result, Ok):
            data = {"status": "OK"}
        else:
            data = {"status": "KO", "error": result.value}
        return json.dumps(data).encode()

    @cherrypy.expose
    def stats(self):
        result = self.demoinfo.stats()
        if isinstance(result, Ok):
            data = {"status": "OK"}
            data.update(**result.value)
        else:
            data = {"status": "KO", "error": result.value}
        return json.dumps(data).encode()


class Core:
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

    def __init__(self):
        """
        Constructor
        """
        ### Read the configuration file
        self.server_environment = cherrypy.config.get("env")

        self.logger = init_logging()
        self.project_folder = cherrypy.config.get("project_folder")
        self.blobs_folder = cherrypy.config.get("blobs_folder")

        self.shared_folder_rel = cherrypy.config.get("shared_folder")
        self.shared_folder_abs = os.path.join(
            self.project_folder, self.shared_folder_rel
        )
        self.demo_extras_main_dir = os.path.join(
            self.shared_folder_abs, cherrypy.config.get("demoExtrasDir")
        )
        self.dl_extras_dir = os.path.join(
            self.shared_folder_abs, cherrypy.config.get("dl_extras_dir")
        )
        self.share_run_dir_rel = cherrypy.config.get("running.dir")
        self.share_run_dir_abs = os.path.join(
            self.shared_folder_abs, self.share_run_dir_rel
        )

        # Security: authorized IPs
        self.authorized_patterns_file = cherrypy.config.get("authorized_patterns_file")
        self.authorized_patterns = self.read_authorized_patterns()

        # create needed directories
        os.makedirs(self.share_run_dir_abs, exist_ok=True)
        os.makedirs(self.shared_folder_abs, exist_ok=True)
        os.makedirs(self.dl_extras_dir, exist_ok=True)
        os.makedirs(self.demo_extras_main_dir, exist_ok=True)

        base_url = os.environ["IPOL_URL"]
        demorunners_path = cherrypy.config["demorunners_file"]
        policy = cherrypy.config["dispatcher_policy"]
        self.dispatcher = dispatcher.Dispatcher(
            workload_provider=dispatcher.APIWorkloadProvider(base_url),
            ping_provider=dispatcher.APIPingProvider(base_url),
            demorunners=dispatcher.parse_demorunners(demorunners_path),
            policy=dispatcher.make_policy(policy),
        )

        self.converter = conversion.Converter()

        demoinfo_db = cherrypy.config["demoinfo_db"]
        demoinfo_dl_extras_dir = cherrypy.config["demoinfo_dl_extras_dir"]
        self.demoinfo = demoinfo.DemoInfo(
            dl_extras_dir=demoinfo_dl_extras_dir,
            database_path=demoinfo_db,
            base_url=base_url,
        )

    def get_dispatcher_api(self) -> DispatcherAPI:
        return DispatcherAPI(self.dispatcher)

    def get_conversion_api(self) -> ConversionAPI:
        return ConversionAPI(self.converter)

    def get_demoinfo_api(self) -> DemoInfoAPI:
        return DemoInfoAPI(self.demoinfo)

    def read_authorized_patterns(self):
        """
        Read from the IPs conf file
        """
        # Check if the config file exists
        if not os.path.isfile(self.authorized_patterns_file):
            self.logger.error(
                "read_authorized_patterns: Can't open {}".format(
                    self.authorized_patterns_file
                )
            )
            return []

        # Read config file
        try:
            cfg = configparser.ConfigParser()
            cfg.read([self.authorized_patterns_file])
            patterns = []
            for item in cfg.items("Patterns"):
                patterns.append(item[1])
            return patterns
        except configparser.Error:
            self.logger.exception(
                "Bad format in {}".format(self.authorized_patterns_file)
            )
            return []

    @cherrypy.expose
    def index(self, code_starts=None):
        """
        Index page
        """
        result = self.demoinfo.demo_list()

        cherrypy.response.headers["Content-Type"] = "text/html"
        if result.is_err():
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

        demo_list = result.value

        # Get all publication states
        demos_by_state = OrderedDict()
        for demo in demo_list:
            editorsdemoid = demo["editorsdemoid"]

            # If the user specified a demo code prefix, then ignore the
            # demos which don't start with that prefix.
            if code_starts and not str(editorsdemoid).startswith(code_starts):
                continue

            publication_state = demo["state"]
            if publication_state not in demos_by_state:
                demos_by_state[publication_state] = []

            demos_by_state[publication_state].append(
                {"editorsdemoid": editorsdemoid, "title": demo["title"]}
            )

        demos_string = ""

        # Show demos according to their state
        for publication_state in demos_by_state:
            # Sort demo list by demo ID
            demos_by_state[publication_state] = sorted(
                demos_by_state[publication_state],
                key=lambda d: (d["editorsdemoid"]),
                reverse=True,
            )

            if demos_by_state[publication_state]:
                demos_string += "<h2 id='{0}'>{0}</h2>".format(publication_state)
            #
            for demo_data in demos_by_state[publication_state]:
                editorsdemoid = str(demo_data["editorsdemoid"])

                demos_string += "Demo #{0}{1}: <a href='/demo/clientApp/demo.html?id={0}' target='_blank'>{2}</a><br>".format(
                    editorsdemoid,
                    " (private)" if editorsdemoid.startswith("33333") else "",
                    demo_data["title"],
                )

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
                 """.format(
            demos_string
        )

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

    # --------------------------------------------------------------------------
    #           END BLOCK OF INPUT TOOLS
    # --------------------------------------------------------------------------

    @staticmethod
    def input_upload(work_dir, blobs, inputs_desc):
        """
        use the uploaded input files
        file_0, file_1, ... are the input files
        ddl_input is the input section of the demo description
        """
        nb_inputs = len(inputs_desc)

        inputs_names = {}

        for i in range(nb_inputs):
            file_up = blobs.pop("file_%i" % i, None)

            if file_up is None or file_up.filename == "":
                if (
                    "required" not in list(inputs_desc[i].keys())
                    or inputs_desc[i]["required"]
                ):
                    # missing file
                    raise IPOLMissingRequiredInputError(i)
                # skip this input
                continue

            inputs_names[i] = {"origin": file_up.filename}

            mime = magic.Magic(mime=True)
            file_up.file.seek(0)
            mime_uploaded_blob = mime.from_buffer(file_up.file.read())
            type_of_uploaded_blob, _ = mime_uploaded_blob.split("/")

            # Reject the uploaded file it it doesn't match the type in the DDL
            if inputs_desc[i]["type"] != type_of_uploaded_blob and (
                inputs_desc[i]["type"] not in ["data", "map"]
            ):
                message = (
                    "The DDL type ({}) doesn't match the uploaded blob ({})".format(
                        inputs_desc[i]["type"], type_of_uploaded_blob
                    )
                )
                raise IPOLUploadedInputRejectedError(message)

            # Reject the uploaded file it's not 'data' and it can't be guessed
            ext_of_uploaded_blob = mimetypes.guess_extension(mime_uploaded_blob)
            if inputs_desc[i]["type"] != "data" and ext_of_uploaded_blob is None:
                error_message = "The type of the uploaded file could not be recognized and it has been rejected"
                raise IPOLUploadedInputRejectedError(error_message)

            # If it's data, we just put the extension given at the DDL
            if inputs_desc[i]["type"] == "data":
                ext_of_uploaded_blob = inputs_desc[i]["ext"]

            # Here we save the file with the final extension, regardless
            # the actual content.
            # Later Core will eventually ask the system to convert the
            # data (for example, encode in PNG).
            file_save = os.path.join(work_dir, "input_%i" % i + ext_of_uploaded_blob)

            # Read and save the file
            max_size = None
            if "max_weight" in inputs_desc[i]:
                max_size = evaluate(inputs_desc[i]["max_weight"])
            Core.write_data_to_file(
                file_up, file_save, max_size=max_size, input_index=i
            )

        return inputs_names

    def copy_blobset_from_physical_location(self, demo_id, work_dir, blobset_id):
        """
        use the selected available input images
        input parameters:
        returns:
        """
        try:
            demo_blobs, _ = self.post(
                "api/blobs/get_blobs", "post", data={"demo_id": demo_id}
            )
            demo_blobs = demo_blobs.json()
        except json.JSONDecodeError as e:
            self.logger.exception(
                f"Blobs get_blobs didn't return valid json at Core's copy_blobset_from_physical_location. {e}"
            )
            raise IPOLCopyBlobsError("Couldn't reach blobs")

        if not demo_blobs["sets"] or demo_blobs["status"] == "KO":
            self.logger.exception(
                "Blobs get_blobs returned KO at Core's copy_blobset_from_physical_location"
            )
            raise IPOLCopyBlobsError("Couldn't reach blobs")

        try:
            blobset = demo_blobs["sets"][blobset_id]
        except IndexError:
            raise IPOLCopyBlobsError("Blobset {} doesn't exist".format(blobset_id))

        inputs_names = {}

        for input_idx, blob in blobset["blobs"].items():
            blob_path = blob["blob"].split("/api/blobs/")[1]
            try:
                extension = os.path.splitext(blob_path)[1]
                final_path = os.path.join(
                    work_dir, "input_{0}{1}".format(input_idx, extension)
                )
                shutil.copy(os.path.join(self.blobs_folder, blob_path), final_path)
            except Exception as ex:
                self.logger.exception(
                    "Error copying blob from {} to {}".format(blob_path, final_path)
                )
                print(
                    "Couldn't copy  blobs from {} to {}. Error: {}".format(
                        blob_path, final_path, ex
                    )
                )

            inputs_names[int(input_idx)] = {"origin": os.path.basename(blob["blob"])}

        return inputs_names

    def copy_blobs(self, work_dir, demo_id, input_type, blobs, blobset_id, ddl_inputs):
        """
        Copy the input blobs to the execution folder.
        """
        if input_type == "upload":
            inputs_names = self.input_upload(work_dir, blobs, ddl_inputs)
        elif input_type == "blobset":
            if blobset_id is None:
                raise IPOLCopyBlobsError("blobset_id absent")
            inputs_names = self.copy_blobset_from_physical_location(
                demo_id, work_dir, blobset_id
            )

        for i, desc in enumerate(ddl_inputs):
            ext = desc.get("ext", "")
            filename = f"input_{i}{ext}"
            if i in inputs_names:
                inputs_names[i]["converted"] = filename

        return inputs_names

    @staticmethod
    def copy_inpainting_data(work_dir, blobs, ddl_inputs):
        """
        Copy the existing input inpainting data to the execution folder.
        """
        for i, ddl_input in enumerate(ddl_inputs):
            if f"inpainting_data_{str(i)}" not in blobs:
                continue
            blob_data = blobs[f"inpainting_data_{str(i)}"]
            if ddl_input["control"] == "mask":
                filepath = os.path.join(work_dir, f"mask_{i}.png")
                Core.write_data_to_file(blob_data, filepath)
            else:
                filepath = os.path.join(work_dir, f"inpainting_data_{i}.txt")
                with open(filepath, "w") as file:
                    for point in json.loads(blob_data):
                        file.write("%s\n" % point)

    @staticmethod
    def write_data_to_file(blob_data, filepath, max_size=None, input_index=None):
        """
        Write input data to a given file destination.
        """
        size = 0
        with open(filepath, "wb") as file:
            blob_data.file.seek(0)
            while True:
                data = blob_data.file.read(128)
                if not data:
                    break
                size += len(data)
                if max_size is not None and size > max_size:
                    # file too heavy
                    raise IPOLInputUploadTooLargeError(input_index, max_size)
                file.write(data)

    @staticmethod
    def check_ddl(ddl):
        """
        Check for required DDL fields and their types.
        """
        # Check that all mandatory sections are present
        sections = ("general", "build", "run", "results")
        for section in sections:
            if section not in ddl:
                raise IPOLCheckDDLError(
                    "Bad DDL syntax: missing '{}' section.".format(section)
                )

        # Empty run
        if not ddl["run"] or ddl["run"].isspace():
            raise IPOLCheckDDLError("Bad DDL run section: run is empty.")

        if "inputs" in ddl:
            # Inputs must be a list.
            if not isinstance(ddl["inputs"], list):
                raise IPOLCheckDDLError("Bad DDL inputs section: expected list.")

            required_fields = {
                "video": ("max_pixels", "max_frames"),
                "image": ("max_pixels", "ext", "dtype"),
                "map": ("ext",),
                "data": ("ext",),
            }

            # Integer and positive values
            natural_fields = ("max_pixels", "max_frames")

            # If it's a map demo, it can only have one input
            is_map_demo = "map" in [inp["type"] for inp in ddl["inputs"]]
            if is_map_demo and len(ddl["inputs"]) != 1:
                raise IPOLCheckDDLError(
                    f"A demo containing a map must have a single input but the DDL contains {len(ddl['inputs'])} inputs."
                )

            for inputs_counter, input_in_ddl in enumerate(ddl["inputs"]):
                if "type" not in input_in_ddl:
                    raise IPOLCheckDDLError(
                        "Bad DDL inputs section: missing 'type' field in input #{}.".format(
                            inputs_counter
                        )
                    )

                if input_in_ddl["type"] not in required_fields:
                    raise IPOLCheckDDLError(
                        "Bad DDL inputs section: unknown input type '{}' in input #{}".format(
                            input_in_ddl["type"], inputs_counter
                        )
                    )

                for required_field in required_fields[input_in_ddl["type"]]:
                    if required_field not in input_in_ddl:
                        raise IPOLCheckDDLError(
                            "Bad DDL inputs section: missing '{}' field in input #{}.".format(
                                required_field, inputs_counter
                            )
                        )

                for field in input_in_ddl:
                    if field in natural_fields:
                        try:
                            value = evaluate(input_in_ddl[field])
                        except IPOLEvaluateError as ex:
                            raise IPOLCheckDDLError(
                                "Bad DDL inputs section: invalid expression '{}' in '{}' field at input #{}.".format(
                                    ex, field, inputs_counter
                                )
                            )

                        integer = float(value) == int(value)
                        if value <= 0 or not integer:
                            raise IPOLCheckDDLError(
                                "Bad DDL inputs section: '{}' field must be a natural value in input #{}.".format(
                                    field, inputs_counter
                                )
                            )

        # The params must be a list
        if (
            "archive" in ddl
            and "params" in ddl["archive"]
            and not isinstance(ddl["archive"]["params"], list)
        ):
            raise IPOLCheckDDLError(
                "Bad DDL archive section: expected list of parameters, but found {}".format(
                    type(ddl["archive"]["params"]).__name__
                )
            )

    @staticmethod
    def download(url_file, filename):
        """
        Downloads a file from its URL
        """
        urllib.request.urlretrieve(url_file, filename)

    @staticmethod
    def set_dl_extras_date(filepath, date):
        """
        Sets the modification time
        """
        os.utime(filepath, (date, date))

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

        if zipfile.is_zipfile(filename):
            ar_zip = zipfile.ZipFile(filename)
            content_zip = ar_zip.namelist()
            return ar_zip, content_zip

        raise IPOLExtractError("The file is neither a ZIP nor TAR")

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
            # DUE TO SOME ODD BEHAVIOR OF extractall IN Python 2.6.1 (OSX 10.6.8)
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
                    open_file = open(os.path.join(target, member), "wb")
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

            os.makedirs(demo_extras_folder, exist_ok=True)
            self.extract(compressed_file, demo_extras_folder)
        except Exception as ex:
            raise IPOLDemoExtrasError(ex)

    def ensure_extras_updated(self, demo_id: int):
        """
        Ensure that the demo extras of a given demo are updated with respect to demoinfo information.
        and exists in the core folder.
        """
        try:
            result = self.demoinfo.get_demo_extras_info(demo_id)

            if isinstance(result, Err):
                raise IPOLDemoExtrasError(
                    f"Failed to obtain demoExtras info ({result.value})"
                )

            demoextras_compress_dir = os.path.join(self.dl_extras_dir, str(demo_id))
            info = result.value
            if info is None:
                if os.path.exists(demoextras_compress_dir):
                    shutil.rmtree(demoextras_compress_dir)
                if os.path.exists(
                    os.path.join(self.demo_extras_main_dir, str(demo_id))
                ):
                    shutil.rmtree(os.path.join(self.demo_extras_main_dir, str(demo_id)))
                return

            os.makedirs(demoextras_compress_dir, exist_ok=True)

            demoextras_file = glob.glob(demoextras_compress_dir + "/*")

            # Check if demoinfo has a newer demoextras
            if demoextras_file:
                demoextras_file = demoextras_file[0]

                demoinfo_demoextras_date = info["date"]
                demoinfo_demoextras_size = info["size"]
                extras_stat = os.stat(demoextras_file)
                core_demoextras_date = extras_stat.st_ctime
                core_demoextras_size = extras_stat.st_size

                # If it is already up to date finish
                if (
                    core_demoextras_date > demoinfo_demoextras_date
                    and core_demoextras_size == demoinfo_demoextras_size
                ):
                    return
                # Remove old extras file to download a new version
                shutil.rmtree(demoextras_compress_dir)
                os.makedirs(demoextras_compress_dir, exist_ok=True)

            # Download new demoextras
            demoextras_name = os.path.basename(info["url"])
            demoextras_filename = urllib.parse.unquote(
                os.path.join(demoextras_compress_dir, demoextras_name)
            )
            self.download(info["url"], demoextras_filename)
            self.set_dl_extras_date(demoextras_filename, info["date"])
            self.extract_demo_extras(demo_id, demoextras_filename)

        except Exception as ex:
            self.logger.exception(ex)
            error_message = "Error processing the demoExtras of demo #{}: {}".format(
                demo_id, ex
            )
            raise IPOLDemoExtrasError(error_message)

    @staticmethod
    def create_new_execution_key(logger):
        """
        create a new experiment identifier
        """
        keygen = hashlib.md5()
        seeds = [
            cherrypy.request.remote.ip,
            # use port to improve discrimination
            # for proxied or NAT clients
            cherrypy.request.remote.port,
            datetime.now(),
            random(),
        ]

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
        demo_path = os.path.join(
            self.shared_folder_abs, self.share_run_dir_abs, str(demo_id), key
        )
        os.makedirs(demo_path, exist_ok=True)
        return demo_path

    def get_demo_metadata(self, demo_id):
        """
        Gets demo meta data given its editor's ID
        """
        userdata = {"demoid": demo_id}
        resp, _ = self.post("api/demoinfo/read_demo_metainfo", "post", data=userdata)
        return resp.json()

    def get_demo_editor_list(self, demo_id):
        """
        Get the list of editors of the given demo
        """
        # Get the list of editors of the demo
        userdata = {"demo_id": demo_id}
        resp, status_code = self.post(
            "api/demoinfo/demo_get_editors_list", "post", data=userdata
        )
        response = resp.json()
        status = response["status"]

        if status_code != 200:
            self.error_log(
                f"Failed to obtain the editors of demo #{demo_id} from demoInfo: {status}"
            )
            return ()

        editor_list = response["editor_list"]

        if not editor_list:
            return ()  # No editors given

        # Get the names and emails of the editors
        emails = []
        for entry in editor_list:
            emails.append({"name": entry["name"], "email": entry["mail"]})

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
        msg["Subject"] = subject
        msg["From"] = "{} <{}>".format(sender["name"], sender["email"])
        msg["To"] = emails_str  # Must pass only a comma-separated string here
        msg.preamble = text

        if zip_filename is not None:
            with open(zip_filename, "rb") as open_file:
                zip_data = MIMEApplication(open_file.read())
                zip_data.add_header(
                    "Content-Disposition", "attachment", filename="experiment.zip"
                )
            msg.attach(zip_data)

        text_data = MIMEText(text)
        msg.attach(text_data)
        try:
            email = smtplib.SMTP("localhost")
            # Must pass only a list here
            email.sendmail(msg["From"], emails, msg.as_string())
            email.quit()
        except Exception:
            pass

    def send_compilation_error_email(self, demo_id, text, demorunner):
        """
        Send email to editor when compilation fails
        """
        emails = []

        try:
            demo_state = self.get_demo_metadata(demo_id)["state"].lower()
        except BrokenPipeError:
            demo_state = "<???>"

        # Add Tech and Edit only if this is the production server and
        # the demo has been published

        config_emails = self.read_emails_from_config()
        if not config_emails:
            return

        for editor_mail in self.get_demo_editor_list(demo_id):
            emails.append(editor_mail["email"])

        if self.server_environment == "production" and demo_state == "published":
            emails += config_emails["tech"]["email"].split(",")
            emails += config_emails["edit"]["email"].split(",")
        if not emails:
            return

        # Send the email
        subject = "Compilation of demo #{} failed on {}".format(demo_id, demorunner)
        self.send_email(subject, text, emails, config_emails["sender"])

    def send_internal_error_email(self, message):
        """
        Send email to the IPOL team when an Internal Error has been detected
        """
        config_emails = self.read_emails_from_config()
        if not config_emails:
            return

        emails = config_emails["tech"]["email"].split(",")
        if not emails:
            return

        # Send the email
        subject = "IPOL Internal Error"
        text = "An Internal Error has been detected in IPOL.\n\n"
        text += str(message) + "\n"
        text += "Traceback follows:\n"
        text += traceback.format_exc()

        print(
            "**** INTERNAL ERROR! Sorry for the inconvenience. We're working on it\n\n"
        )
        print(text)

        self.send_email(subject, text, emails, config_emails["sender"])

    def read_emails_from_config(self):
        """
        Read the list of emails from the configuration file
        """
        try:
            emails_file_path = os.path.join(
                self.project_folder,
                "ipol_demo",
                "modules",
                "config_common",
                "emails.conf",
            )
            cfg = configparser.ConfigParser()
            if not os.path.isfile(emails_file_path):
                self.logger.error(
                    "read_emails_from_config: Can't open {}".format(emails_file_path)
                )
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
        """
        Zip a directory
        """
        # ziph is zipfile handle
        for root, _, files in os.walk(path):
            for zip_file in files:
                ziph.write(os.path.join(root, zip_file))

    def send_runtime_error_email(self, demo_id, key, message, demorunner):
        """
        Send email to editor when the execution fails
        """

        id_list = []
        if os.path.exists("ignored_ids.txt"):
            id_list = [int(id) for id in read_commented_text_file("ignored_ids.txt")]

        try:
            demo_state = self.get_demo_metadata(demo_id)["state"].lower()
        except BrokenPipeError:
            demo_state = "<???>"

        # Add Tech and Edit only if this is the production server and
        # the demo has been published
        emails = []
        config_emails = self.read_emails_from_config()
        if not config_emails:
            return

        for editor in self.get_demo_editor_list(demo_id):
            emails.append(editor["email"])

        if self.server_environment == "production" and demo_state == "published":
            emails += config_emails["tech"]["email"].split(",")
            emails += config_emails["edit"]["email"].split(",")

        if not emails:
            return

        # Attach experiment in zip file and send the email
        text = "This is the IPOL Core machine.\n\n\
The execution with key={} of demo #{} on {} has failed.\nProblem: {}.\nPlease find \
attached the failed experiment data.".format(
            key, demo_id, demorunner, message
        )

        if self.server_environment == "production":
            machine = "Core"
        else:
            machine = "Integration"

        subject = "[IPOL {}] Demo #{} execution failure".format(machine, demo_id)

        # Zip the contents of the tmp/ directory of the failed experiment
        zip_filename = "/tmp/{}.zip".format(key)
        zipf = zipfile.ZipFile(zip_filename, "w", zipfile.ZIP_DEFLATED)
        self.zipdir("{}/run/{}/{}".format(self.shared_folder_abs, demo_id, key), zipf)
        zipf.close()

        # Send email only if the demo is not in the ignored id list
        if demo_id not in id_list:
            self.send_email(
                subject,
                text,
                emails,
                config_emails["sender"],
                zip_filename=zip_filename,
            )
        try:
            os.remove(zip_filename)
        except OSError:
            pass

    def send_demorunner_unresponsive_email(self, unresponsive_demorunners):
        """
        Send email to tech if any demorunner is down
        """
        emails = []
        config_emails = self.read_emails_from_config()
        if not config_emails:
            return

        if self.server_environment == "production":
            emails += config_emails["tech"]["email"].split(",")
        if not emails:
            return

        hostname = socket.gethostname()
        hostbyname = socket.gethostbyname(hostname)

        unresponsive_demorunners_list = ",".join(unresponsive_demorunners)

        text = (
            "This is the IPOL Core machine ({}, {}).\n"
            "\nThe list of demorunners unresponsive is: {}.".format(
                hostname, hostbyname, unresponsive_demorunners_list
            )
        )
        subject = "[IPOL Core] Demorunner unresponsive"
        self.send_email(subject, text, emails, config_emails["sender"])

    def send_email_no_demorunner(self, demo_id):
        """
        Send email to tech when there isn't any suitable DR for a published demo
        """
        emails = []
        config_emails = self.read_emails_from_config()
        if not config_emails:
            return

        if self.server_environment == "production":
            emails += config_emails["tech"]["email"].split(",")
        if not emails:
            return

        hostname = socket.gethostname()
        hostbyname = socket.gethostbyname(hostname)

        text = (
            "This is the IPOL Core machine ({}, {}).\n"
            "\nThere isn't any suitable DR for demo: {}.".format(
                hostname, hostbyname, demo_id
            )
        )
        subject = "[IPOL Core] No suitable DR"
        self.send_email(subject, text, emails, config_emails["sender"])

    @staticmethod
    def decode_interface_request(interface_arguments):
        """
        Decode the arguments and extract the files send by the web interface
        """
        if "clientData" not in interface_arguments:
            raise IPOLDecodeInterfaceRequestError("clientData not found.")
        clientdata = json.loads(interface_arguments["clientData"])
        origin = clientdata.get("origin", None)
        if origin is not None:
            origin = origin.lower()

        blobs = {}
        blobset_id = None
        if origin == "upload":
            for key, value in interface_arguments.items():
                if key.startswith("file_"):
                    fname = key
                    blobs[fname] = value

        elif origin == "blobset":
            blobs = clientdata["blobs"]
            blobset_id = clientdata["setId"]
        elif not origin:
            pass
        else:
            raise IPOLDecodeInterfaceRequestError(
                "Wrong origin value from the interface."
            )

        for key, value in interface_arguments.items():
            if key.startswith("inpainting_data_"):
                fname = key
                blobs[fname] = value

        return (
            clientdata["demo_id"],
            origin,
            clientdata.get("params", None),
            clientdata.get("crop_info", None),
            clientdata.get("private_mode", None),
            blobs,
            blobset_id,
        )

    def read_ddl(self, demo_id: int) -> dict:
        """
        This function returns the DDL after checking its syntax.
        """
        result = self.demoinfo.get_ddl(demo_id)
        if isinstance(result, Err):
            raise IPOLReadDDLError(
                f"Couldn't get DDL for demo {demo_id}: {result.value}"
            )

        ddl = json.loads(result.value)
        return ddl

    def find_suitable_demorunner(self, general_info):
        """
        This function returns the demorunner that fits with the requirements of a given demo
        and according to the dispatcher policies
        """
        requirements = general_info.get("requirements", "")
        result = self.dispatcher.get_suitable_demorunner(requirements)

        if isinstance(result, Err):
            err = result.value

            if isinstance(err, dispatcher.UnresponsiveDemorunnerError):
                self.send_demorunner_unresponsive_email(err.dr_name)

            error_message = err.error()
            raise IPOLFindSuitableDR(error_message)

        else:
            return result.value

    @staticmethod
    def get_response_error_or_content(response):
        """
        Returns a string representation of the response in case an error
        happens with the normal code path, or returns the content.
        """
        if response.status_code != 200:
            return f"(http error {response.status_code}, reason: {response.reason})"
        try:
            if not response.content:
                return "(no response.content)"
        except Exception as ex:
            return "(no response.content. Ex: {})".format(ex)
        return response.content

    def ensure_compilation(self, dr_name, demo_id, ddl_build):
        """
        Ensure that the source codes of the demo are all updated and compiled correctly
        """
        build_data = {"demo_id": demo_id, "ddl_build": json.dumps(ddl_build)}
        ssh_response, _ = self.post(
            "api/demoinfo/get_ssh_keys", "post", data={"demo_id": demo_id}
        )
        ssh_response = ssh_response.json()
        if ssh_response["status"] == "OK":
            build_data["ssh_key.public"] = ssh_response["pubkey"]
            build_data["ssh_key.private"] = ssh_response["privkey"]

        url = f"api/demorunner/{dr_name}/ensure_compilation"
        dr_response, _ = self.post(url, "post", data=build_data)

        # Read the JSON response from the DR
        try:
            demorunner_response = dr_response.json()
        except Exception as ex:
            dr_response_content = Core.get_response_error_or_content(dr_response)
            error_message = "**An internal error has occurrred in the demo system, sorry for the inconvenience.\
                The IPOL Team has been notified and will fix the issue as soon as possible**. Bad format in the response \
                        from DR server {} in demo #{}. {} - {}".format(
                dr_name, demo_id, dr_response_content, ex
            )
            self.logger.exception(error_message)
            raise IPOLEnsureCompilationError(error_message)

        # Check if the compilation was successful
        if demorunner_response["status"] != "OK":
            print("Compilation error in demo #{}".format(demo_id))
            # Add the compilation failure info into the exception
            buildlog = demorunner_response.get("buildlog", "")
            demorunner_message = demorunner_response["message"]
            error_message = "DR={}, {}  - {}".format(
                dr_name, buildlog, demorunner_message
            )
            raise IPOLEnsureCompilationError(error_message)

    def prepare_folder_for_execution(
        self, demo_id, origin, blobs, blobset_id, ddl_inputs, params, crop_info
    ):
        """
        Creates the working directory for a new execution. Then it copies and
        eventually converts the input blobs
        """
        key = self.create_new_execution_key(self.logger)
        if not key:
            raise IPOLKeyError(
                "**An internal error has occurred in the demo system, sorry for the inconvenience.\
                The IPOL team has been notified and will fix the issue as soon as possible**.\
                     Failed to create a valid execution key"
            )
        try:
            work_dir = self.create_run_dir(demo_id, key)
            # save parameters as a params.json file.
            # Used in failure email or as an input for DemoExtras
            try:
                json_filename = os.path.join(work_dir, "params.json")
                with open(json_filename, "w") as resfile:
                    resfile.write(json.dumps(params))
            except (OSError, IOError):
                error_message = "Failed to save {} in demo {}".format(
                    json_filename, demo_id
                )
                self.logger.exception(error_message)
        except Exception as ex:
            raise IPOLWorkDirError(ex)

        if not origin:
            return work_dir, key, [], {}
        # Copy input blobs
        try:
            inputs_names = self.copy_blobs(
                work_dir, demo_id, origin, blobs, blobset_id, ddl_inputs
            )
            self.copy_inpainting_data(work_dir, blobs, ddl_inputs)
            result = self.converter.convert(
                work_dir=work_dir, input_list=ddl_inputs, crop_info=crop_info
            )

            if isinstance(result, Err):
                raise IPOLConversionError(result.value)

            conversion_info = result.unwrap()
        except IPOLConversionError as ex:
            raise IPOLPrepareFolderError(str(ex))
        except IPOLInputUploadTooLargeError as ex:
            error_message = (
                "Uploaded input #{} over the maximum allowed weight {} bytes".format(
                    ex.index, ex.max_weight
                )
            )
            raise IPOLPrepareFolderError(error_message)
        except IPOLMissingRequiredInputError as ex:
            error_message = "Missing required input #{}".format(ex.index)
            raise IPOLPrepareFolderError(error_message)
        except IPOLEvaluateError as ex:
            error_message = (
                "Invalid expression '{}' found in the DDL of demo {}".format(
                    str(ex), demo_id
                )
            )
            raise IPOLPrepareFolderError(error_message)
        except IPOLCopyBlobsError as ex:
            error_message = (
                "** INTERNAL ERROR **. Error copying blobs of demo {}: {}".format(
                    demo_id, ex
                )
            )
            self.logger.exception(error_message)
            raise IPOLPrepareFolderError(error_message, error_message)
        except IPOLInputUploadError as ex:
            error_message = "Error uploading input of demo #{} with key={}: {}".format(
                demo_id, key, ex
            )
            self.logger.exception(error_message)
            raise IPOLPrepareFolderError(error_message)
        except IPOLProcessInputsError as ex:
            error_message = (
                "** INTERNAL ERROR **. Error processing inputs of demo {}: {}".format(
                    demo_id, ex
                )
            )
            self.logger.exception(error_message)
            raise IPOLPrepareFolderError(error_message, error_message)
        except (IOError, OSError) as ex:
            error_message = "** INTERNAL ERROR **. I/O error processing inputs"
            log_message = (error_message + ". {}: {}").format(
                type(ex).__name__, str(ex)
            )
            self.logger.exception(log_message)
            raise IPOLPrepareFolderError(error_message, log_message)

        messages = []

        for input_key, conv_info in conversion_info.items():
            if conv_info.code == conversion.ConversionStatus.Error:
                error = conv_info.error
                error_message = f"Input #{input_key}: {error}"
                raise IPOLPrepareFolderError(error_message)

            if conv_info.code == conversion.ConversionStatus.NeededButForbidden:
                error_message = f"Input #{input_key} needs to be pre-processed, but this is forbidden in this demo."
                raise IPOLPrepareFolderError(error_message)

            if conv_info.code == conversion.ConversionStatus.Done:
                modifications_str = ", ".join(conv_info.modifications)
                message = "Input #{} has been preprocessed {{{}}}.".format(
                    input_key, modifications_str
                )
                messages.append(message)

        return work_dir, key, messages, inputs_names

    def execute_experiment(
        self,
        dr_name,
        demo_id,
        key,
        params,
        inputs_names,
        ddl_run,
        ddl_general,
        work_dir,
    ):
        """
        Execute the experiment in the given DR.
        """
        params = {**params}
        for i, input_item in inputs_names.items():
            params[f"orig_input_{i}"] = input_item["origin"]
            params[f"input_{i}"] = input_item["converted"]

        userdata = {
            "demo_id": demo_id,
            "key": key,
            "params": json.dumps(params),
            "ddl_run": ddl_run,
        }

        if "timeout" in ddl_general:
            userdata["timeout"] = ddl_general["timeout"]

        i = 0
        inputs = {}
        for root, _, files in os.walk(work_dir):
            for file in files:
                path = os.path.join(root, file)
                relative_path = path.replace(work_dir, "./")
                fd = open(path, "rb")
                inputs[f"inputs.{i}"] = (relative_path, fd, "application/octet-stream")
                i += 1

        url = f"api/demorunner/{dr_name}/exec_and_wait"
        resp, status_code = self.post(url, "post", data=userdata, files=inputs)

        if status_code != 200:
            demo_state = self.get_demo_metadata(demo_id)["state"].lower()
            error = "IPOLDemorunnerUnresponsive"
            website_message = (
                f"Demorunner {dr_name} not responding (error {resp.status_code})"
            )
            raise IPOLDemoRunnerResponseError(website_message, demo_state, key, error)

        zipcontent = io.BytesIO(resp.content)
        zip = zipfile.ZipFile(zipcontent)
        zip.extractall(work_dir)

        try:
            demorunner_response = json.load(
                open(os.path.join(work_dir, "exec_info.json"))
            )
        except Exception as ex:
            error_message = "**An internal error has occurred in the demo system, sorry for the inconvenience.\
                    The IPOL team has been notified and will fix the issue as soon as possible**. Bad format in the response from DR server {} in demo #{}. - {}".format(
                dr_name, demo_id, ex
            )
            self.logger.exception(error_message)
            raise IPOLExecutionError(error_message, error_message)

        if demorunner_response["status"] != "OK":
            print("DR answered KO for demo #{}".format(demo_id))

            try:
                demo_state = self.get_demo_metadata(demo_id)["state"].lower()
            except BrokenPipeError:
                demo_state = "<???>"

            # Message for the web interface
            error_msg = (demorunner_response["algo_info"]["error_message"]).strip()
            error = demorunner_response.get("error", "").strip()

            # Prepare a message for the website.
            website_message = "DR={}\n{}".format(dr_name, error_msg)
            # In case of a timeout, send a human-oriented message to the web interface
            if error == "IPOLTimeoutError":
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
            failure_filepath = os.path.join(work_dir, "demo_failure.txt")
            if os.path.exists(failure_filepath):
                with open(failure_filepath, "r") as open_file:
                    failure_message = "{}".format(open_file.read())
                raise IPOLExecutionError(failure_message)
        except (OSError, IOError):
            error_message = "Failed to read {} in demo {}".format(
                failure_filepath, demo_id
            )
            self.logger.exception(error_message)
            raise IPOLExecutionError(error_message, error_message)

        algo_info_dic = self.read_algo_info(work_dir)
        for name in algo_info_dic:
            demorunner_response["algo_info"][name] = algo_info_dic[name]

        demorunner_response["work_url"] = (
            os.path.join(
                "/api/core/",
                self.shared_folder_rel,
                self.share_run_dir_rel,
                str(demo_id),
                key,
            )
            + "/"
        )

        return demorunner_response

    @cherrypy.expose
    def run(self, **kwargs):
        """
        Run a demo. The presentation layer requests the Core to execute a demo.
        """
        demo_id = None
        try:
            (
                demo_id,
                origin,
                params,
                crop_info,
                private_mode,
                blobs,
                blobset_id,
            ) = self.decode_interface_request(kwargs)

            ddl = self.read_ddl(demo_id)

            # Check the DDL for missing required sections and their format
            self.check_ddl(ddl)

            # Find a demorunner according the requirements of the demo and the dispatcher policy
            dr_name = self.find_suitable_demorunner(ddl["general"])

            # Ensure that the demoExtras are updated
            self.ensure_extras_updated(demo_id)

            # Ensure that the source code is updated
            self.ensure_compilation(dr_name, demo_id, ddl["build"])

            ddl_inputs = ddl.get("inputs")
            # Create run directory in the shared folder, copy blobs and delegate in the conversion module
            # the conversion of the input data if it is requested and not forbidden
            (
                work_dir,
                key,
                prepare_folder_messages,
                input_names,
            ) = self.prepare_folder_for_execution(
                demo_id, origin, blobs, blobset_id, ddl_inputs, params, crop_info
            )

            # Delegate in the the chosen DR the execution of the experiment in the run folder
            demorunner_response = self.execute_experiment(
                dr_name,
                demo_id,
                key,
                params,
                input_names,
                ddl["run"],
                ddl["general"],
                work_dir,
            )

            # Archive the experiment, if the 'archive' section exists in the DDL and it is not a private execution
            # Also check if it is an original uploaded data from the user (origin != 'blobset') or is enabled archive_always
            if (
                not private_mode
                and "archive" in ddl
                and (origin != "blobset" or ddl["archive"].get("archive_always"))
            ):
                base_url = os.environ.get("IPOL_URL", "http://" + socket.getfqdn())
                try:
                    response, status_code = send_to_archive(
                        demo_id,
                        work_dir,
                        kwargs,
                        ddl["archive"],
                        demorunner_response,
                        base_url,
                        input_names,
                    )
                    if status_code != 201:
                        response = response.json()
                        id_experiment = response.get("experiment_id", None)
                        message = f"Error {status_code} from archive module when archiving an experiment: demo={demo_id}, key={key}, id={id_experiment}."
                        self.logger.exception(message)
                except Exception as ex:
                    message = (
                        "Error archiving an experiment: demo={}, key={}. Error: {}."
                    )
                    self.logger.exception(message.format(demo_id, key, str(ex)))

            # Save the execution, so the users can recover it from the URL
            self.save_execution(demo_id, kwargs, demorunner_response, work_dir)

            messages = []
            messages.extend(prepare_folder_messages)

            return json.dumps(
                dict(demorunner_response, **{"messages": messages})
            ).encode()
        except (IPOLDecodeInterfaceRequestError, IPOLUploadedInputRejectedError) as ex:
            return json.dumps({"error": str(ex), "status": "KO"}).encode()
        except (IPOLDemoExtrasError, IPOLKeyError) as ex:
            error_message = str(ex)
            self.send_internal_error_email(error_message)
            self.logger.exception(error_message)
            return json.dumps({"error": error_message, "status": "KO"}).encode()
        except IPOLEnsureCompilationError as ex:
            error_message = " --- Compilation error. --- {}".format(str(ex))
            self.send_compilation_error_email(demo_id, error_message, dr_name)
            return json.dumps({"error": str(ex), "status": "KO"}).encode()
        except IPOLFindSuitableDR as ex:
            try:
                if self.get_demo_metadata(demo_id)["state"].lower() == "published":
                    self.send_email_no_demorunner(demo_id)
            except BrokenPipeError:
                pass

            error_message = str(ex)
            self.logger.exception(error_message)
            return json.dumps({"error": error_message, "status": "KO"}).encode()
        except IPOLWorkDirError as ex:
            error_message = "Could not create work_dir for demo {}".format(demo_id)
            # do not output full path for public
            internal_error_message = (error_message + ". Error: {}").format(str(ex))
            self.logger.exception(internal_error_message)
            self.send_internal_error_email(internal_error_message)
            return json.dumps({"error": error_message, "status": "KO"}).encode()
        except IPOLReadDDLError as ex:
            # code -1: the DDL of the requested ID doesn't exist
            # code -2: Invalid demo_id
            error_message = "{} Demo #{}".format(str(ex.error_message), demo_id)
            self.logger.exception(error_message)
            if not ex.error_code or ex.error_code not in (-1, -2):
                self.send_internal_error_email(error_message)
            return json.dumps({"error": error_message, "status": "KO"}).encode()
        except IPOLCheckDDLError as ex:
            error_message = "{} Demo #{}".format(str(ex), demo_id)
            if self.get_demo_metadata(demo_id)["state"].lower() == "published":
                self.send_runtime_error_email(demo_id, "<NA>", error_message, "no-dr")
            return json.dumps({"error": error_message, "status": "KO"}).encode()
        except IPOLPrepareFolderError as ex:
            # Do not log: function prepare_folder_for_execution will decide when to log
            if ex.email_message:
                self.send_internal_error_email(ex.email_message)
            return json.dumps({"error": ex.interface_message, "status": "KO"}).encode()
        except IPOLExecutionError as ex:
            # Do not log: function execute_experiment will decide when to log
            if ex.email_message:
                self.send_internal_error_email(ex.email_message)
            return json.dumps({"error": ex.interface_message, "status": "KO"}).encode()
        except IPOLEvaluateError as ex:
            error_message = "IPOLEvaluateError '{}' detected in demo {}".format(
                str(ex), demo_id
            )
            self.logger.exception(error_message)
            self.send_internal_error_email(error_message)
            return json.dumps({"error": error_message, "status": "KO"}).encode()
        except IPOLDemoRunnerResponseError as ex:
            # Send email to the editors
            # (unless it's a timeout in a published demo)
            if not (ex.demo_state == "published" and ex.error == "IPOLTimeoutError"):
                self.send_runtime_error_email(demo_id, ex.key, ex.message, dr_name)
            return json.dumps({"error": ex.message, "status": "KO"}).encode()
        except Exception as ex:
            # We should never get here.
            #
            # If we arrive here it means that we missed to catch and
            # take care of some exception type.
            error_message = "**An internal error has occurred in the demo system, sorry for the inconvenience.\
                The IPOL team has been notified and will fix the issue as soon as possible.** \
                  Error in the run function of the Core in demo {}, {}. Received kwargs: {}".format(
                demo_id, ex, str(kwargs)
            )
            print(traceback.format_exc())
            self.logger.exception(error_message)
            self.send_internal_error_email(error_message)
            return json.dumps({"status": "KO", "error": error_message}).encode()

    @staticmethod
    def save_execution(demo_id, request, response, work_dir):
        """
        Save all needed data to recreate an execution.
        """
        clientdata = json.loads(request["clientData"])

        if clientdata.get("origin", "") == "upload":
            # Count how many file entries and remove them
            file_keys = [key for key in request if key.startswith("file_")]
            list(map(request.pop, file_keys))
            clientdata["files"] = len(file_keys)

        execution_json = {}
        execution_json["demo_id"] = demo_id
        execution_json["request"] = clientdata
        execution_json["response"] = response

        # Save file
        with open(os.path.join(work_dir, "execution.json"), "w") as outfile:
            json.dump(execution_json, outfile)

    @cherrypy.expose
    def load_execution(self, demo_id, key):
        """
        Load the data needed to recreate an execution.
        """
        filename = os.path.join(
            self.share_run_dir_abs, str(demo_id), key, "execution.json"
        )
        if not os.path.isfile(filename):
            message = "Execution with key={} not found".format(key)
            res_data = {"error": message, "status": "KO"}
            print(message)
            return json.dumps(res_data).encode()

        try:
            with open(filename, "r") as open_file:
                lines = open_file.read()
        except Exception as ex:
            message = (
                "** INTERNAL ERROR ** while reading execution with key={}: {}".format(
                    key, ex
                )
            )
            self.logger.exception(message)
            self.send_internal_error_email(message)
            res_data = {"error": message, "status": "KO"}
            return json.dumps(res_data).encode()

        return json.dumps({"status": "OK", "experiment": lines}).encode()

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
            if len(line.split("=", 1)) < 2 or line.split("=", 1)[0].strip() == "":
                print("incorrect format in algo_info.txt, in line {}".format(line))
                self.logger.error(
                    "run: incorrect format in algo_info.txt, at line {}".format(line)
                )
                continue

            # Add name and assigned value to the output dict
            name, value = line.split("=", 1)
            name = name.strip()
            dic[name] = value

        open_file.close()
        return dic

    @cherrypy.expose
    @cherrypy.tools.allow(methods=["POST"])  # allow only post
    @authenticate
    def delete_demo(self, demo_id):
        """
        Delete the specified demo
        """
        demo_id = int(demo_id)
        data = {}
        data["status"] = "OK"
        userdata = {"demo_id": demo_id}
        error_message = ""

        try:
            # delete demo, blobs and extras associated to it
            result = self.demoinfo.delete_demo(demo_id)
            if not isinstance(result, Ok):
                error_message += f"Error when removing demo: {result.value} \n"

            result = self.demoinfo.delete_demoextras(demo_id)
            if not isinstance(result, Ok):
                error_message += f"Error when removing demoextras: {result.value} \n"

            response, _ = self.post("/api/blobs/delete_demo", "post", data=userdata)
            if response.json()["status"] != "OK":
                error_message += "API call /blobs/delete_demo failed.'\n"

            # delete the archive
            _, status_code = self.post(f"/api/archive/demo/{demo_id}", "delete")
            if status_code == 404:
                error_message += (
                    f"API call /api/archive/demo to delete  demo failed. {demo_id}"
                )
            if error_message:
                data["status"] = "KO"
                data["error"] = f"Failed to delete demo: {demo_id}."
                self.send_internal_error_email(error_message)

        except Exception as ex:
            error_message = f"Failed to delete demo {demo_id}. Error: {ex}"
            data["status"] = "KO"
            data["error"] = error_message
            self.send_internal_error_email(error_message)

        return json.dumps(data).encode()

    @staticmethod
    def post(api_url, method=None, **kwargs):
        """
        General purpose function to make http requests.
        """
        base_url = os.environ.get("IPOL_URL", "http://" + socket.getfqdn())
        headers = {"Content-Type": "application/json; charset=UTF-8"}
        if method == "get":
            response = requests.get(f"{base_url}/{api_url}")
            return response.json(), response.status_code
        elif method == "put":
            response = requests.put(f"{base_url}/{api_url}", **kwargs, headers=headers)
            return response.json(), response.status_code
        elif method == "post":
            response = requests.post(f"{base_url}/{api_url}", **kwargs)
            return response, response.status_code
        elif method == "delete":
            response = requests.delete(
                f"{base_url}/{api_url}", **kwargs, headers=headers
            )
            return response, response.status_code
        else:
            assert False


def init_logging():
    """
    Initialize the error logs of the module.
    """
    logger = logging.getLogger("core")

    logger.setLevel(logging.DEBUG)
    handler = logging.StreamHandler()
    formatter = logging.Formatter(
        "%(asctime)s; [%(filename)s:%(lineno)s - %(funcName)20s() ] %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )
    handler.setFormatter(formatter)

    logger.addHandler(handler)
    return logger

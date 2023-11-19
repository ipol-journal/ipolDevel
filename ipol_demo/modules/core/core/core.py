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
from datetime import datetime
from email.mime.application import MIMEApplication
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from random import random

import magic
import requests
from config import settings
from conversion import conversion
from core.errors import (
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
from demoinfo import demoinfo
from dispatcher import dispatcher
from ipolutils.evaluator.evaluator import IPOLEvaluateError, evaluate
from ipolutils.read_text_file import read_commented_text_file
from result import Err


class Core:
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
        self.server_environment: str = os.environ.get("env", "local")
        self.module_dir: str = (
            os.path.expanduser("~") + "/ipolDevel/ipol_demo/modules/blobs"
        )
        self.logs_dir: str = "logs/"
        self.config_common_dir: str = (
            os.path.expanduser("~") + "/ipolDevel/ipol_demo/modules/config_common"
        )

        self.base_url: str = os.environ["IPOL_URL"]

        self.project_folder = os.path.expanduser("~") + "/ipolDevel"
        self.blobs_folder = (
            os.path.expanduser("~") + "/ipolDevel/ipol_demo/modules/blobs"
        )

        self.shared_folder_rel: str = "shared_folder/"
        self.shared_folder_abs = os.path.join(
            self.project_folder, self.shared_folder_rel
        )
        self.demo_extras_main_dir = os.path.join(self.shared_folder_abs, "demoExtras/")
        self.dl_extras_dir = os.path.join(self.shared_folder_abs, "dl_extras/")
        self.share_run_dir_rel: str = "run/"
        self.share_run_dir_abs = os.path.join(
            self.shared_folder_abs, self.share_run_dir_rel
        )

        # create needed directories
        os.makedirs(self.share_run_dir_abs, exist_ok=True)
        os.makedirs(self.shared_folder_abs, exist_ok=True)
        os.makedirs(self.dl_extras_dir, exist_ok=True)
        os.makedirs(self.demo_extras_main_dir, exist_ok=True)

        base_url = os.environ["IPOL_URL"]
        demorunners_path = (
            os.path.expanduser("~")
            + "/ipolDevel/ipol_demo/modules/config_common/demorunners.xml"
        )
        policy = "lowest_workload"
        self.dispatcher = dispatcher.Dispatcher(
            workload_provider=dispatcher.APIWorkloadProvider(base_url),
            ping_provider=dispatcher.APIPingProvider(base_url),
            demorunners=dispatcher.parse_demorunners(demorunners_path),
            policy=dispatcher.make_policy(policy),
        )

        self.demoinfo = demoinfo.DemoInfo(
            dl_extras_dir=settings.demoinfo_dl_extras_dir,
            database_path=settings.demoinfo_db,
            base_url=settings.base_url,
        )

        self.converter = conversion.Converter()

    def index(self, code_starts=None):
        """
        Index page
        """
        result = self.demoinfo.demo_list()

        if result.is_err():
            self.send_internal_error_email("Unable to get the list of demos")
            html_content = """
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
            return html_content

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

        html_content = """
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
            html_content += """
                        <h3>The demos whose ID begins with '77777' are public workshops and those with '33333' are private.
                        Test demos begin with '55555' whereas Example demos begin with '11111'.</h3><br>
                        """
        html_content += """
                    {}
                    </body>
                    </html>
                    """.format(
            demos_string
        )
        return html_content

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
            demo_blobs, status = self.post(f"api/blobs/demo_blobs/{demo_id}", "get")
        except json.JSONDecodeError as ex:
            logger.exception(f"{ex}")
            raise IPOLCopyBlobsError(f"{ex}")

        if not demo_blobs or status != 200:
            error_msg = (
                "Failed to get blobs at Core's copy_blobset_from_physical_location"
            )
            logger.exception(error_msg)
            raise IPOLCopyBlobsError(error_msg)

        try:
            blobset = demo_blobs[blobset_id]
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
                logger.exception(
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
            logger.exception(ex)
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
            # cherrypy.request.remote.ip,
            # use port to improve discrimination
            # for proxied or NAT clients
            # cherrypy.request.remote.port,
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
        resp = self.demoinfo.read_demo_metainfo(demo_id)
        return resp.value

    def get_demo_editor_list(self, demo_id):
        """
        Get the list of editors of the given demo
        """
        # Get the list of editors of the demo
        response, status_code = self.post(f"api/demoinfo/editors/{demo_id}", "get")

        error = response["error"]

        if status_code != 200:
            self.error_log(
                f"Failed to obtain the editors of demo #{demo_id} from demoInfo: {error}"
            )
            return ()

        editor_list = response

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
                logger.error(
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
            logger.exception("Can't read emails of journal staff")
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
    def decode_interface_request(interface_arguments, files):
        """
        Decode the arguments and extract the files send by the web interface
        """
        clientdata = interface_arguments
        origin = clientdata.get("origin", None)
        if origin is not None:
            origin = origin.lower()

        blobs = {}
        blobset_id = None
        if origin == "upload":
            for key, value in files.items():
                if key.startswith("file"):
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

        for key, value in files.items():
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
        build_data = {"ddl_build": ddl_build}
        result = self.demoinfo.get_ssh_keys(demo_id)
        if result.is_ok():
            pubkey, privkey = result.value
            build_data["ssh_keys"] = {
                "public_key": pubkey,
                "private_key": privkey,
            }

        url = f"api/demorunner/{dr_name}/compilations/{demo_id}"
        dr_response, dr_response_code = self.post(
            url, "post", data=json.dumps(build_data)
        )

        # Check if the compilation was successful
        if dr_response_code != 201:
            # Read the JSON response from the DR
            demorunner_response = dr_response.json()

            print("Compilation error in demo #{}".format(demo_id))
            # Add the compilation failure info into the exception
            buildlog = demorunner_response.get("buildlog", "")
            demorunner_message = demorunner_response["detail"]
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
        key = self.create_new_execution_key(logger)
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
                logger.exception(error_message)
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
            logger.exception(error_message)
            raise IPOLPrepareFolderError(error_message, error_message)
        except IPOLInputUploadError as ex:
            error_message = "Error uploading input of demo #{} with key={}: {}".format(
                demo_id, key, ex
            )
            logger.exception(error_message)
            raise IPOLPrepareFolderError(error_message)
        except IPOLProcessInputsError as ex:
            error_message = (
                "** INTERNAL ERROR **. Error processing inputs of demo {}: {}".format(
                    demo_id, ex
                )
            )
            logger.exception(error_message)
            raise IPOLPrepareFolderError(error_message, error_message)
        except (IOError, OSError) as ex:
            error_message = "** INTERNAL ERROR **. I/O error processing inputs"
            log_message = (error_message + ". {}: {}").format(
                type(ex).__name__, str(ex)
            )
            logger.exception(log_message)
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
        parameters = {**params}
        for i, input_item in inputs_names.items():
            parameters[f"orig_input_{i}"] = input_item["origin"]
            parameters[f"input_{i}"] = input_item["converted"]

        payload = {
            "key": key,
            "ddl_run": ddl_run,
            "parameters": json.dumps(parameters),
        }

        if "timeout" in ddl_general:
            payload["timeout"] = ddl_general["timeout"]

        files = []
        for root, _, wd_files in os.walk(work_dir):
            for file in wd_files:
                path = os.path.join(root, file)
                files.append(
                    (
                        "files",
                        (
                            file,
                            open(path, "rb"),
                            "application/octet-stream",
                        ),
                    )
                )

        url = f"api/demorunner/{dr_name}/exec_and_wait/{demo_id}"
        dr_response, status_code = self.post(
            url,
            "post",
            params=payload,
            files=files,
        )
        if status_code != 200:
            demo_state = self.get_demo_metadata(demo_id)["state"].lower()
            error = "IPOLDemorunnerUnresponsive"
            website_message = (
                f"Demorunner {dr_name} not responding (error {dr_response.status_code})"
            )
            raise IPOLDemoRunnerResponseError(website_message, demo_state, key, error)

        zipcontent = io.BytesIO(dr_response.content)
        zip = zipfile.ZipFile(zipcontent)
        zip.extractall(work_dir)

        try:
            dr_response = json.load(open(os.path.join(work_dir, "exec_info.json")))
        except Exception as ex:
            error_message = "**An internal error has occurred in the demo system, sorry for the inconvenience.\
                    The IPOL team has been notified and will fix the issue as soon as possible**. Bad format in the response from DR server {} in demo #{}. - {}".format(
                dr_name, demo_id, ex
            )
            logger.exception(error_message)
            raise IPOLExecutionError(error_message, error_message)

        if dr_response.get("error"):
            print("DR answered KO for demo #{}".format(demo_id))

            try:
                demo_state = self.get_demo_metadata(demo_id)["state"].lower()
            except BrokenPipeError:
                demo_state = "<???>"

            # Message for the web interface
            error_msg = (dr_response["algo_info"]["error_message"]).strip()
            error = dr_response.get("error", "").strip()

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
            logger.exception(error_message)
            raise IPOLExecutionError(error_message, error_message)

        algo_info_dic = self.read_algo_info(work_dir)
        for name in algo_info_dic:
            dr_response["algo_info"][name] = algo_info_dic[name]

        dr_response["work_url"] = (
            os.path.join(
                "/api/core/",
                self.shared_folder_rel,
                self.share_run_dir_rel,
                str(demo_id),
                key,
            )
            + "/"
        )

        return dr_response

    @staticmethod
    def save_execution(demo_id, clientdata, response, work_dir, files):
        """
        Save all needed data to recreate an execution.
        """

        if clientdata.get("origin", "") == "upload":
            # Count how many file entries and remove them
            file_keys = [key for key in files if key.startswith("file_")]
            list(map(files.pop, file_keys))
            clientdata["files"] = len(file_keys)

        execution_json = {}
        execution_json["demo_id"] = demo_id
        execution_json["request"] = clientdata
        execution_json["response"] = response

        # Save file
        with open(os.path.join(work_dir, "execution.json"), "w") as outfile:
            json.dump(execution_json, outfile)

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
                logger.error(
                    "run: incorrect format in algo_info.txt, at line {}".format(line)
                )
                continue

            # Add name and assigned value to the output dict
            name, value = line.split("=", 1)
            name = name.strip()
            dic[name] = value

        open_file.close()
        return dic

    @staticmethod
    def post(api_url, method=None, **kwargs):
        """
        General purpose function to make http requests.
        """
        base_url = os.environ["IPOL_URL"]
        if method == "get":
            response = requests.get(f"{base_url}/{api_url}")
            return response.json(), response.status_code
        elif method == "put":
            response = requests.put(f"{base_url}/{api_url}", **kwargs)
            return response.json(), response.status_code
        elif method == "post":
            response = requests.post(f"{base_url}/{api_url}", **kwargs)
            return response, response.status_code
        elif method == "delete":
            response = requests.delete(f"{base_url}/{api_url}", **kwargs)
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


logger = init_logging()

import configparser
import json
import logging
import os
import re
import socket
import traceback

import requests
from config import settings
from core import core
from core.archive import send_to_archive
from core.errors import (
    IPOLCheckDDLError,
    IPOLDecodeInterfaceRequestError,
    IPOLDemoExtrasError,
    IPOLDemoRunnerResponseError,
    IPOLEnsureCompilationError,
    IPOLExecutionError,
    IPOLFindSuitableDR,
    IPOLKeyError,
    IPOLPrepareFolderError,
    IPOLReadDDLError,
    IPOLUploadedInputRejectedError,
    IPOLWorkDirError,
)
from fastapi import APIRouter, Depends, File, Form, HTTPException, Request, UploadFile
from fastapi.responses import HTMLResponse
from ipolutils.evaluator.evaluator import IPOLEvaluateError
from result import Ok

coreRouter = APIRouter(prefix="/core")
core = core.Core()


def validate_ip(request: Request) -> bool:
    # Check if the request is coming from an allowed IP address
    patterns = []
    ip = request.headers["x-real-ip"]
    # try:
    for pattern in read_authorized_patterns():
        patterns.append(
            re.compile(pattern.replace(".", "\\.").replace("*", "[0-9a-zA-Z]+"))
        )
    for pattern in patterns:
        if pattern.match(ip) is not None:
            return True
    raise HTTPException(status_code=403, detail="IP not allowed")


def read_authorized_patterns() -> list:
    """
    Read from the IPs conf file
    """
    # Check if the config file exists
    authorized_patterns_path = os.path.join(
        settings.config_common_dir, settings.authorized_patterns
    )
    if not os.path.isfile(authorized_patterns_path):
        logger.exception(
            f"read_authorized_patterns: \
                      File {authorized_patterns_path} doesn't exist"
        )
        return []

    # Read config file
    try:
        cfg = configparser.ConfigParser()
        cfg.read([authorized_patterns_path])
        patterns = []
        for item in cfg.items("Patterns"):
            patterns.append(item[1])
        return patterns
    except configparser.Error:
        logger.exception(f"Bad format in {authorized_patterns_path}")
        return []


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


@coreRouter.get("/demo", status_code=201)
def demo(code_starts=None) -> HTMLResponse:
    """
    Return an HTML page with the list of demos.
    """
    html_content = core.index(code_starts=code_starts)
    return HTMLResponse(content=html_content, status_code=200)


@staticmethod
@coreRouter.get("/ping", status_code=201)
def ping():
    """
    Ping: answer with a PONG.
    """
    return {"status": "OK", "ping": "pong"}


@coreRouter.on_event("shutdown")
def shutdown_event():
    logger.info("Application shutdown")


@coreRouter.get("/load_execution", status_code=201)
def load_execution(demo_id: int, key: str):
    """
    Load the data needed to recreate an execution.
    """
    filename = os.path.join(
        settings.share_run_dir_abs, str(demo_id), key, "execution.json"
    )
    if not os.path.isfile(filename):
        message = "Execution with key={} not found".format(key)
        print(message)
        raise HTTPException(status_code=500, detail=message)

    try:
        with open(filename, "r") as open_file:
            lines = open_file.read()
    except Exception as ex:
        message = "** INTERNAL ERROR ** while reading execution with key={}: {}".format(
            key, ex
        )
        logger.exception(message)
        core.send_internal_error_email(message)
        raise HTTPException(status_code=500, detail=message)

    return {"experiment": json.loads(lines)}


@coreRouter.delete(
    "/demo/{demo_id}", dependencies=[Depends(validate_ip)], status_code=204
)
def delete_demo(demo_id: int) -> None:
    """
    Delete the specified demo
    """
    data = {}
    error_message = ""

    try:
        # delete demo, blobs and extras associated to it
        result = settings.demoinfo.delete_demo(demo_id)
        if not isinstance(result, Ok):
            error_message += f"Error when removing demo: {result.value} \n"

        result = settings.demoinfo.delete_demoextras(demo_id)
        if not isinstance(result, Ok):
            error_message += f"Error when removing demoextras: {result.value} \n"
        resp = requests.delete(f"{settings.base_url}/api/blobs/demos/{demo_id}")

        if resp.status_code != 204:
            error_message += "API call /blobs/delete_demo failed.'\n"

        # delete the archive
        resp = requests.delete(f"{settings.base_url}/api/archive/demo/{demo_id}")
        if resp.status_code == 404:
            error_message += (
                f"API call /api/archive/demo to delete  demo failed. {demo_id}"
            )
        if error_message:
            data["status"] = "KO"
            data["error"] = f"Failed to delete demo: {demo_id}."
            core.send_internal_error_email(error_message)
            raise HTTPException(status_code=500, detail=data)

    except Exception as ex:
        error_message = f"Failed to delete demo {demo_id}. Error: {ex}"
        data["status"] = "KO"
        data["error"] = error_message
        core.send_internal_error_email(error_message)
        raise HTTPException(status_code=500, detail=data)


# def run(clientData: str = Form(), files: list[UploadFile] = File(None)):
@coreRouter.post("/run", status_code=201)
async def run(
    request: Request, clientData: str = Form(), files: list[UploadFile] = File(None)
):
    """
    Run a demo. The presentation layer requests the Core to execute a demo.
    """
    form = await request.form()
    form = dict(form)
    clientData = json.loads(clientData)
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
        ) = core.decode_interface_request(clientData, form)

        ddl = core.read_ddl(demo_id)
        # Check the DDL for missing required sections and their format
        core.check_ddl(ddl)

        # Find a demorunner according the requirements of the demo and the dispatcher policy
        dr_name = core.find_suitable_demorunner(ddl["general"])

        # Ensure that the demoExtras are updated
        core.ensure_extras_updated(demo_id)

        # Ensure that the source code is updated
        core.ensure_compilation(dr_name, demo_id, ddl["build"])

        ddl_inputs = ddl.get("inputs")

        # Create run directory in the shared folder, copy blobs and delegate in the conversion module
        # the conversion of the input data if it is requested and not forbidden
        (
            work_dir,
            key,
            prepare_folder_messages,
            input_names,
        ) = core.prepare_folder_for_execution(
            demo_id, origin, blobs, blobset_id, ddl_inputs, params, crop_info
        )

        # Delegate in the the chosen DR the execution of the experiment in the run folder
        demorunner_response = core.execute_experiment(
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
                    clientData,
                    ddl["archive"],
                    demorunner_response,
                    base_url,
                    input_names,
                    form,
                )
                if status_code != 201:
                    response = response.json()
                    id_experiment = response.get("experiment_id", None)
                    message = f"Error {status_code} from archive module when archiving an experiment: demo={demo_id}, key={key}, id={id_experiment}."
                    logger.exception(message)
            except Exception as ex:
                message = "Error archiving an experiment: demo={}, key={}. Error: {}."
                logger.exception(message.format(demo_id, key, str(ex)))

        # Save the execution, so the users can recover it from the URL
        core.save_execution(demo_id, clientData, demorunner_response, work_dir, form)

        messages = []
        messages.extend(prepare_folder_messages)

        return dict(demorunner_response, **{"messages": messages})
    except (IPOLDecodeInterfaceRequestError, IPOLUploadedInputRejectedError) as ex:
        return {"error": str(ex), "status": "KO"}
    except (IPOLDemoExtrasError, IPOLKeyError) as ex:
        error_message = str(ex)
        core.send_internal_error_email(error_message)
        logger.exception(error_message)
        return {"error": error_message, "status": "KO"}
    except IPOLEnsureCompilationError as ex:
        error_message = " --- Compilation error. --- {}".format(str(ex))
        core.send_compilation_error_email(demo_id, error_message, dr_name)
        return {"error": str(ex), "status": "KO"}
    except IPOLFindSuitableDR as ex:
        try:
            if core.get_demo_metadata(demo_id).json()["state"].lower() == "published":
                core.send_email_no_demorunner(demo_id)
        except BrokenPipeError:
            pass

        error_message = str(ex)
        logger.exception(error_message)
        return {"error": error_message, "status": "KO"}
    except IPOLWorkDirError as ex:
        error_message = "Could not create work_dir for demo {}".format(demo_id)
        # do not output full path for public
        internal_error_message = (error_message + ". Error: {}").format(str(ex))
        logger.exception(internal_error_message)
        core.send_internal_error_email(internal_error_message)
        return {"error": error_message, "status": "KO"}
    except IPOLReadDDLError as ex:
        # code -1: the DDL of the requested ID doesn't exist
        # code -2: Invalid demo_id
        error_message = "{} Demo #{}".format(str(ex.error_message), demo_id)
        logger.exception(error_message)
        if not ex.error_code or ex.error_code not in (-1, -2):
            core.send_internal_error_email(error_message)
        return {"error": error_message, "status": "KO"}
    except IPOLCheckDDLError as ex:
        error_message = "{} Demo #{}".format(str(ex), demo_id)
        if core.get_demo_metadata(demo_id)["state"].lower() == "published":
            core.send_runtime_error_email(demo_id, "<NA>", error_message, "no-dr")
        return {"error": error_message, "status": "KO"}
    except IPOLPrepareFolderError as ex:
        # Do not log: function prepare_folder_for_execution will decide when to log
        if ex.email_message:
            core.send_internal_error_email(ex.email_message)
        return {"error": ex.interface_message, "status": "KO"}
    except IPOLExecutionError as ex:
        # Do not log: function execute_experiment will decide when to log
        if ex.email_message:
            core.send_internal_error_email(ex.email_message)
        return {"error": ex.interface_message, "status": "KO"}
    except IPOLEvaluateError as ex:
        error_message = "IPOLEvaluateError '{}' detected in demo {}".format(
            str(ex), demo_id
        )
        logger.exception(error_message)
        core.send_internal_error_email(error_message)
        return {"error": error_message, "status": "KO"}
    except IPOLDemoRunnerResponseError as ex:
        # Send email to the editors
        # (unless it's a timeout in a published demo)
        if not (ex.demo_state == "published" and ex.error == "IPOLTimeoutError"):
            core.send_runtime_error_email(demo_id, ex.key, ex.message, dr_name)
        return {"error": ex.message, "status": "KO"}
    except Exception as ex:
        # We should never get here.
        #
        # If we arrive here it means that we missed to catch and
        # take care of some exception type.
        error_message = "**An internal error has occurred in the demo system, sorry for the inconvenience.\
            The IPOL team has been notified and will fix the issue as soon as possible.** \
                Error in the run function of the Core in demo {}, {}. Received clientData: {}".format(
            demo_id, ex, str(clientData)
        )
        print(traceback.format_exc())
        logger.exception(error_message)
        core.send_internal_error_email(error_message)
        return {"status": "KO", "error": error_message}


logger = init_logging()

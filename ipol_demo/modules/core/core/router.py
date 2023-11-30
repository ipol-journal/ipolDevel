import json
import os
import traceback

from archive import archive
from blobs import blobs
from config import settings
from core import core
from core.archive_utils import send_to_archive
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
from demoinfo import demoinfo
from fastapi import APIRouter, Depends, File, Form, HTTPException, Request, UploadFile
from fastapi.responses import HTMLResponse
from guards import validate_ip
from ipolutils.evaluator.evaluator import IPOLEvaluateError
from logger import logger
from result import Err, Ok

coreRouter = APIRouter(prefix="/core")
core = core.Core()
demoinfo = demoinfo.DemoInfo(
    dl_extras_dir=settings.demoinfo_dl_extras_dir,
    database_path=settings.demoinfo_db,
    base_url=settings.base_url,
)

blobs = blobs.Blobs()
archive = archive.Archive()


@coreRouter.get("/demo", status_code=201)
def demo(code_starts=None) -> HTMLResponse:
    """
    Return an HTML page with the list of demos.
    """
    html_content = core.index(code_starts=code_starts)
    return HTMLResponse(content=html_content, status_code=200)


@staticmethod
@coreRouter.get("/ping", status_code=200)
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
        result = demoinfo.delete_demo(demo_id)
        if not isinstance(result, Ok):
            error_message += f"Error when removing demo: {result.value} \n"

        result = demoinfo.delete_demoextras(demo_id)
        if not isinstance(result, Ok):
            error_message += f"Error when removing demoextras: {result.value} \n"

        delete_blobs = blobs.delete_blob_container({"dest": "demo", "demo_id": demo_id})
        if not delete_blobs:
            error_message += f"Blobs failed to delete demo {demo_id} related content.\n"

        # delete the archive
        resp = archive.delete_demo(demo_id)
        if isinstance(resp, Err):
            error_message += f"Archive failed to delete demo {demo_id} related content"

        if error_message:
            error = f"Failed to delete demo: {demo_id}."
            core.send_internal_error_email(error_message)
            raise HTTPException(status_code=500, detail=error)

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
            base_url = os.environ["IPOL_URL"]
            try:
                blobs, parameters, execution = send_to_archive(
                    demo_id,
                    work_dir,
                    clientData,
                    ddl["archive"],
                    demorunner_response,
                    base_url,
                    input_names,
                    form,
                )
                result = archive.create_experiment(
                    demo_id=demo_id,
                    blobs=blobs,
                    parameters=parameters,
                    execution=execution,
                )
                if isinstance(result, Err):
                    experiment_id = result.value["experiment_id"]
                    message = f"Error from archive module when archiving an experiment: demo={demo_id}, key={key}, id={experiment_id}."
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
            if core.get_demo_metadata(demo_id)["state"].lower() == "published":
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

#!/usr/bin/env python3
# -*- coding:utf-8 -*-

"""
The demoRunner module is responsible for running IPOL demos
"""

import codecs
import configparser
import errno
import io
import json
import logging
import os

# add lib path for import
import os.path
import re
import shlex
import shutil
import subprocess
import tempfile
import time
import urllib.error
import urllib.parse
import urllib.request
import zipfile
from string import Template
from subprocess import PIPE, Popen
from threading import Lock
from typing import Annotated, List, Optional

import Tools.build as build
import Tools.run_demo_base as run_demo_base
import virtualenv.run as virtualenv
from fastapi import (
    APIRouter,
    Body,
    Depends,
    FastAPI,
    File,
    HTTPException,
    Request,
    UploadFile,
    status,
)
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse, StreamingResponse
from pydantic import BaseModel, BaseSettings
from Tools.run_demo_base import IPOLTimeoutError


class Settings(BaseSettings):
    default_timeout = 60
    authorized_patterns: str = "authorized_patterns.conf"

    compilation_lock_filename: str = "ipol_construct.lock"

    main_bin_dir: str = os.path.join(
        os.path.dirname(os.path.realpath(__file__)), "binaries"
    )
    main_log_dir: str = "logs"
    share_demoExtras_dir: str = (
        os.path.expanduser("~") + "/ipolDevel/shared_folder/demoExtras"
    )
    extra_path: str = (
        os.path.expanduser("~")
        + "/ipolDevel/ipol_demo/modules/demorunner/venv/bin:/bin:/usr/bin:/usr/local/bin"
    )
    log_file: str = os.path.join(main_log_dir, "error_logs.log")

    config_common_dir: str = (
        os.path.expanduser("~") + "/ipolDevel/ipol_demo/modules/config_common"
    )
    MATLAB_path: str = "/usr/local/matlab/R2015b"


settings = Settings()
app = FastAPI(
    docs_url="/docs",
    openapi_url="/openapi.json",
    redoc_url=None,
)
lock_run = Lock()


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


private_route = APIRouter(dependencies=[Depends(validate_ip)])


class IPOLCompileError(Exception):
    """
    IPOLCompileError
    """


def mkdir_p(path):
    """
    Implement the UNIX shell command "mkdir -p"
    with given path as parameter.
    """
    try:
        os.makedirs(path)
    except OSError as exc:
        if exc.errno == errno.EEXIST and os.path.isdir(path):
            pass
        else:
            raise


def init_logging():
    """
    Initialize the error logs of the module.
    """
    logger = logging.getLogger("demorunner")
    # handle all messages for the moment
    logger.setLevel(logging.DEBUG)
    handler = logging.StreamHandler()
    formatter = logging.Formatter(
        "%(asctime)s ERROR in %(message)s", datefmt="%Y-%m-%d %H:%M:%S"
    )
    handler.setFormatter(formatter)

    logger.addHandler(handler)
    return logger


#####
# web utilities
#####


@app.get("/ping", status_code=200)
def ping() -> dict[str, str]:
    """
    Ping service: answer with a pong.
    """
    return {"status": "OK", "ping": "pong"}


@app.on_event("shutdown")
def shutdown_event():
    logger.info("Application shutdown")


@app.get("/workload", status_code=200)
def get_workload() -> float:
    """
    Return the workload of this DR
    """
    # Command to obtain the workload for a specific user
    cmd = 'ps -eo %U,%C| grep ipol | cut -d "," -f2'
    try:
        # Get the workload
        processes, _ = subprocess.Popen(
            cmd,
            shell=True,
            executable="/bin/bash",
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        ).communicate()
        # Get the number of cores
        nproc, _ = subprocess.Popen(
            "nproc",
            shell=True,
            executable="/bin/bash",
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        ).communicate()
        total = 0.0
        # Get the total workload
        for process in processes.decode().split("\n"):
            if process != "":
                total += float(process)
        return total / float(nproc)
    except Exception:
        logger.exception("Could not get workload from the DR")
        return 100.0


def remove_path(path):
    """
    Removes from disk the given path (a file or a directory)
    """
    if os.path.isfile(path):
        os.remove(path)  # Remove file
    elif os.path.isdir(path):
        shutil.rmtree(path)  # Remove directories recursively


def construct(compilation_path, ddl_builds):
    """
    program build/update
    """
    dl_dir = os.path.join(compilation_path, "dl/")
    src_dir = os.path.join(compilation_path, "src/")
    bin_dir = os.path.join(compilation_path, "bin/")
    log_file = os.path.join(compilation_path, "build.log")
    try:
        mkdir_p(compilation_path)
        lock_path = os.path.join(compilation_path, settings.compilation_lock_filename)
        while construct_is_locked(lock_path):
            time.sleep(1)
        acquire_construct_lock(lock_path)

        # Ensure needed compilation folders do exist
        mkdir_p(dl_dir)
        extract_needed = any_extraction_needed(ddl_builds, dl_dir)
        if extract_needed:
            if os.path.isdir(bin_dir):
                shutil.rmtree(bin_dir)
        mkdir_p(bin_dir)

        for build_item in list(ddl_builds.values()):
            # These are mandatory
            url = build_item.get("url")
            if not url:
                raise IPOLCompileError(
                    f"Missing build item: url. ddl_build: {ddl_builds}"
                )

            files_to_move = build_item.get("move")
            if not files_to_move:
                raise IPOLCompileError(
                    f"Missing build item: move. ddl_build: {ddl_builds}"
                )

            zip_filename = urllib.parse.urlsplit(url).path.split("/")[-1]
            tgz_file = os.path.join(dl_dir, zip_filename)

            # Get files to move path
            files_path = []
            for f in files_to_move.split(","):
                files_path.append(
                    os.path.join(bin_dir, os.path.basename(f.strip("/ ")))
                )

            # Check if a rebuild is needed
            if extract_needed or not all_files_exist(files_path):
                if os.path.isdir(src_dir):
                    shutil.rmtree(src_dir)
                mkdir_p(src_dir)
                # Move to the compilation directory, in case the
                # instructions in the move directive have changed it
                os.chdir(src_dir)
                # Extract source code
                build.extract(tgz_file, src_dir)
                # Create virtualenv if specified by DDL
                if "virtualenv" in build_item:
                    create_venv(build_item, bin_dir, src_dir)

                construct = build_item.get("construct")
                if construct:
                    # Execute the construct
                    returncode = build.run(construct, log_file, cwd=src_dir)
                    if 0 != returncode:
                        raise IPOLCompileError

                # Move files
                for file_to_move in files_to_move.split(","):
                    # Remove possible white spaces
                    file_to_move = file_to_move.strip("/ ")
                    if not file_to_move:
                        continue

                    path_from = os.path.realpath(os.path.join(src_dir, file_to_move))
                    path_to = os.path.realpath(
                        os.path.join(bin_dir, os.path.basename(file_to_move))
                    )
                    src_path = os.path.realpath(src_dir)
                    bin_path = os.path.realpath(bin_dir)

                    if not path_from.startswith(src_path) or not path_to.startswith(
                        bin_path
                    ):
                        raise IPOLCompileError(
                            f"Construct failed: unauthorized access. Move: {file_to_move}"
                        )

                    # Check origin
                    if not os.path.exists(path_from):
                        raise IPOLCompileError(
                            f"Construct failed. File not found. Construct can't move file since it doesn't exist: {path_from}"
                        )

                    try:
                        # Remove path_to if it exists
                        remove_path(path_to)
                        # Do move
                        shutil.move(path_from, path_to)
                    except (IOError, OSError):
                        logger.error(
                            f"construct: Can't move file {path_from} --> {path_to}",
                        )
                        # If can't move, write in the log file, so
                        # the user can see it
                        f = open(log_file, "w")
                        f.write(f"Failed to move {path_from} --> {path_to}")
                        f.close()
                        raise
    finally:
        release_lock(lock_path)


def construct_is_locked(lock_path):
    """
    Check if compilation path is locked
    """
    if os.path.isfile(lock_path):
        current_time = time.time()
        creation_time = os.path.getctime(lock_path)
        # In case of error it might leave dangling lockfiles, remove it if it's old.
        if current_time - creation_time >= 20 * 60:
            release_lock(lock_path)
            return False
        return True
    return False


def acquire_construct_lock(lock_path):
    """
    Create compilation path lock in order to protect against simultaneous compilations
    """
    open(lock_path, "w+").close()


def release_lock(lock_path):
    """
    Releases (removes) a lock given its path
    """
    try:
        os.remove(lock_path)
    except FileNotFoundError:
        pass


def any_extraction_needed(ddl_builds, dl_dir):
    """
    Check if binaries should be extracted
    """
    extract_needed = False
    for build_item in list(ddl_builds.values()):
        url = build_item.get("url")
        if not url:
            raise IPOLCompileError(f"Missing build item: url. ddl_build: {ddl_builds}")
        username = build_item.get("username")
        password = build_item.get("password")
        zip_filename = urllib.parse.urlsplit(url).path.split("/")[-1]
        tgz_file = os.path.join(dl_dir, zip_filename)
        if build.download(url, tgz_file, username, password):
            extract_needed = True
    return extract_needed


def all_files_exist(files):
    """
    Checks if all given file names exist
    """
    return all([os.path.isfile(f) or os.path.isdir(f) for f in files])


class SSHKeys(BaseModel):
    public_key: str
    private_key: str


@app.post("/compilations/{demo_id}", status_code=201)
def ensure_compilation(
    demo_id: int,
    ddl_build: Annotated[dict, Body()],
    ssk_keys: Optional[SSHKeys] = None,
) -> None:
    """
    Ensures that the source codes of the given demo are compiled and
    moved correctly.
    """
    compilation_path = os.path.join(settings.main_bin_dir, str(demo_id))
    mkdir_p(compilation_path)
    try:
        if "build1" in ddl_build:
            # we should have a dict or a list of dict
            compile_source(ddl_build, compilation_path)
            return
        message = f"Bad build syntax: 'build1' not found. Build: {str(ddl_build)}"
    except IPOLCompileError as ex:
        message = f"Demo #{demo_id} could not compile \n{ex}"

        build_filename = "build.log"
        log_file = os.path.join(compilation_path, build_filename)

        if os.path.isfile(log_file):
            log_content = read_workdir_file(compilation_path, build_filename)
        else:
            log_content = ""
        response = {"message": message, "buildlog": log_content}
        raise HTTPException(status_code=500, detail=response)

    except urllib.error.HTTPError as ex:
        logger.exception("ensure_compilation - HTTPError")

        build_name = list(ddl_build.keys())[0]
        if "password" in ddl_build[build_name]:
            ddl_build[build_name]["password"] = "*****"
            ddl_build[build_name]["username"] = "*****"
        message = f"{ex}, ddl_build: {ddl_build}"

    except urllib.error.URLError:
        message = "Construct failed. Could not reach the source code."

    except EnvironmentError as ex:
        message = f"Construct failed. Environment error. {str(ex)}"

    except ValueError as ex:
        message = f"Construct failed. Bad value: {str(ex)}"

    except Exception as ex:
        message = f"INTERNAL ERROR in ensure_compilation. {ex}"
        logger.exception(f"INTERNAL ERROR in ensure_compilation, demo {demo_id}")

    raise HTTPException(status_code=500, detail=message)


@private_route.post("/compilations", status_code=201)
def test_compilation(ddl_build, compilation_path) -> None:
    """
    Test the compilation in a test path, not in the demo path
    """
    ddl_build = json.loads(ddl_build)
    try:
        if os.path.isdir(compilation_path):
            shutil.rmtree(compilation_path)
        if "build1" in ddl_build:
            compile_source(ddl_build, compilation_path)
        else:
            message = f"Bad build syntax: 'build1' not found. Build: {ddl_build}"
            raise HTTPException(status_code=404, detail=message)

    except IPOLCompileError as ex:
        message = ex
        raise HTTPException(status_code=404, detail=message)


@app.delete("/compilations/{demo_id}", status_code=204)
def delete_compilation(demo_id: int) -> None:
    """
    Remove compilation folder if exists
    """
    compilation_path = os.path.join(settings.main_bin_dir, str(demo_id))
    if os.path.isdir(compilation_path):
        shutil.rmtree(compilation_path)


def compile_source(ddl_build, compilation_path):
    """
    Do the compilation
    """
    # we should have a dict or a list of dict
    if isinstance(ddl_build, dict):
        builds = [ddl_build]
    else:
        builds = ddl_build

    for build_block in builds:
        construct(compilation_path, build_block)


def create_venv(build_item, bin_dir, src_dir):
    """
    Create a virtualEnv and install the requirements specified within the source code
    """
    packages_file = build_item["virtualenv"]
    venv_path = os.path.join(bin_dir, "venv")
    pip_bin = os.path.join(venv_path, "bin/pip")
    virtualenv.cli_run([venv_path])

    cmd = [pip_bin, "install", "-r", os.path.join(src_dir, packages_file)]
    cmd = shlex.split(" ".join(cmd))
    install_proc = Popen(cmd, stdout=PIPE, stderr=PIPE)
    _, stderr_data = install_proc.communicate()

    if install_proc.returncode != 0:
        raise IPOLCompileError(
            f"Construct failed. Can't create virtualenv:\n{stderr_data}"
        )


# ---------------------------------------------------------------------------
# Algorithm runner
# ---------------------------------------------------------------------------
def run_algo(
    demo_id: int,
    work_dir: str,
    bin_path: str,
    ddl_run: str,
    params: dict,
    res_data: dict,
    timeout: int,
) -> int:
    """
    the core algo runner
    """
    lock_path = os.path.join(bin_path, settings.compilation_lock_filename)
    while construct_is_locked(lock_path):
        time.sleep(1)
    rd = run_demo_base.RunDemoBase(bin_path, work_dir, logger, timeout)
    rd.set_algo_params(params)
    rd.set_algo_info(res_data["algo_info"])
    rd.set_MATLAB_path(settings.MATLAB_path)
    rd.set_extra_path(settings.extra_path)
    rd.set_demo_id(demo_id)
    rd.set_commands(ddl_run)

    rd.set_share_demoExtras_dirs(settings.share_demoExtras_dir, demo_id)

    if not isinstance(ddl_run, str):
        return -1  # Bad run syntax: not a string

    # Substitute variables and run algorithm
    cmd = variable_substitution(ddl_run, demo_id, params)

    rd.run_algorithm(cmd, lock_run)

    res_data["params"] = rd.get_algo_params()  # Should not be used
    # Info interface --> algo
    res_data["algo_info"] = rd.get_algo_info()
    return 0


def variable_substitution(ddl_run: str, demo_id: int, params: dict) -> str:
    """
    Replace the variables with its values and return the command to be executed
    """
    params["demoextras"] = os.path.join(settings.share_demoExtras_dir, str(demo_id))
    params["matlab_path"] = settings.MATLAB_path
    params["bin"] = get_bin_dir(demo_id)
    params["virtualenv"] = get_bin_dir(demo_id) + "venv"
    return Template(ddl_run).substitute(**params)


def get_bin_dir(demo_id: int) -> str:
    """
    Returns the directory with the peer-reviewed author programs
    """
    return os.path.join(settings.main_bin_dir, f"{demo_id}/bin/")


def read_workdir_file(work_dir: str, filename: str) -> str:
    """
    Read a text file from the working directory and return its contents as UTF-8
    """
    full_file = os.path.join(work_dir, filename)
    content = ""
    if os.path.isfile(full_file):
        with codecs.open(full_file, "r", "utf8", errors="replace") as f:
            content = f.read()
    return content


@app.post("/exec_and_wait/{demo_id}", status_code=200)
async def exec_and_wait(
    demo_id: int,
    key: str,
    ddl_run: str,
    parameters: str,
    files: Annotated[List[UploadFile], File()],
    timeout: int = settings.default_timeout,
) -> UploadFile:
    """
    Run the algorithm
    """
    parameters = json.loads(parameters)

    work_dir_handle = tempfile.TemporaryDirectory()
    work_dir = work_dir_handle.name

    for input in files:
        assert ".." not in input.filename
        path = os.path.join(work_dir, input.filename)
        dirname = os.path.dirname(path)
        os.makedirs(dirname, exist_ok=True)
        open(path, "wb").write(input.file.read())

    path_with_the_binaries = os.path.join(settings.main_bin_dir, f"{demo_id}/")
    res_data = {}
    res_data["key"] = key
    res_data["params"] = parameters
    res_data["algo_info"] = {}
    # run the algorithm
    try:
        run_time = time.time()
        # A maximum of 10 min, regardless the config
        timeout = min(timeout, 10 * 60)
        # At least five seconds
        timeout = max(timeout, 5)

        # Run algorithm and control exceptions
        code = run_algo(
            demo_id,
            work_dir,
            path_with_the_binaries,
            ddl_run,
            parameters,
            res_data,
            timeout,
        )

        if code == -1:  # Bad run syntax
            logger.error(f"exec_and_wait: Bad run syntax, demo_id={demo_id}")
            err = "Bad run syntax (not a string): {}".format(str(ddl_run))
            res_data["error"] = err
            res_data["algo_info"]["error_message"] = err
        else:
            res_data["algo_info"]["error_message"] = " "
            res_data["algo_info"]["run_time"] = time.time() - run_time

    except IPOLTimeoutError:
        res_data["error"] = "IPOLTimeoutError"
        res_data["algo_info"][
            "error_message"
        ] = "IPOLTimeoutError, Timeout={} s".format(timeout)
        logger.error(f"exec_and_wait IPOLTimeoutError, demo_id={demo_id}")
    except RuntimeError as ex:
        # Read stderr and stdout
        stderr_content = read_workdir_file(work_dir, "stderr.txt")
        stdout_content = read_workdir_file(work_dir, "stdout.txt")
        # Put them in the message for the web interface
        res_data["algo_info"][
            "error_message"
        ] = "Runtime error\n\
stderr: {}\nstdout: {}".format(
            stderr_content, stdout_content
        )
        res_data["error"] = str(ex)
        logger.error(res_data)

    except OSError as ex:
        error_str = "{} - errno={}, filename={}, ddl_run={}".format(
            str(ex), ex.errno, ex.filename, ddl_run
        )
        logger.error(f"exec_and_wait: OSError, demo_id={demo_id}, {error_str}")
        res_data["algo_info"]["error_message"] = error_str
        res_data["error"] = error_str
    except KeyError as ex:
        error_str = "KeyError. Hint: variable not defined? - {}, ddl_run={}".format(
            str(ex), ddl_run
        )
        logger.error(f"exec_and_wait: KeyError, demo_id={demo_id}, {error_str}")
        res_data["algo_info"]["error_message"] = error_str
        res_data["error"] = error_str
    except Exception as ex:
        error_str = "Uncatched Exception, demo_id={}".format(demo_id)
        logger.exception(error_str)
        res_data["algo_info"]["error_message"] = error_str
        res_data["error"] = "Error: {}".format(ex)

    # write in exec_info.json the status of the execution (error if any, run time, ...)
    open(os.path.join(work_dir, "exec_info.json"), "w").write(json.dumps(res_data))

    # create a zip in memory containing all the files in work_dir,
    # including the input files sent in the payload to the execution,
    # and additional files such as stdout.txt, stderr.txt and exec_info.json
    fd = io.BytesIO()
    with zipfile.ZipFile(fd, "w", zipfile.ZIP_STORED) as zip:
        for root, _, files in os.walk(work_dir):
            for zip_file in files:
                path = os.path.join(root, zip_file)
                in_zip_path = path.replace(work_dir, "./")
                zip.write(path, in_zip_path)

    # send the zip as the reply to the request
    fd.seek(0)
    return StreamingResponse(
        fd,
        media_type="application/zip",
        headers={"Content-Disposition": "attachment;filename=uploaded_files.zip"},
    )


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


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    exc_str = f"{exc}".replace("   ", " ")
    logging.error(f"{request}: {exc_str}")
    logging.error(f"{request.path_params}")

    logging.error(f"{request.query_params}")
    content = {"status_code": 10422, "message": exc_str, "data": None}
    return JSONResponse(
        content=content, status_code=status.HTTP_422_UNPROCESSABLE_ENTITY
    )


app.include_router(private_route)

mkdir_p(settings.main_bin_dir)
mkdir_p(settings.main_log_dir)

logger = init_logging()

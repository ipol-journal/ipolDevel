#!/usr/bin/env python3
# -*- coding:utf-8 -*-

"""
The demoRunner module is responsible for running IPOL demos
"""

import codecs
import configparser
import errno
import json
import logging
import os
# add lib path for import
import os.path
import re
import shlex
import shutil
import subprocess
import time
import urllib.error
import urllib.parse
import urllib.request
from string import Template
from subprocess import PIPE, Popen
from threading import Lock

import cherrypy
import Tools.build as build
import Tools.run_demo_base as run_demo_base
import virtualenv
from Tools.run_demo_base import IPOLTimeoutError


class IPOLMissingBuildItem(Exception):
    """
    IPOLMissingBuildItem
    """

class IPOLConstructFileNotFound(Exception):
    """
    IPOLConstructFileNotFound
    """

class IPOLUnauthorizedAccess(Exception):
    """
    IPOLUnauthorizedAccess
    """

class IPOLConstructVirtualenvError(Exception):
    """
    IPOLConstructVirtualenvError
    """

def authenticate(func):
    '''
    Wrapper to authenticate before using an exposed function
    '''

    def authenticate_and_call(*args, **kwargs):
        """
        Invokes the wrapped function if authenticated
        """
        if "X-Real-IP" in cherrypy.request.headers \
                and is_authorized_ip(cherrypy.request.headers["X-Real-IP"]):
            return func(*args, **kwargs)
        error = {"status": "KO", "error": "Authentication Failed"}
        return json.dumps(error).encode()

    def is_authorized_ip(ip):
        """
        Validates the given IP
        """
        demorunner = DemoRunner.get_instance()
        patterns = []
        # Creates the patterns  with regular expressions
        for authorized_pattern in demorunner.authorized_patterns:
            patterns.append(re.compile(authorized_pattern.replace(
                ".", "\\.").replace("*", "[0-9a-zA-Z]+")))
        # Compare the IP with the patterns
        for pattern in patterns:
            if pattern.match(ip) is not None:
                return True
        return False

    return authenticate_and_call


class DemoRunner():
    """
    This class implements Web services to run IPOL demos
    """

    instance = None
    last_execution = {'demo_id': 0, 'key': '---', 'date': '---'}

    @staticmethod
    def get_instance():
        '''
        Singleton pattern
        '''
        if DemoRunner.instance is None:
            DemoRunner.instance = DemoRunner()
        return DemoRunner.instance


    @staticmethod
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

    def init_logging(self):
        """
        Initialize the error logs of the module.
        """
        logger = logging.getLogger("core_log")
        logger.setLevel(logging.ERROR)
        handler = logging.FileHandler(self.log_file)
        formatter = logging.Formatter('%(asctime)s ERROR in %(message)s', datefmt='%Y-%m-%d %H:%M:%S')
        handler.setFormatter(formatter)
        logger.addHandler(handler)
        return logger

    def write_log(self, function_name, message):
        """
        Write an error log in the logs_dir defined in proxy.conf
        """
        log_string = "{}: {}".format(function_name, message)
        #
        self.logger.error(log_string)


    def __init__(self):
        """
        Initialize DemoRunner
        """
        self.lock_run = Lock()

        base_dir = os.path.dirname(os.path.realpath(__file__))
        self.share_running_dir = cherrypy.config['share.running.dir']
        self.main_bin_dir = os.path.join(base_dir, cherrypy.config['main.bin.dir'])
        self.main_log_dir = cherrypy.config['main.log.dir']
        self.main_log_name = cherrypy.config['main.log.name']
        self.share_demoExtras_dir = cherrypy.config['share.demoExtras.dir']
        self.MATLAB_path = cherrypy.config['demo.matlab_path']
        self.extra_path = cherrypy.config['demo.extra_path']
        self.log_file = os.path.join(self.main_log_dir, self.main_log_name)

        self.png_compresslevel = 1
        self.stack_depth = 0

        self.mkdir_p(self.main_bin_dir)
        self.mkdir_p(self.main_log_dir)

        self.logger = self.init_logging()
        self.config_common_dir = cherrypy.config.get("config_common_dir")

        # Security: authorized IPs
        self.authorized_patterns = self.read_authorized_patterns()
        if not os.path.isdir(self.share_running_dir):
            error_message = "The folder does not exist: " + self.share_running_dir
            self.write_log("__init__", error_message)
            print(error_message)


    #####
    # web utilities
    #####


    def read_authorized_patterns(self):
        '''
        Read from the IPs conf file
        '''
        # Check if the config file exists
        authorized_patterns_path = os.path.join(self.config_common_dir, "authorized_patterns.conf")
        if not os.path.isfile(authorized_patterns_path):
            self.write_log("read_authorized_patterns",
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

    @staticmethod
    @cherrypy.expose
    def index():
        """
        HTML presentation page
        """
        return "This is the IPOL DemoRunner module"

    @staticmethod
    @cherrypy.expose
    def ping():
        """
        Ping service: answer with a PONG.
        """
        data = {}
        data["status"] = "OK"
        data["ping"] = "pong"
        return json.dumps(data).encode()

    @cherrypy.expose
    @authenticate
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
            self.write_log("shutdown", str(ex))
        return json.dumps(data).encode()

        # ---------------------------------------------------------------------------

    @staticmethod
    @cherrypy.expose
    def default(attr):
        """
        Default method invoked when asked for non-existing service.
        """
        data = {}
        data["status"] = "KO"
        data["message"] = "Unknown service '{}'".format(attr)
        return json.dumps(data).encode()


    @cherrypy.expose
    def get_workload(self):
        """
        Return the workload of this DR
        """
        data = {}
        data["status"] = "OK"
        # Command to obtain the workload for a specific user
        cmd = 'ps -eo %U,%C| grep ipol | cut -d "," -f2'
        try:
            # Get the workload
            processes, _ = subprocess.Popen(cmd, shell=True, executable="/bin/bash", stdout=subprocess.PIPE,
                                            stderr=subprocess.PIPE).communicate()
            # Get the number of cores
            nproc, _ = subprocess.Popen("nproc", shell=True, executable="/bin/bash", stdout=subprocess.PIPE,
                                        stderr=subprocess.PIPE).communicate()
            total = 0.0
            # Get the total workload
            for process in processes.decode().split("\n"):
                if process != "":
                    total += float(process)
            data['workload'] = total / float(nproc)
        except Exception as ex:
            data["status"] = "KO"
            self.logger.exception("Could not get workload from the DR")
            print("Could not get workload from the DR -", ex)

        return json.dumps(data).encode()

    @cherrypy.expose
    def get_stats(self):
        '''
        Get statistics of the module
        '''
        try:
            response = {}
            response['status'] = 'OK'
            response['demo_id'] = self.last_execution['demo_id']
            response['key'] = self.last_execution['key']
            response['date'] = self.last_execution['date']
            return json.dumps(response).encode()
        except Exception:
            return json.dumps({'status': 'KO'}).encode()


    @staticmethod
    def remove_path(path):
        '''
        Removes from disk the given path (a file or a directory)
        '''
        if os.path.isfile(path):
            os.remove(path) # Remove file
        elif os.path.isdir(path):
            shutil.rmtree(path) # Remove directories recursively


    def construct(self, compilation_path, ddl_builds):
        """
        program build/update
        """
        dl_dir = os.path.join(compilation_path, 'dl/')
        src_dir = os.path.join(compilation_path, 'src/')
        bin_dir = os.path.join(compilation_path, 'bin/')
        log_file = os.path.join(compilation_path, 'build.log')
        try:
            self.mkdir_p(compilation_path)
            while self.construct_is_locked(compilation_path):
                time.sleep(1)
            self.acquire_construct_lock(compilation_path)
            
            # Ensure needed compilation folders do exist
            self.mkdir_p(dl_dir)
            extract_needed = self.any_extraction_needed(ddl_builds, dl_dir)
            if extract_needed:
                if os.path.isdir(bin_dir):
                    shutil.rmtree(bin_dir)
            self.mkdir_p(bin_dir)

            for build_item in list(ddl_builds.values()):
                # These are mandatory
                url = build_item.get('url')
                if not url:
                    raise IPOLMissingBuildItem("url")

                files_to_move = build_item.get('move')
                if not files_to_move:
                    raise IPOLMissingBuildItem("move")

                zip_filename = urllib.parse.urlsplit(url).path.split('/')[-1]
                tgz_file = os.path.join(dl_dir, zip_filename)

                # Get files to move path
                files_path = []
                for f in files_to_move.split(","):
                    files_path.append(os.path.join(bin_dir, os.path.basename(f.strip())))

                # Check if a rebuild is needed
                if extract_needed or not self.all_files_exist(files_path):
                    if os.path.isdir(src_dir):
                        shutil.rmtree(src_dir)
                    self.mkdir_p(src_dir)
                    # Move to the compilation directory, in case the
                    # instructions in the move directive have changed it
                    os.chdir(src_dir)
                    # Extract source code
                    build.extract(tgz_file, src_dir)

                    # Create virtualenv if specified by DDL
                    if "virtualenv" in build_item:
                        self.create_venv(build_item, bin_dir, src_dir)

                    construct = build_item.get('construct')
                    if construct:
                        # Execute the construct
                        build.run(construct, log_file, cwd=src_dir)

                    # Move files
                    for file_to_move in files_to_move.split(","):
                        # Remove possible white spaces
                        file_to_move = file_to_move.strip()

                        path_from = os.path.realpath(os.path.join(src_dir, file_to_move))
                        path_to = os.path.realpath(os.path.join(bin_dir, os.path.basename(file_to_move)))

                        src_path = os.path.realpath(src_dir)
                        bin_path = os.path.realpath(bin_dir)

                        if not path_from.startswith(src_path) or not path_to.startswith(bin_path):
                            raise IPOLUnauthorizedAccess(file_to_move)


                        # Check origin
                        if not os.path.exists(path_from):
                            raise IPOLConstructFileNotFound(\
    "Construct can't move file since it doesn't exist: {}".\
    format(path_from))

                        try:
                            # Remove path_to if it exists
                            self.remove_path(path_to)
                            # Do move
                            shutil.move(path_from, path_to)
                        except (IOError, OSError):
                            os.remove(os.path.join(compilation_path, 'ipol_construct.lock'))
                            self.write_log("construct", "Can't move file {} --> {}".format(path_from, path_to))
                            # If can't move, write in the log file, so
                            # the user can see it
                            f = open(log_file, 'w')
                            f.write("Failed to move {} --> {}".\
                                format(path_from, path_to))
                            f.close()
                            raise
        finally:
            os.remove(os.path.join(compilation_path, 'ipol_construct.lock'))

    @staticmethod
    def construct_is_locked(compilation_path):
        lock_filepath = os.path.join(compilation_path, 'ipol_construct.lock')
        if os.path.isfile(lock_filepath):
            current_time = time.time()
            creation_time = os.path.getctime(lock_filepath)
            if current_time - creation_time >= 3600:
                os.remove(lock_filepath)
                return False
            return True
        return False

    @staticmethod
    def acquire_construct_lock(compilation_path):
        lock_file = open(os.path.join(compilation_path,'ipol_construct.lock'),'w+')
        lock_file.close()


    @staticmethod
    def any_extraction_needed(ddl_builds, dl_dir):
        """
        Check if binaries should be extracted
        """
        extract_needed = False
        for build_item in list(ddl_builds.values()):
            url = build_item.get('url')
            if not url:
                raise IPOLMissingBuildItem("url")
            username = build_item.get('username')
            password = build_item.get('password')
            zip_filename = urllib.parse.urlsplit(url).path.split('/')[-1]
            tgz_file = os.path.join(dl_dir, zip_filename)
            if build.download(url, tgz_file, username, password):
                extract_needed = True
        return extract_needed

    @staticmethod
    def all_files_exist(files):
        '''
        Checks if all given file names exist
        '''
        return all([os.path.isfile(f) or os.path.isdir(f) \
          for f in files])


    @cherrypy.expose
    def ensure_compilation(self, demo_id, ddl_build):
        """
        Ensures that the source codes of the given demo are compiled and
        moved correctly.
        """
        ddl_build = json.loads(ddl_build)

        compilation_path = os.path.join(self.main_bin_dir, demo_id)
        self.mkdir_p(compilation_path)
        try:
            if 'build1' in ddl_build:
                # we should have a dict or a list of dict
                self.compile_source(ddl_build, compilation_path)
            else:
                data = {}
                data['status'] = 'KO'
                data['message'] = "Bad build syntax: 'build1' not found. \
Build: {}".format(str(ddl_build))
                return json.dumps(data).encode()
            data = {}
            data['status'] = "OK"
            data['message'] = "Build of demo {0} OK".format(demo_id)

        except build.IPOLHTTPMissingHeader as ex:
            data = {}
            data['status'] = 'KO'
            data['message'] = "Incomplete HTTP response. {}. Hint: do not use GitHub, \
GitLab, or Dropbox as a file server.\nddl_build: {}".\
format(str(ex), str(ddl_build))

        except IPOLMissingBuildItem as ex:
            data = {}
            data['status'] = 'KO'
            data['message'] = "Missing build item: {}. ddl_build: {}".\
format(str(ex), str(ddl_build))

        except urllib.error.HTTPError as ex:
            print("HTTPError")
            self.logger.exception("ensure_compilation - HTTPError")
            data = {}

            build_name = list(ddl_build.keys())[0]
            if 'password' in ddl_build[build_name]:
                ddl_build[build_name]['password'] = "*****"
                ddl_build[build_name]['username'] = "*****"
            data['status'] = 'KO'
            data['message'] = "{}, ddl_build: {}".format(str(ex), str(ddl_build))

        except urllib.error.URLError as ex:
            data = {}
            data['status'] = 'KO'
            data['message'] = "Construct failed. Could not reach the source code."

        except build.IPOLCompilationError as ex:
            print("Build failed with exception " + str(ex) + " in demo " + demo_id)

            build_filename = 'build.log'
            log_file = os.path.join(compilation_path, build_filename)

            if os.path.isfile(log_file):
                content = DemoRunner.read_workdir_file(compilation_path, build_filename)
            else:
                content = ""

            data = {}
            data['status'] = 'KO'
            data['message'] = "Build for demo #{} failed".format(demo_id)
            data['buildlog'] = content

        except IPOLConstructFileNotFound as ex:
            data = {}
            data['status'] = 'KO'
            data['message'] = "Construct failed. File not found. {}".format(str(ex))

        except IPOLConstructVirtualenvError as ex:
            data = {}
            data['status'] = 'KO'
            data['message'] = "Construct failed. Can't create virtualenv:\n{}".format(str(ex))

        except IPOLUnauthorizedAccess as ex:
            data = {}
            data['status'] = 'KO'
            data['message'] = "Construct failed: unauthorized access. Move: {}".format(str(ex))

        except EnvironmentError as ex:
            data = {}
            data['status'] = 'KO'
            data['message'] = "Construct failed. Environment error. {}".format(str(ex))

        except ValueError as ex:
            data = {}
            data['status'] = 'KO'
            data['message'] = "Construct failed. Bad value: {}".format(str(ex))

        except Exception as ex:
            data = {}
            data['status'] = 'KO'
            data['message'] = "INTERNAL ERROR in ensure_compilation. {}".format(str(ex))
            self.logger.exception("INTERNAL ERROR in ensure_compilation, demo {}".format(demo_id))

        return json.dumps(data).encode()


    @cherrypy.expose
    @authenticate
    def test_compilation(self, ddl_build, compilation_path):
        """
        Test the compilation in a test path, not in the demo path
        """
        data = {'status':'KO'}
        ddl_build = json.loads(ddl_build)
        try:
            if os.path.isdir(compilation_path):
                shutil.rmtree(compilation_path)
            if 'build1' in ddl_build:
                self.compile_source(ddl_build, compilation_path)
            else:
                data['status'] = 'KO'
                data['error'] = "Bad build syntax: 'build1' not found. Build: {}".format(str(ddl_build))
                return json.dumps(data).encode()

            data['status'] = 'OK'
        except Exception:
            data['status'] = 'KO'
        return json.dumps(data).encode()

    @cherrypy.expose
    def delete_compilation(self, demo_id):
        """
        Remove compilation folder if exists
        """
        path_of_the_compilation = os.path.join(self.main_bin_dir, demo_id)
        try:
            if os.path.isdir(path_of_the_compilation):
                shutil.rmtree(path_of_the_compilation)
        except Exception as ex:
            self.logger.exception("Exception trying to delete the compilation folder, demo {}. {}".format(demo_id, str(ex)))

    def compile_source(self, ddl_build, compilation_path):
        """
        Do the compilation
        """
        # we should have a dict or a list of dict
        if isinstance(ddl_build, dict):
            builds = [ddl_build]
        else:
            builds = ddl_build

        for build_block in builds:
            self.construct(compilation_path, build_block)

    @staticmethod
    def create_venv(build_item, bin_dir, src_dir):
        """
        Create a virtualEnv and install the requirements specified within the source code
        """
        packages_file = build_item["virtualenv"]
        venv_path = os.path.join(bin_dir, "venv")
        pip_bin = os.path.join(venv_path, "bin/pip")
        virtualenv.create_environment(venv_path)

        cmd = [pip_bin, "install", "-r", os.path.join(src_dir, packages_file)]
        cmd = shlex.split(" ".join(cmd))
        install_proc = Popen(cmd, stdout=PIPE, stderr=PIPE)
        _, stderr_data = install_proc.communicate()

        if install_proc.returncode != 0:
            raise IPOLConstructVirtualenvError(stderr_data)

    # ---------------------------------------------------------------------------
    # Algorithm runner
    # ---------------------------------------------------------------------------
    def run_algo(self, demo_id, work_dir, bin_path, ddl_run, params, res_data, timeout):
        """
        the core algo runner
        """
        while self.construct_is_locked(bin_path):
            time.sleep(1)
        rd = run_demo_base.RunDemoBase(bin_path, work_dir, self.logger, timeout)
        rd.set_algo_params(params)
        rd.set_algo_info(res_data['algo_info'])
        rd.set_MATLAB_path(self.MATLAB_path)
        rd.set_extra_path(self.extra_path)
        rd.set_demo_id(demo_id)
        rd.set_commands(ddl_run)

        rd.set_share_demoExtras_dirs(self.share_demoExtras_dir, demo_id)

        if not isinstance(ddl_run, str):
            return -1 # Bad run syntax: not a string

        # Substitute variables and run algorithm
        cmd = self.variable_substitution(ddl_run, demo_id, params)
        rd.run_algorithm(cmd, self.lock_run)

        res_data['params'] = rd.get_algo_params() # Should not be used
        # Info interface --> algo
        res_data['algo_info'] = rd.get_algo_info()
        return 0

    def variable_substitution(self, ddl_run, demo_id, params):
        """
        Replace the variables with its values and return the command to be executed
        """
        params["demoextras"] = os.path.join(self.share_demoExtras_dir, demo_id)
        params["matlab_path"] = self.MATLAB_path
        params["bin"] = self.get_bin_dir(demo_id)
        params["virtualenv"] = self.get_bin_dir(demo_id) + "venv"
        return Template(ddl_run).substitute(**params)

    def get_bin_dir(self, demo_id):
        '''
        Returns the directory with the peer-reviewed author programs
        '''
        return os.path.join(self.main_bin_dir, demo_id, 'bin/')

    @staticmethod
    def read_workdir_file(work_dir, filename):
        '''
        Read a text file from the working directory and return its contents as UTF-8
        '''
        full_file = os.path.join(work_dir, filename)
        content = ""
        if os.path.isfile(full_file):
            with codecs.open(full_file, "r", "utf8", errors="replace") as f:
                content = f.read()
        return content

    @cherrypy.expose
    def exec_and_wait(self, demo_id, key, params, ddl_run, timeout=60):
        '''
        Run the algorithm
        '''

        # Statistics
        self.last_execution['demo_id'] = demo_id
        self.last_execution['key'] = key
        self.last_execution['date'] = time.strftime("%d/%m/%Y at %H:%M:%S")

        ddl_run = json.loads(ddl_run)
        params = json.loads(params)
        path_with_the_binaries = os.path.join(self.main_bin_dir, demo_id + "/")
        work_dir = os.path.join(self.share_running_dir, demo_id + '/' + key + "/")
        res_data = {}
        res_data["key"] = key
        res_data['params'] = params
        res_data['algo_info'] = {}
        # run the algorithm
        try:
            if not os.path.isdir(work_dir):
                res_data['status'] = 'KO'
                err = 'Work directory does not exist: {}'.format(work_dir)
                res_data['error'] = err
                res_data['algo_info']['error_message'] = err
                return json.dumps(res_data).encode()

            run_time = time.time()
            timeout = float(timeout)
            # A maximum of 10 min, regardless the config
            timeout = min(timeout, 10*60)
            # At least five seconds
            timeout = max(timeout, 5)

            # Run algorithm and control exceptions
            code = self.run_algo(demo_id, work_dir, \
                                 path_with_the_binaries, \
                                 ddl_run, params, res_data, \
                                 timeout)

            if code == -1: # Bad run syntax
                self.write_log("exec_and_wait", "Bad run syntax, demo_id={}".format(demo_id))
                res_data['status'] = 'KO'
                err = "Bad run syntax (not a string): {}".format(str(ddl_run))
                res_data['error'] = err
                res_data['algo_info']['error_message'] = err
                return json.dumps(res_data).encode()

            res_data['algo_info']['error_message'] = " "
            res_data['algo_info']['run_time'] = time.time() - run_time
            res_data['status'] = 'OK'
            return json.dumps(res_data).encode()

        except IPOLTimeoutError:
            res_data['status'] = 'KO'
            res_data['error'] = 'IPOLTimeoutError'
            res_data['algo_info']['error_message'] = 'IPOLTimeoutError, Timeout={} s'.format(timeout)
            print("exec_and_wait IPOLTimeoutError, demo_id={}".format(demo_id))
            return json.dumps(res_data).encode()
        except RuntimeError as ex:
            # Read stderr and stdout
            stderr_content = self.read_workdir_file(work_dir, "stderr.txt")
            stdout_content = self.read_workdir_file(work_dir, "stdout.txt")
            # Put them in the message for the web interface
            res_data['algo_info']['error_message'] = 'Runtime error\n\
stderr: {}\nstdout: {}'.format(stderr_content, stdout_content)
            res_data['status'] = 'KO'
            res_data['error'] = str(ex)
            print(res_data)
            return json.dumps(res_data).encode()

        except OSError as ex:
            error_str = "{} - errno={}, filename={}, ddl_run={}".format(str(ex), ex.errno, ex.filename, ddl_run)
            self.write_log("exec_and_wait", "OSError, demo_id={}, {}".format(demo_id, error_str))
            res_data['status'] = 'KO'
            res_data['algo_info']['error_message'] = error_str
            res_data['error'] = error_str
            print(res_data)
            return json.dumps(res_data).encode()
        except KeyError as ex:
            error_str = "KeyError. Hint: variable not defined? - {}, ddl_run={}".format(str(ex), ddl_run)
            self.write_log("exec_and_wait", "KeyError, demo_id={}, {}".format(demo_id, error_str))
            res_data['status'] = 'KO'
            res_data['algo_info']['error_message'] = error_str
            res_data['error'] = error_str
            print(res_data)
            return json.dumps(res_data).encode()
        except Exception as ex:
            error_str = "Uncatched Exception, demo_id={}".format(demo_id)
            self.logger.exception(error_str)
            res_data['status'] = 'KO'
            res_data['algo_info']['error_message'] = error_str
            res_data['error'] = 'Error: {}'.format(ex)
            print(res_data)
            return json.dumps(res_data).encode()

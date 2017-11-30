#!/usr/bin/env python
# -*- coding:utf-8 -*-

"""
The demoRunner module is responsible for running IPOL demos
"""

# add lib path for import
import os.path
import os
import urllib2
import json
import shutil
import time
import subprocess
import errno
import logging
import urlparse
from string import Template
from threading import Lock
import ConfigParser
import re
import codecs
import cherrypy
import Tools.build as build
import Tools.run_demo_base as run_demo_base
from Tools.run_demo_base import IPOLTimeoutError


class IPOLMissingBuildItem(Exception):
    """
    IPOLMissingBuildItem
    """
    pass

class IPOLConstructFileNotFound(Exception):
    """
    IPOLConstructFileNotFound
    """
    pass

def authenticate(func):
    '''
    Wrapper to authenticate before using an exposed function
    '''

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
        '''
        Validates the given IP
        '''
        demorunner = DemoRunner.get_instance()
        patterns = []
        # Creates the patterns  with regular expresions
        for authorized_pattern in demorunner.authorized_patterns:
            patterns.append(re.compile(authorized_pattern.replace(".", "\\.").replace("*", "[0-9]*")))
        # Compare the IP with the patterns
        for pattern in patterns:
            if pattern.match(ip) is not None:
                return True
        return False

    return authenticate_and_call


class DemoRunner(object):
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
        created = 'false'
        try:
            os.makedirs(path)
            created = 'true'
        except OSError as exc:
            if exc.errno == errno.EEXIST and os.path.isdir(path):
                pass
            else:
                raise

        return created

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
        self.lock_construct = Lock()

        base_dir = os.path.dirname(os.path.realpath(__file__))
        self.share_running_dir = cherrypy.config['share.running.dir']
        self.main_bin_dir = os.path.join(base_dir, cherrypy.config['main.bin.dir'])
        self.main_log_dir = cherrypy.config['main.log.dir']
        self.main_log_name = cherrypy.config['main.log.name']
        self.share_demoExtras_dir = cherrypy.config['share.demoExtras.dir']
        self.MATLAB_path = cherrypy.config['demo.matlab_path']
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
            print error_message


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
            cfg = ConfigParser.ConfigParser()
            cfg.read([authorized_patterns_path])
            patterns = []
            for item in cfg.items('Patterns'):
                patterns.append(item[1])
            return patterns
        except ConfigParser.Error:
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
        return json.dumps(data)

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
        return json.dumps(data)

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
        return json.dumps(data)


    @cherrypy.expose
    def get_workload(self):
        """
        Return the workload of this DR
        """
        data = {}
        data["status"] = "OK"
        # Command to obtain the workload for a specific user
        cmd = "ps -eo %U,%C| grep ipol | cut -d \",\" -f2"
        try:
            # Get the workload
            processes, _ = subprocess.Popen(cmd + " &", shell=True, executable="/bin/bash", stdout=subprocess.PIPE,
                                            stderr=subprocess.PIPE).communicate()
            # Get the number of cores
            nproc, _ = subprocess.Popen("nproc &", shell=True, executable="/bin/bash", stdout=subprocess.PIPE,
                                        stderr=subprocess.PIPE).communicate()
            total = 0.0
            # Get the total workload
            for process in processes.split("\n"):
                if process != "":
                    total += float(process)
            data['workload'] = total / float(nproc)
        except Exception as ex:
            data["status"] = "KO"
            self.logger.exception("Could not get workload from the DR")
            print "Could not get workload from the DR -", ex

        return json.dumps(data)

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
            return json.dumps(response)
        except Exception:
            return json.dumps({'status': 'KO'})


    @staticmethod
    def remove_path(path):
        '''
        Removes from disk the given path (a file or a directory)
        '''
        if os.path.isfile(path):
            os.remove(path) # Remove file
        elif os.path.isdir(path):
            shutil.rmtree(path) # Remove directories recursively


    def construct(self, path_for_the_compilation, ddl_builds):
        """
        program build/update
        """
        dl_dir = os.path.join(path_for_the_compilation, 'dl/')
        src_dir = os.path.join(path_for_the_compilation, 'src/')
        bin_dir = os.path.join(path_for_the_compilation, 'bin/')
        log_file = os.path.join(path_for_the_compilation, 'build.log')
        try:
            # Clear src/ folder
            self.mkdir_p(dl_dir)
            self.mkdir_p(bin_dir)
        except Exception:
            self.logger.exception("Directory operation failed")
            raise

        for build_item in ddl_builds.items():

            build_item = build_item[1]

            # These are mandatory
            url = build_item.get('url')
            if not url:
                raise IPOLMissingBuildItem("url")

            files_to_move = build_item.get('move')
            if not files_to_move:
                raise IPOLMissingBuildItem("move")

            # These are optional
            construct = build_item.get('construct')
            username = build_item.get('username')
            password = build_item.get('password')

            zip_filename = urlparse.urlsplit(url).path.split('/')[-1]
            tgz_file = os.path.join(dl_dir, zip_filename)

            # Get files to move path
            files_path = []
            for f in files_to_move.split(","):
                files_path.append(os.path.join(bin_dir, os.path.basename(f.strip())))

            # Download
            extract_needed = build.download(url, tgz_file, username, password)

            # Check if a rebuild is nedded
            if extract_needed or not self.all_files_exist(files_path):
                with self.lock_construct:
                    if os.path.isdir(src_dir):
                        shutil.rmtree(src_dir)
                    self.mkdir_p(src_dir)
                    # Move to the compilation directory, in case the
                    # instructions in the move directive have changed it
                    os.chdir(src_dir)
                    # Extract source code
                    build.extract(tgz_file, src_dir)

                    if construct is not None:
                        # Execute the construct
                        build.run(construct, log_file, cwd=src_dir)

                    # Move files
                    for file_to_move in files_to_move.split(","):
                        # Remove possible white spaces
                        file_to_move = file_to_move.strip()
                        #
                        path_from = os.path.join(src_dir, file_to_move)
                        path_to = os.path.join(bin_dir, os.path.basename(file_to_move))

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
                            self.write_log("construct", "Can't move file {} --> {}".format(path_from, path_to))
                            # If can't move, write in the log file, so
                            # the user can see it
                            f = open(log_file, 'w')
                            f.write("Failed to move {} --> {}".\
                              format(path_from, path_to))
                            f.close()
                            raise


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
        moved correcty.
        """
        ddl_build = json.loads(ddl_build)

        path_for_the_compilation = os.path.join(self.main_bin_dir, demo_id)
        self.mkdir_p(path_for_the_compilation)
        try:
            if 'build1' in ddl_build:
                # we should have a dict or a list of dict
                self.do_compile(ddl_build, path_for_the_compilation)
            else:
                data = {}
                data['status'] = 'KO'
                data['message'] = "Bad build syntax: 'build1' not found. Build: {}".format(str(ddl_build)).encode('utf8')
                return json.dumps(data)
            data = {}
            data['status'] = "OK"
            data['message'] = "Build of demo {0} OK".format(demo_id).encode('utf8')

        except build.IPOLHTTPMissingHeader as ex:
            data = {}
            data['status'] = 'KO'
            data['message'] = "Incomplete HTTP response. {}. Hint: do not use GitHub, \
GitLab, or Dropbox as a file server.\nddl_build: {}".\
format(str(ex), str(ddl_build)).encode('utf8')

        except IPOLMissingBuildItem as ex:
            data = {}
            data['status'] = 'KO'
            data['message'] = "Missing build item: {}. ddl_build: {}".\
format(str(ex), str(ddl_build)).encode('utf8')

        except urllib2.HTTPError as ex:
            print "HTTPError"
            self.logger.exception("ensure_compilation - HTTPError")
            data = {}

            build_name = ddl_build.keys()[0]
            if 'password' in ddl_build[build_name]:
                ddl_build[build_name]['password'] = "*****"
                ddl_build[build_name]['username'] = "*****"
            data['status'] = 'KO'
            data['message'] = "{}, ddl_build: {}".format(str(ex), str(ddl_build)).encode('utf8')

        except build.IPOLCompilationError as ex:
            print "Build failed with exception " + str(ex) + " in demo " + demo_id

            build_filename = 'build.log'
            log_file = os.path.join(path_for_the_compilation, build_filename)

            if os.path.isfile(log_file):
                content = DemoRunner.read_workdir_file(path_for_the_compilation, build_filename)
            else:
                content = ""

            #content = ""
            #if os.path.isfile(log_file):
            #    with open(log_file) as f:
            #        content = f.readlines()
            data = {}
            data['status'] = 'KO'
            data['message'] = "Build for demo {0} failed".format(demo_id).encode('utf8')
            data['buildlog'] = content
        except IPOLConstructFileNotFound as ex:
            data = {}
            data['status'] = 'KO'
            data['message'] = "Construct failed. File not found. {}".format(str(ex))
        except urllib2.URLError as ex:
            data = {}
            data['status'] = 'KO'
            data['message'] = "Construct failed. URL problem. {}".format(str(ex))
        except IOError as ex:
            data = {}
            data['status'] = 'KO'
            data['message'] = "Construct failed. I/O error. {}".format(str(ex))
        except Exception as ex:
            data = {}
            data['status'] = 'KO'
            data['message'] = "INTERNAL ERROR in ensure_compilation"
            self.logger.exception("INTERNAL ERROR in ensure_compilation, demo {}".format(demo_id))

        return json.dumps(data)


    @cherrypy.expose
    def test_compilation(self, ddl_build, path_for_the_compilation):
        """
        Test the compilation in a test path, not in the demo path
        """
        data = {'status':'KO'}
        ddl_build = json.loads(ddl_build)
        try:
            if 'build1' in ddl_build:
                self.do_compile(ddl_build, path_for_the_compilation)
            else:
                data['status'] = 'KO'
                data['error'] = "Bad build syntax: 'build1' not found. Build: {}".format(str(ddl_build))
                return json.dumps(data)

            data['status'] = 'OK'
        except Exception:
            data['status'] = 'KO'
        return json.dumps(data)

    def do_compile(self, ddl_build, path_for_the_compilation):
        """
        Do the compilation
        """
        # we should have a dict or a list of dict
        if isinstance(ddl_build, dict):
            builds = [ddl_build]
        else:
            builds = ddl_build

        for build_block in builds:
            self.construct(path_for_the_compilation, build_block)

    # ---------------------------------------------------------------------------
    # Algorithm runner
    # ---------------------------------------------------------------------------
    def run_algo(self, demo_id, work_dir, bin_path, ddl_run, params, res_data, timeout):
        """
        the core algo runner
        """
        rd = run_demo_base.RunDemoBase(bin_path, work_dir, self.logger, timeout)
        rd.set_algo_params(params)
        rd.set_algo_info(res_data['algo_info'])
        rd.set_MATLAB_path(self.MATLAB_path)
        rd.set_demo_id(demo_id)
        rd.set_commands(ddl_run)

        rd.set_share_demoExtras_dirs(self.share_demoExtras_dir, demo_id)

        # Note: use isinstance(s, str) if moving to Python 3
        if not isinstance(ddl_run, basestring):
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
        return content.encode('utf8')

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
                return json.dumps(res_data)

            run_time = time.time()
            timeout = float(timeout)
            # A maximum of 10 min, regardless the config
            timeout = min(timeout, 10*60)
            # At least five seconds
            timeout = max(timeout, 5)

            # Run algorithm and control exceptions
            code = self.run_algo(demo_id, work_dir, \
                                 path_with_the_binaries, \
                                 ddl_run, params, res_data, timeout)

            if code == -1: # Bad run syntax
                self.write_log("exec_and_wait", "Bad run syntax, demo_id={}".format(demo_id))
                res_data['status'] = 'KO'
                err = "Bad run syntax (not a string): {}".format(str(ddl_run))
                res_data['error'] = err
                res_data['algo_info']['error_message'] = err
                return json.dumps(res_data)

            res_data['algo_info']['error_message'] = " "
            res_data['algo_info']['run_time'] = time.time() - run_time
            res_data['status'] = 'OK'
            return json.dumps(res_data)

        except IPOLTimeoutError:
            res_data['status'] = 'KO'
            res_data['error'] = 'IPOLTimeoutError'
            res_data['algo_info']['error_message'] = 'IPOLTimeoutError, Timeout={} s'.format(timeout)
            print "exec_and_wait IPOLTimeoutError, demo_id={}".format(demo_id)
            return json.dumps(res_data)
        except RuntimeError as ex:
            # Read stderr and stdout
            stderr_content = self.read_workdir_file(work_dir, "stderr.txt")
            stdout_content = self.read_workdir_file(work_dir, "stdout.txt")
            # Put them in the message for the web interface
            res_data['algo_info']['error_message'] = 'Runtime error\n\
stderr: {}\nstdout: {}'.format(stderr_content, stdout_content)
            res_data['status'] = 'KO'
            res_data['error'] = str(ex)
            print res_data
            return json.dumps(res_data)

        except OSError as ex:
            error_str = "{} - errno={}, filename={}, ddl_run={}".format(str(ex), ex.errno, ex.filename, ddl_run)
            self.write_log("exec_and_wait", "OSError, demo_id={}, {}".format(demo_id, error_str))
            res_data['status'] = 'KO'
            res_data['algo_info']['error_message'] = error_str
            res_data['error'] = error_str
            print res_data
            return json.dumps(res_data)
        except KeyError as ex:
            error_str = "KeyError. Hint: variable not defined? - {}, ddl_run={}".format(str(ex), ddl_run)
            self.write_log("exec_and_wait", "KeyError, demo_id={}, {}".format(demo_id, error_str))
            res_data['status'] = 'KO'
            res_data['algo_info']['error_message'] = error_str
            res_data['error'] = error_str
            print res_data
            return json.dumps(res_data)
        except Exception as ex:
            error_str = "Uncatched Exception, demo_id={}".format(demo_id)
            self.logger.exception(error_str)
            res_data['status'] = 'KO'
            res_data['algo_info']['error_message'] = error_str
            res_data['error'] = 'Error: {}'.format(ex)
            print res_data
            return json.dumps(res_data)

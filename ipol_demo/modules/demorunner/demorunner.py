#!/usr/bin/env python
# -*- coding:utf-8 -*-

"""
This file implements the demo runner module,
which takes care of running an IPOL demo using web services
"""

# add lib path for import
import os.path, sys
sys.path.append(os.path.join(os.path.dirname(os.path.realpath(__file__)), "Tools"))


import hashlib
from   datetime import datetime

import urllib2
from   timeit   import default_timer as timer
from   image    import thumbnail, image
from   misc     import prod
import PIL.ImageDraw

import threading
import cherrypy
import os
import json
import glob
import shutil
import time

import  run_demo_base
from    run_demo_base import RunDemoBase
from    run_demo_base import IPOLTimeoutError

import traceback


import subprocess
import errno
import logging


import urlparse
import os, shutil

from misc import ctime

import shutil
import stat
import urlparse
from os import path

import build

import tempfile
import time

from string import Template
from threading import Lock
import ConfigParser
import re


def authenticate(func):
    '''
    Wrapper to authenticate before using an exposed function
    '''

    def authenticate_and_call(*args, **kwargs):
        '''
        Invokes the wrapped function if authenticated
        '''
        if not is_authorized_ip(cherrypy.request.remote.ip) and not (
                "X-Real-IP" in cherrypy.request.headers and is_authorized_ip(cherrypy.request.headers["X-Real-IP"])):
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
            patterns.append(re.compile(authorized_pattern.replace(".", "\.").replace("*", "[0-9]*")))
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


    @cherrypy.expose
    def index(self):
        """
        HTML presentation page
        """
        return ("This is the IPOL DemoRunner module")

    @cherrypy.expose
    def ping(self):
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

    @cherrypy.expose
    def default(self, attr):
        """
        Default method invoked when asked for non-existing service.
        """
        data = {}
        data["status"] = "KO"
        data["message"] = "Unknown service '{}'".format(attr)
        return json.dumps(data)

    # -----------------------------------------------------------------------------
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
            processes, error = subprocess.Popen(cmd + " &",
                                                shell=True,
                                                executable="/bin/bash",
                                                stdout=subprocess.PIPE,
                                                stderr=subprocess.PIPE).communicate()
            # Get the number of cores
            nproc, error = subprocess.Popen("nproc &",
                                            shell=True,
                                            executable="/bin/bash",
                                            stdout=subprocess.PIPE,
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
            # Read DDL
            url = build_item['url']
            files_to_move = build_item['move']
            construct = build_item['construct'] if 'construct' in build_item else None

            username = build_item['username'] if 'username' in build_item else None
            password = build_item['password'] if 'password' in build_item else None

            zip_filename = urlparse.urlsplit(url).path.split('/')[-1]
            tgz_file = path.join(dl_dir, zip_filename)

            # Get files to move path
            files_path = []
            for file in files_to_move.split(","):
                files_path.append(path.join(bin_dir,os.path.basename(file.strip())))

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
                        path_from = path.join(src_dir,file_to_move)
                        path_to = path.join(bin_dir, os.path.basename(file_to_move))

                        try:
                            shutil.move(path_from, path_to)
                        except (IOError, OSError):
                            # If can't move, write in the log file, so
                            # the user can see it
                            f = open(log_file, 'w')
                            f.write("Failed to move {} --> {}".\
                              format(path_from, path_to))
                            f.close()
                            raise



    def all_files_exist(self, files):
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
                data['message'] = "Bad build syntax: 'build1' not found. Build: {}".format(str(build_block))
                return json.dumps(data)
            data = {}
            data['status'] = "OK"
            data['message'] = "Build of demo {0} OK".format(demo_id)
        except urllib2.HTTPError as e:
            print "HTTPError"
            self.logger.exception("ensure_compilation - HTTPError")
            data = {}

            build_name = build_block.keys()[0]
            if 'password' in build_block[build_name]:
                build_block[build_name]['password'] = "*****"
                build_block[build_name]['username'] = "*****"
            data['status'] = 'KO'
            data['message'] = "{}, build_block: {}".format(str(e), str(build_block))
        except Exception as e:
            print "Build failed with exception " + str(e) + " in demo " + demo_id

            log_file = os.path.join(path_for_the_compilation, 'build.log')
            #
            lines = ""
            if os.path.isfile(log_file):
                with open(log_file) as f:
                    lines = f.readlines()
            data = {}
            data['status'] = 'KO'
            data['message'] = "Build for demo {0} failed".format(demo_id)
            data['buildlog'] = lines
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
                data['error'] = "Bad build syntax: 'build1' not found. Build: {}".format(str(build_block))
                return json.dumps(data)

            data['status'] = 'OK'
        except Exception as ex:
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
        rd = run_demo_base.RunDemoBase(bin_path, work_dir, self.logger,timeout)
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
        cmd = self.variable_substitution(ddl_run,demo_id, params)
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
        

    def read_workdir_file(self, work_dir, filename):
        '''
        Reads a text files from the working directory
        '''
        full_file = os.path.join(work_dir, filename)
        lines = ""
        if os.path.isfile(full_file):
            with open(full_file) as f:
                lines = f.readlines()
        return lines

    @cherrypy.expose
    def exec_and_wait(self, demo_id, key, params, ddl_run, ddl_config=None, timeout=60):
        '''
        Called by the Core to run the algorithm
        '''
        ddl_run = json.loads(ddl_run)
        params = json.loads(params)

        path_with_the_binaries = os.path.join(self.main_bin_dir, demo_id + "/")
        work_dir = os.path.join(self.share_running_dir, demo_id + '/' + key + "/")

        res_data = {}
        res_data["key"] = key
        res_data['params'] = params
        res_data['status'] = 'KO'
        res_data['algo_info'] = {}

        # run the algorithm
        try:
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
                res_data['algo_info']['status'] = err
                print res_data
                return json.dumps(res_data)

            res_data['algo_info']['run_time'] = time.time() - run_time
            res_data['status'] = 'OK'
        except IPOLTimeoutError:
            res_data['status'] = 'KO'
            res_data['error'] = 'IPOLTimeoutError'
            res_data['algo_info']['status'] = 'IPOLTimeoutError, Timeout={} s'.format(timeout)
            print "exec_and_wait IPOLTimeoutError, demo_id={}".format(demo_id)
            return json.dumps(res_data)
        except RuntimeError as e:            

            # Read stderr and stdout
            stderr_lines = self.read_workdir_file(work_dir, "stderr.txt")
            stdout_lines = self.read_workdir_file(work_dir, "stdout.txt")
                        
            # Put them in the message for the web interface
            res_data['algo_info']['status'] = 'RuntimeError, \
stderr={}, stdout={}'.format(stderr_lines, stdout_lines)

            res_data['status'] = 'KO'
            res_data['error'] = str(e)
            print res_data
            return json.dumps(res_data)

        except OSError as ex:
            error_str = "{} - errno={}, filename={}, ddl_run={}".format(str(ex), ex.errno, ex.filename, ddl_run)
            self.write_log("exec_and_wait", "OSError, demo_id={}, {}".format(demo_id, error_str))
            res_data['status'] = 'KO'
            res_data['algo_info']['status'] = error_str
            res_data['error'] = error_str
            print res_data
            return json.dumps(res_data)
        except KeyError as ex:
            error_str = "KeyError. Hint: variable not defined? - {}, ddl_run={}".format(str(ex), ddl_run)
            self.write_log("exec_and_wait", "KeyError, demo_id={}, {}".format(demo_id, error_str))
            res_data['status'] = 'KO'
            res_data['algo_info']['status'] = error_str
            res_data['error'] = error_str
            print res_data
            return json.dumps(res_data)
        except Exception as e:
            self.logger.exception("Uncatched Exception, demo_id={}".format(demo_id))
            res_data['status'] = 'KO'
            res_data['error'] = 'Error: {}'.format(e)
            print res_data
            return json.dumps(res_data)

        # check if new config fields
        if ddl_config != None:
            ddl_config = json.loads(ddl_config)
            if 'info_from_file' in ddl_config.keys():
                for info in ddl_config['info_from_file']:
                    filename = ddl_config['info_from_file'][info]
                    try:
                        f = open(os.path.join(work_dir, filename))
                        file_lines = f.read().splitlines()
                        print file_lines
                        # remove empty lines and replace new lines with ' | '
                        new_string = " | ".join([ll.rstrip() for ll in file_lines if ll.strip()])
                        print new_string
                        res_data['algo_info'][info] = new_string
                        f.close()
                    except Exception as e:
                        self.logger.exception("DDL - Failed to get info from {}".format(os.path.join(work_dir, filename)))
                        print "failed to get info ", info, " from file ", os.path.join(work_dir, filename)
                        print "Exception ", e

        return json.dumps(res_data)

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

import urllib
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

class DemoRunner(object):
    """
    This class implements Web services to run IPOL demos
    """
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

    def error_log(self, function_name, error):
        """
        Write an error log in the logs_dir defined in proxy.conf
        """
        error_string = function_name + ": " + error
        self.logger.error(error_string) 

        
    def __init__(self):
        """
        Initialize DemoRunner
        """
        base_dir = os.path.dirname(os.path.realpath(__file__))
        self.share_running_dir = cherrypy.config['share.running.dir']
        self.main_bin_dir  = os.path.join(base_dir, cherrypy.config['main.bin.dir'])
        self.main_log_dir  = cherrypy.config['main.log.dir']
        self.main_log_name = cherrypy.config['main.log.name']
        self.share_demoExtras_dir = cherrypy.config['share.demoExtras.dir']
        self.MATLAB_path = cherrypy.config['demo.matlab_path']
        self.log_file = os.path.join(self.main_log_dir, self.main_log_name)

        self.png_compresslevel=1
        self.stack_depth = 0
        
        self.mkdir_p(self.main_bin_dir)
        self.mkdir_p(self.main_log_dir)
        
        self.logger = self.init_logging()

        if not os.path.isdir(self.share_running_dir):
            error_message = "There not exist the folder: " + self.share_running_dir
            print error_message
            self.error_log("__init__", error_message)
        

#####
# web utilities
#####
    @cherrypy.expose
    def index(self):
        """
        Small index for the demorunner.
        """
        return ("This is the IPOL DemoRunner module")


    @cherrypy.expose
    def ping(self):
        """
        Ping pong.
        :rtype: JSON formatted string
        """
        data = {}
        data["status"] = "OK"
        data["ping"] = "pong"
        return json.dumps(data)

    @cherrypy.expose
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
            self.error_log("shutdown", str(ex))
        return json.dumps(data)
    
    @cherrypy.expose
    def get_load_state(self):
        """
        return CPU charge
        """
        data = {}
        data["status"] = "KO"
        try:
            mpstat_result = subprocess.check_output(['mpstat'])
            CPU_information = str(mpstat_result).split()
            CPU_information = CPU_information[-1].replace(",",".")
            data["status"] = "OK"
            data["CPU"] = float (CPU_information)
        except Exception as ex:
            self.error_log("get_load_state", str(ex))
        return json.dumps(data)    
        
    #---------------------------------------------------------------------------
    @cherrypy.expose
    def default(self, attr):
        """
        Default method invoked when asked for non-existing service.
        """
        data = {}
        data["status"] = "KO"
        data["message"] = "Unknown service '{}'".format(attr)
        return json.dumps(data)

    
    #-----------------------------------------------------------------------------
    @cherrypy.expose
    def get_workload(self):
        """
        Return the workload from this DR
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
            data['workload'] = total/float(nproc)
        except Exception as ex:
            data["status"] = "KO"
            self.logger.exception("Could not get workload from the DR")
            print "Could not get workload from the DR -",ex

        return json.dumps(data)


    def make(self, path_for_the_compilation, ddl_build, clean_previous=True):
        """
        program build/update
        """
        
        print "make begin"
        total_start = time.time()
        make_info = ""
        
        print "make(clean_previous={0})".format(clean_previous)
        zip_filename  = urlparse.urlsplit(ddl_build['url']).path.split('/')[-1]
        src_dir_name  = ddl_build['srcdir']
        
        dl_dir        = os.path.join(path_for_the_compilation, 'dl/')
        scripts_dir   = os.path.join(path_for_the_compilation, 'scripts/')
        log_file      = os.path.join(path_for_the_compilation, 'build.log')
        src_dir       = os.path.join(path_for_the_compilation, 'src/')
        bin_dir       = os.path.join(path_for_the_compilation, 'bin/')
        src_path      = os.path.join(src_dir, src_dir_name)
        
        
        self.mkdir_p(dl_dir)
        tgz_file  = path.join(dl_dir, zip_filename)
        
        print "Initing the make in ",path_for_the_compilation
        # get the latest source archive
        try:
            build.download(ddl_build['url'], tgz_file)
        except Exception as ex:
            self.error_log("make", "Failed to download the sources: {}".format(tgz_file))
            raise
            
        rebuild_needed = False

        ## test if the dest file is missing, or too old, for each program to build
        if 'binaries' in ddl_build:
            programs = ddl_build['binaries']
            for program in programs:
                print "build ", program
                # use first binary name to check time
                prog_filename = program[1]                
                try:
                    prog_file = path.join(bin_dir, os.path.basename(prog_filename))  ### AQUI GUARDA EL BINARIO AL FINAL
                    if os.path.basename(prog_filename)=='' and len(program)==3:
                        prog_file = path.join(bin_dir,program[2])
                    if not(path.isfile(prog_file)) or (ctime(tgz_file) > ctime(prog_file)):
                        rebuild_needed = True
                except Exception as ex:
                    self.logger.exception("make")
                    raise

        # test timestamp for scripts too
        if 'scripts' in ddl_build.keys():
            for script in ddl_build['scripts']:
                try:
                    script_file = path.join(scripts_dir, script[1])
                    if os.path.basename(script[1])=='' and len(script)==3:
                        script_file = path.join(scripts_dir,script[1],script[2])
                    if not(path.isfile(script_file)) or (ctime(tgz_file) > ctime(script_file)):
                        rebuild_needed = True
                except Exception as ex:
                    self.logger.exception("make")
                    raise

        #--- build
        if not(rebuild_needed):
            make_info += "no rebuild needed "
            print "no rebuild needed for demo ",path_for_the_compilation
        else:
            
            print "Extracting code for demo ",path_for_the_compilation
            # extract the archive
            start = time.time()#040404
            
            if clean_previous and path.isdir(src_dir): 
                shutil.rmtree(src_dir)

            self.mkdir_p(src_dir)
            build.extract(tgz_file, src_dir)
            make_info += "extracting archive: " + tgz_file + " sec.; ".format(time.time()-start)
            print make_info
            
            print "creating bin_dir"
            if clean_previous and path.isdir(bin_dir): 
                shutil.rmtree(bin_dir)

            self.mkdir_p(bin_dir)
            
            print "creating scripts dir"
            if clean_previous and path.isdir(scripts_dir): 
                shutil.rmtree(scripts_dir)

            self.mkdir_p(scripts_dir)
            
                    
            ##----- CMAKE build
            start = time.time()
            print "creating bin_dir"
            if  ('build_type' in ddl_build.keys()) and \
                (ddl_build['build_type'].upper()=='cmake'.upper()):
                
                print "using CMAKE"
                # Run cmake first:
                # create temporary build dir IPOL_xxx_build
                build_dir = path.join(src_path,"__IPOL_build__")
                self.mkdir_p(build_dir)
                
                # prepare_cmake can fix some options before configuration
                if ('prepare_cmake' in ddl_build.keys()):
                    print 'prepare_cmake :', ddl_build['prepare_cmake']
                    build.run(ddl_build['prepare_cmake'], stdout=log_file, cwd=src_path)
                
                print "..."
                # set release mode by default, other options could be added
                if ('cmake_flags' in ddl_build.keys()):
                    cmake_flags = ddl_build['cmake_flags']
                else:
                    cmake_flags = ''
                
                build.run("cmake -D CMAKE_BUILD_TYPE:string=Release "+cmake_flags+ " " +src_path,
                            stdout=log_file, cwd=build_dir)
                # build
                build.run("make %s " % (ddl_build['flags']), stdout=log_file,cwd=build_dir)
                
                ## copy binaries
                for program in programs:
                    prog_path=path.join(build_dir, program[0])
                    bin_path =path.join(prog_path, program[1])
                    
                    if os.path.isdir(bin_path):
                        print "copying all files in bin dir"
                        # copy all files to bin dir
                        #src_files = os.listdir(bin_path)
                        for file_name in src_files:
                            full_file_name = os.path.join(bin_path, file_name)
                        if (os.path.isfile(full_file_name)):
                            print "{0}; ".format(file_name),
                            shutil.copy(full_file_name, bin_dir)
                        print ''
                    else:
                        # copy binary to bin dir
                        print "{0}-->{1}".format(bin_path, bin_dir)
                        shutil.copy(bin_path, bin_dir)
            else:
                if  ('build_type' in ddl_build.keys()) and \
                    (ddl_build['build_type'].upper()=='make'.upper()):
                    #----- MAKE build
                    print "using MAKE"

                    # prepare_cmake can fix some options before configuration
                    if ('prepare_make' in ddl_build.keys()):
                        print 'prepare_make :', ddl_build['prepare_make']
                        build.run(ddl_build['prepare_make'], stdout=log_file, cwd=src_path)
                    
                    print "..."

                    # build the programs for make
                    for program in programs:
                        prog_path=path.join(src_path,  program[0])
                        bin_path =path.join(prog_path, program[1])
                    
                        # build
                        if os.path.isdir(bin_path):
                            cmd = "make %s -C %s" % (ddl_build['flags'], prog_path)
                        else:
                            cmd = "make %s -C %s %s" % (ddl_build['flags'], prog_path, program[1])
                    
                        print cmd
                        build.run(cmd, stdout=log_file)
                    
                        if os.path.isdir(bin_path):
                            print "copying all files in bin dir ", bin_path
                            # copy all files to bin dir
                            src_files = os.listdir(bin_path)
                            for file_name in src_files:
                                full_file_name = os.path.join(bin_path, file_name)
                                if (os.path.isfile(full_file_name)):
                                    print "{0}; ".format(file_name),
                                    shutil.copy(full_file_name, bin_dir)
                        else:
                            # copy binary to bin dir
                            print "{0}-->{1}".format(bin_path, bin_dir)
                            shutil.copy(bin_path, bin_dir)

            # if build_type is 'script', just execute this part
            if 'scripts' in ddl_build.keys():
                print ddl_build['scripts']
                # Move scripts to the scripts dir
                for script in ddl_build['scripts']:
                    print "moving ",path.join(src_path, script[0], script[1]), " to ", scripts_dir
                    new_file = path.join( scripts_dir, script[1])
                
                    if os.path.exists(new_file):
                        if path.isfile(new_file): 
                            os.remove(new_file)
                        else:
                            os.chmod( new_file, stat.S_IRWXU )
                            shutil.rmtree(new_file)
                    shutil.move(path.join(src_path, script[0], script[1]), scripts_dir)
                    # Give exec permission to the script
                    os.chmod( new_file, stat.S_IREAD | stat.S_IEXEC )
            
            # prepare_cmake can fix some options before configuration
            if ('post_build' in ddl_build.keys()):
                print 'post_build command:', ddl_build['post_build']
                build.run(ddl_build['post_build'],
                        stdout=log_file, cwd=src_path)
                
            # cleanup the source dir
            shutil.rmtree(src_dir)
            make_info += "build: {0} sec.; ".format(time.time()-start)

        make_info += "total elapsed time: {0} sec.".format(time.time()-total_start)
        print "make end"
        
        return make_info

    @cherrypy.expose
    def ensure_compilation(self, demo_id, ddl_build):
        """
            Ensure compilation in the demorunner
        """
        print "\nDEMO ID " + demo_id + " is in ensure_compilation\n"
        
        data = {}
        data['status'] = 'KO'
        
        ddl_build = json.loads(ddl_build)
        
        path_for_the_compilation = os.path.join(self.main_bin_dir, demo_id)
        self.mkdir_p(path_for_the_compilation)
        
        
        #we should have a dict or a list of dict
        if isinstance(ddl_build,dict):
            builds = [ ddl_build ]
        else:
            builds = ddl_build

        first_build = True
        for build_params in builds:
            try:
                make_info = self.make(path_for_the_compilation, build_params, first_build)
                print make_info
                first_build=False
                data['status']  = "OK"
                data['message'] = "Build for demo {0} checked".format(demo_id)
                data['info']    = make_info
            except Exception as e:
                print "Build failed with exception " + str(e) + " in demo " + demo_id
                self.logger.exception("ensure_compilation")
                data['message'] = "Build for demo {0} failed".format(demo_id)
                return json.dumps(data)
            
        print ""
        
        return json.dumps(data)
    
    #---------------------------------------------------------------------------
    @cherrypy.expose
    def exec_and_wait(self, demo_id, key, params, ddl_run, ddl_config=None, meta=None):        
        print "#### run demo ####"
        print "demo_id = ",demo_id
        ddl_run = json.loads(ddl_run)
        print "ddl_run = ",ddl_run
        params  = json.loads(params)
        print "params = ",params
        
        path_with_the_binaries = os.path.join(self.main_bin_dir, demo_id + "/")
        print "path_with_the_binaries = ",path_with_the_binaries
        work_dir = os.path.join(self.share_running_dir, demo_id + '/' + key + "/")
        print "run dir = ",work_dir
        
        res_data = {}
        res_data["key"] = key
        res_data['params'] = params
        res_data['status'] = 'KO' 
        res_data['algo_info'] = {}
        if meta !=None:
            res_data['algo_meta'] = json.loads(meta)
            print res_data['algo_meta']
        
        
        # TODO:this code will be moved to the CORE
        # save parameters as a params.json file
        try:
            with open(os.path.join(work_dir,"params.json"),"w") as resfile:
                json.dump(params,resfile)
        except Exception as ex:
            self.logger.exception("Save params.json")
            print "Failed to save params.json file"
            res_data['status'] = 'KO'
            res_data['error'] = 'Save params.json'
            return json.dumps(res_data)

          
        #run the algorithm
        try:
            run_time = time.time()
            
            print "Demoid: ",demo_id
            
            self.run_algo(demo_id, work_dir, path_with_the_binaries, ddl_run, params, res_data)

            # re-read the config in case it changed during the execution
            res_data['algo_info']['run_time'] = time.time() - run_time
            res_data['status'] = 'OK'
        except IPOLTimeoutError:
            res_data['status'] = 'KO'
            res_data['error'] = 'timeout'
            self.logger.exception("exec_and_wait")
            return json.dumps(res_data)
        except RuntimeError as e:
            res_data['status']   = 'KO'
            res_data['algo_info']['status']   = 'IPOLTimeoutError'
            res_data['algo_info']['run_time'] = time.time() - run_time
            res_data['error']    = "DR RuntimeError in run_algo"
            self.logger.exception("exec_and_wait")
            print res_data
            return json.dumps(res_data)
        
        # TODO:this code will be moved to the CORE
        # get back parameters
        try:
            with open(os.path.join(work_dir,"params.json")) as resfile:
                res_data['params'] = json.load(resfile)
        except Exception as ex:
            print "Failed to read params.json file"
            self.logger.exception("exec_and_wait")
            res_data['status'] = 'KO'
            res_data['error'] = 'Read params.json'
            return json.dumps(res_data)
        
        # check if new config fields
        if ddl_config != None:
            ddl_config = json.loads(ddl_config)
            if 'info_from_file' in ddl_config.keys():
                for info in ddl_config['info_from_file']:
                    print "*** ",info
                    filename = ddl_config['info_from_file'][info]
                    try:
                        f = open(os.path.join(work_dir,filename))
                        print "open ok"
                        file_lines = f.read().splitlines()
                        print file_lines
                        # remove empty lines and replace new lines with ' | '
                        new_string = " | ".join([ll.rstrip() for ll in file_lines if ll.strip()])
                        print new_string
                        res_data['algo_info'][info] = new_string
                        f.close()
                    except Exception as e:
                        self.logger.exception("Failed to get info from {}".format(os.path.join(work_dir,filename)))
                        print "failed to get info ",  info, " from file ", os.path.join(work_dir,filename)
                        print "Exception ",e
        
        print res_data
        return json.dumps(res_data)
        
         
        
    #---------------------------------------------------------------------------
    # Core algorithm runner
    #---------------------------------------------------------------------------
    def run_algo(self, demo_id, work_dir, bin_path, ddl_run, params, res_data):
        """
        the core algo runner
        """
        print "\n\n----- run_algo begin -----\n\n"
        try:
            rd = run_demo_base.RunDemoBase(bin_path, work_dir)
            rd.set_algo_params(params)
            rd.set_algo_info  (res_data['algo_info'])
            rd.set_algo_meta  (res_data['algo_meta'])
            rd.set_MATLAB_path(self.MATLAB_path)
            rd.set_demo_id(demo_id)
            rd.set_commands(ddl_run)
            
            rd.set_share_demoExtras_dirs(self.share_demoExtras_dir, demo_id)
            rd.run_algorithm()
        except Exception as e:
            raise RuntimeError(e.message)
            self.logger.exception("run_algo")
        ## take into account possible changes in parameters
        
        res_data['params']      = rd.get_algo_params()
        res_data['algo_info']   = rd.get_algo_info()
        res_data['algo_meta']   = rd.get_algo_meta()
        print "----- run_algo end -----"
        return
        

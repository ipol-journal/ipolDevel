import os
from os import path
from subprocess import Popen
import subprocess
import time
import re
import math
# importing image for python commands in DDL scripts
from image import image
import PIL

# -----------------------------------------------------------------------------
from threading import Lock


class IPOLTimeoutError(Exception):
    def __init__(self, value=None):
        self.value = value

    def __str__(self):
        return repr(self.value)


# -------------------------------------------------------------------------------
class RunDemoBase:
    # default timeout to 1 minute
    default_timeout = 60

    # -----------------------------------------------------------------------------
    def __init__(self, base_dir, work_dir, logger):
        self.base_dir = base_dir
        self.work_dir = work_dir
        self.logger = logger

        self.ipol_scripts = os.path.join(os.path.dirname(os.path.realpath(__file__)), 'PythonTools/')
        self.bin_dir = os.path.join(base_dir, 'bin/')
        self.scripts_dir = os.path.join(base_dir, 'scripts/')
        self.python_dir = os.path.join(base_dir, 'python/')
        self.dl_dir = os.path.join(base_dir, 'dl/')
        self.MATLAB_path = None
        self.demo_id = None

    # -----------------------------------------------------------------------------
    # set the running commands as a dictionnary (usually read from JSON file)
    def set_commands(self, commands):
        self.commands = commands

    # -----------------------------------------------------------------------------
    def set_demo_id(self, demo_id):
        self.demo_id = demo_id

    # -----------------------------------------------------------------------------
    def get_demo_id(self):
        return self.demo_id

    # -----------------------------------------------------------------------------
    # set the algorihtm parameters as a  dictionnary
    def set_algo_params(self, algo_params):
        self.algo_params = algo_params

    # -----------------------------------------------------------------------------
    def get_algo_params(self):
        return self.algo_params

    # -----------------------------------------------------------------------------
    # set the algorihtm info as a  dictionnary
    def set_algo_info(self, algo_info):
        self.algo_info = algo_info

    def get_algo_info(self):
        return self.algo_info

    # -----------------------------------------------------------------------------
    # set the algorihtm meta info as a  dictionnary
    def set_algo_meta(self, algo_meta):
        self.algo_meta = algo_meta

    def get_algo_meta(self):
        return self.algo_meta

    # -----------------------------------------------------------------------------
    def set_extra_path(self, p):
        self.extra_path = p

    # -----------------------------------------------------------------------------
    def get_extra_path(self):
        try:
            return self.extra_path
        except:
            return None

    # -----------------------------------------------------------------------------
    def set_MATLAB_path(self, p):
        self.MATLAB_path = p

    # -----------------------------------------------------------------------------
    def get_MATLAB_path(self):
        return self.MATLAB_path

    # ------------------- demoextras functions ------------------------------------
    def set_share_demoExtras_dirs(self, share_demoExtras_dir, demo_id):
        self.main_demoExtras_Folder = os.path.join(share_demoExtras_dir, demo_id)

    def get_demoExtras_main_folder(self):
        return self.main_demoExtras_Folder

    # -----------------------------------------------------------------------------
    def run_algorithm(self, timeout=False):
        """
    the core algo runner
    could also be called by a batch processor
    """

        lock = Lock()

        # convert parameters to variables
        for _k_ in self.algo_params:
            exec ("{0} = {1}".format(_k_, repr(self.algo_params[_k_])))
        # convert meta info to variables
        for _k_ in self.algo_meta:
            exec ("{0} = {1}".format(_k_, repr(self.algo_meta[_k_])))

        demoextras = self.get_demoExtras_main_folder()
        # scriptsCommon = self.ipol_scripts

        ## there is a problem in Python, seems that locals() should not be modified
        ## http://stackoverflow.com/questions/1450275/modifying-locals-in-python
        # locals().update(self.algo_params)
        # locals().update(self.algo_meta)

        # if run several commands, is it in series?
        # TODO: deal with timeout for each command



        # saving all shell commands in a text file
        shell_cmds = open(self.work_dir + "shell_cmds.txt", "w")
        last_shell_cmd = ""

        for cmd in self.commands:
            # check if command is an array
            run_cmd = True
            if type(cmd) == list:
                # first string is a condition to check...
                exec ("run_cmd={0}".format(cmd[0]))
                print "condition: ", cmd[0], "run_cmd=", run_cmd
                cmds = cmd[1:]
            else:
                cmds = [cmd]

            if run_cmd:
                for subcmd in cmds:
                    print "subcmd = ", subcmd

                    # [Miguel] [ToDo] Use a case-insensitive replace
                    # Perhaps with a regex.
                    subcmd = subcmd.replace("$matlab_path", self.get_MATLAB_path())
                    subcmd = subcmd.replace("${matlab_path}", self.get_MATLAB_path())
                    #
                    subcmd = subcmd.replace("$demoextras", self.get_demoExtras_main_folder())
                    subcmd = subcmd.replace("${demoextras}", self.get_demoExtras_main_folder())

                    # accept # for comments
                    if subcmd.startswith('#'):
                        continue

                    # python commands start with "python:"
                    if subcmd.startswith('python:'):
                        print "Running python command ", subcmd[7:]
                        with lock:
                            os.chdir(self.work_dir)
                            exec (subcmd[7:])
                        continue

                    # get argument list, but keep strings
                    args = re.findall(r'(?:[^\s"]|"(?:\\.|[^"])*")+', subcmd)
                    stdout_file = None
                    stderr_file = open(self.work_dir + "stderr.txt", 'w')
                    # variable used to skip redirections at the end of the argument list
                    last_arg_pos = len(args) - 1
                    # replace variables
                    for i, p in enumerate(args):
                        print p
                        # strip double quotes
                        args[i] = p.strip('"')

                        # 1 replace simple variables
                        v = re.search(r'\$\w+', p)
                        # more complicate, search all variables and replace them
                        if v != None:
                            while v != None:
                                try:
                                    p = p[:v.start()] + str(eval(v.group()[1:])) + p[v.end():]
                                    print "argument number ", i, " evaluated to: ", p
                                except:
                                    print "Failed to evaluate argument ", p
                                    break
                                v = re.search(r'\$\w+', p)
                            args[i] = p

                        # 2 replace more complex expressions, of type ${expression},
                        # where expression does not contain '{' or '}' characters
                        v = re.search(r'\$\{[^\{\}]*\}', p)
                        # more complicate, search all variables and replace them
                        if v != None:
                            while v != None:
                                try:
                                    p = p[:v.start()] + str(eval(v.group()[2:-1])) + p[v.end():]
                                    print "argument number ", i, " evaluated to: ", p
                                    v = re.search(r'\$\{[^\{\}]*\}', p)
                                except:
                                    print "Failed to evaluate argument ", p
                                    break
                            args[i] = p

                        # output file >filename
                        if p[0] == '>':
                            try:
                                if p[1] == '>':
                                    print "opening ", self.work_dir + p[2:]
                                    stdout_file = open(self.work_dir + p[2:], 'a')
                                else:
                                    print "opening ", self.work_dir + p[1:]
                                    stdout_file = open(self.work_dir + p[1:], 'w')
                            except:
                                print "failed"
                                stdout_file = None
                            last_arg_pos = min(last_arg_pos, i - 1)

                        # output file >filename finishes also the build command
                        if p[:2] == "2>":
                            # redirect errors to stdout
                            if p == '2>&1':
                                stderr_file = stdout_file
                            else:
                                # allow 2>>
                                if p[2] == '>':
                                    startpos = 3
                                    openmode = 'a'
                                else:
                                    startpos = 2
                                    openmode = 'w'
                                try:
                                    print "opening ", self.work_dir + p[startpos:]
                                    stderr_file.close()
                                    stderr_file = open(self.work_dir + p[startpos:], openmode)
                                except:
                                    print "failed"
                                    stderr_file = None
                                last_arg_pos = min(last_arg_pos, i - 1)

                    last_shell_cmd = ' '.join(args)
                    shell_cmds.write(last_shell_cmd + '\n')

                    print "running ", repr(args[:last_arg_pos + 1])

                    with lock:
                        os.chdir(self.work_dir)
                        proc_name = args[:last_arg_pos + 1]
                        try:
                            p = self.run_proc(proc_name, stdout=stdout_file, stderr=stderr_file)
                        except OSError:
                            self.logger.exception("OSError when run_proc with proc_name={}".format(proc_name))
                            raise
                            
                    self.wait_proc(p)

                    # Close stderr, stdout files
                    if stderr_file != None:
                        stderr_file.close()
                    if stdout_file != None:
                        stdout_file.close()

        # convert back variables to parameters
        for _k_ in self.algo_params:
            try:
                cmd = "self.algo_params['{0}'] = {0}".format(_k_)
                exec (cmd)
            except:
                print "failed to get back parameter ", _k_

        shell_cmds.close()

    def run_proc(self, args, stdin=None, stdout=None, stderr=None, env=None):
        """
    execute a sub-process from the share run folder
    """
        if env is None:
            env = {}
        # update the environment
        newenv = os.environ.copy()
        # add local environment settings
        newenv.update(env)

        newenv.update({'demoextras': self.get_demoExtras_main_folder()})
        newenv.update({'matlab_path': self.get_MATLAB_path()})

        # TODO clear the PATH, hard-rewrite the exec arg0
        # TODO use shell-string execution

        # Add PATH in configuration
        # [Miguel] ToDo it seems that this is useless.
        # IT should use only self.get_extra_path()
        path = self.bin_dir
        path += ":/bin:/usr/bin:/usr/local/bin"
        path += ":" + self.get_MATLAB_path()
        path += ":" + self.ipol_scripts  # scripts of PythonTools

        ###TODO: Remove these lines when the DDL's are correct
        # We are only using these for the moment
        # We do not want to break the old system yet...
        path += ":" + self.scripts_dir
        path += ":" + self.python_dir  # Scripts of the demo

        # Check if there are extra paths
        if self.get_extra_path() is not None:
            path += ":" + self.get_extra_path()

        newenv.update({'PATH': path, 'LD_LIBRARY_PATH': self.bin_dir})

        # run
        return Popen(args, stdin=stdin, stdout=stdout, stderr=stderr,
                     env=newenv, cwd=self.work_dir)

    # -----------------------------------------------------------------------------
    @staticmethod
    def wait_proc(process, timeout=default_timeout):
        """
    wait for the end of a process execution with an optional timeout
    timeout: False (no timeout) or a numeric value (seconds)
    process: a process or a process list, tuple, ...
    """

        ## If production and timeout is not set, assign a security value

        if isinstance(process, Popen):
            # require a list
            process_list = [process]
        else:
            # duck typing, suppose we have an iterable
            process_list = process

        # http://stackoverflow.com/questions/1191374/
        # wainting for better : http://bugs.python.org/issue5673
        start_time = time.time()
        run_time = 0
        while True:
            if all([p.poll() is not None for p in process_list]):
                # all processes have terminated
                break
            run_time = time.time() - start_time
            if run_time > timeout:
                for p in process_list:
                    try:
                        p.terminate()
                    except OSError:
                        # could not stop the process
                        # probably self-terminated
                        pass
                raise IPOLTimeoutError(timeout)
            time.sleep(0.1)

        if any([0 != p.returncode for p in process_list]):
            raise RuntimeError
        return

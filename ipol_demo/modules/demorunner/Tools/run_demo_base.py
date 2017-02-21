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

    # -----------------------------------------------------------------------------
    def __init__(self, base_dir, work_dir, logger, timeout):
        self.base_dir = base_dir
        self.work_dir = work_dir
        self.logger = logger
        self.timeout = timeout

        self.ipol_scripts = os.path.join(os.path.dirname(os.path.realpath(__file__)), 'PythonTools/')
        self.bin_dir = os.path.join(base_dir, 'bin/')
        self.scripts_dir = os.path.join(base_dir, 'scripts/')
        self.python_dir = os.path.join(base_dir, 'python/')
        self.dl_dir = os.path.join(base_dir, 'dl/')
        self.MATLAB_path = None
        self.demo_id = None

    # -----------------------------------------------------------------------------
    def write_log(self, function_name, message):
        """
        Write an error log in the logs_dir defined in proxy.conf
        """
        log_string = "{}: {}".format(function_name, message)
        #
        self.logger.error(log_string)

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
    def run_algorithm(self, cmd, lock):
        '''
        Executes an algorithm given a command line.
        '''
        # Open stderr and stdlog files
        stderr_file = open(os.path.join(self.work_dir, "stderr.txt"), 'w')
        stdout_file = open(os.path.join(self.work_dir, "stdout.txt"), 'w')

        # We need to lock the working directory change and
        # creating on the process to prevent that another thread
        # changes also the working directory in between.
        with lock:
            os.chdir(self.work_dir)
            prog_name_and_params = cmd.split()
            print "prog_name_and_params ", prog_name_and_params
            try:
                p = self.run_proc(prog_name_and_params, stdout=stdout_file, stderr=stderr_file)
            except OSError:
                self.logger.exception("OSError when run_proc with prog_name_and_params={}".format(prog_name_and_params))
                raise
            except RuntimeError:
                self.logger.exception(
                    "RuntimeError when run_proc with prog_name_and_params={}".format(prog_name_and_params))
                raise

        # This second try executes the command line
        try:
            self.wait_proc(p)
        except OSError:
            self.logger.exception("OSError when wait_proc with prog_name_and_params={}".format(prog_name_and_params))
            raise
        except RuntimeError:
            self.logger.exception(
                "RuntimeError when run_proc with wait_name_and_params={}".format(prog_name_and_params))
            raise

        # Close files
        stderr_file.close()
        stdout_file.close()

    def run_algorithm_karl(self, timeout=False):
        """
        the core algo runner
        could also be called by a batch processor
        """
        self.write_log("run_algorithm_karl", \
          "Using deprecated run_algorithm_karl function to run demo {}".\
            format(self.demo_id))

        lock = Lock()

        # convert parameters to variables
        for _k_ in self.algo_params:
            exec ("{0} = {1}".format(_k_, repr(self.algo_params[_k_])))

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
                        proc_name_and_params = args[:last_arg_pos + 1]
                        try:
                            p = self.run_proc(proc_name_and_params, stdout=stdout_file, stderr=stderr_file)
                            self.wait_proc(p)
                        except OSError:
                            self.logger.exception("OSError when run_proc with proc_name_and_params={}".format(proc_name_and_params))
                            raise
                        except RuntimeError:
                            self.logger.exception("RuntimeError when run_proc with proc_name_and_params={}".format(proc_name_and_params))
                            raise
                            
                    

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
        newenv.update({'bin': self.bin_dir})

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
    def wait_proc(self, process):
        """
        wait for the end of a process execution with an optional timeout
        """
        if isinstance(process, Popen):
            # require a list
            process_list = [process]
        else:
            # duck typing: suppose we have an iterable
            process_list = process

        # http://stackoverflow.com/questions/1191374/
        # waiting for better: http://bugs.python.org/issue5673
        start_time = time.time()
        #
        while True:
            if all([p.poll() is not None for p in process_list]):
                # all processes have terminated
                break

            run_time = time.time() - start_time
            if run_time > self.timeout:
                for p in process_list:
                    try:
                        p.terminate()   # Send signal to stop the process
                        p.communicate() # Needed to avoid that the process is left as a zombie
                    except OSError:
                        # could not stop the process
                        # probably self-terminated
                        pass
                raise IPOLTimeoutError(self.timeout)
            time.sleep(1)

        if any([0 != p.returncode for p in process_list]):
            raise RuntimeError

import os
import shlex

# importing image for python commands in DDL scripts
import signal
import time
from subprocess import Popen

import psutil

from .error import VirtualEnvError

# -----------------------------------------------------------------------------




class IPOLTimeoutError(Exception):
    def __init__(self, value=None):
        self.value = value

    def __str__(self):
        return repr(self.value)


# -------------------------------------------------------------------------------
class RunDemoBase:

    # -----------------------------------------------------------------------------
    def __init__(self, base_dir, work_dir, logger, timeout):
        self.base_dir = base_dir
        self.work_dir = work_dir
        self.logger = logger
        self.timeout = timeout

        self.ipol_scripts = os.path.join(os.path.dirname(os.path.realpath(__file__)), 'PythonTools/')
        self.bin_dir = os.path.join(base_dir, 'bin/')
        self.dl_dir = os.path.join(base_dir, 'dl/')
        self.MATLAB_path = None
        self.extra_path = None
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
        return self.extra_path

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
            p = self.run_proc(prog_name_and_params, stdout=stdout_file, stderr=stderr_file) if prog_name_and_params else None

        # Execute it
        if p:
            self.wait_proc(p)

        # Close files
        stderr_file.close()
        stdout_file.close()

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

        if "VIRTUAL_ENV" not in newenv:
            raise VirtualEnvError('Running without a virtualenv')
        # Check if there are extra paths
        extra_path = self.get_extra_path()
        if not extra_path:
            raise Exception("Missing extra_path field in config")

        path = self.bin_dir
        path += ":" + extra_path
        path += ":" + self.get_MATLAB_path()
        path += ":" + self.ipol_scripts  # scripts of PythonTools

        newenv.update({'PATH': path, 'LD_LIBRARY_PATH': self.bin_dir})

        # run
        cmd = shlex.split(" ".join(args))
        return Popen(cmd, stdin=stdin, stdout=stdout, stderr=stderr,
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
                        self.kill_child_processes(p.pid)
                        p.kill()   # Send signal to kill the process
                        p.communicate() # Needed to avoid that the process is left as a zombie
                    except OSError:
                        # could not stop the process
                        # probably self-terminated
                        pass
                raise IPOLTimeoutError(self.timeout)
            time.sleep(1)

        if any([0 != p.returncode for p in process_list]):
            raise RuntimeError

    @staticmethod
    def kill_child_processes(parent_pid, sig=signal.SIGKILL):
        """
        kill all the child processes of the parent
        """
        try:
            parent = psutil.Process(parent_pid)
        except psutil.NoSuchProcess:
            return
        children = parent.children(recursive=True)
        for process in children:
            process.send_signal(sig)

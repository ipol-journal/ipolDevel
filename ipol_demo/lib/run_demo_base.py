import os
from os import path
from subprocess import Popen
import time


#-----------------------------------------------------------------------------
class TimeoutError(Exception):
  def __init__(self, value):
    self.value = value
  def __str__(self):
    return repr(self.value)

#
# needs from cherrypy:
#   log
#   - config. use:
#      if 'demo.extra_path' in cherrypy.config:
#        set_extra_path(cherrypy.config['demo.extra_path'])
#   TimeoutError
#   get_MATLAB_path()
#

#-------------------------------------------------------------------------------
class RunDemoBase:

  # default timeout to 1 minute
  default_timeout = 60

  #-----------------------------------------------------------------------------
  def __init__(self,base_dir, work_dir):
    self.base_dir    = base_dir
    self.work_dir    = work_dir
    self.bin_dir     = os.path.join(self.base_dir,'bin/')
    self.scripts_dir = os.path.join(self.base_dir,'scripts/')
    self.python_dir  = os.path.join(self.base_dir,'python/')
    self.dl_dir      = os.path.join(self.base_dir,'dl/')
    self.log_file    = os.path.join(self.base_dir, "build.log"   )
    self.logger      = None
    self.MATLAB_path = None
    self.demo_id     = None
  
  #-----------------------------------------------------------------------------
  # set the running commands as a dictionnary (usually read from JSON file)
  def set_commands(self,commands):
    self.commands=commands

  #-----------------------------------------------------------------------------
  def set_demo_id(self,id):
    self.demo_id = id

  #-----------------------------------------------------------------------------
  def get_demo_id(self):
    return self.demo_id

  #-----------------------------------------------------------------------------
  # set the algorihtm parameters as a  dictionnary
  def set_algo_params(self,algo_params):
    self.algo_params=algo_params

  #-----------------------------------------------------------------------------
  def set_extra_path(self,p):
    self.extra_path = p
    
  #-----------------------------------------------------------------------------
  def get_extra_path(self):
    try:
      return self.extra_path
    except:
      return None
    
  #-----------------------------------------------------------------------------
  def set_MATLAB_path(self,p):
    self.MATH_path = p

  #-----------------------------------------------------------------------------
  def get_MATLAB_path(self):
    return self.MATLAB_path

  #-----------------------------------------------------------------------------
  def set_logger(self,logger):
    self.logger = logger
    
  #-----------------------------------------------------------------------------
  def log(self,*args, **kwargs):
    if self.logger!=None:
      return self.logger(*args,**kwargs)
    

  #-----------------------------------------------------------------------------
  def run_algo(self, timeout=False):
    """
    the core algo runner
    could also be called by a batch processor
    """
    
    # convert parameters to variables
    for k in self.algo_params:
      exec("{0} = {1}".format(k,repr(self.algo_params[k])))
    
    # if run several commands, is it in series?
    # TODO: deal with timeout for each command
    
    for cmd in self.commands:
      args = cmd.split()
      # replace variables
      for i,p in enumerate(args):
        if p[0]=='$':
          args[i] = str(eval(p[1:]))
      try:
        self.log("running %s" % repr(args),
                  context='SETUP/%s' % self.get_demo_id(), 
                  traceback=False)
        p = self.run_proc(args)
        self.wait_proc(p)
      except ValueError as e:
        self.log("Error %s" % e,
                  context='SETUP/%s' % self.get_demo_id(), 
                  traceback=False)
        

  #-----------------------------------------------------------------------------
  #
  # SUBPROCESS
  #
  def run_proc(self, args, stdin=None, stdout=None, stderr=None, env=None):
    """
    execute a sub-process from the 'tmp' folder
    """

    if env is None:
        env = {}
    # update the environment
    newenv = os.environ.copy()
    # add local environment settings
    
    newenv.update(env)

    # TODO clear the PATH, hard-rewrite the exec arg0
    # TODO use shell-string execution

    # Add PATH in configuration
    path = self.bin_dir
    # add also the scripts dir
    path = path + ":" + self.scripts_dir
    # add also the python dir
    path = path + ":" + self.python_dir
    
    # Check if there are extra paths
    if self.get_extra_path()!=None:
      path = path + ":" + self.get_extra_path()
      
    #
    p = self.get_MATLAB_path()
    if p is None:
      self.log("warning: MATLAB path directory %s does not exist" % p,
                context='SETUP/%s' % self.get_demo_id(), 
                traceback=False)
    else:
      path = path + ":" + p
    #
    newenv.update({'PATH' : path})

    # run
    return Popen(args,  stdin=stdin, stdout=stdout, stderr=stderr,
                        env=newenv, cwd=self.work_dir)

  #-----------------------------------------------------------------------------
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
        raise TimeoutError()
      time.sleep(0.1)
          
    if any([0 != p.returncode for p in process_list]):
      raise RuntimeError
    return



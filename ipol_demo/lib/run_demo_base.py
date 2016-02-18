import os
from os import path
from subprocess import Popen
import subprocess
import time
import re
import six
import math
# importing image for python commands in DDL scripts
from .image import image
import PIL

#-----------------------------------------------------------------------------
class IPOLTimeoutError(Exception):
  def __init__(self, value=None):
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
    self.pytools_dir = os.path.join(self.base_dir,'../../PythonTools/')
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
  def get_algo_params(self):
    return self.algo_params

  #-----------------------------------------------------------------------------
  # set the algorihtm info as a  dictionnary
  def set_algo_info(self,algo_info):
    self.algo_info=algo_info

  def get_algo_info(self):
    return self.algo_info

  #-----------------------------------------------------------------------------
  # set the algorihtm meta info as a  dictionnary
  def set_algo_meta(self,algo_meta):
    self.algo_meta=algo_meta

  def get_algo_meta(self):
    return self.algo_meta

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
    for _k_ in self.algo_params:
      exec("{0} = {1}".format(_k_,repr(self.algo_params[_k_])))
    # convert meta info to variables
    for _k_ in self.algo_meta:
      exec("{0} = {1}".format(_k_,repr(self.algo_meta[_k_])))
    
    # if run several commands, is it in series?
    # TODO: deal with timeout for each command
    
    # saving all shell commands in a text file
    shell_cmds = open(self.work_dir+"shell_cmds.txt", "w")
    last_shell_cmd = ""
    
    for cmd in self.commands:
      # check if command is an array
      run_cmd=True
      if type(cmd)==list:
        # first string is a condition to check...
        exec("run_cmd={0}".format(cmd[0]))
        print "condition: ", cmd[0], "run_cmd=",run_cmd
        cmds = cmd[1:]
      else:
        cmds = [ cmd ]
        
      if run_cmd:
        for subcmd in cmds:
          print "subcmd = ", subcmd
          
          # accept # for comments
          if subcmd.startswith('#'):
              continue

          # python commands start with "python:"
          if subcmd.startswith('python:'):
            print "Running python command ",subcmd[7:]
            exec(subcmd[7:])
            continue
          
          # get argument list, but keep strings
          args = re.findall(r'(?:[^\s"]|"(?:\\.|[^"])*")+', subcmd)
          stdout_file = None
          stderr_file = open(self.work_dir+"stderr.txt", 'w')
          # variable used to skip redirections at the end of the argument list
          last_arg_pos = len(args)-1
          # replace variables
          for i,p in enumerate(args):
            print p
            # strip double quotes
            args[i] = p.strip('"')
            
            # 1 replace simple variables
            v = re.search(r'\$\w+',p)
            # more complicate, search all variables and replace them
            if v!=None:
              while v!=None:
                p = p[:v.start()]+str(eval(v.group()[1:]))+p[v.end():]
                print "argument number ",i," evaluated to: ",p
                v = re.search(r'\$\w+',p)
              args[i] = p
              
            # 2 replace more complex expressions, of type ${expression},
            # where expression does not contain '{' or '}' characters
            v = re.search(r'\$\{[^\{\}]*\}',p)
            # more complicate, search all variables and replace them
            if v!=None:
              while v!=None:
                p = p[:v.start()]+str(eval(v.group()[2:-1]))+p[v.end():]
                print "argument number ",i," evaluated to: ",p
                v = re.search(r'\$\{[^\{\}]*\}',p)
              args[i] = p

            # output file >filename 
            if p[0]=='>':
              try:
                if p[1]=='>':
                  print "opening ", self.work_dir+p[2:]
                  stdout_file = open(self.work_dir+p[2:], 'a')
                else:
                  print "opening ", self.work_dir+p[1:]
                  stdout_file = open(self.work_dir+p[1:], 'w')
              except:
                print "failed"
                stdout_file = None
              last_arg_pos = min(last_arg_pos,i-1)
              
            # output file >filename finishes also the build command
            if p[:2]=="2>":
              # redirect errors to stdout
              if p=='2>&1':
                stderr_file = stdout_file
              else:
                # allow 2>> 
                if p[2]=='>':
                    startpos=3
                    openmode='a'
                else:
                    startpos=2
                    openmode='w'
                try:
                  print "opening ", self.work_dir+p[startpos:]
                  stderr_file.close()
                  stderr_file = open(self.work_dir+p[startpos:], openmode)
                except:
                  print "failed"
                  stderr_file = None
                last_arg_pos = min(last_arg_pos,i-1)
              
              
          last_shell_cmd = ' '.join(args)
          shell_cmds.write(last_shell_cmd+'\n')
              
          try:
            print "running ",repr(args[:last_arg_pos+1])
            self.log("running %s" % repr(args[:last_arg_pos+1]),
                      context='SETUP/%s' % self.get_demo_id(), 
                      traceback=False)
            p = self.run_proc(args[:last_arg_pos+1], stdout=stdout_file, stderr=stderr_file)
            self.wait_proc(p)
          except ValueError as e:
            self.log("Error %s" % e,
                      context='SETUP/%s' % self.get_demo_id(), 
                      traceback=False)
          except RuntimeError as e:
            print "**** run_algo: RuntimeError "
            with open(self.work_dir+"stderr.txt", "r") as errfile:
              errors=errfile.read()
            if errors:
              print errors
              print "***"
            else:
              errors= "%s" %e
            raise RuntimeError(errors)
            
          # the files should close automatically with their scope ...
          # but we do it anyway just in case
          if stderr_file!=None and stderr_file!=stdout_file:
            stderr_file.close()
          if stdout_file!=None:
            stdout_file.close()
      
    # convert back variables to parameters 
    for _k_ in self.algo_params:
      cmd = "self.algo_params['{0}'] = {0}".format(_k_)
      exec(cmd)
      
    shell_cmds.close()
        

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
    # add also the python tools dir
    path = path + ":" + self.pytools_dir

    path=path+":/bin:/usr/bin:/usr/local/bin"

    # Check if there are extra paths
    if self.get_extra_path()!=None:
      path = path + ":" + self.get_extra_path()
      
    #
    p = self.get_MATLAB_path()
    if not (p is None):
      path = path + ":" + p
    #else:
      #self.log("warning: MATLAB path directory %s does not exist" % p,
                #context='SETUP/%s' % self.get_demo_id(), 
                #traceback=False)
      
    newenv.update({'PATH' : path, 'LD_LIBRARY_PATH' : self.bin_dir})

    # check for pipelines in arguments??
    # TODO: allow pipelines: more tricky since we need to measure the 
    # processing time ...
    #if args.count('|')>1:
      #self.log("error: only one pipe is allowed in running command line" % p,
                #context='SETUP/%s' % self.get_demo_id(), 
                #traceback=False)
      
    #if args.count('|')==1:
      #pipe_pos = args.index('|')
      #args1 = args[:pipe_pos]
      #args2 = args[pipe_pos+1:]
      #p1 = Popen(args1, stdin=stdin,      stdout=PIPE)
      #p2 = Popen(args2, stdin=p1.stdout,  stdout=PIPE)
      #p1.stdout.close()  # Allow p1 to receive a SIGPIPE if p2 exits.
      #output = p2.communicate()[0]     
    #else:
    
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
        raise IPOLTimeoutError(timeout)
      time.sleep(0.1)
          
    if any([0 != p.returncode for p in process_list]):
      #with open(self.work_dir+"stderr.txt", "r") as errfile:
        #errors=errfile.read()
      #raise RuntimeError(errors)
      #print "**** wait_proc: raising RuntimeError"
      raise RuntimeError
    return



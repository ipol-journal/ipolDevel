"""
Base class for BuildDemo

Karl Krissian

"""

import os, shutil
from lib.misc import ctime
import shutil
import stat
import urlparse
from os import path
from lib import build
import tempfile

#-------------------------------------------------------------------------------
class BuildDemoBase:
  
  #-----------------------------------------------------------------------------
  def __init__(self,base_dir):
    self.base_dir    = base_dir
    self.src_dir     = os.path.join(self.base_dir,'src/')
    self.bin_dir     = os.path.join(self.base_dir,'bin/')
    self.scripts_dir = os.path.join(self.base_dir,'scripts/')
    self.dl_dir      = os.path.join(self.base_dir,'dl/')
    self.log_file    = os.path.join(self.base_dir, "build.log"   )
      
  #-----------------------------------------------------------------------------
  # set the build parameters as a dictionnary (usually read from JSON file)
  def set_params(self,params):
    self.params=params
      
  #-----------------------------------------------------------------------------
  def make(self):
    # can be overridden, need self.params to be defined
    """
    program build/update
    """
    zip_filename  = urlparse.urlsplit(self.params['url']).path.split('/')[-1]
    src_dir_name  = self.params['srcdir']
    src_path      = path.join(self.src_dir, src_dir_name)
    # use first binary name to check time
    prog_filename = self.params['binaries'][0][1]

    # store common file path in variables
    tgz_file  = path.join( self.dl_dir,   zip_filename  )
    prog_file = path.join( self.bin_dir,  prog_filename )
    # get the latest source archive
    build.download(self.params['url'], tgz_file)

    # test if the dest file is missing, or too old
    if path.isfile(prog_file) and (ctime(tgz_file) < ctime(prog_file)):
      print("no rebuild needed")
    else:
      # extract the archive
      build.extract(tgz_file, self.src_dir)

      # delete and create bin dir
      if path.isdir(self.bin_dir): shutil.rmtree(self.bin_dir)
      os.mkdir(self.bin_dir)

      # delete and create scripts dir
      if path.isdir(self.scripts_dir): shutil.rmtree(self.scripts_dir)
      os.mkdir(self.scripts_dir)
      
      programs = self.params['binaries']
      #----- CMAKE build
      if  ('build_type' in self.params.keys())and\
          (self.params['type'].upper()=='CMake'.upper()):
        # Run cmake first:
        # create temporary build dir IPOL_xxx_build
        build_dir = path.join(src_path,"__IPOL_build__")
        os.mkdir(build_dir)
        # set release mode by default, other options could be added
        build.run("cmake -D CMAKE_BUILD_TYPE:string=Release "+src_path,
                  stdout=self.log_file, cwd=build_dir)
        # build
        build.run("make %s " % ( self.params['flags']), 
                  stdout=self.log_file,cwd=build_dir)
        # move binaries
        for program in programs:
          # move binary to bin dir
          shutil.copy(path.join(build_dir, program[0], program[1]), 
                      path.join(self.bin_dir, program[1]))
      else:
      #----- MAKE build
        # build the programs for make
        for program in programs:
          prog_path=path.join(src_path, program[0])
          # build
          build.run("make %s -C %s %s" % (self.params['flags'], 
                                          prog_path, program[1]), stdout=self.log_file)
          # move binary to bin dir
          shutil.copy(path.join(prog_path, program[1]), path.join(self.bin_dir, program[1]))

      if 'scripts' in self.params.keys():
        # Move scripts to the scripts dir
        for script in self.params['scripts']:
          shutil.move(path.join(src_path, script[0], script[1]),self.scripts_dir)
          # Give exec permission to the script
          os.chmod( path.join( self.scripts_dir, script[1]), stat.S_IREAD | stat.S_IEXEC )

      # cleanup the source dir
      shutil.rmtree(self.src_dir)
    return

  
  #-----------------------------------------------------------------------------
  def clean(self):
    "Cleaning"
    if path.exists(self.src_dir):      shutil.rmtree(self.src_dir)
    if path.exists(self.bin_dir):      shutil.rmtree(self.bin_dir)
    if path.exists(self.scripts_dir):  shutil.rmtree(self.scripts_dir)
    if path.exists(self.dl_dir) :      shutil.rmtree(self.dl_dir)
    # clean log?

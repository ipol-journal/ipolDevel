#!/usr/bin/python

import os, sys
CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
# go up 3 levels ...
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(CURRENT_DIR))))

from lib import config
import subprocess

#-------------------------------------------------------------------------------
if __name__ == '__main__':
  
  # read the config file
  cfg = config.cfg_open('.')
  # save the number of detections
  num_lines = sum(1 for line in open('output.txt'))
  cfg['info']['num_detections'] = num_lines
  # save the binary version
  try:
    version_file = open("version.txt", "w")
    p = subprocess.call(["../../bin/lsd", "--version"], stdout=version_file)
    version_file.close()
    version_file = open("version.txt", "r")
    version_info = version_file.readline()
    version_file.close()
  except Exception:
    version_info = "unknown"
  cfg['info']['version'] = version_info

  cfg.save()

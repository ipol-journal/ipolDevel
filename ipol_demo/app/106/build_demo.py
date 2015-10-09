#! /usr/bin/python
"""
Ponomarenko et al. IPOL demo web app

Miguel Colom
http://mcolom.info/
"""


import os, sys
# include ../.. in path to be able to import lib
CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.append(os.path.dirname(os.path.dirname(CURRENT_DIR)))

from lib import build_demo_base
from lib.build_demo_base import BuildDemoBase


class BuildDemo(BuildDemoBase):
  def __init__(self, base_dir):
    BuildDemoBase.__init__(self,base_dir)
    self.params = { 
                  'url'     : 'http://www.ipol.im/pub/art/2014/106/ldm_q1p.zip', 
                  'srcdir'  : '.',
                  'binaries': [ ['.','lens_distortion_correction_division_model_1p'] ],
                  'flags'   : 'OMP=1 -j4',
                   }


if __name__ == '__main__':
  print sys.argv
  bd = BuildDemo(os.path.dirname(os.path.abspath(__file__)))
  if (len(sys.argv) == 2)and(sys.argv[1]=="clean"):
      bd.clean()
  else:
    bd.make()


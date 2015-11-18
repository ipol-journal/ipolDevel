#! /usr/bin/python

import json
import os, sys
CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
# go up 3 levels ...
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(CURRENT_DIR))))

from lib import config
import subprocess

#-------------------------------------------------------------------------------
def SaveInfo(name,value):
  # read the config file
  cfg = config.cfg_open('.')
  cfg['info'][name] = value
  cfg.save()

#-------------------------------------------------------------------------------
def Run(cmd):
  print "Running ", cmd
  os.system(cmd)

#-------------------------------------------------------------------------------
if __name__ == '__main__':
  
  # read json param files
  params_file = open("params.json")
  params = json.load(params_file)
  params_file.close()
  print params
  
  # Compute lambda from empirical formula
  r = float(params['kernelsize'])
  s = max(1.0/3, float(params['noiselevel']))        
  
  if params['kernel'] == 'disk':
      Kopt = 'disk:' + str(r)
      params['lambda'] = r*(427.9/s + 466.4/(s*s))
  else:
      Kopt = 'gaussian:' + str(r/2)
      params['lambda'] = r*(117.0/s + 4226.3/(s*s))
  
  # save lambda as a parameter in JSON file
  SaveInfo("lambda",params['lambda'])
  
  # run_mode: 0 deconvolve, 1: convolve, add noise then deconvolve
  if params['run_mode'] == 0:
    Run('tvdeconv K:{0} lambda:{1} input_0.sel.png tvdeconv.png tvdeconv.png >output.txt 2>&1'.format(Kopt,params['lambda']))
  else:
    Run('imblur   K:{0} noise:gaussian:{1}  input_0.sel.png blurry.png'   .format(Kopt,params['noiselevel']))
    Run('tvdeconv K:{0} lambda:{1} blurry.png tvdeconv.png >output.txt 2>&1'.format(Kopt,params['lambda']))
    Run('imdiff -mpsnr  input_0.sel.png blurry.png    > psnr_blurry.txt')
    Run('imdiff -mpsnr  input_0.sel.png tvdeconv.png  > psnr_tvdeconv.txt')
    Run('imdiff -D40    input_0.sel.png blurry.png   diff_blurry.png   > diff_blurry.txt')
    Run('imdiff -D40    input_0.sel.png tvdeconv.png diff_tvdeconv.png > diff_tvdeconv.txt')
  
  

#! /usr/bin/python

import json
import os

#-------------------------------------------------------------------------------
if __name__ == '__main__':
  
  # read json param files
  params_file = open("params.json")
  params = json.load(params_file)
  print params
  
  sigma = params['sigma']
  if sigma<=2.0:
    cmd = "gaussian_demo -s {0} -a fir -t1e-15 input_0.sel.png output-exact.png".format(sigma)
    print "Running ",cmd
    os.system(cmd)
  else:  
    cmd = "gaussian_demo -s {0} -a dct -t1e-15 input_0.sel.png output-exact.png".format(sigma)
    print "Running ",cmd
    os.system(cmd)
    
  
  for p in params.keys():
    if p[:5]=="algo_":
      algo=p[5:]
      if not("_" in algo):
        cmd = "gaussian_demo -s {0} -a {1} -t1e-15 input_0.sel.png output-{1}.png".format(sigma,algo)
        print cmd
        os.system(cmd)
      else:
        cmd = "gaussian_demo -s {0} -a {1} -K {2} input_0.sel.png output-{3}.png".format(
          sigma,
          algo.split('_')[0],
          algo.split('_')[1],
          algo)
        print cmd
        os.system(cmd)
      cmd = "imdiff output-exact.png output-{0}.png >metrics_{0}.txt".format(algo)
      print cmd
      os.system(cmd)
            

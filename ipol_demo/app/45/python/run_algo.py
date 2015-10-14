#! /usr/bin/python


import os, sys
# include ../.. in path to be able to import lib
CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
# go up 3 levels ...
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(CURRENT_DIR))))

from lib import image
from lib import config
from subprocess import Popen
import time
from math import sqrt

# 1 minute
default_timeout = 60

#-----------------------------------------------------------------------------
class TimeoutError(Exception):
  def __init__(self, value):
    self.value = value
  def __str__(self):
    return repr(self.value)

#-------------------------------------------------------------------------------
def run_proc(path, args, stdin=None, stdout=None, stderr=None, env=None):
  """
  execute a sub-process from the 'tmp' folder
  """
  if env is None:
      env = {}
  # update the environment
  newenv = os.environ.copy()
  # add local environment settings
  newenv.update(env)
  newenv.update({'PATH' : path})
  # run
  return Popen(args,  stdin=stdin, stdout=stdout, stderr=stderr,
                      env=newenv, cwd='.')

#-------------------------------------------------------------------------------
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


#-------------------------------------------------------------------------------
def RMSE_scale(filename, A, B, scale):
  """
  Computes the RMSE at each scale knowing the A and B parameters
  """
  f = open(filename)
  #
  line = f.readline()
  values = line.strip().split()
  num_stds = len(values)/2
  MSE = 0.0
  num_bins = 0
  while len(values) > 0:
      for i in range(num_stds):
          mean = float(values[i])
          tilde_std = float(values[i+num_stds])
          std = sqrt(A + B*mean) / (2.0**scale)
          err = tilde_std - std
          MSE += err ** 2.0
      #
      line = f.readline()
      values = line.strip().split()
      num_bins += 1
  #
  f.close()
  #
  MSE /= float(num_bins) * num_stds
  return sqrt(MSE)

#-------------------------------------------------------------------------------
def get_compatible_size(sizeX, sizeY):
  """
  Returns a compatible known size given an arbitrary size
  """
  image_pixels = sizeX * sizeY
  pixels = [6000000.0, 1500000.0, 375000.0, 93750.0, 23438.0]
  #
  minimum_idx = 0
  min_err = abs(pixels[minimum_idx] - image_pixels)
  for i in range(len(pixels)):
      err = abs(pixels[i] - image_pixels)
      if err < min_err:
          min_err = err
          minimum_idx = i
  #
  return minimum_idx

#-------------------------------------------------------------------------------
def get_num_bins(size):
  """
  Returns a recommended number of bins given the size of the image
  """
  nb = [0, 0, 0, 4, 1]
  return nb[size]

#-------------------------------------------------------------------------------
# Get number of channels
def get_num_channels(filename):
  """
  Returns the number of channels given an estimation file
  """
  f = open(filename)
  line = f.readline()
  f.close()
  num_channels = len(line.split()) / 2
  return num_channels

#-------------------------------------------------------------------------------
# Remove last bin
def remove_last_bin(filename):
  """
  removes the last bin from the noise estimation file
  """
  lines = []

  # Read lines structure
  f = open(filename, 'r')  

  EOF = False
  while not EOF:
      line = f.readline()
      s = line.split()
      EOF = (line == '')
      lineStrip = line.strip()
      isWhiteLine = (not EOF and lineStrip == '')
      isComment = lineStrip.startswith('#')
      if not (EOF or isWhiteLine or isComment):
          lines.append(s)

  f.close()

  if len(lines) < 2:
      return

  # Re-write file
  f = open(filename, 'w')  
  #
  for line in lines[0:len(lines)-1]:
      for intensity_str in line[0:len(line)/2]:
          f.write(intensity_str + " ")
      for std_str in line[len(line)/2:]:
          f.write(std_str + " ")
      f.write("\n")
  #
  f.close()

#-------------------------------------------------------------------------------
# Correct quantization error
def correct_quantization_error(filename, scale):
  """
  sustracts the quantization error from the noise estimation file
  """
  lines = []

  # Read lines structure
  f = open(filename, 'r')  

  EOF = False
  while not EOF:
      line = f.readline()
      s = line.split()
      EOF = (line == '')
      lineStrip = line.strip()
      isWhiteLine = (not EOF and lineStrip == '')
      isComment = lineStrip.startswith('#')
      if not (EOF or isWhiteLine or isComment):
          lines.append(s)

  f.close()

  # Correct stds and re-write file
  f = open(filename, 'w')
  #
  for line in lines:
      for intensity_str in line[0:len(line)/2]:
          intensity = float(intensity_str)
          f.write(str(intensity) + " ")
      for std_str in line[len(line)/2:]:
          std = float(std_str)
          D = std**2.0 - (1.0/4)**scale * (1.0/12)                
          std = sqrt(D) if D >= 0 else 0
          f.write(str(std) + " ")
      f.write("\n")
  #
  f.close()

#-------------------------------------------------------------------------------
if __name__ == '__main__':
  #
  # needs: 
  #  timeout: as parameter?
  #
  # TODO:
  #
  
  #params_file = open("params.json")
  #params = json.load(params_file)
  
  # read also the config in the current directory
  cfg = config.cfg_open('.')
  params = cfg['param']
  print params
  
  timeout = 60

  # convert parameters to variables
  for k in params:
    print "running {0} = {1}".format(k,repr(params[k]))
    exec("{0} = {1}".format(k,repr(params[k])))
  
  # Increment the number of bins, since the last will be
  # removed later
  if bins > 0:
      bins += 1

  # Get input size
  ima = image('input_0.sel.png')
  sizeX, sizeY = ima.size

  print "Image size = ", sizeX, "x", sizeY

  # Determine the number of scales
  num_scales = 0
  scale_OK = (num_scales <= 4 and sizeX*sizeY >= 20000)
  sizes = {}
  while scale_OK:
    sizes[num_scales] = (sizeX, sizeY)
    # Data for the next scale
    sizeX /= 2
    sizeY /= 2
    # Next scale
    num_scales += 1
    scale_OK = (num_scales <= 4 and sizeX*sizeY >= 20000)
    
  print "Number of scales = ", num_scales, " scale_OK = ", scale_OK

  # Create sub-scales
  for scale in range(num_scales):
    if scale != num_scales - 1:
      # Create next subscale scale s{i+1} for s{i}.
      os.system("../../bin/subscale -s2 scale_s{0}.rgb scale_s{1}.rgb".format(scale,scale+1))

  # Estimate the noise, in parallel,
  processes = []
  fds = []
  for scale in range(num_scales):
      sizeX, sizeY = sizes[scale]
      # Number of bins
      compatible_size = get_compatible_size(sizeX, sizeY)
      num_bins = (get_num_bins(compatible_size) if bins == 0 else bins / 2**scale)

      # Estimate noise
      fd = open('estimation_s%d.txt' % scale, "w")
      if percentile < 0:
          percentile = 0 # Use algorithm's K

      procOptions = ['ponomarenko', 
                      '-p%.4f' % percentile , 
                      '-b%d' % num_bins, 
                      '-w%d' % block, 
                      '-m%d' % mean_type, 
                      '-g%d' % curvefilter]
      #          
      if removeequals == 1:
          procOptions.append('-r')
      #
      procOptions.append('scale_s%d.rgb' % scale)

      # Run
      #pid = self.run_proc(procOptions, stdout=fd, stderr=fd)
      #self.wait_proc(pid, timeout*0.8)
      #fd.close()

      processes.append(run_proc("../../bin",procOptions, stdout=fd, stderr=fd))
      fds.append(fd)

  # Wait for the parallel processes to end
  wait_proc(processes, timeout*0.8)

  # Close the file descriptors
  for fd in fds:
      fd.close()

  # Remove last bin, correct quantization error and draw noise curves
  RMSEs = ''
  for scale in range(num_scales):
      estimation_filename = 'estimation_s%d.txt' % scale

      # Remove the last bin
      remove_last_bin(estimation_filename)

      correct_quantization_error(estimation_filename, scale)

      # Compute RMSE of the current scale
      if anoise > 0.0 or bnoise > 0.0: # Only if user added noise
          RMSE = RMSE_scale(estimation_filename,  anoise, bnoise, scale)
          RMSEs += '%f,' % RMSE

      # Get number of channels
      num_channels = get_num_channels(estimation_filename)

      # Generate figure
      procOptions = [ 'writeNoiseCurve.sh', 
                      'estimation_s%d.txt' % scale, 
                      '%d' % num_channels, 
                      'curve_s%d.png' % scale]
      # Run
      procDesc = run_proc("../../scripts",procOptions)
      wait_proc(procDesc, timeout*0.8)

  # Cleanup
  for i in range(num_scales):
      os.unlink('scale_s%d.rgb' % ((i)))

  cfg['param']['scales'] = num_scales
  cfg['param']['rmses'] = RMSEs
  cfg.save()

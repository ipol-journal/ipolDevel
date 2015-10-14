#! /usr/bin/python

import os, sys

#-------------------------------------------------------------------------------
# Get number of channels
def get_num_channels(filename):
  '''
  Reads the specified file and returns its number of channels
  '''
  f = open(filename)
  line = f.readline()
  f.close()
  num_channels = len(line.split()) / 2
  return num_channels

#-------------------------------------------------------------------------------
# Get the min and max ranges for the X and Y axes to mantain the
# same visualization ranges of the noise curves.
def nc_get_min_max(filename):
  '''
  Returns the minimum and maximum ranges for
  the X and Y axes
  '''
  x_min, x_max, y_min, y_max = 1E9, -1E9, 1E9, -1E9

  # Read data
  f = open(filename, 'r')

  EOF = False
  lines = []
  while not EOF:
      line = f.readline()
      s = line.split()
      EOF = (line == '')
      lineStrip = line.strip()
      isWhiteLine = (not EOF and lineStrip == '')
      isComment = lineStrip.startswith('#')
      if not (EOF or isWhiteLine or isComment):
          lines.append(s)
  #
  f.close()

  # Guess number number of channels
  numBins = len(lines)
  if numBins > 0:
      numChannels = len(lines[0])/2
  else:
      numChannels = 0

  # Read data values
  for b in range(numBins):
      line = lines[b]
      #
      for ch in range(numChannels):
          x_value = line[ch].strip().upper()
          y_value = line[ch+numChannels].strip().upper()
          #
          if x_value.upper() != 'X' and y_value.upper() != 'X':
              x = float(x_value)
              y = float(y_value)
              if x < x_min:
                  x_min = x
              if y < y_min:
                  y_min = y
              if x > x_max:
                  x_max = x
              if y > y_max:
                  y_max = y
  #
  return x_min, x_max, y_min, y_max


#-------------------------------------------------------------------------------
if __name__ == '__main__':
  
  if len(sys.argv)==1:
    nbscales = 1
  else:
    nbscales = int(sys.argv[1])
  
  # Get number of channels
  num_channels = get_num_channels('denoised_noiseCurves_H_0.txt')

  # Get noise curve bounds
  x_min, x_max, y_min, y_max = 1E9, -1E9, 1E9, -1E9
  for i in range(nbscales):
      for C in ["L", "H"]:
          filename = "denoised_noiseCurves_%s_%d.txt" % ((C, i))
          x_min_im, x_max_im,  y_min_im, y_max_im =  nc_get_min_max(filename)
          x_min = min(x_min, x_min_im)
          x_max = max(x_max, x_max_im)
          y_min = min(y_min, y_min_im)
          y_max = max(y_max, y_max_im)


  base_dir   = os.path.dirname(os.path.abspath(__file__))
  script_dir = os.path.join(base_dir,'..','scripts')
  # Generate noise curve figures
  for i in range(nbscales):
      filename = 'denoised_noiseCurves_H_%d.txt' % i
      for C in ["L", "H"]:
          estimation = "denoised_noiseCurves_%s_%d.txt" % ((C, i))
          figure = "denoised_noiseCurves_%s_%d.png" % ((C, i))
          os.system(script_dir+'/writeNoiseCurve.sh '+  
                    estimation            +
                    ' %s ' % num_channels +
                    ' %f ' % (x_min*0.9)  +
                    ' %f ' % (x_max*1.1)  +
                    ' %f ' % (y_min*0.9)  +
                    ' %f ' % (y_max*1.1)  +
                          figure)



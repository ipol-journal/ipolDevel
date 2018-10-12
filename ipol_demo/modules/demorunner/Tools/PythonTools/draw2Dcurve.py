#!/usr/bin/env python3
# -*- coding: utf-8 -*-

# GNU General Public Licence (GPL)
# 
# This program is free software; you can redistribute it and/or modify it under
# the terms of the GNU General Public License as published by the Free Software
# Foundation; either version 2 of the License, or (at your option) any later
# version.
# This program is distributed in the hope that it will be useful, but WITHOUT
# ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS
# FOR A PARTICULAR PURPOSE.  See the GNU General Public License for more
# details.
# You should have received a copy of the GNU General Public License along with
# this program; if not, write to the Free Software Foundation, Inc., 59 Temple
# Place, Suite 330, Boston, MA  02111-1307  USA
#

# Miguel Colom
# http://mcolom.info

__author__  = '''Miguel Colom'''
__docformat__ = 'plaintext'

import optparse
import sys

import numpy as np

import matplotlib as mpl
import matplotlib.pyplot as plt
from cycler import cycler

plt.switch_backend('Agg')



# Set color cycle
mpl.rcParams['axes.prop_cycle'] = cycler('color', ['r', 'g', 'b', 'c', 'm', 'y', 'k', '#67d100'])   

# Parse program arguments
parser = optparse.OptionParser()
#
const_NO_VALUE = -9E9
#
parser.add_option('--output', help='output PNG file', default='curve.png')
parser.add_option('--title', help='title', default='Title')
parser.add_option('--xName', help='X-axis name', default='X-axis')
parser.add_option('--yName', help='Y-axis name', default='Y-axis')
parser.add_option('--x0', help='X-axis first value', default=const_NO_VALUE)
parser.add_option('--x1', help='X-axis last value', default=const_NO_VALUE)
parser.add_option('--y0', help='Y-axis first value', default=const_NO_VALUE)
parser.add_option('--y1', help='Y-axis last value', default=const_NO_VALUE)
parser.add_option('--legend', help='Legend for each data channel', default='')
parser.add_option('--grid', help='use grid', default=1)
parser.add_option('--markers', help='use markers', default=1)
parser.add_option('--markersize', help='marker size', default=5)
parser.add_option('--style', help='use custom line style', default='')

(opts, args) = parser.parse_args()

if len(args) < 1:
    print("Error: no input files specified!\n")
    parser.print_help()
    sys.exit(-1)

# Read parameters
outputName = opts.output
title = opts.title
x0 = float(opts.x0)
x1 = float(opts.x1)
y0 = float(opts.y0)
y1 = float(opts.y1)
grid = (int(opts.grid) > 0)
xName = opts.xName
yName = opts.yName
legend = opts.legend
useMarkers = (int(opts.markers) > 0)
markersize = float(opts.markersize)
lines_style = opts.style
  
if not outputName.lower().endswith('.png'):
    #print "Error: only PNG format accepted\n"
    #sys.exit(-1)
    pass

# Init plot
plt.close('all')
  
fig = plt.figure()
plt.grid(b=grid)
plt.xlabel(xName)
plt.ylabel(yName)
if title == '':
  plt.title('Noise curve')
else:
  plt.title(title)

# Read all input files
is_first_loop = True
for filename in args:
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
  
  # Guess number of channels
  numBins = len(lines)
  if numBins > 0:
    numChannels = len(lines[0])//2
  else:
    numChannels = 0
  
  # Check number of channels
  for i in range(numBins):
    if len(lines[i])/2 != numChannels:
      print('Error: in line ' + str(i+1) + ': number of channels doesn\'t match!')
      sys.exit(-2)
  #
  # Check if number of channels keeps the same for all input files
  if is_first_loop:
    num_channels_all = numChannels
  else: # Num channels check
    if numChannels != num_channels_all:
      print('Error: number of channels mismatch for file ' + filename)
      exit(-2)

  # Read data values
  X = np.zeros((numChannels, numBins))
  Y = np.zeros((numChannels, numBins))
  indexes = np.zeros(numChannels, dtype=int)
  for bin in range(numBins):
    line = lines[bin]
    for ch in range(numChannels):
      x_value = line[ch].strip().upper()
      y_value = line[ch+numChannels].strip().upper()
      if x_value.upper() != 'X' and y_value.upper() != 'X':
        index = indexes[ch]
        X[ch, index] = x_value
        Y[ch, index] = y_value
        indexes[ch] += 1

  if is_first_loop:
    if legend != '':
      legendNames = legend.split(',')
      if len(legendNames) != numChannels:
        print('Error: number of legends doesn\'t match number of channels!')
        sys.exit(-3)
    #
    if lines_style != '':
      lines_style_split = lines_style.split(',')
      if len(lines_style_split)/2 != numChannels:
        print('Error: number of parameters in styles doesn\'t match number of channels!')
        sys.exit(-4)
      #
      lines_colors = []
      lines_sty = []
      for i in range(len(lines_style_split)//2):
        lines_colors.append(lines_style_split[2*i])
        lines_sty.append(lines_style_split[2*i+1])

  # Plot curves
  for ch in range(numChannels):
    kwargs = {}
    if useMarkers:
      kwargs['marker'] = 'o'
      kwargs['markersize'] = markersize
  
    if lines_style != '':
      kwargs['color'] = lines_colors[ch]
      kwargs['linestyle'] = lines_sty[ch]
  
    if legend != '':
      chName = legendNames[ch]
      kwargs['label'] = chName
  
    plt.plot(X[ch,0:indexes[ch]], Y[ch,0:indexes[ch]], **kwargs)

  # Horizontal and vertical limits
  l0, l1 = plt.xlim()
  if x0 != const_NO_VALUE:
    l0 = x0
  if x1 != const_NO_VALUE:
    l1 = x1
  plt.xlim((l0, l1))
  
  l0, l1 = plt.ylim()
  if y0 != const_NO_VALUE:
    l0 = y0
  if y1 != const_NO_VALUE:
    l1 = y1
  plt.ylim((l0, l1))


  if is_first_loop:
    if legend != '':
      leg = plt.legend(loc='best', fancybox=True)
      leg.get_frame().set_alpha(0.7)
      leg.get_frame().set_facecolor('0.85')

  is_first_loop = False
  
# Save result
fig.savefig(outputName)

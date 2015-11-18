#! /usr/bin/python

import os, sys
CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
# go up 3 levels ...
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(CURRENT_DIR))))

from lib import config
from lib import image
import PIL.Image

def check_grayimage(nameimage):
  """
  Check if image is monochrome (1 channel or 3 identical channels)
  """
  isGray = True

  im = PIL.Image.open(nameimage)
  if im.mode not in ("L", "RGB"):
      raise ValueError("Unsuported image mode for histogram computation")

  if im.mode == "RGB":
      pix = im.load()
      size = im.size
      for y in range(0, size[1]):
          if not isGray:
              break
          for x in range(0, size[0]):
              if not isGray:
                  break
              if (pix[x, y][0] != pix[x, y][1]) or \
                  (pix[x, y][0] != pix[x, y][2]):
                  isGray = False


  return isGray

#-------------------------------------------------------------------------------
if __name__ == '__main__':

  #check if input image is monochrome
  isGray = check_grayimage('input_0.sel.png')
  #cfg = config.cfg_open('.')
  #cfg['info']['isgray'] = isGray

  #Compute histograms of images
  im0 = image('input_0.sel.png')
  imI = image('output_I.png')
  if not isGray:
      imRGB = image('output_RGB.png')
  #compute maximum of histogram values
  maxH = im0.max_histogram(option="all")
  #draw all the histograms using the same reference maximum
  im0.histogram(option="all", maxRef=maxH)
  im0.save('input_0_sel_hist.png')
  imI.histogram(option="all", maxRef=maxH)
  imI.save('output_I_hist.png')
  if not isGray:
      imRGB.histogram(option="all", maxRef=maxH)
      imRGB.save('output_RGB_hist.png')

  sizeYhist = image('input_0_sel_hist.png').size[1]
  # add 60 pixels to the histogram size to take margin into account
  #sizeYmax = max(sizeY, sizeYhist+60)
    
  #cfg['info']['displayheight'] = sizeYmax
  #cfg.save()
  
  #cfg['param']['stdout'] = \
      #open('stdout.txt', 'r').read()

#! /usr/bin/python

import os.path
import PIL.Image
import PIL.ImageOps
import getopt
import sys

def InvertImage(imfile):
  im = PIL.Image.open(imfile)
  im = PIL.ImageOps.invert(im)
  im.save(imfile)

if __name__ == '__main__':
  try:
    opts, args = getopt.getopt(sys.argv[1:], "i:", ["invert="])
  except getopt.GetoptError as err:
    usage()
    sys.exit(2)

  #print opts
  invert = 0
  for o, a in opts:
    if o in ("-i","--invert"):
      invert = int(a)
  if invert>0:
    for imfile in args:
      #print "inverting image ", imfile
      InvertImage(imfile)
    

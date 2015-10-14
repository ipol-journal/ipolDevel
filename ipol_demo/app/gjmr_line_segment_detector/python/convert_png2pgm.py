#! /usr/bin/python

import PIL.Image
import sys

if __name__ == '__main__':
  imfile = sys.argv[1]
  im = PIL.Image.open(imfile+".png")
  im.save(imfile+".pgm")

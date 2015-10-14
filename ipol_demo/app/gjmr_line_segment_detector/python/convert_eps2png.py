#! /usr/bin/python

import PIL.Image
import PIL.ImageOps
import sys, os


if __name__ == '__main__':
  
  imfile = sys.argv[1]

  # convert the EPS result into a PNG image
  try:
    os.system('/usr/bin/gs -dNOPAUSE -dBATCH -sDEVICE=pnggray -dGraphicsAlphaBits=4 -r72 -dEPSCrop -sOutputFile=output.png output.eps')
    im = PIL.Image.open(imfile+".png")
    im = im.convert('L') # corresponds to '1x8i'
    im = PIL.ImageOps.invert(im)
    im.save(imfile+"-inv.png")
  except Exception:
    print >> sys.stderr, "eps->png conversion failed, GS is probably missing on this system"
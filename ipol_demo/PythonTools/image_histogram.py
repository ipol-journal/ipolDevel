#!/usr/bin/python
#
# compute and save image histograms for a set of images
# using the maximum of the first image as maxref
# histograms are save as the image basename + "_hist.png"
#

import os, sys
CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
# go up 1 level ...
sys.path.append(os.path.dirname(CURRENT_DIR))

from lib import image

#-------------------------------------------------------------------------------
if __name__ == '__main__':

  if len(sys.argv)>1:
    # process first image
    try:
      imname = sys.argv[1]
      print imname
      im = image(imname)
      maxH = im.max_histogram(option="all")
      im.histogram(option="all", maxRef=maxH)
      im.save(os.path.splitext(imname)[0]+"_hist.png")
      
      for imname in sys.argv[2:]:
        try:
          im = image(imname)
          im.histogram(option="all", maxRef=maxH)
          im.save(os.path.splitext(imname)[0]+"_hist.png")
        except:
          print "failed to create histogram for ", imname
    except:
      print "Histogram creation failed"
  else:
    print "need at least one input image to process"

#!/usr/bin/python
#
# compute and save image histograms for a set of images
# using the maximum of the first image as maxref
# histograms are save as the image basename + "_hist.png"
#

import os, sys
# go up 1 level ...
sys.path.append(os.path.join(os.path.dirname(os.path.realpath(__file__)), ".."))

from image import image
import logging

#-------------------------------------------------------------------------------
if __name__ == '__main__':

  if len(sys.argv)>1:
    # process first image
    try:
      imname = sys.argv[1]
      print imname
      im = image(imname)
      
      # histogram does not allow RGBA so convert to RGB
      if im.im.mode=="RGBA":
          im.convert("3x8i")
      
      try:
        maxH = im.max_histogram(option="all")
        im.histogram(option="all", maxRef=maxH)
      except Exception as e:
        logging.exception( "Histogram creation failed ");
        
      im.save(os.path.splitext(imname)[0]+"_hist.png")
      
      for imname in sys.argv[2:]:
        try:
          im = image(imname)
          # histogram does not allow RGBA so convert to RGB
          if im.im.mode=="RGBA":
            im.convert("3x8i")
          try:
            im.histogram(option="all", maxRef=maxH)
          except Exception as e:
            logging.exception( "Histogram creation failed ");
          im.save(os.path.splitext(imname)[0]+"_hist.png")
        except Exception as e:
          print "failed to create histogram for ", imname, " ", e
    except Exception as e:
      logging.exception( "Histogram creation failed ");
  else:
    print "need at least one input image to process"

#!/usr/bin/python
#
# simple script to count lines in a file and save the result to a text file
#
# usage:
# count_lines.py input output.txt
#

import sys

#-------------------------------------------------------------------------------
if __name__ == '__main__':
  
  # save the number of detections
  if len(sys.argv)>2:
    input_file = sys.argv[1]
    output_file = sys.argv[2]
    f = open(output_file,'w')
    s = sum(1 for line in open(sys.argv[1])) 
    f.write( "{0}".format(s))
    f.close()
    

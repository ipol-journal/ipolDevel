#! /usr/bin/python

'''
Used by the demos which write lines to read the lines from the
parameters file and save in line_primitives.dat
'''
import json
import os
import sys

#-------------------------------------------------------------------------------
if __name__ != '__main__':
    sys.exit(0)

# read json param files
params_file = open("params.json")
params = json.load(params_file)

# save the line information text file
if not "drawlines" in params:
    print "Error: missing 'drawlines' parameter in the JSON file"
    sys.exit(-1)

# write the poly points in a file
ofile = file("line_primitives.dat", "w")
lines = params["drawlines"]

ofile.writelines("%i\n" % len(lines))

for ii in range(0, len(lines)) :
    ofile.writelines("%i\n" % len(lines[ii]) )
    ofile.writelines("%i %i \n" % (x, y) for (x, y) in lines[ii] )
ofile.close()


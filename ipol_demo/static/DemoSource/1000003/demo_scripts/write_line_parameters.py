#! /usr/bin/python

import json
import os, sys


#-------------------------------------------------------------------------------
if __name__ == '__main__':
    #

    # read json param files
    params_file = open("params.json")
    params = json.load(params_file)

    # save the line information text file
    if "drawlines" in params:

        # write the poly points in a file
        ofile = file("line_primitives.dat", "w")
        lines = params["drawlines"]

        ofile.writelines("%i\n" % len(lines) )

        for ii in range(0, len(lines)) :
            ofile.writelines("%i\n" % len(lines[ii]) )
            ofile.writelines("%i %i \n" % (x, y) for (x, y) in lines[ii] )
        ofile.close()
    else
        print "Error: missing drawlines parameter"
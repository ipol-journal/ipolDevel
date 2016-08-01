#!/usr/bin/python
#
# ply2obj.py : Convert a .ply mesh (Stanford) to a .obj mesh (wavefront)
#
#
# Copyright (C) 2010  Clement Creusot
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.


import sys
import os
import string


def print_help():
    print "Usage: "+os.path.basename(sys.argv[0])+" filein.ply [fileout.obj]"
    sys.exit()

def print_error(str):
    print "ERROR: "+str
    sys.exit()

if (len(sys.argv) < 2):
    print_help()

plyfilename = sys.argv[1];
objfilename = sys.argv[1].replace(".ply","")+".obj"; 
if (len(sys.argv) == 3):
    objfilename = sys.argv[2];


objfile = open(objfilename, "w")
plyfile = open(plyfilename, "r")

line = plyfile.readline()
tab = string.split(line)
if cmp(tab[0],"ply") != 0:
    print_error("Bad PLY file header")

# Read header
pointNb = -1
faceNb = -1
line = plyfile.readline()
while line != "":
    t = string.split(line)
    if t!= []:
        if t[0][0] != '#':
            if cmp(t[0], "element")==0 and cmp(t[1], "vertex")==0:
                pointNb = int(t[2])
            if cmp(t[0], "element")==0 and cmp(t[1], "face")==0:
                faceNb = int(t[2])
            if cmp(t[0], "end_header")==0:
                break
    line = plyfile.readline()

if pointNb == -1 or faceNb == -1:
    print_error("Imcomplete PLY file header")

objfile.write("# File type: ASCII OBJ\n")

for i in range(pointNb):
    line = plyfile.readline()
    t = string.split(line)
    objfile.write("v "+t[0]+" "+t[1]+" "+t[2]+"\n")


for i in range(faceNb):
    line = plyfile.readline()
    t = string.split(line)
    ## In obj files the first vertex is 1 not 0
    polyDegree = int(t[0]) # number of vertex per polygone
    tOut = []        
    for j in range(polyDegree):
        tOut.append(str(int(t[j+1]) +1))
    objfile.write("f "+string.join(tOut," ")+"\n")

objfile.close()
plyfile.close()

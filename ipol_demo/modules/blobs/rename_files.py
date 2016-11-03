#!/usr/bin/python

"""
A little script for renaming files !
"""

import glob
import os

def get_new_path(filename, create_dir=True, depth=2):
    """
    This method creates a new fullpath for a given file path,
    where new directories are created for each 'depth' first letters
    of the filename, for example:
      input  is /tmp/abvddff.png
      output is /tmp/a/b/v/d/abvddff.png
      where the full path /tmp/a/b/v/d has been created

      if the filename name starts with thumbnail_, use the name without
      'thumbnail_' to define its new path
      for example:
      /tmp/thumbnail_abvddff.png will be /tmpl/a/b/v/d/thumbnail_abvddff.png

    """
    prefix = ""
    bname = os.path.basename(filename)
    if bname.startswith("thumbnail_"):
        prefix = "thumbnail_"
        bname = bname[len(prefix):]
    dname = os.path.dirname(filename)
    fname = bname.split(".")[0]
    l = min(len(fname), depth)
    subdirs = '/'.join(list(fname[:l]))
    new_dname = dname + '/' + subdirs + '/'
    if create_dir and not os.path.isdir(new_dname):
        os.makedirs(new_dname)
    return new_dname + prefix + bname

def main():
    """
    Function to be called when direct use of the script.
    """
    print "start"
    for filename in glob.glob("./*.*"):
        new_filename = get_new_path(filename)
        print filename, " --> ", new_filename
        os.rename(filename, new_filename)

if __name__ == '__main__':
    main()

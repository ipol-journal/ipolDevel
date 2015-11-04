#!/usr/bin/python

import os,sys,glob,shutil
import ConfigParser

#-------------------------------------------------------------------------------
if __name__ == '__main__':
  # list directories in flowpairs
  base_dir = "./flowpairs"
  new_dir = "./created_input"

  # get configs
  config = ConfigParser.ConfigParser()
  config.read(os.path.join(base_dir,"index.cfg"))
  
  # new config
  new_config = ConfigParser.ConfigParser()

  l = os.listdir(base_dir)
  for d in l:
    print "-----"
    if os.path.isdir(os.path.join(base_dir,d)):
      print d
      # search in config
      found=False
      found_section=''
      for s in config.sections():
        if d==config.get(s,'subdir'):
          print "found path in section ",s," title=",config.get(s,'title')
          found         = True
          found_section = s
      if found:
        # create dir
        blobset_dir = os.path.join(new_dir,d)
        try:
          os.makedirs(blobset_dir)
        except OSError:
          pass
        
        new_config.add_section(found_section)
        new_config.set(found_section,'title',
                       config.get(found_section,'title'))
        files = ""
        # list images there
        # list png
        pngs = sorted(glob.glob(os.path.join(base_dir,d,"*.png")))
        for f in pngs: 
          # copy file
          shutil.copy(f,blobset_dir)
          files += "{0}:".format(pngs.index(f))+f[len(base_dir)+1:]+" "
        # list tiffs
        tiffs = glob.glob(os.path.join(base_dir,d,"*.tiff"))
        for f in tiffs: 
          # copy file
          shutil.copy(f,blobset_dir)
          files += "2:"+f[len(base_dir)+1:]+" "
        new_config.set(found_section,'files',files)
        
      else:
        print "*** NOT FOUND ***"
        
    cfgfile = open(os.path.join(new_dir,"index.cfg"),'w')
    new_config.write(cfgfile)
    cfgfile.close()
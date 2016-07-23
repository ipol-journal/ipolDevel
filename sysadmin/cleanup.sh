#!/bin/bash

# Very simple script to clean temporal run directories
# Miguel Colom, 2016

find "/home/ipol/ipolDevel/ipol_demo/modules/demorunner/run/" -maxdepth 3 -ctime +30 -path '*/tmp/*' -type d -exec rm -rf {} \;


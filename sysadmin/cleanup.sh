#!/bin/bash

# Very simple script to clean temporal run directories
# Miguel Colom, 2016

find "/home/ipol/ipolDevel/shared_folder/run/" -maxdepth 2 -ctime +30 -type d -exec rm -rf {} \;

#!/bin/bash

# Very simple script to clean temporal run directories
# Miguel Colom, 2016
BASE="/home/ipol/ipolDevel/shared_folder/run/"

find ${BASE} -maxdepth 2 -ctime +30 -type d -exec rm -rf {} \;

# Remove demo directories without any executions
find ${BASE} -maxdepth 1 -type d -empty -exec rm -rf {} \;

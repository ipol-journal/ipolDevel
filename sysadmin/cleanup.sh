#!/bin/bash

# Very simple script to clean temporal run directories
# Miguel Colom, 2016
BASE="/home/ipol/ipolDevel/shared_folder/run/"

find ${BASE} -maxdepth 2 -ctime +30 -type d -exec rm -rf {} \;

# Remove demo directories without any executions
find ${BASE} -maxdepth 1 -type d -empty -exec rm -rf {} \;

# Remove error archive ZIP files older than 30 days
ERROR_ARCHIVES="/home/ipol/ipolDevel/shared_folder/error_archives/"

if [ -d "$ERROR_ARCHIVES" ]; then
    find ${ERROR_ARCHIVES} -type f -name "*.zip" -mtime +30 -exec rm -f {} \;
fi
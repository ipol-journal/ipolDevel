#!/bin/bash

sharedFolder="/home/ipol/ipolDevel/shared_folder"

if [ $(mount | grep -c shared_folder) -eq 0 ];then
    sshfs ipol_core:$sharedFolder $sharedFolder -o uid=$(id -u ipol),gid=$(id -g ipol)
fi

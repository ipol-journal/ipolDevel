#!/bin/bash

# Very simple script to make backups
# Miguel Colom, 2016

backupsLocation="/home/ipol/backups"
folderToBackup="/home/ipol/ipolDevel"

snapshot=$(date +"snapshot_%q-%Y")
snapshotName=${backupsLocation}/${snapshot}

backupFilename=$(date +"backup_%m-%d-%Y.tgz")
fullFilename=${backupsLocation}/${backupFilename}

mkdir -p ${backupsLocation}
tar -g $snapshotName -cpzf $fullFilename $folderToBackup

##############
# To restore a backup pipe a cat with all .tgz files into tar extract 
# command and specify a destination path (restore_folder)
##############

# cat *.tgz | tar xvfz - -g /dev/null --ignore-zeros -C restore_folder

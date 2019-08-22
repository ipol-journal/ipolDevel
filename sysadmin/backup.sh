#!/bin/bash

# Very simple script to make backups
# Miguel Colom, 2016

backupsFolder="/home/ipol/backups"
folderToBackup="/home/ipol/ipolDevel"

snapshot=$(date +"snapshot_%Y-%q")
yearPeriod=$(date +"%Y-%q")

snapshotName=${backupsFolder}/${yearPeriod}/${snapshot}

backupFilename=$(date +"backup_%m-%d-%Y.tgz")
fullFilename=${backupsFolder}/${yearPeriod}/${backupFilename}

mkdir -p ${backupsFolder}/${yearPeriod}
tar -g $snapshotName -cpzf $fullFilename $folderToBackup

##############
# To restore a backup pipe a cat with all .tgz files into tar extract 
# command and specify a destination path (restore_folder)
##############

# cat *.tgz | tar xvfz - -g /dev/null --ignore-zeros -C restore_folder

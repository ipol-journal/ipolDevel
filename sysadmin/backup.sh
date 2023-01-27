#!/bin/bash

# Very simple script to make backups
# Miguel Colom, 2016

backupsFolder="/home/ipol/backups"
ipolDevelCopyPath=${backupsFolder}/ipolDevelCopy
yearPeriod=$(date +"%Y-%q")

# Backup modules databases
modulesWithDB=("archive" "blobs" "core")
modulesPath="/home/ipol/ipolDevel/ipol_demo/modules/"
for module in ${modulesWithDB[@]}; do
  sqlite3 $modulesPath"$module"/db/$module.db ".backup '${modulesPath}${module}/db/${module}_backup.db'"
done
echo "Databases backed up"


mkdir -p ${ipolDevelCopyPath}
rsync -azuP --delete --exclude 'shared_folder' /home/ipol/ipolDevel ${ipolDevelCopyPath}
echo "ipolDevel cloned to ${ipolDevelCopyPath}"

snapshot=$(date +"snapshot_%Y-%q")
snapshotName=${backupsFolder}/${yearPeriod}/${snapshot}

backupFilename=$(date +"backup_%m-%d-%Y.tgz")
fullFilename=${backupsFolder}/${yearPeriod}/${backupFilename}

mkdir -p $backupsFolder/$yearPeriod
tar -g $snapshotName -czf $fullFilename $ipolDevelCopyPath
echo "ipolDevel clone compressed into: $fullFilename"

##############
# To restore a backup pipe a cat with all .tgz files into tar extract 
# command and specify a destination path (restore_folder)
# tar xvpzf tar_file1.tgz -g /dev/null --ignore-zeros -C restore_folder 
##############
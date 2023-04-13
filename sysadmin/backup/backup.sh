#!/bin/bash

# Very simple script to make backups
# Miguel Colom, 2016

user=ipol # Remember to set it back to "ipol" after testing
modulesPath=/home/${user}/ipolDevel/ipol_demo/modules
ipolDevelCopyPath=/home/${user}/backups/ipolDevelCopy
ipolDevelCopyModulesPath=${ipolDevelCopyPath}/ipolDevel/ipol_demo/modules

# Clone all
mkdir -p ${ipolDevelCopyPath}
rsync -azuP --delete --exclude 'shared_folder' /home/${user}/ipolDevel ${ipolDevelCopyPath}
echo "ipolDevel cloned to ${ipolDevelCopyPath}"

# Export databases
databases=("blobs/db/blobs.db" "core/db/demoinfo.db" "archive/db/archive.db")

for database in ${databases[@]}; do
  sqlite3 $modulesPath/${database} ".backup '${ipolDevelCopyModulesPath}/${database}'"
  cp $modulesPath/${database} ${ipolDevelCopyModulesPath}/${database}.bak
done
echo "Databases backed up"

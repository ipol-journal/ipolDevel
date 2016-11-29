#!/bin/bash

# This script is executed by root on reboot

me=ipol #$(whoami)
modulesDir="/home/${me}/ipolDevel/ipol_demo/modules/"
sharedFolder="/home/${me}/ipolDevel/shared_folder"

# File with the modules name
modules="modules.txt"

today=$(date)
machine_hostname=$(hostname)

# Start nginx
/usr/sbin/nginx

# Start every IPOL module
while read -r module
do
    sudo -u ${me} ${modulesDir}${module}/start.sh
done < ${modules}

# Mount shared folder
if [ $(hostname) != "ipol_core" ]
then
    sudo -u ${me} sshfs ipol_core:$sharedFolder $sharedFolder
fi


# Send report by email
sendTo=$(cat /home/ipol/ipolDevel/sysadmin/email_tech.txt)
echo "This is the ${machine_hostname} machine. This machine has rebooted at ${today}: starting IPOL modules." | mutt -s "[${machine_hostname}] Reboot notice" -- ${sendTo}

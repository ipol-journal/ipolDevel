#!/bin/bash

# This script is executed by root on reboot

me=ipol #$(whoami)
modulesDir="/home/${me}/ipolDevel/ipol_demo/modules/"

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



# Send report by email
sendTo=$(cat /home/ipol/ipolDevel/sysadmin/email_tech.txt)
echo "This is the ${machine_hostname} machine. This machine has rebooted at ${today}: starting IPOL modules." | mutt -s "[${machine_hostname}] Reboot notice" -- ${sendTo}

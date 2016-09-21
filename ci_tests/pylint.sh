#!/bin/bash

# Pylint report
# Miguel Colom, 2016

modulesDir="ipolDevel/ipol_demo/modules/"
modules="archive blobs demoinfo demorunner proxy"
report="pylint_report.txt"

#truncate -s 0 ${report}
today=$(date)
echo "IPOL PyLint report on ${date}" > ${report}
echo >> ${report}

# PyLint test on each IPOL module
for module in ${modules}
do
    echo "**** MODULE: ${module}" >> ${report}
    pylint ~/${modulesDir}${module}/*.py >> ${report}
done

# Core (just for now, since it's not a real module yet)
pylint ~/ipolDevel/ipol_demo/demo.py ~/ipolDevel/ipol_demo/lib/*.py >> ${report}

# Send report by email
host=$(hostname)
sendTo=$(cat send_to.txt)
echo $sendTo
exit

echo "PyLint report from ${host}" | mutt -a ${report} -s "[ipolDevel] CI test: PyLint report" -- ${sendTo}

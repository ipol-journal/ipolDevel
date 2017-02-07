#!/bin/bash

# Pylint report
# Miguel Colom, 2016

me=ipol #$(whoami)
modulesDir="/home/${me}/ipolDevel/ipol_demo/modules/"
report="/home/${me}/ipolDevel/ci_tests/pylint_report.txt"
modules="core archive blobs demoinfo demorunner dispatcher"

#truncate -s 0 ${report}
today=$(date)
echo "IPOL PyLint report on ${today}" > ${report}
echo >> ${report}

# PyLint test on each IPOL module
for module in ${modules}
do
    echo "**** MODULE: ${module}" >> ${report}
    pylint --rcfile=/home/${me}/ipolDevel/ci_tests/pylintrc ${modulesDir}${module}/*.py >> ${report}
done

# Send report by email
sendTo=$(cat /home/ipol/ipolDevel/ci_tests/send_to.txt)
echo "PyLint report" | mutt -a ${report} -s "[ipolDevel] CI test: PyLint" -- ${sendTo}

#!/bin/bash

# Pylint report
# Miguel Colom, 2016

me=$(whoami)
ci_folder="/home/${me}/ipolDevel/ci_tests"
modulesDir="/home/${me}/ipolDevel/ipol_demo/modules/"
report="/home/${me}/ipolDevel/ci_tests/pylint_report.txt"
modules="core archive blobs demoinfo demorunner dispatcher conversion"

#truncate -s 0 ${report}
today=$(date)
echo "IPOL PyLint report on ${today}" > ${report}
echo >> ${report}

# PyLint test on each IPOL module
cur_dir=$(pwd)

if [ ! -d "${ci_folder}/venv" ]; then
    python3 -m virtualenv ${ci_folder}/venv
    source ${ci_folder}/venv/bin/activate
    pip install -r ${ci_folder}/requirements.txt
fi

for module in ${modules}
do
    echo "**** MODULE: ${module}" >> ${report}
    cd ${modulesDir}${module}
    # Lint the module after activating its virtualenv
    source ${ci_folder}/venv/bin/activate
    pylint --rcfile=${ci_folder}/pylintrc *.py >> ${report}
    deactivate
    cd ${cur_dir}
done

# Send report by email
sendTo=$(cat /home/ipol/ipolDevel/ci_tests/send_to.txt)
echo "PyLint report" | mutt -a ${report} -s "[ipolDevel] CI test: PyLint" -- ${sendTo}

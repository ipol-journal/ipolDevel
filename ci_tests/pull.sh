#!/usr/bin/env bash

host=$(hostname)
today=$(date)
user=$(whoami)

# Git pull
cd /home/${user}/ipolDevel/
git pull

# Send email to warn about tests failure
function send_email () {
    msg="$*"
    sendTo=$(cat /home/${user}/ipolDevel/ci_tests/send_to.txt)
    echo -e "This is the ${host} machine. The tests failed on ${today}:\n${msg}" | mutt -s "[${host}] Test failed" -- ${sendTo}
}

if [ ! -d "/home/${user}/ipolDevel/ci_tests/venv" ]; then
    python3.9 -m virtualenv ci_tests/venv
    source ci_tests/venv/bin/activate
    pip install -r ci_tests/requirements.txt
fi

# Executes all the tests for integration and production
if [ $host == "integration" ] || [ $host == "ipolcore" ];then
    source ci_tests/venv/bin/activate
    out=$(python /home/${user}/ipolDevel/ci_tests/all.py)
    if [ $? -ne 0 ];then
        send_email "$out"
    fi
    deactivate
fi
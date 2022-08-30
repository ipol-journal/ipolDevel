#!/usr/bin/env bash

host=$(hostname)
today=$(date)

function send_email () {
    msg="$*"
    sendTo=$(cat /home/ipol/ipolDevel/ci_tests/send_to.txt)
    echo -e "This is the ${host} machine. The compilation tests failed on ${today}:\n${msg}" | mutt -s "[${host}] Compilation failed" -- ${sendTo}
}

ci_tests_dir=/home/ipol/ipolDevel/ci_tests

out=$(python3 ${ci_tests_dir}/published_codes_compilation_test.py)
if [ $? -ne 0 ];then
    send_email "$out"
fi


#!/usr/bin/env bash

today=$(date)

# Git pull

function send_email () {
    msg="$*"
    sendTo=$(cat /home/ipol/ipolDevel/ci_tests/send_to.txt)
    echo -e "This is the ${host} machine. The tests failed on ${today}:\n${msg}" | mutt -s "[${host}] Test failed" -- ${sendTo}
}

out=$(python /home/ipol/ipolDevel/ci_tests/published_codes_compilation_test.py)
if [ $? -ne 0 ];then
    send_email "$out"
fi



#!/usr/bin/env bash

host=$(hostname)
today=$(date)

function send_email () {
    msg="$*"
    sendTo=$(cat /home/ipol/ipolDevel/ci_tests/send_to.txt)
    echo -e "This is the ${host} machine. The compilation tests failed on ${today}:\n${msg}" | mutt -s "[${host}] Compilation failed" -- ${sendTo}
}

script_dir=$( cd -- "$( dirname -- "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )
ignored_ids_file_path=$(realpath ignored_ids.txt)

out=$(python3 /home/ipol/ipolDevel/ci_tests/published_codes_compilation_test.py ${ignored_ids_file_path})
if [ $? -ne 0 ];then
    send_email "$out"
fi


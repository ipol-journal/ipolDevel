#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import getpass
import os
import random
import shlex
import time
from subprocess import PIPE, Popen

user = getpass.getuser()

system_test = '/home/{}/ipolDevel/ci_tests/system.py'.format(user)
archive_test = '/home/{}/ipolDevel/ipol_demo/modules/archive/test.py'.format(user)
blobs_test = '/home/{}/ipolDevel/ipol_demo/modules/blobs/test.py'.format(user)
demorunner_test = '/home/{}/ipolDevel/ipol_demo/modules/demorunner/test.py'.format(user)

resources = '/home/{}/ipolDevel/ci_tests/resources'.format(user)
demorunners = '/home/{}/ipolDevel/ipol_demo/modules/config_common/demorunners.xml'.format(user)
shared_folder = '/home/{}/ipolDevel/shared_folder'.format(user)

tests = [blobs_test, archive_test, demorunner_test, system_test]

def start():
    """
    Start the script
    """
    try:
        while not can_execute():
            # Wait random time between 5 and 10 sec to try to execute the test again
            time.sleep(5 + random.random() * 5)

        run_tests()
    finally:
        os.remove('test.lock')


def can_execute():
    """
    Check if the test can be executed. Only one test can be executed simultaneously
    """
    if os.path.isfile('test.lock'):
        return False

    open('test.lock', 'w')
    return True


def run_tests():
    """
    Execute all the tests
    """
    # wait 3 seconds to give time to restart the modules
    time.sleep(3)
    for test in tests:
        module_dir = os.path.dirname(test)
        python_dir = os.path.join(module_dir, "venv/bin/python")

        # Execute test
        cmd = shlex.split(
            " ".join([python_dir, test, resources, demorunners, shared_folder]))
        process = Popen(cmd, stdout=PIPE, stderr=PIPE)
        stdout, stderr = process.communicate()

        if process.returncode != 0:
            module_name = os.path.basename(os.path.split(test)[0])
            if module_name == 'ci_tests':
                module_name = 'System'
            print("{} test failed:".format(module_name))
            print(stderr)
            print(stdout)
            exit(process.returncode)


start()

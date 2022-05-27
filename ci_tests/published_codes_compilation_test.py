#!/usr/bin/env python3
# -*- coding: utf-8 -*-
from sys import exit
import errno
import json
import os
import shutil
import socket
import xml.etree.ElementTree as ET
import requests

import os, sys
sys.path.append(os.path.join(os.path.dirname(__file__), "../ipol_demo/modules/"))
from dispatcher.demorunnerinfo import DemoRunnerInfo
from dispatcher.policy import Policy

HOST = socket.gethostbyname(socket.gethostname())
user = 'ipol'
compilation_path = os.path.join("/", "home", user, "ipolDevel", "ci_tests", "compilation_folder")


def main():
    """
    Main
    """
    all_success = True
    demorunners = read_demorunners()
    for demo_id in get_published_demos():
        json_ddl = json.loads(get_ddl(demo_id))
        build_section = json_ddl.get('build')
        requirements = json_ddl.get('general').get('requirements')

        if build_section is None:
            print(f"Demo #{demo_id} doesn't have a build section")
            all_success = False
            continue

        if not build(demo_id, build_section, requirements, demorunners):
            all_success = False

    if all_success:
        exit(0)
    else:
        exit(-1)


def get_compilation_path(demo_id):
    """
    Get compilation path
    """
    return os.path.join(compilation_path, str(demo_id))


def create_dir(path):
    """
    Implement the UNIX shell command "mkdir -p"
    with given path as parameter.
    """
    try:
        os.makedirs(path)
    except OSError as exc:
        if exc.errno == errno.EEXIST and os.path.isdir(path):
            pass
        else:
            raise


def get_published_demos():
    """
    Get demos
    """
    resp = post(HOST, 'demoinfo', 'demo_list')
    if resp == None:
        print("Can't get the list of demos!")
        return []

    response = resp.json()
    demos = []
    if response['status'] != 'OK':
        print("ERROR: demo_list returned KO")
        return []
    for demo in response['demo_list']:
        if demo.get('state') == "published":
            demos.append(demo['editorsdemoid'])
    return demos


def get_ddl(demo_id):
    """
    Read the DDL of the demo
    """
    resp = post(HOST, 'demoinfo', 'get_ddl', params={"demo_id": demo_id})
    if resp == None:
        print(f"Can't get the DDL of demo #{demo_id}!")
        return ""

    response = resp.json()
    if response['status'] != 'OK':
        print(f"ERROR: get_ddl returned KO for demo #{demo_id}")
    last_demodescription = response.get('last_demodescription')
    return last_demodescription.get('ddl')


def build(demo_id, build_section, requirements, demorunners):
    """
    Execute the build section.
    Returns False if any build fails. True is everything's fine.
    """
    suitable_demorunners = Policy.get_suitable_demorunners(requirements, demorunners)
    for demorunner in suitable_demorunners:
        demorunner_host = demorunner.server
        params = {'ddl_build': json.dumps(build_section), 'compilation_path': get_compilation_path(demo_id)}
        response = post(demorunner_host, 'demorunner', 'test_compilation', params)

        if response == None or response.status_code == None:
            print(f"Bad response from DR={demorunner.name} when trying to build demo #{demo_id}: {str(response)}")
            return False

        if response.status_code == 200:
            json_response = response.json()            
            if json_response.get('status') == 'OK':
                continue
            else:
                print(f"Couldn't build demo #{demo_id} in DR={demorunner.name} ({json_response}).")
                return False
        else:
            msg = f"Bad HTTP response status_code from DR={demorunner.name} when trying to build demo #{demo_id}."
            if response.status_code == 504:
                msg += " HTTP error 504 (gateway timeout)"
            elif response.status_code == 404:
                msg += f" HTTP error 404 (not found)"
            else:
                msg += f" HTTP error {response.status_code}"
            print(msg)
            return False
        
    # No DR failed or KO: compilation test passed
    return True


def read_demorunners():
    """
    Read demorunners xml
    """
    demorunners = []
    tree = ET.parse(os.path.join("/", "home", user, "ipolDevel", "ipol_demo", "modules",
                                 "config_common", "demorunners.xml"))
    root = tree.getroot()
    for demorunner in root.findall('demorunner'):
        capabilities = []

        for capability in demorunner.findall('capability'):
            capabilities.append(capability.text)

        demorunner = DemoRunnerInfo(
            demorunner.find('server').text,
            demorunner.get('name'),
            demorunner.find('serverSSH').text,
            capabilities
        )

        demorunners.append(demorunner)

    return demorunners


def post(host, module, service, params=None):
    """
    Post
    """
    try:
        url = 'http://{}/api/{}/{}'.format(
            host,
            module,
            service
        )
        return requests.post(url, params=params)
    except Exception as ex:
        return None

main()

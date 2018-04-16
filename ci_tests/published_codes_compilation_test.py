#!/usr/bin/python
# -*- coding: utf-8 -*-
import socket
import xml.etree.ElementTree as ET
import errno
import requests
import json
import os
import shutil

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
            print "Demo #{} doesn't have build section".format(demo_id)
            all_success = False
            continue

        if not build(demo_id, build_section, requirements, demorunners):
            all_success = False

    if not all_success:
        exit(-1)


def get_compilation_path(demo_id):
    """
    Get compilation path
    """
    path = os.path.join(compilation_path, str(demo_id))
    create_dir(path)
    return path


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
    response = resp.json()
    demos = []
    if response['status'] != 'OK':
        print "ERROR: demo_list returned KO"
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
    response = resp.json()
    if response['status'] != 'OK':
        print "ERROR: get_ddl returned KO for demo {}".format(demo_id)
    last_demodescription = response.get('last_demodescription')
    return last_demodescription.get('ddl')


def build(demo_id, build_section, requirements, demorunners):
    """
    Execute the build section. If any build fail the method returns a False
    """
    all_success = True
    suitable_demorunners = get_suitable_demorunners(requirements, demorunners)
    for demorunner in suitable_demorunners.keys():
        demorunner_host = demorunners[demorunner].get('server')
        params = {'ddl_build': json.dumps(build_section), 'path_for_the_compilation': get_compilation_path(demo_id)}
        response = post(demorunner_host, 'demorunner', 'test_compilation', params)
        json_response = response.json()
        if json_response.get('status') != 'OK':
            all_success = False
            print "Couldn't build demo {} in {}.".format(demo_id, demorunner)
    return all_success


def get_suitable_demorunners(requirements, demorunners):
    """
    Return all the suitable demorunners
    """
    if requirements is None:
        return demorunners

    suitable_demorunners = {}
    requirements = requirements.lower().split(',')

    for dr in demorunners.keys():
        dr_capabilities = [cap.lower().strip() for cap in demorunners[dr].get('capability')]

        if all([req.strip() in dr_capabilities for req in requirements]):
            suitable_demorunners[dr] = demorunners[dr]

    return suitable_demorunners


def read_demorunners():
    """
    Read demorunners xml
    """
    dict_demorunners = {}
    tree = ET.parse(os.path.join("/", "home", user, "ipolDevel", "ipol_demo", "modules",
                                 "config_common", "demorunners.xml"))
    root = tree.getroot()
    for demorunner in root.findall('demorunner'):
        dict_tmp = {}
        list_tmp = []

        for capability in demorunner.findall('capability'):
            list_tmp.append(capability.text)

        dict_tmp["server"] = demorunner.find('server').text
        dict_tmp["serverSSH"] = demorunner.find('serverSSH').text
        dict_tmp["capability"] = list_tmp

        dict_demorunners[demorunner.get('name')] = dict_tmp

    return dict_demorunners


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
        print "ERROR: Failure in the post function - {}".format(str(ex))


main()

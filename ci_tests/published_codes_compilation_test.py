#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import errno
import json
import os
import socket
import sys
import xml.etree.ElementTree as ET
from sys import exit

import requests
from ipolutils.read_text_file import read_commented_text_file

sys.path.append(os.path.join(os.path.dirname(__file__), "../ipol_demo/modules/core/"))
from dispatcher.demorunnerinfo import DemoRunnerInfo
from dispatcher.policy import get_suitable_demorunners

HOST = socket.gethostbyname(socket.gethostname())
user = "ipol"
compilation_path = os.path.join(
    "/", "home", user, "ipolDevel", "ci_tests", "compilation_folder"
)
ignored_ids_file_path = os.path.join(os.path.dirname(sys.argv[0]), "ignored_ids.txt")


def main():
    """
    Main
    """
    all_success = True
    demorunners = read_demorunners()
    base_url = get_base_url()

    id_list = []
    if os.path.exists(ignored_ids_file_path):
        id_list = [int(id) for id in read_commented_text_file(ignored_ids_file_path)]

    for demo_id in get_published_demos():
        json_ddl = get_ddl(demo_id)
        build_section = json_ddl.get("build")
        requirements = json_ddl.get("general").get("requirements", "")

        if build_section is None:
            print(f"Demo #{demo_id} doesn't have a build section")
            all_success = False
            continue

        if demo_id in id_list:
            continue

        if requirements and "docker" in requirements.split(","):
            # don't test the compilation of docker demos since we keep images
            continue

        if not build(base_url, demo_id, build_section, requirements, demorunners):
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
    resp = requests.get(f"http://{HOST}/api/demoinfo/demos")
    if resp is None:
        print("Can't get the list of demos!")
        return []

    response = resp.json()
    demos = []
    if resp.status_code != 200:
        print("ERROR: demo returned KO")
        return []
    for demo in response:
        if demo.get("state") == "published":
            demos.append(demo["editorsdemoid"])
    return demos


def get_ddl(demo_id):
    """
    Read the DDL of the demo
    """
    resp = requests.get(f"http://{HOST}/api/demoinfo/ddl/{demo_id}")
    if resp is None:
        print(f"Can't get the DDL of demo #{demo_id}!")
        return ""

    ddl = resp.json()
    if resp.status_code != 200:
        print(f"ERROR: get_ddl returned KO for demo #{demo_id}")
    return ddl


def build(base_url, demo_id, build_section, requirements, demorunners):
    """
    Execute the build section.
    Returns False if any build fails. True is everything's fine.
    """
    suitable_demorunners = get_suitable_demorunners(requirements, demorunners)
    for demorunner in suitable_demorunners:
        params = {
            "ddl_build": json.dumps(build_section),
            "compilation_path": get_compilation_path(demo_id),
        }
        response = post(
            f"{base_url}api/demorunner/{demorunner.name}/compilations", params
        )

        if response is None or response.status_code is None:
            print(
                f"Bad response from DR={demorunner.name} when trying to build demo #{demo_id}: {str(response)}"
            )
            return False

        if response.status_code == 201:
            continue
        else:
            print(
                f"Bad HTTP response status_code from DR={demorunner.name} when trying to build demo #{demo_id}. HTTP error: {response.status_code}"
            )
            return False

    # No DR failed or KO: compilation test passed
    return True


def read_demorunners():
    """
    Read demorunners xml
    """
    demorunners = []
    tree = ET.parse(
        os.path.join(
            "/",
            "home",
            user,
            "ipolDevel",
            "ipol_demo",
            "modules",
            "config_common",
            "demorunners.xml",
        )
    )
    root = tree.getroot()
    for demorunner in root.findall("demorunner"):
        capabilities = []

        for capability in demorunner.findall("capability"):
            capabilities.append(capability.text)

        demorunner = DemoRunnerInfo(
            name=demorunner.get("name"),
            capabilities=capabilities,
        )

        demorunners.append(demorunner)

    return demorunners


def get_base_url():
    filename = os.path.join(
        "/",
        "home",
        user,
        "ipolDevel",
        "ipol_demo",
        "modules",
        "config_common",
        "modules.xml",
    )
    tree = ET.parse(filename)
    root = tree.getroot()
    element = root.find("baseURL")
    assert element is not None, f"Couldn't find <baseURL> in {filename}"
    return element.text


def post(url, params=None):
    """
    Post
    """
    try:
        return requests.post(url, params=params)
    except Exception:
        return None


main()

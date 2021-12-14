#!/usr/bin/env python3
# -*- coding: utf-8 -*-

# GNU General Public Licence (GPL)
#
# This program is free software; you can redistribute it and/or modify it under
# the terms of the GNU General Public License as published by the Free Software
# Foundation; either version 2 of the License, or (at your option) any later
# version.
# This program is distributed in the hope that it will be useful, but WITHOUT
# ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS
# FOR A PARTICULAR PURPOSE.  See the GNU General Public License for more
# details.
# You should have received a copy of the GNU General Public License along with
# this program; if not, write to the Free Software Foundation, Inc., 59 Temple
# Place, Suite 330, Boston, MA  02111-1307  USA
#

import argparse
import requests
import json
from urllib.parse import urlparse

def post(service, params=None, json=None):
    """
    Do the post to demoinfo
    """
    try:
        url = f'http://{HOST}/api/demoinfo/{service}'
        return requests.post(url, params=params, data=json)
    except Exception as ex:
        print(f"ERROR: Failure in the post function - {ex}")

def get_demo_list():
    """
    Returns the list of demos
    """
    resp = post('demo_list')
    response = resp.json()
    if response['status'] != 'OK':
        print("ERROR: demo_list returned KO")
        return
    return response['demo_list']


def read_DDL(editors_demoid):
    """
    Returs the DDL for the demo with the given editordemoid
    """
    try:
        resp = post('get_ddl', params={"demo_id": editors_demoid})
        response = resp.json()
        if response['status'] != 'OK':
            print(f"ERROR: get_ddl returned KO for demo {editors_demoid}")
            return
        if response['last_demodescription'] is None:
            return
        last_demodescription = response['last_demodescription']
        ddl_json = last_demodescription['ddl']
        return ddl_json
    except Exception as ex:
        print(f"ERROR: Failed to read DDL from {editors_demoid} - {ex}")


def check_ddl(ddl):
    """
    Check if there is any DDL
    """
    if ddl is None:
        return {"DDL": "This demo does not have any DDL"}

    ddl_json = json.loads(ddl)

    if len(ddl_json.keys()) == 0:
        return {"DDL": "No sections found"}

    return {}

def check_run_in_DDL(ddl):
    """
    Check if the run is correct
    """
    ddl_json = json.loads(ddl)

    if "run" not in ddl_json:
        return {"Run": "Missing 'run' section"}

    if isinstance(ddl_json["run"], list):
        return {"Run":"This demo has runs with the deprecated syntax"}
    return {}

def check_build_in_DDL(ddl):
    """
    Check if the build is correct
    """
    ddl_json = json.loads(ddl)

    if not 'build' in ddl_json:
        return {"Build": "Missing 'build' section"}

    ddl_build = ddl_json["build"]
    if not 'build1' in ddl_build:
        return {"Build": "'build1' section not found"}
    
    # Check every build
    i = 1
    build_i = f'build{i}'
    while build_i in ddl_build:
        construct = ddl_build[build_i].get('construct', None)
        if construct:
            if 'pip' in construct or 'install' in construct:
                return {"Build": "Demo might be using 'pip install'"}

        i += 1
        build_i = f'build{i}'

    return {}

def check_url_in_DDL(ddl):
    """
    Check the url in the build
    """
    ddl_json = json.loads(ddl)
    url = json.dumps(ddl_json["build"]).split("\"url\":")[1].split("\"")[1].strip()
    if not urlparse(url).hostname == "www.ipol.im":
        return{"URL": f"This demo is using an external resource: {url}"}
    return {}


def has_demo_extras(editors_demoid):
    """
    Check if the demo has or not demo extras and returns a boolean
    """
    resp = post('get_demo_extras_info', {"demo_id":editors_demoid})
    response = resp.json()
    if not response['status'] == 'OK':
        print("ERROR: get_demo_extras_info returned KO")
        return
    return 'url' in response # If there is a URL in the response it means there are demoExtras


def check_demo_extras(editors_demoid, ddl):
    """
    Returns a dict with the errors in the demo extras
    """
    if not has_demo_extras(editors_demoid):
        if "$DEMOEXTRAS" in ddl or "${DEMOEXTRAS}" in ddl or "CUSTOM_JS" in ddl.upper():
            return {"Demoextras": "This demo uses demo extras, but there is not any demoExtras file"}
    return {}

def get_editors(editors_demoid):
    """
    Return the list of editors
    """
    resp = post('demo_get_editors_list', {"demo_id": editors_demoid})
    response = resp.json()
    if not response['status'] == 'OK':
        print("ERROR: get_editors returned KO")
        return
    editors_list = {}
    # print(response['editor_list'][0]['name'])
    for editor in response['editor_list']:
        editors_list[editor["mail"]] = editor["name"]

    return editors_list

def check_editors(editors):
    """
    Returns a dict with the errors in the editors
    """

    if len(editors) < 1:
        return {"Editors": "This demo does not have any editor"}
    return {}


def print_errors(editors_demoid, state, title, errors, editors):
    """
    Print all the errors found
    """
    if len(errors) == 0:
        return

    print(f"Demo #{editors_demoid} \"{title.encode('utf8')}\"")
    print(f"Type: {state}")

    # Print editors
    editors_msg = []
    for editor in editors:
        editors_msg.append(f"{editors[editor].encode('utf-8')} <{editor}>")
    if len(editors_msg) > 0:
        print(f"Editors: {', '.join(editors_msg)}")

    # Print Errors
    print("Found 1 error:" if len(errors) == 1 else f"Found {len(errors)} errors:")
    for error in errors:
        print(f"    - In {error} - {errors[error]}")
    print("\n")


# Parse program arguments
###
parser = argparse.ArgumentParser()
parser.add_argument("environment")
parser.parse_args()
args = parser.parse_args()

if args.environment in ['integration', 'int', 'i']:
    HOST = "integration.ipol.im"
elif args.environment in ['production', 'prod', 'p']:
    HOST = "ipolcore.ipol.im"
elif args.environment in ['local', 'l']:
    HOST = "127.0.0.1"
else:
    print(f"Unknown environment '{args.environment}'")
    exit (-1)

demos = get_demo_list()
number_of_errors=0
number_of_wrong_demos=0
for demo in demos:
    state = demo['state']

    editors_demoid = demo['editorsdemoid']
    title = demo['title']
    errors = {}

    # Read the DDL
    ddl = read_DDL(demo['editorsdemoid'])

    # Read and check editors
    editors = get_editors(editors_demoid)
    #if state in ["production", "preprint", "workshop"]:
    errors.update(check_editors(editors))

    # Check the DDL
    errors.update(check_ddl(ddl))

    if ddl is None:
        # If there is no DDL print errors continue to the next demo
        print_errors(editors_demoid, state, title, errors, editors)
        continue

    # Check the build in the DDL
    errors.update(check_build_in_DDL(ddl))
    # Check the run in the DDL
    errors.update(check_run_in_DDL(ddl))
    # Check the url in the DDL if the demo is published
    if (demo['state'] == "published"):
        errors.update(check_url_in_DDL(ddl))
    # Check the demo extras
    errors.update(check_demo_extras(editors_demoid,ddl))

    # print errors
    print_errors(editors_demoid, state, title, errors, editors)
    if len(errors)>0:
        number_of_errors += len(errors)
        number_of_wrong_demos += 1
if number_of_wrong_demos > 0:
    print(f"Number of wrong demos:  {number_of_wrong_demos}")
    print(f"Number of total errors: {number_of_errors}")

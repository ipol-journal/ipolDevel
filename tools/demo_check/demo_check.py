#!/usr/bin/python
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

import optparse
import requests
import json
from urlparse import urlparse


def post(service, params=None, json=None):
    """
    Do the post to demoinfo
    """
    try:
        url = 'http://{}/api/demoinfo/{}'.format(
            HOST,
            service
        )
        return requests.post(url, params=params, data=json)
    except Exception as ex:
        print "ERROR: Failure in the post function - {}".format(str(ex))

def get_demo_list():
    """
    Returns the list of demos
    """
    resp = post('demo_list')
    response = resp.json()
    if response['status'] != 'OK':
        print "ERROR: demo_list returned KO"
        return
    return response['demo_list']


def read_DDL(editors_demoid):
    """
    Returs the DDL for the demo with the given editordemoid
    """
    try:
        resp = post('read_last_demodescription_from_demo', params={"demo_id": editors_demoid, "returnjsons": True})
        response = resp.json()
        if response['status'] != 'OK':
            print "ERROR: read_last_demodescription_from_demo returned KO for demo {}".format(editors_demoid)
            return
        if response['last_demodescription'] is None : return
        last_demodescription = response['last_demodescription']
        ddl_json = last_demodescription['json']
        return ddl_json
    except Exception as ex:
        print "ERROR: Failed to read DDL from {} - {}".format(editors_demoid, ex)


def check_ddl(ddl):
    """
    Check if there is any DDL
    """
    if ddl is None:
        return {"DDL":"This demo does not have any DDL"}

    return {}

def check_run_in_DDL(ddl):
    """
    Check if the run is correct
    """
    ddl_json = json.loads(ddl)

    if isinstance(ddl_json["run"], list):
        return {"Run":"This demo has runs with the deprecated syntax"}
    return {}

def check_build_in_DDL(ddl):
    """
    Check if the build is correct
    """
    ddl_json = json.loads(ddl)

    if not 'build1' in ddl_json["build"]:
        return {"Build":"This demo has builds with the deprecated syntax"}
    return {}

def check_url_in_DDL(ddl):
    """
    Check the url in the build
    """
    ddl_json = json.loads(ddl)
    url = json.dumps(ddl_json["build"]).split("\"url\":")[1].split("\"")[1].strip()
    if not urlparse(url).hostname == "www.ipol.im":
        return{"URL":"This demo is using an external resource: {}".format(url)}
    return {}


def has_demo_extras(editors_demoid):
    """
    Check if the demo has or not demo extras and returns a boolean
    """
    resp = post('get_compressed_file_url_ws', {"demo_id":editors_demoid})
    response = resp.json()
    if not response['status'] == 'OK':
        print "ERROR: get_compressed_file_url_ws returned KO"
        return
    return response['code'] == '2' # Code: 1=doesn't have demoextras, code=2 have demoextras


def check_demo_extras(editors_demoid, ddl):
    """
    Returns a dict with the errors in the demo extras
    """
    if not ("$demoextras" in ddl or "${demoextras}" in ddl):
        if has_demo_extras(editors_demoid):
            return {"Demoextras":"This demo does not use demo extras, but there is a demo extras file"}
    else:
        if not has_demo_extras(editors_demoid):
            return {"Demoextras":"This demo uses demo extras, but there is not any demo extras file"}
    return {}

def get_editors(editors_demoid):
    """
    Return the list of editors
    """
    resp = post('demo_get_editors_list', {"demo_id": editors_demoid})
    response = resp.json()
    if not response['status'] == 'OK':
        print "ERROR: get_editors returned KO"
        return
    editors_list = {}
    # print response['editor_list'][0]['name']
    for editor in response['editor_list']:
        editors_list[editor["mail"]]=editor["name"]

    return editors_list

def check_editors(editors):
    """
    Returns a dict with the errors in the editors
    """

    if len(editors) < 1:
        return {"Editors":"This demo does not have any editor"}
    return {}


def print_errors(editors_demoid, state, title, errors, editors):
    """
    Print all the errors found
    """
    if len(errors) == 0:
        return

    print "Demo #{} \"{}\"".format(editors_demoid, title)
    print "Type: {}".format(state)

    # Print editors
    editors_msg = []
    for editor in editors:
        editors_msg.append("{} <{}>".format(editors[editor], editor))
    if len(editors_msg) > 0:
        print "Editors: {}".format(", ".join(editors_msg))

    # Print Errors
    print "Found 1 error:" if len(errors) == 1 else "Found {} errors:".format(len(errors))
    for error in errors:
        print "    - In {} - {}".format(error, errors[error])
    print "\n"


def start_test():
    demos = get_demo_list()
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
            print_errors(editors_demoid, title, errors, editors)
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




# Parse program arguments
parser = optparse.OptionParser()
(opts, args) = parser.parse_args()

if len(args) != 1:
    print "Wrong number of arguments (given {}, expected 1)".format(len(args))
    exit (0)

environment = args[0].lower()

if environment == 'integration':
    HOST = "integration.ipol.im"
elif environment == 'production' :
    HOST = "ipolcore.ipol.im"
elif environment == 'local':
    HOST = "127.0.1.1"
else:
    print "Unknown environment '{}'".format(environment)
    exit (-1)

start_test()
            

            
            
            
            
            
            
            
            
            
            
            
            
            
            
            
            
            
            
            
            
            
            
            
            
            
            
            
            
            
            

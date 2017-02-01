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
    Returns a dict with the errors in the DDL
    """
    errors = {}

    # Check if there is any DDL
    if ddl is None:
        errors["DDL"] = "This demo does not have any DDL"
        return errors
    ddl_json = json.loads(ddl)

    # Check if the run is correct
    if isinstance(ddl_json["run"], list):
        errors["Run"]="This demo has runs with the deprecated syntax"

    # Check if the build is correct
    if not 'build1' in ddl_json["build"]:
        errors["Build"]="This demo has builds with the deprecated syntax"

    # Check the url in the build
    url = json.dumps(ddl_json["build"]).split("\"url\":")[1].split(",")[0].strip()[1:-1]
    if not urlparse(url).hostname == "www.ipol.im":
        errors["URL"] = "This demo has an incorrect url: {}".format(url)
    return errors


def have_demo_extras(editors_demoid):
    """
    Check if the demo have or not demo extras and returns a boolean
    """
    resp = post('get_compressed_file_url_ws', {"demo_id":editors_demoid})
    response = resp.json()
    if not response['status'] == 'OK':
        print "ERROR: get_compressed_file_url_ws returned KO"
        return
    return response['code'] == '2' # Code = 1 don't have demoextra, code = 2 have demoextras


def check_demo_extras(editors_demoid, ddl):
    """
    Returns a dict with the errors in the demo extras
    """
    if not ("$demoextras" in ddl or "${demoextras}" in ddl):
        if have_demo_extras(editors_demoid):
            return {"Demoextras":"This demo does not use demo extras, but there is a demo extras file"}
    else:
        if not have_demo_extras(editors_demoid):
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

    return response['editor_list']

def check_editors(editors):
    """
    Returns a dict with the errors in the editors
    """

    if len(editors) < 1:
        return {"Editors":"This demo does not have any editor"}
    return {}


def print_errors(editors_demoid, title, errors):
    """
    Print all the errors found
    """
    if len(errors) > 0:
        if len(errors) == 1:
            print "Demo {} with id {} have 1 error:".format(title, editors_demoid)
        else:
            print "Demo {} with id {} have {} errors:".format(title, editors_demoid, len(errors))
        for error in errors:
            print "    - In {} - {}".format(error, errors[error])


def start_test():
    demos = get_demo_list()
    for demo in demos:
        if not (demo['state'] == "published" or demo['state'] == "preprint"):
            # Only checks the demos that are published or in preprint
            continue
        editors_demoid = demo['editorsdemoid']
        title = demo['title']

        # Read and check editors
        editors = get_editors(editors_demoid)
        editors_error = check_editors(editors)

        # Read and check the DDL
        ddl = read_DDL(demo['editorsdemoid'])
        ddl_errors = check_ddl(ddl)

        if ddl is None:
            print_errors(editors_demoid, title, dict(ddl_errors.items() + editors_error.items()))
            continue

        # Check the demo extras
        demo_extras_errors = check_demo_extras(editors_demoid,ddl)
        print_errors(editors_demoid, title, dict(ddl_errors.items() + editors_error.items() + demo_extras_errors.items()))




# Parse program arguments
parser = optparse.OptionParser()
(opts, args) = parser.parse_args()

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
            

            
            
            
            
            
            
            
            
            
            
            
            
            
            
            
            
            
            
            
            
            
            
            
            
            
            
            
            
            
            

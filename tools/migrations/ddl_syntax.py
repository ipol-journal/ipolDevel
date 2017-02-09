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
import os
import requests
import json

HOST = "integration.ipol.im"
# HOST = "127.0.1.1"

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
    Return the list of demos
    """
    resp = post('demo_list')
    response = resp.json()
    if response['status'] != 'OK':
        print "ERROR: demo_list returned KO"
        return
    return response['demo_list']


def read_DDL(editors_demoid):
    """
    Return the DDL for the demo with the given editordemoid
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


def do_write(editors_demoid, ddl):
    '''
    Write a DDL
    '''
    try:
        resp = post('save_demo_description', params={"demoid": editors_demoid}, json = ddl)
        response = resp.json()
        if response['status'] != 'OK':
            print "ERROR: save_demo_description returned KO for demo {}".format(editors_demoid)
    except Exception as ex:
        print "ERROR: Could not write DDL for demo {} - {}".format(editors_demoid, ex)


def fix_run(ddl):
    """
    Return a DDL with the run fixed
    """
    ddl_json = json.loads(ddl)
    if not isinstance(ddl_json["run"], list):
        # Run is correct
        return ddl
    if len(ddl_json["run"]) > 1:
        return ddl
    if ">stdout.txt" in json.dumps(ddl_json["run"]):
        ddl_json["run"] = ddl_json["run"][0].split(">")[0]
        return json.dumps(ddl_json, indent=4, separators=(',', ': '))
    elif ">" in json.dumps(ddl_json["run"]):
        return ddl

    ddl_json["run"] = ddl_json["run"][0]
    return json.dumps(ddl_json, indent=4, separators=(',', ': '))


def fix_build(ddl):
    """
    Return a DDL with the build fixed
    """
    ddl_json = json.loads(ddl)
    if 'build1' in ddl_json["build"]:
        # Build is correct
        return ddl

    index = 1
    new_build = {}
    for build in ddl_json["build"]:
        dic = {}

        # Get url
        if "url*previous" in build:
            dic["url"] = build["url*previous"]
        elif "url*previous*" in build:
            dic["url"] = build["url*previous*"]
        elif "url" in build:
            dic["url"] = build["url"]

        # Get construct
        if "build_type" in build:
            if build["build_type"] == "cmake":
                # Can't convert cmake yet
                return ddl

            if "flags" in build:
                dic["construct"] = "{} {} -C {}".format(build["build_type"],build["flags"],build["srcdir"])
            else:
                dic["construct"] = "{} -C {}".format(build["build_type"], build["srcdir"])

        # Get files to move
        binaries = []
        if "binaries" in build:
            for binary in build["binaries"]:
                binaries.append(os.path.normpath(os.path.join(build["srcdir"], "/".join(binary))))

        scripts = []
        if "scripts" in build:
            for script in build["scripts"]:
                scripts.append(os.path.normpath(os.path.join(build["srcdir"],"/".join(script))))

        if len(binaries+scripts) > 0:
            dic["move"] = ", ".join(binaries + scripts)

        str = "build{}".format(index)
        new_build[str] = dic
        index += 1
        ddl_json["build"] = new_build
    return json.dumps(ddl_json, indent=4, separators=(',', ': '))


if __name__ == '__main__':
    demos = get_demo_list()
    for demo in demos:
        editors_demoid = demo['editorsdemoid']
        title = demo['title']
        original_ddl = read_DDL(editors_demoid)

        # Fix the DDL
        new_ddl = fix_run(original_ddl)
        new_ddl = fix_build(new_ddl)

        if not original_ddl == new_ddl:
            print "Demo #{} \"{}\" was modified".format(editors_demoid,title)
            # Stores the new DDL
            do_write(editors_demoid, new_ddl)



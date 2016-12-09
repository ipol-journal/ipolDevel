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
import sys
import requests
import json
import os

HOST = "integration.ipol.im"


def post(service, params=None, json=None):
    try:
        url = 'http://{}/api/demoinfo/{}'.format(
            HOST,
            service
        )
        # print "JSON - ",json
        return requests.post(url, params=params, json=json)
    except Exception as ex:
        print "ERROR: Failure in the post function - {}".format(str(ex))


def do_read(args):
    '''
    Read a DDL
    '''
    for editorsdemoid in args:
        try:
            resp = post('read_last_demodescription_from_demo', params={"demo_id": editorsdemoid, "returnjsons": True})
            response = resp.json()
            if response['status'] != 'OK':
                print "ERROR: read_last_demodescription_from_demo returned KO for demo {}".format(editorsdemoid)
                continue
            last_demodescription = response['last_demodescription']
            ddl_json = json.loads(json.loads(last_demodescription['json']))

            file = open("DDLs/" + str(editorsdemoid) + ".json", "wb")
            file.write(json.dumps(ddl_json, indent=4, sort_keys=True))
            file.close()
        except Exception as ex:
            print "ERROR: Failed to read DDL from {} - {}".format(editorsdemoid, ex)


def do_read_all():
    '''
    Read all DDLs
    '''
    resp = post('demo_list')
    response = resp.json()
    if response['status'] != 'OK':
        print "ERROR: demo_list returned KO"
        return
    demos = []
    for demo in response['demo_list']:
        demos.append(demo['editorsdemoid'])
    do_read(demos)


def do_write(demos):
    '''
    Write a DDL
    '''
    for editorsdemoid in demos:
        try:
            file = open("DDLs/" + str(editorsdemoid) + ".json", "r").read()
            # Check if is a valid JSON
            json.loads(file)

            resp = post('save_demo_description', params={"demoid": editorsdemoid}, json=file)
            response = resp.json()
            if response['status'] != 'OK':
                print "ERROR: save_demo_description returned KO for demo {}".format(editorsdemoid)
        except ValueError:
            print "ERROR: Invalid JSON for demo {}".format(editorsdemoid)
        except Exception as ex:
            print "ERROR: Could not write DDL for demo {} - {}".format(editorsdemoid, ex)

def do_write_all():
    '''
    Write all DDLs
    '''
    resp = post('demo_list')
    response = resp.json()
    if response['status'] != 'OK':
        print "ERROR: demo_list returned KO"
        return

    demos = []
    for demo in response['demo_list']:
        demos.append(demo['editorsdemoid'])
    do_write(demos)


# Parse program arguments
parser = optparse.OptionParser()
(opts, args) = parser.parse_args()

if len(args) < 1:
    print "ERROR: no command specified!\n"
    parser.print_help()
    sys.exit(-1)

if not os.path.isdir("DDLs"):
    os.mkdir("DDLs")

command = args[0].lower()
# print command

if command == 'readall' or command == 'getall':
    do_read_all()
elif command == 'read' or command == 'get':
    do_read(args[1:])
elif command == 'write' or command == 'put':
    do_write(args[1:])
# elif command == 'writeall' or command == 'putall':
#     do_write_all()
else:
    print "Unknown command '{}'".format(command)

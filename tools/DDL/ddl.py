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

import argparse
import sys
import requests
import json
import os

def post(service, host, params=None, json=None):
    try:
        url = 'http://{}/api/demoinfo/{}'.format(
            host,
            service
        )
        return requests.post(url, params=params, data=json)
    except Exception as ex:
        print "ERROR: Failure in the post function - {}".format(str(ex))


def do_read(demos, host):
    '''
    Read a DDL
    '''
    for editorsdemoid in demos:
        try:
            file = None
            resp = post('get_ddl', host, params={"demo_id": editorsdemoid})
            response = resp.json()
            if response['status'] != 'OK':
                print "ERROR: get_ddl returned KO for demo {}".format(editorsdemoid)
                continue
                
            DDL = response['last_demodescription']
            if not DDL:
                print "ERROR: Empty or non-existing DDL for demo #{}".format(editorsdemoid)
                continue
                
            last_demodescription = DDL
            ddl_json = last_demodescription['ddl']

            file = open("DDLs/" + str(editorsdemoid) + ".json", "wb")
            file.write(ddl_json)
        except Exception as ex:
            print "ERROR: Failed to read DDL from {} - {}".format(editorsdemoid, ex)
        finally:
            if file:
                file.close()


def do_read_all(host):
    '''
    Read all DDLs
    '''
    resp = post('demo_list', host)
    response = resp.json()
    if response['status'] != 'OK':
        print "ERROR: demo_list returned KO"
        return
    demos = []
    for demo in response['demo_list']:
        demos.append(demo['editorsdemoid'])
    do_read(demos, host)


def do_write(demos, host):
    '''
    Write a DDL
    '''
    for editorsdemoid in demos:
        try:
            ddl_json = open("DDLs/" + str(editorsdemoid) + ".json", "r").read()
            # Check if is a valid JSON
            json.loads(ddl_json)

            resp = post('save_ddl', host, params={"demoid": editorsdemoid}, json=ddl_json)
            response = resp.json()
            if response['status'] != 'OK':
                print "ERROR: save_ddl returned KO for demo {}".format(editorsdemoid)
        except ValueError:
            print "ERROR: Invalid JSON for demo {}".format(editorsdemoid)
        except Exception as ex:
            print "ERROR: Could not write DDL for demo {} - {}".format(editorsdemoid, ex)


def do_write_all(host):
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
    do_write(demos, host)


# Parse program arguments
LOCAL_IP = '127.0.0.1'

parser = argparse.ArgumentParser()
parser.add_argument("-i", "--integration",
  help="Use the Integration environment", action="store_true")
parser.add_argument("-l", "--local",
  help="Use the Local ({}) environment".format(LOCAL_IP), action="store_true")
parser.add_argument("command", nargs='+')
  
args = parser.parse_args()

# Get host
if args.integration:
    host = "integration.ipol.im"
elif args.local:
    host = LOCAL_IP
else:
    host = "ipolcore.ipol.im"

# Create output directory
if not os.path.isdir("DDLs"):
    os.mkdir("DDLs")

command = args.command[0].lower()

# Execute command
if command == 'readall' or command == 'getall':
    do_read_all(host)
elif command == 'read' or command == 'get':
    do_read(args.command[1:], host)
elif command == 'write' or command == 'put':
    do_write(args.command[1:], host)
elif command == 'writeall' or command == 'putall':
    do_write_all(host)
else:
    print "Error: unknown command '{}'".format(command)

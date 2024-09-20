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
import json
import os

import requests


def get(service, host, params=None, json=None):
    try:
        url = "http://{}/api/demoinfo/{}".format(host, service)
        return requests.get(url, params=params, data=json)
    except Exception as ex:
        print(f"ERROR: Failure in the post function - {ex}")


def post(service, host, params=None, json=None):
    try:
        url = "http://{}/api/demoinfo/{}".format(host, service)
        return requests.post(url, params=params, data=json)
    except Exception as ex:
        print(f"ERROR: Failure in the post function - {ex}")


def do_read(demos, host):
    """
    Read a DDL
    """
    for editorsdemoid in demos:
        try:
            file = None
            resp = get(f"ddl/{editorsdemoid}", host)
            response = resp.json()
            if resp.status_code != 200:
                print(f"ERROR: get_ddl returned KO for demo {editorsdemoid}")
                continue

            DDL = response
            if not DDL:
                print(f"ERROR: Empty or non-existing DDL for demo #{editorsdemoid}")
                continue

            with open("DDLs/" + str(editorsdemoid) + ".json", "w") as f:
                json.dump(DDL, f, ensure_ascii=False, indent=3)
        except Exception as ex:
            print("ERROR: Failed to read DDL from {} - {}".format(editorsdemoid, ex))
        finally:
            if file:
                file.close()


def do_read_all(host):
    """
    Read all DDLs
    """
    resp = get("demos", host)
    response = resp.json()
    if resp.status_code != 200:
        print("ERROR: demo_list returned KO")
        return
    demos = []
    for demo in response:
        demos.append(demo["editorsdemoid"])
    do_read(demos, host)


def do_write(demos, host):
    """
    Write a DDL
    """
    for editorsdemoid in demos:
        try:
            request = get("demos", host)
            if request.status_code != 200:
                print(f"ERROR: save_ddl returned KO for demo {editorsdemoid}")
            demos = request.json()
            ddl_json = open("DDLs/" + str(editorsdemoid) + ".json", "r").read()
            # Check if is a valid JSON
            ddl = json.loads(ddl_json)

            if not demo_exist(demos, editorsdemoid):
                create_demo(editorsdemoid, host, ddl["general"]["demo_title"], "test")

            resp = post(f"ddl/{editorsdemoid}", host, json=ddl_json)
            # response = resp.json()
            if resp.status_code != 201:
                print(f"ERROR: Could not save DDL for demo {editorsdemoid}")
        except ValueError:
            print(f"ERROR: Invalid JSON for demo {editorsdemoid}")
        except Exception as ex:
            print(f"ERROR: Could not write DDL for demo {editorsdemoid} - {ex}")


def do_write_all(host):
    """
    Write all DDLs
    """
    resp = get("demos", host)
    response = resp.json()
    if resp.status_code != 201:
        print("ERROR: demo_list returned KO")
        return

    demos = []
    for demo in response["demo_list"]:
        demos.append(demo["editorsdemoid"])
    do_write(demos, host)


def demo_exist(demos, demo_id):
    """
    Check if demo already exists
    """
    for demo in demos:
        if str(demo["editorsdemoid"]) == str(demo_id):
            return demo
    return False


def create_demo(demo_id, host, title, state):
    """
    Create demo in a target host
    """
    params = {"demo_id": demo_id, "title": title, "state": state}
    request = post("demo", host, params)
    if request.status_code != 201:
        print(f"Could not create demo {demo_id}")


def update_ddl(demos):
    """
    Update the build.url field in a DDL
    """

    for editorsdemoid in demos:
        try:
            # Open the JSON file and load its content
            with open("DDLs/" + str(editorsdemoid) + ".json", "r") as file:
                ddl = json.load(file)

            # Update the build.url field
            if 'build' in ddl and 'url' in ddl['build']:
                if ddl['build']['url'] == f"git@github.com:mlbriefs/{editorsdemoid}.git":
                    print(f"Original build URL for {editorsdemoid}: {ddl['build']['url']}")
                    ddl['build']['url'] = f"git@github.com:ipol-journal/{editorsdemoid}.git"
                    print(f"Updated build URL for {editorsdemoid}: {ddl['build']['url']}")
            
            # Write the updated content back to the file
            with open("DDLs/" + str(editorsdemoid) + ".json", 'w') as file:
                json.dump(ddl, file, indent=4)
        except Exception as ex:
            print("ERROR: Failed to update the DDL {} - {}".format(editorsdemoid, ex))


# Parse program arguments
LOCAL_IP = "127.0.0.1"

parser = argparse.ArgumentParser()
parser.add_argument(
    "-i", "--integration", help="Use the Integration environment", action="store_true"
)
parser.add_argument(
    "-l",
    "--local",
    help="Use the Local ({}) environment".format(LOCAL_IP),
    action="store_true",
)
parser.add_argument("command", nargs="+")

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
if command == "readall" or command == "getall":
    do_read_all(host)
elif command == "read" or command == "get":
    do_read(args.command[1:], host)
elif command == "write" or command == "put":
    do_write(args.command[1:], host)
elif command == "writeall" or command == "putall":
    do_write_all(host)
elif command == "update_git_url":
    do_read(args.command[1:], host)
    update_ddl(args.command[1:])
    do_write(args.command[1:], host)
else:
    print(f"Error: unknown command '{command}'")
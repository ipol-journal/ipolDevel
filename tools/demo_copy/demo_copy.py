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
import sys
import requests
import json
import os
import socket
import urllib.request


def post(service, host, params=None, data=None, files=None, servicejson=None):
    """
    Post request to service
    """
    url = 'http://{}{}'.format(host, service)
    return requests.post(url, params=params, data=data, files=files, json=servicejson)

def get(service, host, params=None):
    """
    Get resource
    """
    url = 'http://{}{}/{}'.format(host, service, params)
    return urllib.request.urlopen(url)
    
def copy_demo(demo_id, host, source_host):
    """
    Copy demo main method.
    """
    print("Origin demo:", demo_id)
    new_id = demo_id
    ddl = get_ddl(demo_id, source_host)
    demo_state = get_demo_state(source_host, demo_id)
    if 'demo_title' in ddl['general']:
        demo_title = ddl['general']['demo_title']
    else:
        print('**Please change the demo title and add it to the general section in the ddl**')
        demo_title = "CHANGE THIS DEMO TITLE"

    if ddl_exists(demo_id, host):
        new_id = input("\nA demo with this ID already exists. Choose a new ID or the same to overwrite a demo: ")
        print("Destination demo:", new_id)
        try:
            new_id = int(new_id)
        except ValueError:
            print("That isn't a number")
            return

    create_demo_response = create_demo(new_id, demo_title, demo_state, host)
    if create_demo_response['status'] != 'OK':
        demo_title = input("\nChoose a new title: ") or sys.exit("Title cannot be empty")
        create_demo(new_id, demo_title, demo_state, host)
    
    print('Adding ddl...')
    add = add_ddl(host, new_id)
    os.remove('ddl.json')
    print('Adding demo_extras...')    
    clone_demo_extras(host, source_host, demo_id, new_id)
    print('Adding blobs...')    
    copy_blobs_to_demo(host, source_host, demo_id, new_id)
    
    demo_templates = get_demo_template_names(source_host, demo_id)
    local_templates = get_all_templates(host)
    for template_name in demo_templates:
        if template_name not in local_templates:
            print('Cloning template: {}...'.format(template_name))
            copy_template(host, source_host, demo_id, new_id, template_name)
            associate_template(host, new_id, template_name)
        else:
            print('Associating template: {}...'.format(template_name))
            associate_template(host, new_id, template_name)
    print('Done')

def ddl_exists(demo_id, host):
    """
    Check if DDL exists
    """
    http_response = post('/api/demoinfo/get_ddl', host, params={"demo_id": demo_id}).json()
    if http_response['status'] == 'OK':
        return True
    return False

def get_demo_state(host, demo_id):
    """
    Get a demo state
    """
    response = get('/api/demoinfo/read_demo_metainfo', host, demo_id)
    string = response.read().decode('utf-8')
    json_obj = json.loads(string)
    return json_obj['state']

def get_ddl(demo_id, host):
    """
    Read a DDL
    """
    try:
        resp = post('/api/demoinfo/get_ddl', host, params={"demo_id": demo_id})
        response = resp.json()
        if response['status'] != 'OK':
            message = "ERROR: get_ddl returned KO for demo {} from {}".format(demo_id, host)
            raise GetDDLError(message)

        DDL = response['last_demodescription']
        if not DDL:
            raise GetDDLError("ERROR: Empty or non-existing DDL for demo #{} on {}".format(demo_id, host))

        last_demodescription = DDL
        ddl_json = last_demodescription['ddl']
        with open('ddl.json', 'w') as out:
            out.write(ddl_json)
        return json.loads(ddl_json)
    except GetDDLError:
        print(message)
        sys.exit("Aborted")
    except Exception as ex:
        print("ERROR: Failed to read DDL from {} - {}".format(editorsdemoid, ex))
        sys.exit("Aborted")

def add_ddl(host, demo_id):
    """
    Add the ddl to the demo
    """
    params = {'demoid': demo_id}        
    with open('ddl.json', 'r') as out:
        ddl = out.read()

    response = post('/api/demoinfo/save_ddl', host, params=params, data=ddl)
    return response.json()

def create_demo(demo_id, title, state, host):
    """
    Creates a demo
    """
    response = post('/api/demoinfo/add_demo', host, params={'editorsdemoid': demo_id, 'title': title, 'state': state})
    return response.json()

def clone_demo_extras(host, source_host, demo_id, new_id):
    """
    Get DemoExtras from a demo
    """
    serviceparams = {'demo_id': demo_id}
    response = post('/api/demoinfo/get_demo_extras_info', source_host, params=serviceparams).json()
    if 'url' in response:
        url = response['url']
        filename = response['url'].split("/")[-1]
        demo_extras = urllib.request.urlopen(url)
        add_demo_extras(host, new_id, demo_extras, filename)

def add_demo_extras(host, demo_id, demo_extras, demo_extras_name):
    """
    Add DemoExtras to the demo
    """
    files = {'demoextras': demo_extras}
    params = {'demo_id': demo_id, 'demoextras_name': demo_extras_name}
    response = post('/api/demoinfo/add_demoextras', host, params=params, files=files)
    return response.json()

def copy_blobs_to_demo(host, source_host, demo_id, new_id):
    """
    Copy blobs to demo or template
    """
    params = {'demo_id': demo_id}
    blobs_json = post('/api/blobs/get_demo_owned_blobs', source_host, params=params).json()
    local_demo_blobs = get_demo_owned_blobs(host, new_id)
    for blobset in blobs_json['sets']:
        set_name = blobset['name']
        blobs = blobset['blobs']
        for index in blobs:
            blob = blobs[index]
            if blob['blob'] not in local_demo_blobs:
                title = blob['title']
                credit = blob['credit']
                pos_in_set = index
                blob_file = get_blob_data(source_host, blob['blob'])
                if 'vr' in blob:
                    vr = get_blob_data(source_host, blob['vr'])
                    add_blob_to_demo(host, new_id, blob_file, title, set_name, pos_in_set, credit, vr=vr)
                else:
                    add_blob_to_demo(host, new_id, blob_file, title, set_name, pos_in_set, credit)

def get_demo_owned_blobs(host, demo_id):
    """
    Get all blobs owned by a demo
    """
    params = {'demo_id': demo_id}
    blobs_response = post('/api/blobs/get_demo_owned_blobs', host, params=params).json()
    owned_blobs = []
    for blobset in blobs_response['sets']:
        blobs = blobset['blobs']
        for index in blobs:
            blob = blobs[index]
            owned_blobs.append(blob['blob'])
    return owned_blobs


def get_blob_data(host, url):
    """
    Get a blob binary data from url
    """
    url = 'http://{}{}'.format(host, url)
    blob = urllib.request.urlopen(url)
    return blob

def add_blob_to_demo(host, demo_id, blob, blob_title, set_name, pos_in_set, credit, vr=None):
    """
    Add a blob to demo
    """
    files = {'blob': blob}
    if vr:
        files['blob_vr'] = vr
    params = {'demo_id': demo_id, 'title': blob_title, 'blob_set': set_name, 'pos_set': pos_in_set, 'credit': credit}
    response = post('/api/blobs/add_blob_to_demo', host, params=params, files=files)
    return response.json()

#####################
# Template methods #
#####################
def get_all_templates(host):
    """
    Get all existing templates from a host
    """
    response = post('/api/blobs/get_all_templates', host).json()
    return response['templates']

def get_demo_template_names(host, demo_id):
    """
    Get all templates associated to a demo
    """
    params = {'demo_id': demo_id}
    response = post('/api/blobs/get_demo_templates', host, params=params).json()
    return response['templates']

def associate_template(host, new_id, template_name):
    """
    Associate template to a demo
    """
    params = {'demo_id': new_id, 'template_names': template_name}
    response = post('/api/blobs/add_templates_to_demo', host, params=params)

def copy_template(host, source_host, demo_id, new_id, template_name):
    """
    Copy template to local
    """
    params = {'template_name': template_name}
    response = post('/api/blobs/create_template', host, params=params).json()
    copy_blobs_from_template(host, source_host, template_name)

def copy_blobs_from_template(host, source_host, template_name):
    """
    Copy blobs to template
    """
    params = {'template_name': template_name}
    blobs_json = post('/api/blobs/get_template_blobs', source_host, params=params).json()
    # blobs_json = blobs_response.json()

    for blobset in blobs_json['sets']:
        set_name = blobset['name']
        blobs = blobset['blobs']
        for index in blobs:
            blob = blobs[index]
            title = blob['title']
            credit = blob['credit']
            pos_in_set = index
            blob_file = get_blob_data(source_host, blob['blob'])
            if 'vr' in blob:
                vr = get_blob_data(source_host, blob['vr'])
                add_blob_to_template(host, template_name, blob_file, set_name, pos_in_set, credit, title, vr=vr)
            else:
                add_blob_to_template(host, template_name, blob_file, set_name, pos_in_set, credit, title)

def add_blob_to_template(host, template_name, blob, set_name, pos_in_set, credit, title, vr=None):
    """
    Add a blob to the demo
    """
    files = {'blob': blob}
    if vr:
        files['blob_vr'] = vr
    params = {'template_name': template_name, 'title': title, 'blob_set': set_name, 'pos_set': pos_in_set, 'credit': credit}
    response = post('/api/blobs/add_blob_to_template', host, params=params, files=files)
    return response.json()

class Error(Exception):
    """
    Base class for exceptions in this module.
    """
    pass

class GetDDLError(Error):
    """
    GetDDLError handler
    """
    def __init__(self, message):
        self.message = message


# Command help
parser = argparse.ArgumentParser()
parser.add_argument("demo_id", type=int, help="identifier of the demo to be copied")
parser.add_argument("-i", '--integration', help="Use the Integration environment", action="store_true")
args = parser.parse_args()

# Obtain demo ID from arguments
demo_id = args.demo_id
# Source host
if args.integration:
    source_host = "integration.ipol.im"
else:
    source_host = "ipolcore.ipol.im"

print('Source: ', source_host)
# Host destination of the demo
host = socket.getfqdn()
if (host != "integration.ipol.im" and host != "ipolcore.ipol.im"):
  host = "127.0.0.1"

copy_demo(demo_id, host, source_host)

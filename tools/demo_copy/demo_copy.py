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
import socket
import urllib.request


def post(module, service, host, params=None, data=None, files=None, servicejson=None):
    url = 'http://{}/api/{}/{}'.format(host, module, service)
    return requests.post(url, params=params, data=data, files=files, json=servicejson)

def get(module, service, host, params=None):
    url = 'http://{}/api/{}/{}/{}'.format(host, module, service, params)
    return urllib.request.urlopen(url)
    
def copy_demo(demo_id, host):
    print("Origin demo:", demo_id)
    new_id = demo_id
    ddl = get_ddl(demo_id, source_host)
    demo_state = get_demo_state(source_host, demo_id)
    if 'demo_title' in ddl['general']:
        demo_title = ddl['general']['demo_title']
    else:
        print('**Please change the demo title and add it to the general section in the ddl**')
        demo_title = "CHANGE THIS DEMO TITLE"

    create_demo_response = create_demo(new_id, demo_title, demo_state, host)
    if create_demo_response['status'] == 'KO':
        demo_title = input("\nChoose a new title: ")
        create_demo(new_id, demo_title, demo_state, host)

    if ddl_exists(demo_id, host):
        new_id = input("\nA demo with this ID already exists. Choose a new ID or the same to overwrite a demo: ")
        print("Destination demo:", new_id)
        try:
            new_id = int(new_id)
        except ValueError:
            print("That isn't a number")
            return
    
    
    print('Adding ddl...')
    add = add_ddl(host, new_id)
    os.remove('ddl.json')
    print('Adding demo_extras...')    
    demo_extras_name = clone_demo_extras(source_host, demo_id)
    print('Adding blobs...')    
    copy_blobs_to_demo(host, demo_id, new_id)
    
    demo_templates = get_demo_template_names(source_host, demo_id)
    local_templates = get_all_templates(host)
    for template_name in demo_templates:
        if template_name not in local_templates:
            print('Cloning template: {}...'.format(template_name))
            copy_template(host, demo_id, new_id, template_name)
            associate_template(host, new_id, template_name)
        else:
            print('Associating template: {}...'.format(template_name))
            associate_template(host, new_id, template_name)
    print('Done')

def ddl_exists(demo_id, host):
    """
    Check if DDL exists
    """
    http_response = post("demoinfo", 'get_ddl', host, params={"demo_id": demo_id}).json()
    if http_response['status'] == 'OK':
        return True
    return False

def get_demo_state(host, demo_id):
    response = get('demoinfo', 'read_demo_metainfo', host, demo_id)
    string = response.read().decode('utf-8')
    json_obj = json.loads(string)
    return json_obj['state']

def get_ddl(demo_id, host):
    """
    Read a DDL
    """
    try:
        resp = post("demoinfo", 'get_ddl', host, params={"demo_id": demo_id})
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
        quit()
    except Exception as ex:
        print("ERROR: Failed to read DDL from {} - {}".format(editorsdemoid, ex))
        quit()

def add_ddl(host, demo_id):
    """
    Add the ddl to the demo
    """
    params = {'demoid': demo_id}        
    with open('ddl.json', 'r') as out:
        ddl = out.read()

    response = post('demoinfo', 'save_ddl', host, params=params, data=ddl)
    return response.json()

def create_demo(demo_id, title, state, host):
    """
    Creates a demo
    """
    response = post('demoinfo', 'add_demo', host, params={'editorsdemoid': demo_id, 'title': title, 'state': state})
    return response.json()

def clone_demo_extras(host, demo_id):
    """
    Get DemoExtras from a demo
    """
    serviceparams = {'demo_id': demo_id}
    response = post('demoinfo', 'get_demo_extras_info', source_host, params=serviceparams).json()
    if 'url' in response:
        url = response['url']
        filename = response['url'].split("/")[-1]
        demo_extras = urllib.request.urlopen(url)
        add_demo_extras(host, demo_id, demo_extras, filename)

def add_demo_extras(host, demo_id, demo_extras, demo_extras_name):
    """
    Add DemoExtras to the demo
    """
    files = {'demoextras': demo_extras}
    params = {'demo_id': demo_id, 'demoextras_name': demo_extras_name}
    response = post('demoinfo', 'add_demoextras', host, params=params, files=files)
    return response.json()

def copy_blobs_to_demo(host, demo_id, new_id):
    """
    Copy blobs to demo or template
    """
    params = {'demo_id': demo_id}
    blobs_response = post('blobs', 'get_demo_owned_blobs', source_host, params=params)
    blobs_json = blobs_response.json()

    for blobset in blobs_json['sets']:
        set_name = blobset['name']
        blobs = blobset['blobs']
        for index in blobs:
            blob = blobs[index]
            if not blob_exists(host, demo_id, blob['blob']):
                title = blob['title']
                credit = blob['credit']
                pos_in_set = index
                blob_file = get_blob_data(source_host, blob['blob'])
                if 'vr' in blob:
                    vr = get_blob_data(source_host, blob['vr'])
                    add_blob_to_demo(host, new_id, blob_file, title, set_name, pos_in_set, credit, vr=vr)
                else:
                    add_blob_to_demo(host, new_id, blob_file, title, set_name, pos_in_set, credit)

def blob_exists(host, demo_id, filename):
    params = {'demo_id': demo_id}
    blobs_response = post('blobs', 'get_demo_owned_blobs', host, params=params).json()
    for blobset in blobs_response['sets']:
        blobs = blobset['blobs']
        for index in blobs:
            blob = blobs[index]
            if blob['blob'] == filename:
                return True
    return False


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
    response = post('blobs', 'add_blob_to_demo', host, params=params, files=files)
    return response.json()

#####################
# Template methods #
#####################
def get_all_templates(host):
    """
    Get all existing templates from a host
    """
    response = post('blobs', 'get_all_templates', host).json()
    return response['templates']

def get_demo_template_names(host, demo_id):
    """
    Get all templates associated to a demo
    """
    params = {'demo_id': demo_id}
    response = post('blobs', 'get_demo_templates', host, params=params).json()
    return response['templates']

def associate_template(host, new_id, template_name):
    """
    Associate template to a demo
    """
    params = {'demo_id': new_id, 'template_names': template_name}
    response = post('blobs', 'add_templates_to_demo', host, params=params)

def copy_template(host, demo_id, new_id, template_name):
    """
    Copy template to local
    """
    params = {'template_name': template_name}
    response = post('blobs', 'create_template', host, params=params).json()
    copy_blobs_from_template(host, template_name)

def copy_blobs_from_template(host, template_name):
    """
    Copy blobs to template
    """
    params = {'template_name': template_name}
    blobs_json = post('blobs', 'get_template_blobs', source_host, params=params).json()
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
    response = post('blobs', 'add_blob_to_template', host, params=params, files=files)
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
parser.add_argument("demo_id", help="identifier of the demo to be copied")

args = parser.parse_args()

# Host destination of the demo
host = socket.getfqdn()
if (host != "integration.ipol.im"):
  host = "127.0.0.1"

# Host origin of the demo
source_host = "integration.ipol.im"
# source_host = "ipolcore.ipol.im"

# Obtain demo ID from arguments
demo_id = args.demo_id

copy_demo(demo_id, host)

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

"""
This script creates a template from the blobs of a demo.

It needs to be executed within the server.
Example: ./demo2template.py 271 Clouds_Pushbroom
"""

import argparse
import socket
import urllib.request
import requests


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

#####################
# Template methods #
#####################
def create_template(host, source_host, template_name):
    """
    Create template
    """
    params = {'template_name': template_name}
    post('/api/blobs/create_template', host, params=params).json()
 
def copy_blobs_to_template(host, source_host, demo_id, template_name, blobs_json):
    """
    Copy demo blobs to template
    """
    blobs_json = post('/api/blobs/get_demo_owned_blobs', source_host, params={'demo_id': demo_id}).json()
    
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


# Command help
parser = argparse.ArgumentParser()
parser.add_argument("demo_id", type=int, help="identifier of the demo to be copied")
parser.add_argument("template_name", help="template name")
parser.add_argument("-i", '--integration', help="Use integration environment", action="store_true")
args = parser.parse_args()

# Obtain demo ID from arguments
args_demo_id = args.demo_id
demo_id = args_demo_id
template_name = args.template_name
# Source host
if args.integration:
    origin_host = "integration.ipol.im"
else:
    origin_host = "ipolcore.ipol.im"

# Host destination of the demo
assert False, "this requires to be updated with correct urls"
destination_host = socket.getfqdn()
if (destination_host != "integration.ipol.im" and destination_host != "ipolcore.ipol.im"):
    destination_host = "127.0.0.1"

print('Source: ', origin_host)
print('Destination: ', destination_host)

create_template(destination_host, origin_host, template_name)
blobs = post('/api/blobs/get_demo_owned_blobs', origin_host, params={'demo_id': demo_id}).json()
copy_blobs_to_template(destination_host, origin_host, demo_id, template_name, blobs)

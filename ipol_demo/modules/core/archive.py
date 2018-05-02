#!/usr/bin/env python
# -*- coding:utf-8 -*-

"""
Helper functions for core, related to the archive module.
"""

import os
import traceback
import gzip
import json
import requests
from ipolutils.utils import thumbnail

def create_thumbnail(src_file):
    """
    Create thumbnail when possible from file to archive in run folder,
    returns the filepath of thumbnail when created.
    """
    thumb_height = 128
    if not os.path.exists(src_file):
        return False
    thumb_name, _ = os.path.splitext(os.path.basename(src_file))
    thumb_name = thumb_name.lower() + '_thumbnail.jpeg'
    thumb_file = os.path.join(os.path.dirname(src_file), thumb_name)
    try:
        thumbnail(src_file, thumb_height, thumb_file)
    except Exception:
        return False
    return thumb_file

def send_to_archive(demo_id, work_dir, request, ddl_archive, res_data, host_name):
    """
    Prepare an execution folder for archiving an experiment (thumbnails).
    Collect information and parameters.
    Send data to the archive module.
    """

    ddl_files = ddl_archive.get('files', {})
    ddl_hidden_files = ddl_archive.get('hidden_files', {})

    blobs = []
    if 'files' in ddl_archive or 'hidden_files' in ddl_archive:
        for file_name, file_label in dict(ddl_files, **ddl_hidden_files).iteritems():
            src_file = os.path.join(work_dir, file_name)
            if not os.path.exists(src_file):
                continue # declared file in ddl is not there
            if not file_label: # if no label given, use filename
                file_label = file_name
            value = {file_label: src_file}
            try: # to get a thumbnail
                thumb_file = create_thumbnail(src_file)
            except Exception:
                print traceback.format_exc()
            if thumb_file:
                value[os.path.basename(thumb_file)] = thumb_file
            blobs.append(value)

    if 'compressed_files' in ddl_archive.keys():
        for file_name, file_label in ddl_archive['compressed_files'].iteritems():
            src_file = os.path.join(work_dir, file_name)
            if not os.path.exists(src_file):
                continue # normal?
            src_handle = open(src_file, 'rb')
            gz_file = src_file + '.gz'
            gz_handle = gzip.open(gz_file, 'wb')
            gz_handle.writelines(src_handle)
            src_handle.close()
            gz_handle.close()
            if not file_label: # if no label given, use filename
                file_label = file_name
            blobs.append({file_label: gz_file})

    # let's add all the parameters
    parameters = {}
    if 'params' in ddl_archive.keys():
        for p in ddl_archive['params']:
            if p in res_data['params']:
                parameters[p] = res_data['params'][p]
    if 'enable_reconstruct' in ddl_archive and ddl_archive['enable_reconstruct'] and request is not None:
        clientData = json.loads(request['clientData'])

        if clientData.get("origin", "") == "upload":
            # Count how many file entries and remove them
            file_keys = [key for key in request if key.startswith("file_")]
            files = request.copy()
            map(files.pop, file_keys)
            clientData["files"] = len(file_keys)

        clientData = json.dumps(clientData)

        execution_json = {}
        execution_json['demo_id'] = demo_id
        execution_json['request'] = clientData
        execution_json['response'] = res_data

        execution_json = json.dumps(execution_json)
    else:
        execution_json = None

    # save info
    if 'info' in ddl_archive.keys():
        for i in ddl_archive['info']:
            if i in res_data['algo_info']:
                parameters[ddl_archive['info'][i]] = res_data['algo_info'][i]

    url = 'http://{}/api/archive/add_experiment'.format(host_name)
    data = {
        "demo_id": demo_id,
        "blobs": json.dumps(blobs),
        "parameters": json.dumps(parameters),
        "execution": execution_json
    }
    resp = requests.post(url, data=data)
    return resp.json()

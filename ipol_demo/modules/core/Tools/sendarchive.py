#!/usr/bin/env python
# -*- coding:utf-8 -*-

"""
    file for SendArchive class
"""

import os
import mimetypes
import gzip

import json
import requests

def prepare_archive(demo_id, work_dir, request, ddl_archive, res_data, host_name):
    """
    prepares everything to archive the inputs/results/parameters
    puts the information in res_data['archive_blobs'] and
    res_data['archive_params']
    """
    thumb_height = 128
    work_dir = os.path.normpath(work_dir)
    blobs = []
    if 'files' in ddl_archive.keys():
        for file_name, file_label in ddl_archive['files'].iteritems():
            src_file = os.path.join(work_dir, file_name)
            if not os.path.exists(src_file):
                continue # is it normal? Shall we inform some one by log or an exception ?
            if not file_label: # if no label given, use filename
                file_label = file_name
            value = {file_label: src_file}
            mime_type, _ = mimetypes.guess_type(file_name)
            media_type, _ = mime_type.split('/')
            # thumbnail for some file types
            if media_type in ('image', 'video') and mime_type != 'image/svg+xml':
                # send filepath relative to run dir
                src = os.path.join(os.path.dirname(work_dir), os.path.basename(work_dir), file_name)
                data = {'src': src, 'height': thumb_height}
                url = 'http://{}/api/{}/{}'.format(host_name, 'conversion', 'thumbnail')
                resp = requests.post(url, data=data)
                if not resp.status_code == 200:
                    # something went wrong in thumbnail production, let it, maybe a data tiff file
                    pass
                else:
                    thumb_name, _ = os.path.splitext(file_name)
                    thumb_name = thumb_name.lower() + '_thumbnail.jpeg'
                    thumb_file = os.path.join(work_dir, thumb_name)
                    with open(thumb_file, 'wb') as f:
                        f.write(resp.content) # try ?
                        f.close()
                        value[thumb_name] = thumb_file
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


    if request is not None:
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
    else:
        execution_json = {}

    # save info
    if 'info' in ddl_archive.keys():
        for i in ddl_archive['info']:
            if i in res_data['algo_info']:
                parameters[ddl_archive['info'][i]] = res_data['algo_info'][i]

    userdata = {"demo_id":demo_id, "blobs":json.dumps(blobs), "parameters":json.dumps(parameters)}
    url = 'http://{}/api/{}/{}'.format(host_name, 'archive', 'add_experiment')
    resp = requests.post(url, data=userdata)
    json_response = resp.json()
    status = json_response['status']
    return status

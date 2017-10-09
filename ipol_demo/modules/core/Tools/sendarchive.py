#!/usr/bin/env python
# -*- coding:utf-8 -*-

"""
    file for SendArchive class
"""

import os
import mimetypes
import gzip
from PIL import Image,ImageDraw

import json    
import urllib
import requests

#-------------------------------------------------------------------------------
class SendArchive:
    """
        This class creates all the information needed to send the demo
        results to the archive module
    """
    #---------------------------------------------------------------------------
    @staticmethod
    def get_mime_type(the_file):
        """
        Return format of the file

        :return: format of file (audio, image or video)
        :rtype: string
        """
        mimetype, encoding = mimetypes.guess_type(the_file)
        
        if mimetype is None:
            return ".dat" # Generic data

        # MIME type found
        main_type, _ =  mimetype.split('/')
        return main_type
        
    
    #---------------------------------------------------------------------------
    @staticmethod
    def make_thumbnail(path, work_dir):
        """
        This function make a thumbnail of path.
        """
        
        ### For the moment we are "hardcoring" this value.This will change with the CONVERSION module.
        route, file_extension = os.path.splitext(path)
        name_for_the_thumbnail = route.split('/')[-1].lower() + '_thumbnail'
        name_and_extension_for_the_thumbnail = name_for_the_thumbnail + '.jpeg'
        thumbnail_path = os.path.join(work_dir, name_and_extension_for_the_thumbnail)
        
        image = Image.open(path).convert('RGB')
        ##the size should be in the conf.file....
        image.thumbnail((256, 256))
        image.save(thumbnail_path)
        
        return thumbnail_path, name_for_the_thumbnail

    #---------------------------------------------------------------------------
    @staticmethod
    def prepare_archive(demo_id, work_dir, ddl_archive, res_data, host_name):
        """
            prepares everything to archive the inputs/results/parameters
            puts the information in res_data['archive_blobs'] and 
            res_data['archive_params']
        """
        desc = ddl_archive
        
        blobs_item = []
        blobs = {}
        if 'files' in desc.keys():
          for filename in desc['files']:
            file_complete_route = os.path.join(work_dir, filename)
            print "file route=",file_complete_route
            if os.path.exists(file_complete_route):
                print "ok"
                mime_type = SendArchive.get_mime_type(file_complete_route)
                print mime_type
                file_description = desc['files'][filename]
                # if empty file description, use filename 
                if file_description == "":
                  file_description = filename
                
                ### THIS MUST BE CHANGED WHEN THE CONVERSION MODULE DEALS WITH THE TIFF IMAGES!
                route, file_extension = os.path.splitext(file_complete_route)
                if mime_type == 'image' and file_extension in ['.png','.jpg','.jpeg']:
                    thumbnail = SendArchive.make_thumbnail(file_complete_route, work_dir)
                    value = {file_description : file_complete_route,\
                             thumbnail[1]: thumbnail[0]}
                
                else:
                    value = {file_description: file_complete_route}
                
                blobs_item.append(value)
        
        if 'compressed_files' in desc.keys():
          for filename in desc['compressed_files']:
            file_complete_route = os.path.join(work_dir, filename)
            file_complete_route_compressed = file_complete_route + '.gz'
            if os.path.exists(file_complete_route):
               f_src = open(file_complete_route, 'rb')
               f_dst = gzip.open(file_complete_route_compressed, 'wb')
               f_dst.writelines(f_src)
               f_src.close()
               f_dst.close()

               file_description = desc['compressed_files'][filename]
               # if empty file description, use filename 
               if file_description=="":
                   file_description = filename

               value = {file_description : file_complete_route_compressed}
               blobs_item.append(value)
        
        blobs = blobs_item
        
        # let's add all the parameters
        parameters = {}
        if 'params' in desc.keys():
          for p in desc['params']:
            if p in res_data['params']:
               parameters[p] = res_data['params'][p]
                
        # save info
        if 'info' in desc.keys():
          for i in desc['info']:
            if i in res_data['algo_info']:
               parameters[desc['info'][i]] = res_data['algo_info'][i]
        
        try:
            userdata = {"demo_id":demo_id, "blobs":json.dumps(blobs), "parameters":json.dumps(parameters) }
            url = 'http://{}/api/{}/{}'.format(
                host_name,
                'archive',
                'add_experiment'
            )
            resp = requests.post(url, data=userdata)
            json_response = resp.json() 
            print json_response
            status = json_response['status']
            if status == 'OK':
                print "Archive success"
                
            return status
            
        except Exception as ex:
            return self.error(errcode='modulefailure',
                                errmsg="The archive module has failed: " + str(ex))

            

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

class SendArchive:
    """
        This class creates all the information needed to send the demo
        results to the archive module
    """

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

        im = Image.open(path)
        SendArchive.pil_thumb(im, thumbnail_path)

        return thumbnail_path, name_for_the_thumbnail

    @staticmethod
    def pil_thumb(im, dest_jpeg, dest_height=128):
        """
        This function make a thumbnail from a pil image (can come from file or video)
        General case: dest_height, preserve ratio
        Special cases: src_height < dest_height, extreme ratios (horizontal or vertical lines)
        Exactly same logic should be shared with the sendarchive logic
        [2017-10-17] is in core/Tools/sendarchive.py
        Should be in conversion module
        Video will provide a PIL object
        3D, ??? png ?
        """
        max_width = 2*dest_height # avoid extreme ratio

        src_width = im.width
        src_height = im.height
        # if src image is for example a line of 1 pixel height, keep original height
        dest_height = min(src_height, dest_height)
        dest_width = int(round(float(src_width*dest_height)/src_height))
        dest_width = min(dest_width, src_width, max_width)
        if dest_width <= 0:
            dest_width = src_width
        # resize before RGB problems
        im = im.resize((dest_width, dest_height), Image.LANCZOS)

        # im.info['transparency'], hack from image.py for palette with RGBA
        if im.mode == "P" and "transparency" in im.info and im.info['transparency'] is not None:
            im = im.convert('RGBA') # convert Palette with transparency to RGBA, handle just after
        # RGBA, full colors with canal alpha, resolve transparency with a white background
        if im.mode == "RGBA":
            rgba = im
            im = Image.new("RGB", rgba.size, (255, 255, 255))
            im.paste(rgba, mask=rgba.split()[3]) # 3 is the alpha channel
        if im.mode == "P":
            im = im.convert("RGB")

        if not os.path.isdir(os.path.dirname(dest_jpeg)):
            os.makedirs(os.path.dirname(dest_jpeg))
        im.save(dest_jpeg, 'JPEG', progression=True, subsampling='4:4:4')
        # return something ?


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

                route, file_extension = os.path.splitext(file_complete_route)
                if mime_type == 'image' and file_extension in ['.png','.jpg','.jpeg']:
                    try:
                        thumbnail = SendArchive.make_thumbnail(file_complete_route, work_dir)
                        value = {file_description : file_complete_route,\
                                 thumbnail[1]: thumbnail[0]}
                    except IOError: # Failed to create a thumbnail
                        value = {file_description: file_complete_route}
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

#!/usr/bin/env python
# -*- coding:utf-8 -*-

"""
This file implements the system core of the server
It implements Blob object and manages web page and web service
"""

import cherrypy
import magic
import tempfile
import shutil
import urllib
import json
import hashlib
import urllib2
import os
import os.path
import sys
import yaml
import tarfile
import zipfile
import PIL.Image
import inspect
import string
import re
import ConfigParser as configparser
from database import Database
from error import DatabaseError, print_exception_function,\
print_exception_thumbnail, print_exception_zip
from collections import defaultdict
from mako.lookup import TemplateLookup


def get_new_path( filename, create_dir=True, depth=2):
    """
    This method creates a new fullpath for a given file path,
    where new directories are created for each 'depth' first letters
    of the filename, for example:
      input  is /tmp/abvddff.png
      output is /tmp/a/b/v/d/abvddff.png
      where the full path /tmp/a/b/v/d has been created
      
      if the filename name starts with thumbnail_, use the name without
      'thumbnail_' to define its new path
      for example:
      /tmp/thumbnail_abvddff.png will be /tmpl/a/b/v/d/thumbnail_abvddff.png
      
    """
    prefix=""
    bname = os.path.basename(filename)
    if bname.startswith("thumbnail_"):
        prefix="thumbnail_"
        bname = bname[len(prefix):]
    dname = os.path.dirname(filename)  
    fname = bname.split(".")[0] 
    l = min(len(fname),depth)
    subdirs = '/'.join(list(fname[:l])) 
    new_dname = dname + '/' + subdirs + '/'
    if create_dir and not(os.path.isdir(new_dname)): os.makedirs(new_dname)
    return new_dname + prefix + bname

class MyFieldStorage(cherrypy._cpreqbody.Part):
    """
    This class allows to get uploaded blob creating temporary file in /tmp/
    See: https://cherrypy.readthedocs.org/en/3.3.0/refman/_cpreqbody.html
    """
    def make_file(self):
        return tempfile.NamedTemporaryFile()

cherrypy._cpreqbody.Entity.part_class = MyFieldStorage

class   Blobs(object):
    """
    This class implements Web service and Web Page separate with Cherrypy
    Web Service allows to interact with database (it's controller).
    The format argument (entry/leave) is JSON.
    Web Page allows to display html page. The format argument is HTML text.
    HTML page is templated using Mako
    Library
    """
    def __init__(self):
        """
        Initialize Blob class
        """

        self.tmp_dir = cherrypy.config['tmp.dir']
        self.final_dir = cherrypy.config['final.dir']
        self.thumb_dir = cherrypy.config['thumbnail.dir']
        self.test_dir = cherrypy.config['test.dir']

        self.current_directory = os.getcwd()
        self.html_dir = os.path.join(self.current_directory,
                                     cherrypy.config['html.dir'])
        self.server_address=  'http://{0}:{1}'.format(
                                  cherrypy.config['server.socket_host'],
                                  cherrypy.config['server.socket_port'])

    @cherrypy.expose
    def default(self, attr):
        """
        Default method invoked when asked for non-existing service.
        """
        data = {}
        data["status"] = "KO"
        data["message"] = "Unknown service '{}'".format(attr)
        return json.dumps(data)

    @cherrypy.expose
    def index(self):
        """
        Function exposed corresponding to '/' in url adress
        Return "index" html page for cherrypy.server.socket_host

        :return: mako templated html page (refer to demos.html)
        :rtype: mako.lookup.TemplatedLookup
        """
        data = {}
        res = use_web_service('/demos_ws', data)

        tmpl_lookup = TemplateLookup(directories=[self.html_dir])
        return tmpl_lookup.get_template("demos.html").render(list_demos=res["list_demos"])

    @cherrypy.expose
    def blob(self, demo_id):
        """
        Web page used to upload one blob to one demo

        :param demo_id: id demo
        :type demo_id: integer
        :return: mako templated html page (refer to demos.html)
        :rtype: mako.lookup.TemplatedLookup
        """
        tmpl_lookup = TemplateLookup(directories=[self.html_dir])
        return tmpl_lookup.get_template("add_blob.html").render(demo_id=demo_id)

    @cherrypy.expose
    def archive(self, demo_id):
        """
        Function used for upload zip file to one demo

        :param demo_id: id demo
        :type demo_id: integer
        :return: mako templated html page (refer to index.html)
        :rtype: mako.lookup.TemplatedLookup
        """
        tmpl_lookup = TemplateLookup(directories=[self.html_dir])
        return tmpl_lookup.get_template("add_archive.html").render(demo_id=demo_id)

    @cherrypy.expose
    @cherrypy.tools.accept(media="application/json")
    def add_blob_ws(self, demo_id, path, tag, ext, blob_set, blob_id_in_set,
                    title, credit):
        """
        This function implements get request (from '/add_blob_ws')
        It allows to check if demo given by name and blob given by hash
        is already in database if not it add its.

        :param demo_id:         demo id integer
        :param path:            blob path string
        :param tag:             name tag string
        :param ext:             extension of blob string
        :param blob_set:        string
        :param blob_id_in_set:  number, id of the blob within its blob_set
        :param title:           title blob string
        :param credit:          credit blob string
        :return:                hash of current blob (dictionnary) json format
        """
        print "*********************"
        print "*********************"
        print "add_blob_ws"
        blob_hash = get_hash_blob(path)
        print blob_hash
        fileformat = file_format(path)
        #hash_tmp = -1
        dic = {}
        dic["the_hash"] = blob_hash
        data = instance_database()

        try:
            data.start_transaction()
            blobid = -1
            if not data.blob_is_in_database(blob_hash):
              print "not in database"
              print fileformat
            else:
              print "in database"
              blobid = data.blob_id(blob_hash)
            data.add_blob_in_database(demo_id, blob_hash, fileformat,
                                      ext, tag, blob_set, blob_id_in_set,
                                      title, credit, blobid)

            data.commit()
            dic["return"] = "OK"
        except DatabaseError as error:
          print "Exception ", error
          print_exception_function(error, "Cannot add item in database")
          data.rollback()
          dic["return"] = "KO"

        #dic["the_hash"] = hash_tmp

        return json.dumps(dic)

    @cherrypy.expose
    @cherrypy.tools.accept(media="text/plain")
    def add_blob(self, **kwargs):
        """
        This function implements the web page '/add_blob'

        :param kwargs: list arguments
        :type: dict
        :return: mako templated html page refer to list.html
        :rtype: mako.lookup.TemplatedLookup
        """
        demo      = kwargs['demo[id]']
        tag       = kwargs['demo[tag]']
        blob      = kwargs['demo[blob]']
        blob_set  = kwargs['demo[set]']
        title     = kwargs['demo[title]']
        credit    = kwargs['demo[credit]']

        pattern = re.compile("^\s+|\s*,\s*|\s+$")
        list_tag = [x for x in pattern.split(tag) if x]

        if not list_tag:
            list_tag = [""]

        _, ext = os.path.splitext(blob.filename)
        assert isinstance(blob, cherrypy._cpreqbody.Part)

        tmp_directory = os.path.join(self.current_directory, self.tmp_dir)
        if not os.path.exists(tmp_directory):
            os.makedirs(tmp_directory)

        path = create_tmp_file(blob, tmp_directory)
        data = {"demo_id": demo, "path": path, "tag": list_tag, "ext": ext, 
                "blob_set": blob_set, "blob_id_in_set":0,
                "title": title, "credit": credit}
        res = use_web_service('/add_blob_ws/', data)

        if res["the_hash"] != -1 and res["return"] == "OK":
            file_dest = self.move_to_input_directory(path, res["the_hash"], ext)
            self.create_thumbnail(file_dest)
        else:
            os.remove(path)

        #tmpl_lookup = TemplateLookup(directories=[self.html_dir])
        #return tmpl_lookup.get_template("get_blobs_of_demo.html").render(demo_id=demo)

        return self.get_blobs_of_demo(demo)

    @cherrypy.expose
    @cherrypy.tools.accept(media="application/json")
    def demos_ws(self):
        """
        Web service used to have the list of demos from database

        :return: list of demos (dictionnary)
        :rtype: json format
        """
        data = instance_database()
        dic = {}
        dic["list_demos"] = {}
        try:
            dic["list_demos"] = data.list_of_demos()
            #jak
            #dic["return"] = "OK"
            dic["status"] = "OK"
        except DatabaseError as error:
            print_exception_function(error, "Cannot have the list of demos")
            #dic["return"] = "KO"
            dic["status"] = "KO"

        return json.dumps(dic)

    @cherrypy.expose
    @cherrypy.tools.accept(media="application/json")
    def get_template_demo_ws(self):
        """
        Web service used to have the list of template demos from database

        :return: list of template (dictionnary)
        :rtype: json format
        """
        data = instance_database()
        dic = {}
        dic["template_list"] = {}
        try:
            dic["template_list"] = data.list_of_template()
            dic["return"] = "OK"
        except DatabaseError as error:
            print_exception_function(error, "Cannot have the list of templates demos")
            dic["return"] = "KO"

        return json.dumps(dic)

    @cherrypy.expose
    def demo(self):
        """
        Web page used to add demo to database

        :return: mako templated html page refer to list.html
        :rtype: mako.lookup.TemplatedLookup
        """
        data = {}
        res = use_web_service('/get_template_demo_ws', data)

        tmpl_lookup = TemplateLookup(directories=[self.html_dir])
        return tmpl_lookup.get_template("add_demo.html").render(res_tmpl=res["template_list"])

    @cherrypy.expose
    @cherrypy.tools.accept(media="application/json")
    def set_template_ws(self, demo_id, name):
        """
        Web service used to change the current template used by a demo
        demo

        :param demo_id: id demo
        :type demo_id: integer
        :param name: name of the templated demo selected
        :type name: string
        :return: "OK" if not error else "KO"
        :rtype: json format
        """
        data = instance_database()
        dic = {}
        try:
            template_id = data.demo_id(name)
            if name == 'None':
                template_id = 0
            data.update_template(demo_id, template_id)
            data.commit()
            dic["return"] = "OK"
        except DatabaseError as error:
            print_exception_function(error, "Cannot update template used")
            dic["return"] = "KO"

        return json.dumps(dic)

    @cherrypy.expose
    @cherrypy.tools.accept(media="text/plain")
    def use_template(self, **kwargs):
        """
        Web page used to change templated demo used

        :param kwargs: list arguments
        :type: dict
        :return: mako templated html page (refer to edit_blob.html)
        :rtype: mako.lookup.TemplatedLookup
        """
        demo_id = kwargs["demo[id]"]
        name_tmpl = kwargs["name_template"]

        data = {"demo_id": demo_id, "name": name_tmpl}

        res = use_web_service('/set_template_ws', data)

        return self.get_blobs_of_demo(demo_id)

    @cherrypy.expose
    @cherrypy.tools.accept(media="application/json")
    def add_demo_ws(self, name, is_template, template):
        """
        Web service used to add demo to database

        :param name: name of the demo
        :type name: string
        :param is_template: if demo is a template equal 1 else 0
        :type is_template: boolean cast in integer
        :param template: name of the demo templated used
        :type template: string
        :return: "OK" if not error else "KO" (dictionnary)
        :rtype: json format
        """
        data = instance_database()
        dic = {}
        try:
            id_tmpl = 0
            if template:
                id_tmpl = data.demo_id(template)
            data.add_demo_in_database(name, is_template, id_tmpl)
            data.commit()
            dic["return"] = "OK"
        except DatabaseError as error:
            print_exception_function(error, "Cannot have the list of templates demos")
            data.rollback()
            dic["return"] = "KO"

        return json.dumps(dic)

    @cherrypy.expose
    @cherrypy.tools.accept(media="text/plain")
    def add_demo(self, **kwargs):
        """
        Web page used to add demo to database

        :param kwargs: list arguments
        :type: dict
        :return: mako templated html page refer to list.html
        :rtype: mako.lookup.TemplatedLookup
        """
        demo_name = kwargs["demo"]
        is_tmpl = kwargs["template"]
        is_template = 0
        template = kwargs["name_template"]

        if is_tmpl != '0':
            is_template = 1
            template = ""

        data = {"name": demo_name, "is_template": is_template, "template": template}
        res = use_web_service('/add_demo_ws', data)

        return self.index()

    @cherrypy.expose
    @cherrypy.tools.accept(media="text/plain")
    def add_from_archive(self, **kwargs):
        """
        This function implements post request for /zip
        It corresponds to upload of the zip file

        :param kwargs:
        :type kwargs: dictionnary
        :return: mako templated html page refer to list.html
        :rtype: mako.lookup.TemplatedLookup
        """
        demo_id     = kwargs['demo[id]']
        the_archive = kwargs['archive']

        _, ext = os.path.splitext(the_archive.filename)
        assert isinstance(the_archive, cherrypy._cpreqbody.Part)

        tmp_directory = os.path.join(self.current_directory, self.tmp_dir)
        if not os.path.exists(tmp_directory):
            os.makedirs(tmp_directory)

        print "tmp_directory = ", tmp_directory
        path = create_tmp_file(the_archive, tmp_directory)
        self.parse_archive(ext, path, tmp_directory, the_archive.filename, demo_id)

        return self.get_blobs_of_demo(demo_id)

    @cherrypy.expose
    @cherrypy.tools.accept(media="application/json")
    def delete_blobset_ws(self, demo_id, blobset):
        """
        This functions implements web service associated to '/delete_blob'
        Delete blob from demo name and hash blob in database

        :param demo_id: id demo
        :type demo_id: integer
        :param blobset: id blob
        :type blobset: string
        return: name of the blob if it is not associated to demo and
        "OK" if not error else "KO"
        :rtype: dictionnary
        """
        data = instance_database()
        dic = {}
        dic["delete"] = ""
        try:
            blob_name = data.get_blob_name(blob_id)
            value_return = data.delete_blobset_from_demo(demo_id, blobset)
            data.commit()

            if not value_return:
                dic["delete"] = blob_name
            dic["return"] = "OK"

        except DatabaseError as error:
            print_exception_function(error, "Cannot delete item in database")
            data.rollback()
            dic["return"] = "KO"

        return json.dumps(dic)

    @cherrypy.expose
    @cherrypy.tools.accept(media="application/json")
    def delete_blob_ws(self, demo_id, blob_set, blob_id):
        """
        This functions implements web service associated to '/delete_blob'
        Delete blob from demo name and hash blob in database

        :param demo_id: id demo
        :type demo_id: integer
        :param blob_id: id blob
        :type blob_id: integer
        return: name of the blob if it is not associated to demo and
        "OK" if not error else "KO"
        :rtype: dictionnary
        """
        data = instance_database()
        dic = {}
        dic["delete"] = ""
        try:
            blob_name     = data.get_blob_name(blob_id)
            value_return  = data.delete_blob_from_demo(demo_id, blob_set, blob_id)
            data.commit()

            if not value_return:
                dic["delete"] = blob_name
            dic["return"] = "OK"

        except DatabaseError as error:
            print_exception_function(error, "Cannot delete item in database")
            data.rollback()
            dic["return"] = "KO"

        return json.dumps(dic)

    @cherrypy.expose
    @cherrypy.tools.accept(media="application/json")
    def add_tag_to_blob_ws(self, blob_id, tag):
        """
        Web service of '/op_add_tag_to_blob'

        :param blob_id: id blob
        :type blob_id: integer
        :param tag: list of tag
        :type tag: list
        :return: "OK" if not error else "KO"
        :rtype: dictionnary
        """
        data = instance_database()
        dic = {}
        try:
            res = data.add_tag_in_database(blob_id, tag)
            data.commit()
            dic["return"] = "OK"
        except DatabaseError as error:
            print_exception_function(error, "Cannot add tag in database")
            data.rollback()
            dic["return"] = "KO"

        return json.dumps(dic)

    @cherrypy.expose
    @cherrypy.tools.accept(media="text/plain")
    def op_add_tag_to_blob(self, **kwargs):
        """
        Add tag to blob (POST Request)

        :param kwargs: list arguments
        :type kwargs: dictionnary
        :return: mako templated html page (refer to edit_blob.html)
        :rtype: mako.lookup.TemplatedLookup
        """
        tag = kwargs['tag']
        blob_id = kwargs['blob_id']
        demo_id = kwargs['demo_id']
        pattern = re.compile("^\s+|\s*,\s*|\s+$")
        list_tag = [x for x in pattern.split(tag) if x]

        if not list_tag:
            list_tag = [""]

        data = {"blob_id": blob_id, "tag": list_tag}
        res = use_web_service("/add_tag_to_blob_ws", data)

        return self.edit_blob(blob_id, demo_id)

    @cherrypy.expose
    @cherrypy.tools.accept(media="application/json")
    def remove_tag_from_blob_ws(self, tag_id, blob_id):
        """
        Web service of '/op_remove_tag_from_blob'

        :param tag_id: id tag
        :type tag_id: integer
        :param blob_id: id blob
        :type blob_id: integer
        :return: 'OK' if not error else 'KO'
        :rtype: dictionnary
        """
        data = instance_database()
        dic = {}
        try:
            res = data.delete_tag_from_blob(tag_id, blob_id)
            data.commit()
            dic["return"] = "OK"
        except DatabaseError as error:
            print_exception_function(error, "Cannot delete item in database")
            data.rollback()
            dic["return"] = "KO"

        return json.dumps(dic)

    @cherrypy.expose
    def op_remove_tag_from_blob(self, tag_id, blob_id, demo_id):
        """
        Remove one tag from blob

        :param tag_id: id tag
        :type tag_id: integer
        :param blob_id: id blob
        :type blob_id: integer
        :return: mako templated html page (refer to edit_blob.html)
        :rtype: mako.lookup.TemplatedLookup
        """
        data = {"tag_id": tag_id, "blob_id": blob_id}
        res = use_web_service("/remove_tag_from_blob_ws", data)
        return self.edit_blob(blob_id, demo_id)

    @cherrypy.expose
    def op_remove_blobset_from_demo(self, demo_id, blobset):
        """
        Delete one blobset from demo

        :param demo_id    : demo id
        :type demo_id     : integer
        :param blobset : blobset
        :type blobset  : string
        :return           : mako templated html page (refer to edit_demo_blobs.html)
        :rtype            : mako.lookup.TemplatedLookup
        """
        data = {"demo_id": demo_id, "blobset": blobset}
        res = use_web_service('/delete_blobset_ws', data)

        if (res["return"] == "OK" and res["delete"]):
            path_file = os.path.join(self.current_directory, self.final_dir,
                                     res["delete"])
            path_thumb = os.path.join(self.current_directory, self.thumb_dir,
                                      ("thumbnail_" + res["delete"]))
            # process paths
            path_file  = get_new_path(path_file)
            path_thumb = get_new_path(path_thumb)
            #
            if os.path.isfile(path_file):     os.remove(path_file)
            if os.path.isfile(path_thumb):    os.remove(path_thumb)

        return self.get_blobs_of_demo(demo_id)

    @cherrypy.expose
    def op_remove_blob_from_demo(self, demo_id, blob_set, blob_id):
        """
        Delete one blob from demo

        :param demo_id: id demo
        :type demo_id: integer
        :param blob_id: id blob
        :type blob_id: integer
        :return: mako templated html page (refer to edit_demo_blobs.html)
        :rtype: mako.lookup.TemplatedLookup
        """
        data = {"demo_id": demo_id, "blob_set": blob_set, "blob_id": blob_id}
        res = use_web_service('/delete_blob_ws', data)

        if (res["return"] == "OK" and res["delete"]):
            path_file  = os.path.join(self.current_directory, self.final_dir,  res["delete"])
            path_thumb = os.path.join(self.current_directory, self.thumb_dir, ("thumbnail_" + res["delete"]))
            # process paths
            path_file  = get_new_path(path_file)
            path_thumb = get_new_path(path_thumb)
            # remove blob
            if os.path.isfile(path_file) :  os.remove(path_file)
            if os.path.isfile(path_thumb):  os.remove(path_thumb)

        return self.get_blobs_of_demo(demo_id)

    @cherrypy.expose
    @cherrypy.tools.accept(media="application/json")
    def get_blobs_from_template_ws(self, template):
        """
        Web service used to get the list of blob from demo templated
        associated to another demo

        :param template: name of template demo
        :type template: string
        :return: the list of blobs and 'OK' if not error else 'KO'
        :rtype: dictionnary
        """
        dic = {}
        data = instance_database()
        try:
            template_id = data.demo_id(template)
            print template_id
            dic["blobs"] = data.get_blobs_of_demo(template_id)
            dic["return"] = "OK"
        except DatabaseError as error:
            print_exception_function(error, "Cannot access to blob from template demo")
            dic["return"] = "KO"

        return json.dumps(dic)

    #---------------------------------------------------------------------------
    @cherrypy.expose
    @cherrypy.tools.accept(media="application/json")
    def get_blobs_of_demo_by_name_ws(self, demo_name):
        """
        This function implements get request from '/get_hash' (Web Service)
        It returns list of hash blob corresponding to demo given in parameter
        List is empty if not any blob is associated to demo

        :param demo: name demo
        :type demo: string
        :return: list of hash blob
        :rtype: json format list
        """
        dic  = {}
        data = instance_database()
        try:
            dic                      = data.get_demo_info_from_name(demo_name)
            demo_id                  = dic.keys()[0]
            dic["use_template"]      = data.demo_use_template(demo_id)
            dic["blobs"]             = data.get_blobs_of_demo(demo_id)
            dic["url"]               = self.server_address+"/blob_directory/"
            dic["url_thumb"]         = self.server_address+"/thumbnail/"
            dic["physical_location"] = os.path.join(self.current_directory,
                                                    self.final_dir)
            ## process blobs paths
            #for idx in range(len(dic["blobs"])):
                #dic["blobs"][idx] = get_new_path(dic["blobs"][idx],False)
            dic["return"]            = "OK"
        except DatabaseError as error:
            print_exception_function(error, "Cannot access to blob from demo")
            dic["return"]            = "KO"

        return json.dumps(dic)

    #---------------------------------------------------------------------------
    @cherrypy.expose
    @cherrypy.tools.accept(media="application/json")
    def get_blobs_of_demo_ws(self, demo):
        """
        This function implements get request from '/get_hash' (Web Service)
        It returns list of hash blob corresponding to demo given in parameter
        List is empty if not any blob is associated to demo

        :param demo: name demo
        :type demo: string
        :return: list of hash blob
        :rtype: json format list
        """
        print "get_blobs_of_demo_ws"
        dic  = {}
        data = instance_database()
        try:
          dic = data.get_demo_name_from_id(demo)
          dic["use_template"] = data.demo_use_template(demo)
          dic["blobs"]        = data.get_blobs_of_demo(demo)
          dic["return"]       = "OK"
        except DatabaseError as error:
            print_exception_function(error, "Cannot access to blob from demo")
            dic["return"] = "KO"

        return json.dumps(dic)


    #---------------------------------------------------------------------------
    @cherrypy.expose
    def get_blobs_of_demo(self, demo_id):
        """
        Web page to show the blobs of the demo from id demo

        :param demo_id: id demo
        :type demo_id: integer
        :return: mako templated html page (refer to edit_demo_blobs.html)
        :rtype: mako.lookup.TemplatedLookup
        """

        demo_blobs = use_web_service('/get_blobs_of_demo_ws', {"demo": demo_id})
        template_list_res = use_web_service('/get_template_demo_ws', {})
        template        = {}
        template_blobs  = {}
        #--- if the demo uses a template, process its blobs
        if demo_blobs["use_template"]:
            template_blobs_res = use_web_service('/get_blobs_from_template_ws', 
                                                 {"template": demo_blobs["use_template"]["name"]})
            template_blobs = template_blobs_res['blobs']
            for blob_set in template_blobs:
              blob_size = blob_set[0]['size']
              for idx in range(1,blob_size+1):
                b = blob_set[idx]
                b_name = b["hash"]+b["extension"]
                b["physical_location"]  = os.path.join( self.current_directory, self.final_dir, b_name)
                b["url"]                = self.server_address+"/blob_directory/" + b_name
                b["url_thumb"]          = self.server_address+"/thumbnail/thumbnail_" + b_name
                # process paths
                b["physical_location"]  = get_new_path(blob_set[idx]["physical_location"],False)
                b["url"]                = get_new_path(blob_set[idx]["url"],False)
                b["url_thumb"]          = get_new_path(blob_set[idx]["url_thumb"],False)


        for blob_set in demo_blobs["blobs"]:
          blob_size = blob_set[0]['size']
          for idx in range(1,blob_size+1):
            b = blob_set[idx]
            b_name = b["hash"]+b["extension"]
            b["physical_location"]  = os.path.join(self.current_directory,self.final_dir,b_name)
            b["url"]                = self.server_address+"/blob_directory/" +b_name
            b["url_thumb"]          = self.server_address+"/thumbnail/thumbnail_" + b_name
            # process paths
            b["physical_location"]  = get_new_path(blob_set[idx]["physical_location"],False)
            b["url"]                = get_new_path(blob_set[idx]["url"],False)
            b["url_thumb"]          = get_new_path(blob_set[idx]["url_thumb"],False)


        tmpl_lookup = TemplateLookup(directories=[self.html_dir])
        return tmpl_lookup.get_template("edit_demo_blobs.html").render(
                blobs_list = demo_blobs["blobs"],
                demo_id    = demo_id,
                demo       = demo_blobs,
                tmpl_list  = template_list_res["template_list"],
                tmpl_blobs = template_blobs)

    #---------------------------------------------------------------------------
    @cherrypy.expose
    def edit_blob(self, blob_id, demo_id):
        """
        HTML Page : show thumbnail of one blob, add tag or remove tag

        :param blob_id: id blob
        :type blob_id: integer
        :return: mako templated html page (refer to edit_blob.html)
        :rtype: mako.lookup.TemplatedLookup
        """
        data = {"blob_id": blob_id}
        res = use_web_service('/get_blob_ws', data)

        print "return = ", res["return"]
        if res["return"] == "OK":
            b_name = res["hash"] + res["extension"]
            res["physical_location"] = os.path.join(self.current_directory,
                                                    self.final_dir,
                                                    b_name)
            res["url"]        = self.server_address+"/blob_directory/" + b_name
            res["url_thumb"]  = self.server_address+"/thumbnail/thumbnail_" + b_name
            res["tags"]       = use_web_service('/get_tags_ws', data)
            # process paths
            res["physical_location"]  = get_new_path(res["physical_location"],False)
            res["url"]                = get_new_path(res["url"],False)
            res["url_thumb"]          = get_new_path(res["url_thumb"],False)

        tmpl_lookup = TemplateLookup(directories=[self.html_dir])
        return tmpl_lookup.get_template("edit_blob.html").render(blob_info=res,
                                                                 demoid=demo_id)

    #@cherrypy.expose
    #def get_blob_url_ws(self, blob_hash, blob_ext):
        #dic = {}
        #dic['blob_url'] = self.server_address+"/blob_directory/"+blob_hash+blob_ext
        #return json.dumps(dic)

    #@cherrypy.expose
    #def get_blobpath_url_ws(self):
        #dic = {}
        #dic['blobpath_url'] = self.server_address+"/blob_directory/"
        #return json.dumps(dic)

    #@cherrypy.expose
    #def get_thumbpath_url_ws(self):
        #dic = {}
        #dic['thumbpath_url'] = self.server_address+"/thumbnail/"
        #return json.dumps(dic)

    #@cherrypy.expose
    #def get_blob_url_ws(self, blob_hash, blob_ext):
        #dic = {}
        #dic['blob_url'] = self.server_address+"/blob_directory/"+blob_hash+blob_ext
        #return json.dumps(dic)

    @cherrypy.expose
    @cherrypy.tools.accept(media="application/json")
    def get_blob_ws(self, blob_id):
        """
        Return informations of blob from id

        :param blob_id: id blob
        :type blob_id: integer
        :return: extension, id, hash, credit of blob
        :rtype: dictionnary
        """
        data = instance_database()
        dic = {}
        try:
            dic = data.get_blob(blob_id)
            dic["return"] = "OK"
        except DatabaseError as error:
            print_exception_function(error, "Cannot access to blob from id blob")
            dic["return"] = "KO"

        return json.dumps(dic)

    #---------------------------------------------------------------------------
    @cherrypy.expose
    @cherrypy.tools.accept(media="application/json")
    def get_tags_ws(self, blob_id):
        """
        Web service used to get the tag associated to the blob

        :param blob_id: id blob
        :type blob_id: integer
        :return: list of hash blob
        :rtype: json format list
        """
        lis = []
        data = instance_database()
        try:
            lis = data.get_tags_of_blob(blob_id)
        except DatabaseError as error:
            print_exception_function(error, "Cannot access to tag from blob")
        return json.dumps(lis)

    #---------------------------------------------------------------------------
    @cherrypy.expose
    @cherrypy.tools.accept(media="application/json")
    def op_remove_demo_ws(self, demo_id):
        """
        Web service used to remove demo from id demo

        :param demo_id: id demo
        :type demo_id: integer
        :return: "OK" if not error else "KO"
        :rtype: json format
        """
        data = instance_database()
        dic = {}
        try:
            data.remove_demo(demo_id)
            data.commit()
            dic["return"] = "OK"
        except DatabaseError as error:
            print_exception_function(error, "Cannot delete demo")
            data.rollback()
            dic["return"] = "KO"

        return json.dumps(dic)

    #---------------------------------------------------------------------------
    @cherrypy.expose
    def op_remove_demo(self, demo_id):
        """
        Web page used to remove a demo from id

        :param demo_id: id demo
        :type demo_id: integer
        :return: mako templated html page refer to list.html
        :rtype: mako.lookup.TemplatedLookup
        """
        data = {"demo_id": demo_id}
        resul = use_web_service('/op_remove_demo_ws', data)
        data = {}
        res = use_web_service('/demos_ws', data)

        tmpl_lookup = TemplateLookup(directories=[self.html_dir])
        return tmpl_lookup.get_template("demos.html").render(list_demos=res["list_demos"])

    #---------------------------------------------------------------------------
    def move_to_input_directory(self, path, the_hash, extension):
        """
        Create final blob directory if it doesn't exist
        Move the temporary blob in this directory
        Changing the name of the blob by the hash

        :param path: path of the temporary directory (!= /tmp/)
        :type path: string
        :param the_hash: hash content blob
        :type the_hash: string
        :param extension: extension of blob
        :type extension: string
        """
        file_directory = os.path.join(self.current_directory, self.final_dir)
        if not os.path.exists(file_directory):
            os.makedirs(file_directory)
        file_dest = os.path.join(file_directory, (the_hash + extension))
        file_dest = get_new_path(file_dest)
        shutil.move(path, file_dest)
        return file_dest

    #---------------------------------------------------------------------------
    def create_thumbnail(self, src):
        """
        Create thumbnail with source path of the image
        Needed to improve it for sound and video !

        :param src: source path of the blob
        :type src: string
        """
        file_directory = os.path.join(self.current_directory, self.thumb_dir)
        if not os.path.exists(file_directory):
            os.makedirs(file_directory)
        name = os.path.basename(src)
        file_dest = os.path.join(file_directory, ('thumbnail_' + name))
        name = "thumbnail_" + name
        fil_format = file_format(src)
        print "creating ",file_dest
        try:
            if fil_format == 'image':
                try:
                    image = PIL.Image.open(src)
                except:
                    print "Warning: failed to open image file"
                    return
                image.thumbnail((256, 256))
                image.save(file_dest)
        except IOError:
            print_exception_thumbnail("Cannot create thumbnail",\
                inspect.currentframe().f_code.co_name)

    #---------------------------------------------------------------------------
    def parse_archive(self, ext, path, tmp_directory, the_archive, demo_id):
        """
        Open archive (zip, tar) file
        Extract blob object in function informations in 'index.cfg' file
        Call Web service '/add_blob_ws' to add blob to the database

        :param ext: extension of the archive
        :type ext: string
        :param path: path of the archive
        :type path: string
        :param tmp_directory: path of the temporary directory
        :type tmp_directory: string
        :param the_archive: name zip file
        :type the_archive: string
        """
        if ext == '.zip':
            src = zipfile.ZipFile(path)
            files = src.namelist()
        else:
            src = tarfile.open(path)
            files = src.getnames()

        if 'index.cfg' in files:
            src.extract('index.cfg', path=tmp_directory)
            index_path = os.path.join(tmp_directory, 'index.cfg')
            buff = configparser.ConfigParser()
            buff.readfp(open(index_path))
            for section in buff.sections():
                the_files = buff.get(section, "files")
                list_file = the_files.split()
                for _file in list_file:
                  # to associate a blob image representation, use 
                  # 2 files separated by a comma
                  has_image_representation = False
                  # use the in the list position as the input number
                  file_id = list_file.index(_file)
                  if ',' in _file:
                    pos = _file.find(',')
                    _file_image = _file[pos+1:]
                    _file       = _file[:pos]
                    print "file=",_file, "_file_image=",_file_image
                    has_image_representation = True
                  if _file and _file in files:
                      title = buff.get(section, 'title')
                      print "processing:",title
                      try:
                        credit = buff.get(section, 'credit')
                      except:
                        credit = ""
                      try:
                        tags = buff.get(section, 'tag')
                      except:
                        tags = ""
                      src.extract(_file, path=tmp_directory)
                      tmp_path = os.path.join(tmp_directory, _file)
                      _, ext = os.path.splitext(tmp_path)
                      

                      data = {"demo_id": demo_id, "path": tmp_path,
                              "ext": ext, "blob_set": section, 
                              "blob_id_in_set": file_id, "title": title,
                              "credit": credit}
                      res = use_web_service('/add_blob_ws/', data)
                      
                      # add the tags
                      
                      res = use_web_service('/add_tag_to_blob_ws/', data)
                      
                      print " return = ", res["return"]
                      the_hash = res["the_hash"]
                      print the_hash
                      if the_hash != -1 and res["return"] == "OK":
                        file_dest = self.move_to_input_directory(tmp_path,
                                                                the_hash,
                                                                ext)
                        # in case of blob image representation, process it too
                        if has_image_representation:
                            src.extract(_file_image, path=tmp_directory)
                            tmp_image_path = os.path.join(tmp_directory, _file_image)
                            _, image_ext = os.path.splitext(tmp_image_path)
                            # TODO: force image representation to be PNG? , 
                            # do a conversion if needed?

                            # according to Miguel, don´t add a blob image representation
                            # as a blob item
                            data = {"demo_id": demo_id, "path": tmp_image_path, 
                                    "ext": image_ext, "blob_set": section, 
                                    "blob_id_in_set": file_id, "title": title,
                                    "credit": credit}
                            res = use_web_service('/add_blob_ws/', data)
                            the_hash = res["the_hash"]

                            file_image_dest = self.move_to_input_directory(
                                tmp_image_path,
                                the_hash,
                                image_ext)
                            self.create_thumbnail(file_image_dest)
                        else:
                            self.create_thumbnail(file_dest)
                      else:
                          os.remove(tmp_path)
                  else:
                      pass
        else:
            print_exception_zip(inspect.currentframe().f_code.co_name,\
                                the_archive)
    
    #---------------------------------------------------------------------------
    @cherrypy.expose
    def ping(self):
        """
        Ping pong.
        :rtype: JSON formatted string
        """
        data = {}
        data["status"] = "OK"
        data["ping"] = "pong"
        return json.dumps(data)

    @cherrypy.expose
    def shutdown(self):
        """
        Shutdown the module.
        """
        data = {}
        data["status"] = "KO"
        try:
            cherrypy.engine.exit()
            data["status"] = "OK"
        except Exception as ex:
            print "something went wrong in blobs module"
            sys.exit(1)
        return json.dumps(data)



def create_tmp_file(blob, path):
    """
    Create temporary directory and copy uploaded blob

    :param blob: blob object
    :type blob: class view.myFieldStorage
    :param path: path directory
    :type path: string
    :return: path copy file
    :rtype: string
    """
    (_, filename) = tempfile.mkstemp(dir=path)
    with open(filename, 'wb') as the_file:
        shutil.copyfileobj(blob.file, the_file)
    return filename

def use_web_service(req, data):
    """
    Call get function with urllib2

    :param req: name of get request
    :type req: string
    :param data: data needed for request
    :type data: dict
    :return: json decode
    :rtype: list
    """
    urls_values = urllib.urlencode(data, True)
    url = cherrypy.server.base() + req + '?' + urls_values
    res = urllib2.urlopen(url)
    tmp = res.read()
    return json.loads(tmp)

def get_hash_blob(path):
    """
    Return hash (content of blob in the sha1 form) from path blob

    :param path: path file
    :type path: string
    :return: sha1 content blob to define a blob (if 2 blob are the same hash,
    so it's the same blob
    :rtype:
    """
    with open(path, 'rb') as the_file:
        return hashlib.sha1(the_file.read()).hexdigest()

def file_format(the_file):
    """
    Return format of the file

    :param the_file: path of the file
    :type the_file: string
    :return: format of file (audio, image or video)
    :rtype: string
    """
    # if PIP version
    if "Magic" in dir(magic):
      mime = magic.Magic(mime=True)
      fileformat = mime.from_file(the_file)
      return fileformat[:5]
    else:
      print "This version of magic module is not officially supported by Python"
      print ", we advise you to install it from PIP."
      # if dist version
      if "open" in dir(magic):
        m = magic.open(magic.MAGIC_MIME)
        m.load()
        fileformat = m.file(the_file)
        return fileformat[:5]

def instance_database():
    """
    Create an instance of the Database object
    If an exception is catched, close the program

    :return: a connection to the database
    :rtype: Database object
    """
    try:
        data = Database("blob.db")
        return data
    except DatabaseError as error:
        print_exception_function(error,
                                 "Cannot instantiate Database Object")
        sys.exit(1)



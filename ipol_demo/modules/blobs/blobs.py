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
import threading
import logging
import time

from database import Database
from error import DatabaseError
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

        # control the concurrent access to the blobs instance
        self.blobs_lock = threading.Lock()
        
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
        
        self.database_dir = "db"
        self.database_name = "blob.db"
        
        self.logs_dir = cherrypy.config.get("logs_dir")
        try:
            if not os.path.exists(self.logs_dir):
                os.makedirs(self.logs_dir)
        except Exception as e:
            self.logs_dir = os.path.dirname(os.path.realpath(__file__))
            self.logger   = self.init_logging()
            self.logger.exception(
                    "Failed to create log dir (using file dir) : %s".format(e))
        else:
            self.logger   = self.init_logging()
        
        self.logger.info("----- starting blobs module -----")
                
        try:
            self.database_dir = cherrypy.config.get("database_dir")
        except:
            self.logger.exception("failed to get database_dir config")
        
        try:
            self.database_name = cherrypy.config.get("database_name")
        except:
            self.logger.exception("failed to get database_name config")
        
        ip = cherrypy.request.remote.ip
        print ip
        self.logger.info("---- IP connecting ---> " + ip)
        

    #---------------------------------------------------------------------------
    def init_logging(self):
        """
        Initialize the error logs of the module.
        """
        logger = logging.getLogger("blobs_log")
        # handle all messages for the moment
        logger.setLevel(logging.DEBUG)
        handler = logging.FileHandler(os.path.join(self.logs_dir, 'error.log'))
        formatter = logging.Formatter('%(asctime)s; [%(filename)s:%(lineno)s - %(funcName)20s() ] %(message)s', datefmt='%Y-%m-%d %H:%M:%S')
        handler.setFormatter(formatter)
        
        logger.addHandler(handler)
        return logger

        
    #---------------------------------------------------------------------------
    def instance_database(self):
        """
        Create an instance of the Database object
        If an exception is catched, close the program

        :return: a connection to the database
        :rtype: Database object
        """
        try:
            data = Database(self.database_dir, self.database_name, self.logger)
            return data
        except DatabaseError:
            self.logger.exception("Cannot instantiate Database Object")
            sys.exit(1)
            
        
    @cherrypy.expose
    def default(self, attr):
        """
        Default method invoked when asked for non-existing service.
        """
        data = {}
        cherrypy.response.headers['Content-Type'] = "application/json"
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
    def add_blob_ws(self, demo_id, path, tag, ext, blob_set, blob_pos_in_set,
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
        :param blob_pos_in_set:  number, id of the blob within its blob_set
        :param title:           title blob string
        :param credit:          credit blob string
        :return:                hash of current blob (dictionnary) json format
        """
        cherrypy.response.headers['Content-Type'] = "application/json"

        blob_hash = get_hash_blob(path)
        fileformat = file_format(path)
        #hash_tmp = -1
        dic = {}
        dic["the_hash"] = blob_hash
        data = self.instance_database()

        try:
            data.start_transaction()
            blobid = -1
            if not data.blob_is_in_database(blob_hash):
              self.logger.info( "not in database, format: "+ fileformat)
            else:
              blobid = data.blob_id(blob_hash)
            data.add_blob_in_database(demo_id, blob_hash, fileformat,
                                      ext, tag, blob_set, blob_pos_in_set,
                                      title, credit, blobid)

            data.commit()
            dic["status"] = "OK"
        except DatabaseError:
            self.logger.exception("Cannot add item in database")
            data.rollback()
            dic["status"] = "KO"

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
        tag       = kwargs['blob[tag]']
        blob      = kwargs['blob[file]']
        blob_set  = kwargs['blob[set]']
        blob_pos  = kwargs['blob[pos]']
        title     = kwargs['blob[title]']
        credit    = kwargs['blob[credit]']

        pattern = re.compile("^\s+|\s*,\s*|\s+$")
        list_tag = [x for x in pattern.split(tag) if x]

        if not list_tag:
            list_tag = [""]

        _, ext = os.path.splitext(blob.filename)
        assert isinstance(blob, cherrypy._cpreqbody.Part)

        tmp_directory = os.path.join(self.current_directory, self.tmp_dir)
        if not os.path.exists(tmp_directory):
            os.makedirs(tmp_directory)

        # pos in set 0 by default (if the set does not exists)
        blob_pos_in_set = 0
        
        # add blob to the end of the blobset
        # look for the size of the blobset
        blobset_size = 0
        demo_blobs = use_web_service('/get_blobs_of_demo_ws', {"demo": demo})
        for bs in demo_blobs["blobs"]:
          if bs[0]['set_name'] == blob_set:
              # check if blob_pos is an existing position
              # and also compute the maximal exisiting position
              blob_maxpos = 0
              for i in range(1,bs[0]['size']+1):
                  if str(bs[i]['pos_in_set'])==str(blob_pos):
                      blob_pos_in_set = blob_pos
                      break
                  else:
                      blob_maxpos = max(blob_maxpos,bs[i]['pos_in_set'])
                      blob_pos_in_set = blob_maxpos+1

        path = create_tmp_file(blob, tmp_directory)
        data = {"demo_id": demo, "path": path, "tag": list_tag, "ext": ext, 
                "blob_set": blob_set, "blob_pos_in_set":blob_pos_in_set,
                "title": title, "credit": credit}
        res = use_web_service('/add_blob_ws/', data)

        if res["the_hash"] != -1 and res["status"] == "OK":
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
        data = self.instance_database()
        cherrypy.response.headers['Content-Type'] = "application/json"

        dic = {}
        dic["list_demos"] = {}
        try:
            dic["list_demos"] = data.list_of_demos()
            dic["status"] = "OK"
        except DatabaseError:
            self.logger.exception("Cannot have the list of demos")
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
        data = self.instance_database()
        cherrypy.response.headers['Content-Type'] = "application/json"

        dic = {}
        dic["template_list"] = {}
        try:
            dic["template_list"] = data.list_of_template()
            dic["status"] = "OK"
        except DatabaseError:
            self.logger.exception("Cannot have the list of templates demos")
            dic["status"] = "KO"

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
        data = self.instance_database()
        cherrypy.response.headers['Content-Type'] = "application/json"

        dic = {}
        try:
            template_id = data.demo_id(name)
            if name == 'None':
                template_id = 0
            data.update_template(demo_id, template_id)
            data.commit()
            dic["status"] = "OK"
        except DatabaseError:
            self.logger.exception("Cannot update template used")
            dic["status"] = "KO"

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
        data = self.instance_database()
        dic = {}
        try:
            id_tmpl = 0
            if template:
                id_tmpl = data.demo_id(template)
            data.add_demo_in_database(name, is_template, id_tmpl)
            data.commit()
            dic["status"] = "OK"
        except DatabaseError:
            self.logger.exception("Cannot have the list of templates demos")
            data.rollback()
            dic["status"] = "KO"

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

        self.logger.info("tmp_directory = "+tmp_directory)
        path = create_tmp_file(the_archive, tmp_directory)
        self.parse_archive(ext, path, tmp_directory, the_archive.filename, demo_id)

        return self.get_blobs_of_demo(demo_id)

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
        dic = {}
        dic["delete"] = ""
        
        ip = cherrypy.request.remote.ip
        self.logger.info("-- IP: " + ip + " is removing blobs in delete_blob_ws" + str(cherrypy.request.headers))
        
        
        
        # wait for the lock until timeout in seconds is reach
        # if it can lock, locks and returns True
        # otherwise returns False
        # code based on http://stackoverflow.com/questions/8392640/how-to-
        # implement-a-lock-with-a-timeout-in-python-2-7
        # another option is to use Queue:
        # http://stackoverflow.com/questions/35149889/lock-with-timeout-in-
        # python2-7
        def waitLock(lock,timeout):
            current_time = start_time = time.time()
            while current_time < start_time + timeout:
                if lock.acquire(False):
                    return True
                else:
                    # wait for 50ms and try again
                    time.sleep(0.05)
                    current_time = time.time()
            return False
        
        # prevent simultaneous calls
        # try to acquire lock during 3 seconds
        if waitLock(self.blobs_lock,3):
        
            data = self.instance_database()

            try:
                blob_name     = data.get_blob_filename(blob_id)
                has_no_demo   = data.delete_blob_from_demo(demo_id, blob_set, blob_id)
                data.commit()
                if has_no_demo:
                    dic["delete"] = blob_name
                dic["status"] = "OK"

            except DatabaseError:
                self.logger.exception("Cannot delete item in database")
                data.rollback()
                dic["status"] = "KO"

            finally:
                self.blobs_lock.release()

        else:
            self.logger.error( "Failed to acquire blobs lock")
            dic["status"]  = "KO"
            
        cherrypy.response.headers['Content-Type'] = "application/json"
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
        data = self.instance_database()
        cherrypy.response.headers['Content-Type'] = "application/json"

        dic = {}
        try:
            res = data.add_tag_in_database(blob_id, tag)
            data.commit()
            dic["status"] = "OK"
        except DatabaseError:
            self.logger.exception("Cannot add tag in database")
            data.rollback()
            dic["status"] = "KO"

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
        data = self.instance_database()
        cherrypy.response.headers['Content-Type'] = "application/json"

        dic = {}
        try:
            res = data.delete_tag_from_blob(tag_id, blob_id)
            data.commit()
            dic["status"] = "OK"
        except DatabaseError:
            self.logger.exception("Cannot delete item in database")
            data.rollback()
            dic["status"] = "KO"

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

    #@cherrypy.expose
    #def op_remove_blobset_from_demo(self, demo_id, blobset):
        #"""
        #Delete one blobset from demo

        #:param demo_id    : demo id
        #:type demo_id     : integer
        #:param blobset : blobset
        #:type blobset  : string
        #:return           : mako templated html page (refer to edit_demo_blobs.html)
        #:rtype            : mako.lookup.TemplatedLookup
        #"""
        #data = {"demo_id": demo_id, "blobset": blobset}
        #res = use_web_service('/delete_blobset_ws', data)

        #if (res["status"] == "OK" and res["delete"]):
            #path_file = os.path.join(self.current_directory, self.final_dir,
                                     #res["delete"])
            #path_thumb = os.path.join(self.current_directory, self.thumb_dir,
                                      #("thumbnail_" + res["delete"]))
            ## process paths
            #path_file  = get_new_path(path_file)
            #path_thumb = get_new_path(path_thumb)
            ##
            #if os.path.isfile(path_file):     os.remove(path_file)
            #if os.path.isfile(path_thumb):    os.remove(path_thumb)

        #return self.get_blobs_of_demo(demo_id)

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
        
        ip = cherrypy.request.remote.ip
        self.logger.info("-- IP: " + ip + " is removing blobs in op_remove_blob_from_demo - " + str(cherrypy.request.headers))
        
        if (res["status"] == "OK" and res["delete"]):
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
        cherrypy.response.headers['Content-Type'] = "application/json"

        data = self.instance_database()
        try:
            template_id = data.demo_id(template)
            dic["blobs"] = data.get_blobs_of_demo(template_id)
            dic["status"] = "OK"
        except DatabaseError:
            self.logger.exception("Cannot access to blob from template demo")
            dic["status"] = "KO"

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
        cherrypy.response.headers['Content-Type'] = "application/json"
        dic["status"] = "KO"
        data = self.instance_database()
        try:
            dic                  = data.get_demo_info_from_name(demo_name)
            demo_id                  = dic.keys()[0]
            dic["use_template"]      = data.demo_use_template(demo_id)
            dic["blobs"]             = data.get_blobs_of_demo(demo_id)
            dic["url"]               = self.server_address+"/blob_directory/"
            dic["url_thumb"]         = self.server_address+"/thumbnail/"
            dic["physical_location"] = os.path.join(self.current_directory,
                                                    self.final_dir)
            dic["status"]            = "OK"
        except DatabaseError:
            self.logger.exception("Cannot access to blob from demo")
            

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
        cherrypy.response.headers['Content-Type'] = "application/json"
        dic  = {}
        data = self.instance_database()
        try:
          dic = data.get_demo_name_from_id(demo)
          dic["use_template"] = data.demo_use_template(demo)
          dic["blobs"]        = data.get_blobs_of_demo(demo)
          dic["status"]       = "OK"
        except DatabaseError:
            self.logger.exception("Cannot access to blob from demo")
            dic["status"] = "KO"

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

        if res["status"] == "OK":
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
        data = self.instance_database()
        cherrypy.response.headers['Content-Type'] = "application/json"

        dic = {}
        try:
            dic = data.get_blob(blob_id)
            dic["status"] = "OK"
        except DatabaseError:
            self.logger.exception("Cannot access to blob from id blob")
            dic["status"] = "KO"

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
        cherrypy.response.headers['Content-Type'] = "application/json"

        data = self.instance_database()
        try:
            lis = data.get_tags_of_blob(blob_id)
        except DatabaseError:
            self.logger.exception("Cannot access to tag from blob")
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
        cherrypy.response.headers['Content-Type'] = "application/json"

        data = self.instance_database()
        dic = {}
        try:
            blobfilenames_to_delete = data.remove_demo(demo_id)
            data.commit()
            dic["status"] = "OK"
            
            # remove from disk unused blobs
            for blobfilename in blobfilenames_to_delete:
                self.logger.debug("blobfilename to delete ="+blobfilename)
                path_file  = os.path.join(self.current_directory, self.final_dir,  blobfilename)
                path_thumb = os.path.join(self.current_directory, self.thumb_dir, ("thumbnail_" + blobfilename))
                # process paths
                path_file  = get_new_path(path_file)
                path_thumb = get_new_path(path_thumb)
                # remove blob
                if os.path.isfile(path_file) :  
                    self.logger.info("removing "+path_file)
                    os.remove(path_file)
                if os.path.isfile(path_thumb): 
                    self.logger.info("removing "+path_thumb)
                    os.remove(path_thumb)
            
        except DatabaseError:
            self.logger.exception("Cannot delete demo")
            data.rollback()
            dic["status"] = "KO"

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
        file_dest = get_new_path(file_dest)
        name = "thumbnail_" + name
        fil_format = file_format(src)
        self.logger.info( "creating "+file_dest)
        try:
            if fil_format == 'image':
                try:
                    image = PIL.Image.open(src)
                except:
                    self.logger.exception( "failed to open image file")
                    return
                image.thumbnail((256, 256))
                image.save(file_dest)
        except IOError:
            self.logger.exception("Cannot create thumbnail")

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
                    has_image_representation = True
                  if _file and _file in files:
                      title = buff.get(section, 'title')
                      self.logger.debug("processing:"+title)
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
                              "tag":tags,
                              "ext": ext, "blob_set": section, 
                              "blob_pos_in_set": file_id, "title": title,
                              "credit": credit}
                      self.logger.debug("add_blob_ws data = {0}".format(data))
                      res = use_web_service('/add_blob_ws/', data)
                      
                      # add the tags
                      
                      #res = use_web_service('/add_tag_to_blob_ws/', data)
                      
                      self.logger.debug(" return = "+ res["status"])
                      the_hash = res["the_hash"]
                      if the_hash != -1 and res["status"] == "OK":
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
                                    "tag":tags,
                                    "ext": image_ext, "blob_set": section, 
                                    "blob_pos_in_set": file_id, "title": title,
                                    "credit": credit}
                            self.logger.debug("add_blob_ws data = {0}".format(data))
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
            self.logger.exception(
                            "ZipError: index.cfg missing in " + the_archive +
                            ": Cannot add item in database")
    
    #---------------------------------------------------------------------------
    @cherrypy.expose
    def ping(self):
        """
        Ping pong.
        :rtype: JSON formatted string
        """
        data = {}
        cherrypy.response.headers['Content-Type'] = "application/json"

        data["status"] = "OK"
        data["ping"] = "pong"
        return json.dumps(data)

    @cherrypy.expose
    def shutdown(self):
        """
        Shutdown the module.
        """
        data = {}
        cherrypy.response.headers['Content-Type'] = "application/json"

        data["status"] = "KO"
        try:
            cherrypy.engine.exit()
            data["status"] = "OK"
        except Exception as ex:
            self.logger.error("Failed to shutdown")
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
    #cherrypy.response.headers['Content-Type'] = "application/json"

    urls_values = urllib.urlencode(data, True)
    url = cherrypy.server.base() + req + '?' + urls_values
    print "url=",url
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
      self.logger.warning("This version of magic module is not officially "\
                          "supported by Python, "\
                          "we advise you to install it from PIP.")
      # if dist version
      if "open" in dir(magic):
        m = magic.open(magic.MAGIC_MIME)
        m.load()
        fileformat = m.file(the_file)
        return fileformat[:5]




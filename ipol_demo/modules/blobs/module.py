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

class MyFieldStorage(cherrypy._cpreqbody.Part):
    """
    This class allows to get uploaded blob creating temporary file in /tmp/
    See: https://cherrypy.readthedocs.org/en/3.3.0/refman/_cpreqbody.html
    """
    def make_file(self):
        return tempfile.NamedTemporaryFile()

cherrypy._cpreqbody.Entity.part_class = MyFieldStorage

class   Blob(object):
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
        return tmpl_lookup.get_template("demos.html").render(the_list=res["list_demos"])

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
    def zip(self, demo_id):
        """
        Function used for upload zip file to one demo

        :param demo_id: id demo
        :type demo_id: integer
        :return: mako templated html page (refer to index.html)
        :rtype: mako.lookup.TemplatedLookup
        """
        tmpl_lookup = TemplateLookup(directories=[self.html_dir])
        return tmpl_lookup.get_template("add_zip.html").render(demo_id=demo_id)

    @cherrypy.expose
    @cherrypy.tools.accept(media="application/json")
    def add_blob_ws(self, demo_id, path, tag, ext, the_set, title, credit):
        """
        This function implements get request (from '/add_blob_ws')
        It allows to check if demo given by name and blob given by hash
        is already in databse if not it add its.

        :param demo_id: id demo
        :type demo_id: integer
        :param path: blob path
        :type path: string
        :param tag: name tag
        :type tag: string
        :param ext: extension of blob
        :type ext: string
        :param the_set:
        :type the_set: string
        :param title: title blob
        :type title: string
        :param credit: credit blob
        :type credit: string
        :return: hash current blob (dictionnary)
        :rtype: json format
        """
        hash_blob = get_hash_blob(path)
        fileformat = file_format(path)
        hash_tmp = -1
        dic = {}
        data = instance_database()

        try:
            data.start_transaction()
            if not data.blob_is_in_database(hash_blob):
                if data.format_is_good(fileformat):
                    data.add_blob_in_database(demo_id, hash_blob,
                                              fileformat, ext, tag,
                                              the_set, title, credit)
                    hash_tmp = hash_blob
            else:
                blobid = data.id_blob(hash_blob)
                data.add_blob_in_database(demo_id, hash_blob, fileformat,
                                          ext, tag, the_set,
                                          title, credit, blobid)

            data.commit()
            dic["return"] = "OK"
        except DatabaseError as error:
            print_exception_function(error, "Cannot add item in database")
            data.rollback()
            dic["return"] = "KO"

        dic["the_hash"] = hash_tmp

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
        demo = kwargs['demo[id]']
        tag = kwargs['demo[tag]']
        blob = kwargs['demo[blob]']
        the_set = kwargs['demo[set]']
        title = kwargs['demo[title]']
        credit = kwargs['demo[credit]']

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
        data = {"demo_id": demo, "path": path, "tag": list_tag, "ext": ext, "the_set": the_set,
                "title": title, "credit": credit}
        res = use_web_service('/add_blob_ws/', data)

        if res["the_hash"] != -1 and res["return"] == "OK":
            file_dest = self.move_to_input_directory(path, res["the_hash"], ext)
            self.create_thumbnail(file_dest)
        else:
            os.remove(path)

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
            dic["return"] = "OK"
        except DatabaseError as error:
            print_exception_function(error, "Cannot have the list of demos")
            dic["return"] = "KO"

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
        dic["list_template"] = {}
        try:
            dic["list_template"] = data.list_of_template()
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
        return tmpl_lookup.get_template("add_demo.html").render(res_tmpl=res["list_template"])

    @cherrypy.expose
    @cherrypy.tools.accept(media="application/json")
    def set_template_ws(self, demo_id, name):
        """
        Web service used to change the current template used by another
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
            id_template = data.id_demo(name)
            if name == 'None':
                id_template = 0
            data.update_template(demo_id, id_template)
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
                id_tmpl = data.id_demo(template)
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
    def add_from_zip(self, **kwargs):
        """
        This function implements post request for /zip
        It corresponds to upload of the zip file

        :param kwargs:
        :type kwargs: dictionnary
        :return: mako templated html page refer to list.html
        :rtype: mako.lookup.TemplatedLookup
        """
        demo_id = kwargs['demo[id]']
        the_zip = kwargs['zip']

        _, ext = os.path.splitext(the_zip.filename)
        assert isinstance(the_zip, cherrypy._cpreqbody.Part)

        tmp_directory = os.path.join(self.current_directory, self.tmp_dir)
        if not os.path.exists(tmp_directory):
            os.makedirs(tmp_directory)

        path = create_tmp_file(the_zip, tmp_directory)
        self.parse_archive(ext, path, tmp_directory, the_zip.filename, demo_id)

        return self.get_blobs_of_demo(demo_id)

    @cherrypy.expose
    @cherrypy.tools.accept(media="application/json")
    def delete_blob_ws(self, demo_id, blob_id):
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
            blob_name = data.get_name_blob(blob_id)
            value_return = data.delete_blob_from_demo(demo_id, blob_id)
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
    def op_remove_blob_from_demo(self, demo_id, blob_id):
        """
        Delete one blob from demo

        :param demo_id: id demo
        :type demo_id: integer
        :param blob_id: id blob
        :type blob_id: integer
        :return: mako templated html page (refer to get.html)
        :rtype: mako.lookup.TemplatedLookup
        """
        data = {"demo_id": demo_id, "blob_id": blob_id}
        res = use_web_service('/delete_blob_ws', data)

        if (res["return"] == "OK" and res["delete"]):
            path_file = os.path.join(self.current_directory, self.final_dir,
                                     res["delete"])
            path_thumb = os.path.join(self.current_directory, self.thumb_dir,
                                      ("thumbnail_" + res["delete"]))
            if os.path.isfile(path_file):
                os.remove(path_file)
            if os.path.isfile(path_thumb):
                os.remove(path_thumb)

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
            id_template = data.id_demo(template)
            print id_template
            dic["blobs"] = data.get_blobs_of_demo(id_template)
            dic["return"] = "OK"
        except DatabaseError as error:
            print_exception_function(error, "Cannot access to blob from template demo")
            dic["return"] = "KO"

        return json.dumps(dic)

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
        dic  = {}
        data = instance_database()
        try:
            dic = data.get_demo_name_from_id(demo)
            dic["use_template"] = data.demo_use_template(demo)
            dic["blobs"] = data.get_blobs_of_demo(demo)
            dic["return"] = "OK"
        except DatabaseError as error:
            print_exception_function(error, "Cannot access to blob from demo")
            dic["return"] = "KO"

        return json.dumps(dic)

    @cherrypy.expose
    def get_blobs_of_demo(self, demo_id):
        """
        Web page to show the blobs of the demo from id demo

        :param demo_id: id demo
        :type demo_id: integer
        :return: mako templated html page (refer to get.html)
        :rtype: mako.lookup.TemplatedLookup
        """
        data = {"demo": demo_id}
        res = use_web_service('/get_blobs_of_demo_ws', data)
        data = {}
        result = use_web_service('/get_template_demo_ws', data)
        template = {}
        template["blobs"] = {}
        if res["use_template"]:
            data = {"template": res["use_template"]["name"]}
            template = use_web_service('/get_blobs_from_template_ws', data)
            for item in template["blobs"]:
                item["physical_location"] = os.path.join(self.current_directory,
                                                         self.final_dir,
                                                         (item["hash"] + item["extension"]))
                item["url"] = "http://localhost:7777/blob_directory/" + item["hash"] \
                              + item["extension"]
                item["url_thumb"] = "http://localhost:7777/thumbnail/" + \
                                    "thumbnail_" + item["hash"] + item["extension"]


        for item in res["blobs"]:
            item["physical_location"] = os.path.join(self.current_directory,
                                                     self.final_dir,
                                                     (item["hash"] + item["extension"]))
            item["url"] = "http://localhost:7777/blob_directory/" + item["hash"] \
                          + item["extension"]
            item["url_thumb"] = "http://localhost:7777/thumbnail/" + \
                                "thumbnail_" + item["hash"] + item["extension"]


        tmpl_lookup = TemplateLookup(directories=[self.html_dir])
        return tmpl_lookup.get_template("get.html").render(the_list=res["blobs"],
                                                           demo_id=demo_id,
                                                           demo=res,
                                                           res_tmpl=result["list_template"],
                                                           list_tmpl=template["blobs"])

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

        if res["return"] == "OK":
            res["physical_location"] = os.path.join(self.current_directory,
                                                    self.final_dir,
                                                    (res["hash"] + res["extension"]))
            res["url"] = "http://localhost:7777/blob_directory/" + res["hash"] \
                         + res["extension"]
            res["url_thumb"] = "http://localhost:7777/thumbnail/" + \
                               "thumbnail_" + res["hash"] + res["extension"]

            res["tags"] = use_web_service('/get_tags_ws', data)

        tmpl_lookup = TemplateLookup(directories=[self.html_dir])
        return tmpl_lookup.get_template("edit_blob.html").render(blob_info=res,
                                                                 demoid=demo_id)

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
        return tmpl_lookup.get_template("demos.html").render(the_list=res["list_demos"])

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
        shutil.move(path, file_dest)
        return file_dest

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
        try:
            if fil_format == 'image':
                image = PIL.Image.open(src)
                image.thumbnail((256, 256))
                image.save(file_dest)
        except IOError:
            print_exception_thumbnail("Cannot create thumbnail",\
                inspect.currentframe().f_code.co_name)

    def parse_archive(self, ext, path, tmp_directory, the_zip, demo_id):
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
        :param the_zip: name zip file
        :type the_zip: string
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
            for item in buff.sections():
                the_file = buff.get(item, "files")
                list_file = the_file.split()
                for the_item in list_file:
                    if the_item and the_item in files:
                        title = buff.get(item, 'title')
                        credit = buff.get(item, 'credit')
                        src.extract(the_item, path=tmp_directory)
                        tmp_path = os.path.join(tmp_directory, the_item)
                        _, ext = os.path.splitext(tmp_path)

                        data = {"demo_id": demo_id, "path": tmp_path, "tag": "",
                                "ext": ext, "the_set": item, "title": title,
                                "credit": credit}
                        res = use_web_service('/add_blob_ws/', data)

                        the_hash = res["the_hash"]
                        if the_hash != -1 and res["return"] == "OK":
                            file_dest = self.move_to_input_directory(tmp_path,
                                                                     the_hash,
                                                                     ext)
                            self.create_thumbnail(file_dest)
                        else:
                            os.remove(tmp_path)
                    else:
                        pass
        else:
            print_exception_zip(inspect.currentframe().f_code.co_name,\
                                the_zip)

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
    mime = magic.Magic(mime=True)
    fileformat = mime.from_file(the_file)
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



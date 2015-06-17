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
import os, os.path
from database import Database
import yaml
from collections import defaultdict
from mako.lookup import TemplateLookup

class myFieldStorage(cherrypy._cpreqbody.Part):
    """
    This class allows to get uploaded blob creating temporary file in /tmp/
    See: https://cherrypy.readthedocs.org/en/3.3.0/refman/_cpreqbody.html
    """
    def make_file(self):
        return tempfile.NamedTemporaryFile()

cherrypy._cpreqbody.Entity.part_class = myFieldStorage

class   Blob(object):
    """
    This class implements Web service and Web Page separate with Cherrypy
    Web Service allows to interact with database (it's controller). The format argument (entry/leave) is JSON.
    Web Page allows to display html page. The format argument is HTML text. HTML page is templated using Mako
    Library
    """
    def __init__(self, tmp, final, html):
        """
        Initialize Blob class

        :param tmp: name of tmp directory blob
        :type tmp: string
        :param final: name of final directory blob
        :type final: string
        :param html: name of html directory template page
        :type html: string
        """
        self.tmp_dir = tmp
        self.final_dir = final
        self.html_dir = html

        self.data = Database("blob.db")
        self.current_directory = os.getcwd()


    @cherrypy.expose
    def index(self):
        """
        Function exposed corresponding to '/' in url adress
        Return "index" html page for cherrypy.server.socket_host

        :return: mako templated html page (refer to index.html)
        :rtype: mako.lookup.TemplatedLookup
        """
        tmp_dir = self.current_directory + self.html_dir
        tmpl_lookup = TemplateLookup(directories=[tmp_dir])
        return tmpl_lookup.get_template("index.html").render()

    @cherrypy.expose
    @cherrypy.tools.accept(media="application/json")
    def add_blob_ws(self, name, path, tag):
        """
        This function implements get request (from '/add_blob_ws')
        It allows to check if app given by name and blob given by hash
        is already in databse if not it add its.

        :param name: name app
        :type name: string
        :param path: blob path
        :type path: string
        :param tag: name tag
        :type tag: string
        :return: tuple(list of name and hash, hash current blob)
        :rtype: json format tuple (list, string)
        """
        hash_blob = self.getHashBlob(path)
        fileformat = self.fileFormat(path)
        appid_tmp = -1
        hash_tmp = -1
        if not self.data.appIsInDatabase(name):
            appid_tmp = self.data.addAppInDatabase(name)
            appid = appid_tmp
        else:
            appid = self.data.idApp(name)
        if not self.data.blobIsInDatabase(hash_blob):
            if self.data.formatIsGood(fileformat):
                self.data.addBlobInDatabase(appid, hash_blob, fileformat, tag)
                hash_tmp = hash_blob
            else:
                if appid_tmp != -1:
                    self.data.deleteApp(appid)
        else:
            blobid = self.data.idBlob(hash_blob)
            self.data.addBlobInDatabase(appid, hash_blob, fileformat, tag, blobid)

        self.data.commit()

        list_ddb = self.data.returnList()
        list_sort = self.dictFromList(list_ddb)

        return json.dumps((list_sort, hash_tmp))

    @cherrypy.expose
    @cherrypy.config(**{'response.timeout': 3600})
    @cherrypy.tools.accept(media="text/plain")
    def add_blob(self, **kwargs):
        """
        This function implements post request from '/add_blob'

        :param kwargs: list arguments
        :type: dict
        :return: mako templated html page refer to list.html
        :rtype: mako.lookup.TemplatedLookup
        """
        app = kwargs.pop('app[name]', [])
        tag = kwargs.pop('app[tag]', [])
        blob = kwargs.pop('app[blob]', [])

        assert isinstance(blob, cherrypy._cpreqbody.Part)

        tmp_directory = self.current_directory + self.tmp_dir
        if not os.path.exists(tmp_directory):
            os.makedirs(tmp_directory)

        path = self.create_tmp_file(blob, tmp_directory)
        data = {"name": app, "path": path, "tag": tag}
        res = self.useWebService('/add_blob_ws/', data)

        if res[1] != -1:
            self.moveToInputDirectory(path, res[1])
        else:
            os.remove(path)

        tmp_dir = self.current_directory + self.html_dir
        tmpl_lookup = TemplateLookup(directories=[tmp_dir])
        return tmpl_lookup.get_template("list.html").render(the_list=res[0])

    @cherrypy.expose
    @cherrypy.tools.accept(media="application/json")
    def delete_blob_ws(self, app, hash_blob):
        """
        This functions implements web service associated to '/delete_blob'
        Delete blob from app name and hash blob in database

        :param app: name app
        :type app: string
        :param hash_blob: hash blob
        :type hash_blob: string
        return: True if blob is not associated to any app else False
        :rtype: json format bool
        """
        value_return = self.data.deleteFromBlobApp(app, hash_blob)
        self.data.commit()

        list_ddb = self.data.returnList()
        list_sort = self.dictFromList(list_ddb)

        return json.dumps((list_sort, value_return))

    @cherrypy.expose
    @cherrypy.tools.accept(media="text/plain")
    def delete_blob(self, app, blob):
        """
        Call WebService '/delete_blob_ws' associated
        Delete blob in final directory if it's necessary

        :param app: name app
        :type app: string
        :param blob: hash blob
        :type blob: string
        :return: mako templated html page refer to list.html
        :rtype: mako.lookup.TemplatedLookup
        """
        data = {"app": app, "hash_blob": blob}
        res = self.useWebService('/delete_blob_ws', data)

        if res[1]:
            path_file = self.current_directory + self.final_dir + blob
            print path_file
            os.remove(path_file)

        tmp_dir = self.current_directory + self.html_dir
        tmpl_lookup = TemplateLookup(directories=[tmp_dir])
        return tmpl_lookup.get_template("list.html").render(the_list=res[0])

    @cherrypy.expose
    @cherrypy.tools.accept(media="application/json")
    def get_app_ws(self, hash_blob):
        """
        This function implements get request from '/get_app_ws' (Web Service)
        It returns list of app corresponding to hash blob given in parameter
        List is empty if not any app is associated to blob

        :param hash_blob: hash blob
        :type hash_blob: string
        :return: list of app
        :rtype: json format list
        """
        return json.dumps(self.data.getAppOfHash(hash_blob))

    @cherrypy.expose
    @cherrypy.tools.accept(media="text/plain")
    def get_app_of_hash(self, hash_blob):
        """
        This functions implements get request from '/get_app_of_hash' (Web Page)
        Call Webservice associated

        :param hash_blob: hash blob
        :type hash_blob: string
        :return: mako templated html page (refer to get.html)
        :rtype: mako.lookup.TemplatedLookup
        """
        data = {"hash_blob": hash_blob}
        res = self.useWebService('/get_app_ws', data)

        tmp_dir = self.current_directory + self.html_dir
        tmpl_lookup = TemplateLookup(directories=[tmp_dir])
        return tmpl_lookup.get_template("get.html").render(the_list=res, val=hash_blob)

    @cherrypy.expose
    @cherrypy.tools.accept(media="application/json")
    def get_hash_ws(self, app):
        """
        This function implements get request from '/get_hash' (Web Service)
        It returns list of hash blob corresponding to app given in parameter
        List is empty if not any blob is associated to app

        :param app: name app
        :type app: string
        :return: list of hash blob
        :rtype: json format list
        """
        return json.dumps(self.data.getHashOfApp(app))

    @cherrypy.expose
    @cherrypy.tools.accept(media="text/plain")
    def get_hash_of_app(self, app):
        """
        This functions implements get request from '/get_hash_of_app' (Web Page)
        Call Webservice associated

        :param app: name app
        :type app: string
        :return: mako templated html page (refer to get.html)
        :rtype: mako.lookup.TemplatedLookup
        """
        data = {"app": app}
        res = self.useWebService('/get_hash_ws', data)

        tmp_dir = os.path.join(os.path.dirname(__file__)) + self.html_dir
        tmpl_lookup = TemplateLookup(directories=[tmp_dir])
        return tmpl_lookup.get_template("get.html").render(the_list=res, val=app)

    @cherrypy.expose
    @cherrypy.tools.accept(media="application/json")
    def get_blob_ws(self, tag):
        """
        This function implements get request from '/get_blob' (Web Service)
        It returns list of hash blob corresponding to app given in parameter
        List is empty if not any blob is associated to app

        :param tag: name tag
        :type tag: string
        :return: list of hash blob
        :rtype: json format list
        """
        return json.dumps(self.data.getBlobOfTags(tag))

    @cherrypy.expose
    @cherrypy.tools.accept(media="text/plain")
    def get_blob_of_tag(self, tag):
        """
        This functions implements get request from '/get_blob_of_tag' (Web Page)
        Call Webservice associated

        :param tag: name tag
        :type tag: string
        :return: mako templated html page (refer to get.html)
        :rtype: mako.lookup.TemplatedLookup
        """
        data = {"tag": tag}
        res = self.useWebService('/get_blob_ws', data)

        tmp_dir = os.path.join(os.path.dirname(__file__)) + self.html_dir
        tmpl_lookup = TemplateLookup(directories=[tmp_dir])
        return tmpl_lookup.get_template("get.html").render(the_list=res, val=tag)

    @cherrypy.expose
    @cherrypy.tools.accept(media="application/json")
    def get_tag_ws(self, blob):
        """
        This function implements get request from '/get_tag' (Web Service)
        It returns list of hash blob corresponding to app given in parameter
        List is empty if not any blob is associated to app

        :param blob: name blob
        :type blo: string
        :return: list of hash blob
        :rtype: json format list
        """
        return json.dumps(self.data.getTagsOfBlob(blob))

    @cherrypy.expose
    @cherrypy.tools.accept(media="text/plain")
    def get_tag_of_blob(self, blob):
        """
        This functions implements get request from '/get_tag_of_blobp' (Web Page)
        Call Webservice associated

        :param blob: name blob
        :type blob: string
        :return: mako templated html page (refer to get.html)
        :rtype: mako.lookup.TemplatedLookup
        """
        data = {"blob": blob}
        res = self.useWebService('/get_tag_ws', data)

        tmp_dir = os.path.join(os.path.dirname(__file__)) + self.html_dir
        tmpl_lookup = TemplateLookup(directories=[tmp_dir])
        return tmpl_lookup.get_template("get.html").render(the_list=res, val=blob)

    def create_tmp_file(self, blob, path):
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

    def useWebService(self, req, data):
        """
        Call get function with urllib2

        :param req: name of get request
        :type req: string
        :param data: data needed for request
        :type data: dict
        :return: json decode
        :rtype: list
        """
        urls_values = urllib.urlencode(data)
        url = cherrypy.server.base() + req + '?' + urls_values
        res = urllib2.urlopen(url)
        buff = res.read()
        return yaml.safe_load(buff)

    def moveToInputDirectory(self, path, the_hash):
        """
        Create final blob directory if it doesn't exist
        Move the temporary blob in this directory
        Changing the name of the blob by the hash

        :param path: path of the temporary directory (!= /tmp/)
        :type path: string
        :param the_hash: hash content blob
        :type the_hash: string
        """
        file_directory = self.current_directory + self.final_dir
        if not os.path.exists(file_directory):
            os.makedirs(file_directory)
        file_dest = file_directory + the_hash
        shutil.move(path, file_dest)

    def dictFromList(self, list_ddb, way=0):
        """
        This function creates dict (json) from list of tuple
        It takes another parameter. If way equals zero, it means that you want create
        dictionnary: name app in function hash of blob associated (=list),
        else it's the opposite

        :param list_ddb: list of tuple [(name app, hash blob)]
        :type list_ddb: list of tuple [string, string)]
        :param way: conditional parameter
        :type way: integer
        :return: dict according way parameter
        :rtype: dict {}
        """
        d = defaultdict(list)
        for key, value in list_ddb:
            if way == 0:
                d[key].append(value)
            else:
                d[value].append(key)

        if way == 0:
            d_sort = sorted(d.iteritems(), key=lambda (k, v): k, reverse=False)
        else:
            d_sort = []
            for x in sorted(d, key=d.get):
                d[x] = sorted(d[x])
                d_sort.append([x, d[x]])
        return d_sort

    def getHashBlob(self, path):
        """
        Return hash (content of blob in the sha1 form) from path blob

        :param path: path file
        :type path: string
        :return: sha1 content blob to define a blob (if 2 blob are the same hash, so it's
        the same blob
        :rtype:
        """
        with open(path, 'rb') as the_file:
            return hashlib.sha1(the_file.read()).hexdigest()

    def fileFormat(self, the_file):
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

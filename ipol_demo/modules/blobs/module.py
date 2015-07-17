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

        self.list_of_tags = []

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

        :return: mako templated html page (refer to index.html)
        :rtype: mako.lookup.TemplatedLookup
        """
        data = instance_database()
        list_of_tags = data.get_list_tags()
        tmpl_lookup = TemplateLookup(directories=[self.html_dir])
        return tmpl_lookup.get_template("index.html").render(
            the_list=list_of_tags)

    @cherrypy.expose
    def zip(self):
        """
        Function used for upload zip file from '/zip'

        :return: mako templated html page (refer to index.html)
        :rtype: mako.lookup.TemplatedLookup
        """
        tmpl_lookup = TemplateLookup(directories=[self.html_dir])
        return tmpl_lookup.get_template("zip.html").render()

    @cherrypy.expose
    @cherrypy.tools.accept(media="application/json")
    def add_blob_ws(self, name, path, tag, ext):
        """
        This function implements get request (from '/add_blob_ws')
        It allows to check if demo given by name and blob given by hash
        is already in databse if not it add its.

        :param name: name demo
        :type name: string
        :param path: blob path
        :type path: string
        :param tag: name tag
        :type tag: string
        :param ext: extension of blob
        :type ext: string
        :return: tuple(list of name and hash, hash current blob)
        :rtype: json format tuple (list, string)
        """
        hash_blob = get_hash_blob(path)
        fileformat = file_format(path)
        demoid_tmp = -1
        hash_tmp = -1
        list_ddb = []
        list_sort = []
        data = instance_database()

        try:
            data.start_transaction()
            if not data.demo_is_in_database(name):
                demoid_tmp = data.add_demo_in_database(name)
                demoid = demoid_tmp
            else:
                demoid = data.id_demo(name)
            if not data.blob_is_in_database(hash_blob):
                if data.format_is_good(fileformat):
                    data.add_blob_in_database(demoid, hash_blob,
                                                   fileformat, ext, tag)
                    hash_tmp = hash_blob
                else:
                    if demoid_tmp != -1:
                        data.delete_demo_existed(demoid)
            else:
                blobid = data.id_blob(hash_blob)
                data.add_blob_in_database(demoid, hash_blob, fileformat,
                                               ext, tag, blobid)

            data.commit()

            list_ddb = data.return_list()
            list_sort = dict_from_list(list_ddb)

        except DatabaseError as error:
            print_exception_function(error, "Cannot add item in database")
            data.rollback()

        print list_sort
        return json.dumps((list_sort, hash_tmp))

    @cherrypy.expose
    @cherrypy.tools.accept(media="text/plain")
    def add_blob(self, **kwargs):
        """
        This function implements post request from '/add_blob'

        :param kwargs: list arguments
        :type: dict
        :return: mako templated html page refer to list.html
        :rtype: mako.lookup.TemplatedLookup
        """
        demo = kwargs.pop('demo[name]', [])
        tag = kwargs.pop('demo[tag][]', [])
        blob = kwargs.pop('demo[blob]', [])

        _, ext = os.path.splitext(blob.filename)
        assert isinstance(blob, cherrypy._cpreqbody.Part)

        tmp_directory = os.path.join(self.current_directory, self.tmp_dir)
        if not os.path.exists(tmp_directory):
            os.makedirs(tmp_directory)

        path = create_tmp_file(blob, tmp_directory)
        data = {"name": demo, "path": path, "tag": tag, "ext": ext}
        res = use_web_service('/add_blob_ws/', data)

        if res[1] != -1:
            file_dest = self.move_to_input_directory(path, res[1], ext)
            self.create_thumbnail(file_dest)
        else:
            os.remove(path)

        tmpl_lookup = TemplateLookup(directories=[self.html_dir])
        return tmpl_lookup.get_template("list.html").render(the_list=res[0])


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
        the_zip = kwargs.pop('zip', [])
        print type(the_zip)

        _, ext = os.path.splitext(the_zip.filename)
        print ext
        assert isinstance(the_zip, cherrypy._cpreqbody.Part)

        tmp_directory = os.path.join(self.current_directory, self.tmp_dir)
        if not os.path.exists(tmp_directory):
            os.makedirs(tmp_directory)

        path = create_tmp_file(the_zip, tmp_directory)
        self.parse_archive(ext, path, tmp_directory, the_zip.filename)

        tmpl_lookup = TemplateLookup(directories=[self.html_dir])
        #return tmpl_lookup.get_template("list.html").render()

    @cherrypy.expose
    @cherrypy.tools.accept(media="application/json")
    def delete_blob_ws(self, demo, hash_blob):
        """
        This functions implements web service associated to '/delete_blob'
        Delete blob from demo name and hash blob in database

        :param demo: name demo
        :type demo: string
        :param hash_blob: hash blob
        :type hash_blob: string
        return: True if blob is not associated to any demo else False
        :rtype: json format bool
        """
        list_sort = []
        value_return = None
        data = instance_database()
        try:
            value_return = data.delete_blob_from_demo(demo, hash_blob)
            data.commit()

            list_ddb = data.return_list()
            list_sort = dict_from_list(list_ddb)

        except DatabaseError as error:
            print_exception_function(error, "Cannot delete item in database")
            data.rollback()

        return json.dumps((list_sort, value_return))

    @cherrypy.expose
    @cherrypy.tools.accept(media="text/plain")
    def delete_blob(self, demo, blob):
        """
        Call WebService '/delete_blob_ws' associated
        Delete blob in final directory if it's necessary

        :param demo: name demo
        :type demo: string
        :param blob: hash blob
        :type blob: string
        :return: mako templated html page refer to list.html
        :rtype: mako.lookup.TemplatedLookup
        """
        data = {"demo": demo, "hash_blob": blob}
        res = use_web_service('/delete_blob_ws', data)

        print res[1]

        if not res[1]:
            path_file = os.path.join(self.current_directory, self.final_dir,
                                     blob)
            if os.path.isfile(path_file):
                os.remove(path_file)

        tmpl_lookup = TemplateLookup(directories=[self.html_dir])
        return tmpl_lookup.get_template("list.html").render(the_list=res[0])

    @cherrypy.expose
    @cherrypy.tools.accept(media="application/json")
    def get_demo_ws(self, hash_blob):
        """
        This function implements get request from '/get_demo_ws' (Web Service)
        It returns list of demo corresponding to hash blob given in parameter
        List is empty if not any demo is associated to blob

        :param hash_blob: hash blob
        :type hash_blob: string
        :return: list of demo
        :rtype: json format list
        """
        lis = []
        data = instance_database()
        try:
            lis = data.get_demo_of_hash(hash_blob)
        except DatabaseError as error:
            print_exception_function(error, "Cannot access to demo from hash")
            data.rollback()

        return json.dumps(lis)

    @cherrypy.expose
    @cherrypy.tools.accept(media="text/plain")
    def get_demo_of_hash(self, hash_blob):
        """
        This functions implements get request from '/get_demo_of_hash'
        Call Webservice associated

        :param hash_blob: hash blob
        :type hash_blob: string
        :return: mako templated html page (refer to get.html)
        :rtype: mako.lookup.TemplatedLookup
        """
        data = {"hash_blob": hash_blob}
        res = use_web_service('/get_demo_ws', data)

        tmpl_lookup = TemplateLookup(directories=[self.html_dir])
        return tmpl_lookup.get_template("get.html").render(the_list=res,
                                                           val=hash_blob)

    @cherrypy.expose
    @cherrypy.tools.accept(media="application/json")
    def get_hash_ws(self, demo):
        """
        This function implements get request from '/get_hash' (Web Service)
        It returns list of hash blob corresponding to demo given in parameter
        List is empty if not any blob is associated to demo

        :param demo: name demo
        :type demo: string
        :return: list of hash blob
        :rtype: json format list
        """
        lis = []
        data = instance_database()
        try:
            lis = data.get_hash_of_demo(demo)
        except DatabaseError as error:
            print_exception_function(error, "Cannot access to blob from demo")
            data.rollback()

        return json.dumps(lis)

    @cherrypy.expose
    @cherrypy.tools.accept(media="text/plain")
    def get_hash_of_demo(self, demo):
        """
        This functions implements get request from '/get_hash_of_demo'
        Call Webservice associated

        :param demo: name demo
        :type demo: string
        :return: mako templated html page (refer to get.html)
        :rtype: mako.lookup.TemplatedLookup
        """
        data = {"demo": demo}
        res = use_web_service('/get_hash_ws', data)

        tmpl_lookup = TemplateLookup(directories=[self.html_dir])
        return tmpl_lookup.get_template("get.html").render(the_list=res,
                                                           val=demo)

    @cherrypy.expose
    @cherrypy.tools.accept(media="application/json")
    def get_blob_ws(self, tag):
        """
        This function implements get request from '/get_blob' (Web Service)
        It returns list of hash blob corresponding to demo given in parameter
        List is empty if not any blob is associated to demo

        :param tag: list name tag
        :type tag: list of string
        :return: list of hash blob
        :rtype: json format list
        """
        lis = []
        data = instance_database()
        try:
            lis = data.get_blob_of_tag(tag)
        except DatabaseError as error:
            print_exception_function(error, "Cannot acces to blob from tag")
        return json.dumps(lis)

    @cherrypy.expose
    @cherrypy.tools.accept(media="text/plain")
    def get_blob_of_tag(self, tag):
        """
        This functions implements get request from '/get_blob_of_tag'
        Call Webservice associated

        :param tag: list name tag
        :type tag: list of string
        :return: mako templated html page (refer to get.html)
        :rtype: mako.lookup.TemplatedLookup
        """
        tag = list(tag.split(','))
        tag = [x.encode('UTF8') for x in tag]
        if len(tag) == 1:
            tag.append('')
        data = {"tag": tag}
        res = use_web_service('/get_blob_ws', data)

        tmpl_lookup = TemplateLookup(directories=[self.html_dir])
        return tmpl_lookup.get_template("get.html").render(the_list=res,
                                                           val=tag)

    @cherrypy.expose
    @cherrypy.tools.accept(media="application/json")
    def get_tag_ws(self, blob):
        """
        This function implements get request from '/get_tag' (Web Service)
        It returns list of hash blob corresponding to demo given in parameter
        List is empty if not any blob is associated to demo

        :param blob: name blob
        :type blo: string
        :return: list of hash blob
        :rtype: json format list
        """
        lis = []
        data = instance_database()
        try:
            lis = data.get_tag_of_blob(blob)
        except DatabaseError as error:
            print_exception_function(error, "Cannot access to tag from blob")
        return json.dumps(lis)

    @cherrypy.expose
    @cherrypy.tools.accept(media="text/plain")
    def get_tag_of_blob(self, blob):
        """
        This functions implements get request from '/get_tag_of_blobp'
        Call Webservice associated

        :param blob: name blob
        :type blob: string
        :return: mako templated html page (refer to get.html)
        :rtype: mako.lookup.TemplatedLookup
        """
        data = {"blob": blob}
        res = use_web_service('/get_tag_ws', data)
        print res

        tmpl_lookup = TemplateLookup(directories=[self.html_dir])
        return tmpl_lookup.get_template("get.html").render(the_list=res,
                                                           val=blob)

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
        try:
            image = PIL.Image.open(src)
            image.thumbnail((256, 256))
            image.save(file_dest)
        except IOError:
            print_exception_thumbnail("Cannot create thumbnail",\
                inspect.currentframe().f_code.co_name)

    def parse_archive(self, ext, path, tmp_directory, the_zip):
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
                if the_file and the_file in files:
                    title = buff.get(item, 'title')
                    credit = buff.get(item, 'credit')
                    src.extract(the_file, path=tmp_directory)
                    tmp_path = os.path.join(tmp_directory, the_file)
                    _, ext = os.path.splitext(tmp_path)

                    data = {"name": "", "path": tmp_path, "tag": "", "ext": ext}
                    res = use_web_service('/add_blob_ws/', data)

                    if res[1] != -1:
                        file_dest = self.move_to_input_directory(tmp_path,
                                                     res[1], ext)
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
    buff = res.read()
    return yaml.safe_load(buff)

def dict_from_list(list_ddb, way=0):
    """
    This function creates dict (json) from list of tuple
    It takes another parameter. If way equals zero, it means that you want
    create dictionnary: name demo in function hash of blob associated (=list),
    else it's the opposite

    :param list_ddb: list of tuple [(name demo, hash blob)]
    :type list_ddb: list of tuple [string, string)]
    :param way: conditional parameter
    :type way: integer
    :return: dict according way parameter
    :rtype: dict {}
    """
    the_dict = defaultdict(list)
    for key, value in list_ddb:
        if way == 0:
            the_dict[key].append(value)
        else:
            the_dict[value].append(key)

    if way == 0:
        d_sort = sorted(the_dict.iteritems(), key=lambda (k, v): k,
                        reverse=False)
    else:
        d_sort = []
        for item in sorted(the_dict, key=the_dict.get):
            the_dict[item] = sorted(the_dict[item])
            d_sort.append([item, the_dict[item]])
    return d_sort

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


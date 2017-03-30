#!/usr/bin/env python
# -*- coding:utf-8 -*-

"""
This file implements the system core of the server
It implements Blob object and manages web page and web service
"""

import tempfile
import shutil
import urllib
import json
import hashlib
import urllib2
import os
import os.path
import glob
import sys
import tarfile
import zipfile
import ConfigParser as configparser
import threading
import logging
import time
import base64
import sqlite3 as lite
import PIL.Image
import magic
import cherrypy
from database import Database
from error import DatabaseError
from mako.lookup import TemplateLookup
import ConfigParser
import re

#Get the server socket_host from conf file
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
CONF_FILE = os.path.join(BASE_DIR, 'blobs.conf')
cherrypy.config.update(CONF_FILE)
REALM = cherrypy.config['server.socket_host']

#Get username and password from file
auth_file = open('auth', 'r')
user_name, passwd = auth_file.read().strip().split(':')

class   DatabaseConnection(object):
    """
    Class implementing a safe abstraction for database access.

    with DatabaseConnection(...) as db:
    db.do_stuff()
    """

    def __init__(self, database_dir, database_name, logger):
        """
        Initiating the Database object to be used.
        """
        try:
            self.db = Database(database_dir, database_name, logger)
        except DatabaseError:
            logger.exception("Cannot instantiate Database Object")
            sys.exit(1)

    def __enter__(self):
        """
        Return a connection to a database into a safe context
        declared with the keyword "with"
        """
        return self.db

    def __exit__(self, _type, _value, _traceback):
        """
        Try to automatically close the connection when leaving the
        safe context, if not already done.
        """
        try:
            self.db.close()
        except Exception as _:
            pass


def validate_password(dummy, username, password):
    """
    Validates the username and the password given
    """
    credentials = {user_name: passwd}
    if username in credentials and credentials[username] == password:
        return True
    return False

def dispersed_path(main_directory, blob_hash, extension, is_thumbnail=False, depth=2):
    """
    This function complete the path with the corresponding subdir for a visual representation.
    new path --> /home/ipol/..../tmp/a/b/abvdddddd.png
    new folder --> tmp/a/b/
    subdir     --> a/b
    """
    length_of_the_new_subfolder = min(len(blob_hash), depth)
    subdirs = '/'.join(list(blob_hash[:length_of_the_new_subfolder]))
    new_folder = os.path.join(main_directory, subdirs)

    if is_thumbnail:
        blob = "thumbnail_" + blob_hash + extension
    else:
        blob = blob_hash + extension

    new_path = os.path.join(new_folder, blob)
    return new_path, new_folder, subdirs

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

    instance = None

    @staticmethod
    def get_instance():
        '''
        Singleton pattern
        '''
        if Blobs.instance is None:
            Blobs.instance = Blobs()
        return Blobs.instance


    def __init__(self):
        """
        Initialize Blob class
        """
        # control the concurrent access to the blobs instance
        self.blobs_lock = threading.Lock()

        self.tmp_dir = cherrypy.config['tmp.dir']
        self.final_dir = cherrypy.config['final.dir']
        self.thumb_dir = cherrypy.config['thumbnail.dir']
        self.vr_dir    = cherrypy.config['visual_representation']

        self.base_directory = os.getcwd()
        self.html_dir = os.path.join(self.base_directory,
                                     cherrypy.config['html.dir'])
        self.server_address = 'http://{0}:{1}'.format(
            cherrypy.config['server.socket_host'],
            cherrypy.config['server.socket_port'])
        self.server = cherrypy.config['server.socket_host']
        self.config_common_dir = cherrypy.config.get("config_common_dir")

        # Security: authorized IPs
        self.authorized_patterns = self.read_authorized_patterns()

        self.logs_dir = cherrypy.config.get("logs_dir")
        try:
            if not os.path.exists(self.logs_dir):
                os.makedirs(self.logs_dir)
        except Exception as e:
            self.logs_dir = os.path.dirname(os.path.realpath(__file__))
            self.logger = self.init_logging()
            self.logger.exception(
                "Failed to create log dir (using file dir) : %s".format(e))
        else:
            self.logger = self.init_logging()

        try:
            self.database_dir = cherrypy.config.get("database_dir")
            self.database_name = cherrypy.config.get("database_name")
            self.database_file = os.path.join(self.database_dir, self.database_name)
        except Exception as _:
            self.logger.exception("failed to get database config")

        self.status = self.init_database()
        if not self.status:
            sys.exit("Initialisation of database failed. Check the logs.")

    # ---------------------------------------------------------------------------

    def authenticate(func):
        '''
        Wrapper to authenticate before using an exposed function
        '''
        def authenticate_and_call(*args,**kwargs):
            '''
            Invokes the wrapped function if authenticated
            '''
            if not is_authorized_ip(cherrypy.request.remote.ip) or \
                    ("X-Real-IP" in cherrypy.request.headers and
                         not is_authorized_ip(cherrypy.request.headers["X-Real-IP"])):
                cherrypy.response.headers['Content-Type'] = "application/json"
                error = {"status": "KO", "error": "Authentication Failed"}
                return json.dumps(error)
            return func(*args,**kwargs)

        def is_authorized_ip(ip):
            '''
            Validates the given IP
            '''
            blobs = Blobs.get_instance()
            patterns = []
            # Creates the patterns  with regular expresions
            for authorized_pattern in blobs.authorized_patterns:
                patterns.append(re.compile(authorized_pattern.replace(".","\.").replace("*","[0-9]*")))
            # Compare the IP with the patterns
            for pattern in patterns:
                if pattern.match(ip) is not None:
                    return True
            return False


        return authenticate_and_call

    def read_authorized_patterns(self):
        '''
        Read from the IPs conf file
        '''
        # Check if the config file exists
        authorized_patterns_path = os.path.join(self.config_common_dir, "authorized_patterns.conf")
        if not os.path.isfile(authorized_patterns_path):
            self.error_log("read_authorized_patterns",
                           "Can't open {}".format(authorized_patterns_path))
            return []

        # Read config file
        try:
            cfg = ConfigParser.ConfigParser()
            cfg.read([authorized_patterns_path])
            patterns = []
            for item in cfg.items('Patterns'):
                patterns.append(item[1])
            return patterns
        except ConfigParser.Error:
            self.logger.exception("Bad format in {}".format(authorized_patterns_path))
            return []



    def init_logging(self):
        """
        Initialize the error logs of the module.
        """
        logger = logging.getLogger("blobs_log")
        # handle all messages for the moment
        logger.setLevel(logging.DEBUG)
        handler = logging.FileHandler(os.path.join(self.logs_dir, 'error.log'))
        formatter = logging.Formatter(
            '%(asctime)s; [%(filename)s:%(lineno)s - %(funcName)20s() ] %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S')
        handler.setFormatter(formatter)

        logger.addHandler(handler)
        return logger

    #---------------------------------------------------------------------------
    def init_database(self):
        """
            Initialize the database used by the module if it doesn't exist.
            If the file is empty, the system delete it and create a new one.
            :return: False if there was an error. True otherwise.
            :rtype: bool
        """

        status = True

        if os.path.isfile(self.database_file):

            file_info = os.stat(self.database_file)

            if file_info.st_size == 0:
                try:
                    os.remove(self.database_file)
                except Exception as ex:
                    self.logger.exception("init_database: " + str(ex))
                    status = False
                    return status

        if not os.path.isfile(self.database_file):
            try:
                conn = lite.connect(self.database_file)
                cursor_db = conn.cursor()

                sql_buffer = ""

                with open(self.database_dir+'/drop_create_db_schema.sql', 'r') as sql_file:
                    for line in sql_file:

                        sql_buffer += line
                        if lite.complete_statement(sql_buffer):
                            sql_buffer = sql_buffer.strip()
                            cursor_db.execute(sql_buffer)
                            sql_buffer = ""

                conn.commit()
                conn.close()

            except Exception as ex:
                self.logger.exception("init_database - " + (str(ex)))

                if os.path.isfile(self.database_file):
                    try:
                        os.remove(self.database_file)
                    except Exception as ex:
                        self.logger.exception("init_database - " + str(ex))
                        status = False

        return status

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
            self.logger.exception("Cannot instantiate Database object")
            sys.exit(1)

    @staticmethod
    @cherrypy.expose
    def default(attr):
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
    def blob(self, demo_name):
        """
        Web page used to upload one blob to one demo

        :param demo_name: id demo
        :type demo_name: integer
        :return: mako templated html page (refer to demos.html)
        :rtype: mako.lookup.TemplatedLookup
        """
        tmpl_lookup = TemplateLookup(directories=[self.html_dir])
        return tmpl_lookup.get_template("add_blob.html").render(demo_name=demo_name)

    @cherrypy.expose
    def archive(self, demo_name):
        """
        Function used for upload zip file to one demo

        :param demo_name: id demo
        :type demo_name: integer
        :return: mako templated html page (refer to index.html)
        :rtype: mako.lookup.TemplatedLookup
        """
        tmpl_lookup = TemplateLookup(directories=[self.html_dir])
        return tmpl_lookup.get_template("add_archive.html").render(demo_name=demo_name)

    @cherrypy.expose
    @cherrypy.tools.accept(media="application/json")
    def add_blob_ws(self, demo_name, path, tag, ext, blob_set, blob_pos_in_set,
                    title, credit):
        """
        This function implements get request (from '/add_blob_ws')
        It allows to check if demo given by name and blob given by hash
        is already in database if not it add its.

        :param demo_name:         demo id integer
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

        with DatabaseConnection(self.database_dir, self.database_name, self.logger) as data:

            try:
                data.start_transaction()
                blobid = -1

                if data.blob_is_in_database(blob_hash):
                    blobid = data.blob_id(blob_hash)

                data.add_blob_in_database(demo_name, blob_hash, fileformat,
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
        demo = kwargs['demo[id]']
        # demo_name = kwargs['demo[name]']
        tag = kwargs['blob[tag]']
        blob = kwargs['blob[file]']
        blob_set = kwargs['blob[set]']
        blob_pos = kwargs['blob[pos]']
        title = kwargs['blob[title]']
        credit = kwargs['blob[credit]']

        pattern = re.compile(r"^\s+|\s*,\s*|\s+$")
        list_tag = [x for x in pattern.split(tag) if x]

        if not list_tag:
            list_tag = [""]

        _, ext = os.path.splitext(blob.filename)
        assert isinstance(blob, cherrypy._cpreqbody.Part)

        tmp_directory = os.path.join(self.base_directory, self.tmp_dir)
        if not os.path.exists(tmp_directory):
            os.makedirs(tmp_directory)

        # pos in set 0 by default (if the set does not exists)
        blob_pos_in_set = 0

        # add blob to the end of the blobset
        # look for the size of the blobset
        demo_blobs = use_web_service('/get_blobs_of_demo_by_name_ws', {"demo_name": demo})
        for bs in demo_blobs["blobs"]:
            if bs[0]['set_name'] == blob_set:
                # check if blob_pos is an existing position
                # and also compute the maximal exisiting position
                blob_maxpos = 0
                for i in range(1, bs[0]['size'] + 1):
                    if str(bs[i]['pos_in_set']) == str(blob_pos):
                        blob_pos_in_set = blob_pos
                        break
                    else:
                        blob_maxpos = max(blob_maxpos, bs[i]['pos_in_set'])
                        blob_pos_in_set = blob_maxpos + 1

        try:
            path = create_tmp_file(blob, tmp_directory)
        except Exception as ex:
            error_message = "Failure adding in add_blob --> %s".format(ex)
            self.logger.exception(error_message)
            error_dic = {}
            error_dic['status']= 'KO'
            error_dic['message'] = error_message
            return json.dumps(error_dic)

        data = {"demo_name": demo, "path": path, "tag": list_tag, "ext": ext,
                "blob_set": blob_set, "blob_pos_in_set":blob_pos_in_set,
                "title": title, "credit": credit}
        res = use_web_service('/add_blob_ws/', data)

        if res["the_hash"] != -1 and res["status"] == "OK":
            file_dest = self.move_to_input_directory(path, res["the_hash"], ext)
            self.create_thumbnail(file_dest)
        else:
            os.remove(path)

        return self.get_blobs_of_demo(demo)

    @cherrypy.expose
    @cherrypy.tools.accept(media="text/plain")
    def edit_blobs_information(self, **kwargs):
        """
        Edit blob (POST Request)

        :param kwargs: list arguments
        :type kwargs: dictionnary
        :return: mako templated html page (refer to edit_blob.html)
        :rtype: mako.lookup.TemplatedLookup
        """
        data = {}
        data['demo_name'] = kwargs['demo_name']
        data['blob_id'] = kwargs['blob_id']
        data['blob_set'] = kwargs['blob_set']
        data['blob_pos_in_set'] = kwargs['blob_pos_in_set']
        data['title'] = kwargs['title']
        data['credit'] = kwargs['credit']

        res = use_web_service("/edit_blob_in_database_ws", data)

        if res['status'] == 'OK':
            return self.get_blobs_of_demo(data['demo_name'])
        else:
            error_message = "Failure in edit_blobs_information"
            self.logger.exception(error_message)
            res['message'] = error_message
            return json.dump(res)

    @cherrypy.expose
    @cherrypy.tools.accept(media="application/json")
    def edit_blob_in_database_ws(self, demo_name, blob_id,
				 blob_set, blob_pos_in_set, title, credit):
        """
        Web service used for editing a blob
        :return: OK if success or KO if not
        :rtype:  json format
        """
        dic={}
        with DatabaseConnection(self.database_dir, self.database_name, self.logger) as data:
            cherrypy.response.headers['Content-Type'] = "application/json"

            try:
                data.start_transaction()
                data.edit_blob_in_database(blob_id, blob_set, blob_pos_in_set, title, credit)
                data.commit()
                dic["status"] = "OK"
            except DatabaseError:
                self.logger.exception("Failure editing the blob in demo = '{}'".format(demo_name))
                dic["status"] = "KO"

        return json.dumps(dic)

    @cherrypy.expose
    @cherrypy.tools.accept(media="application/json")
    def upload_visual_representation(self, **kwargs):
        """
        """
        data = {}
        demo_name       = kwargs['demo_name']
        data['blob_id'] = kwargs['blob_id']
        vr_file = kwargs['visual_representation']

        res = use_web_service('/get_blob_ws', data)

        if res['status'] == "OK":

            # The creation of the main folders for blobs, thumbnail and VR 
            # should be in __init__ ???? 
            visrep_folder = os.path.join(self.base_directory, self.vr_dir)
            if not os.path.exists(visrep_folder):
                os.makedirs(visrep_folder)

            blob_hash = res['hash']

            try:

                _, extension = os.path.splitext(vr_file.filename)
                assert isinstance(vr_file, cherrypy._cpreqbody.Part)

                vr_path, vr_folder, _ = dispersed_path(visrep_folder, blob_hash, extension)
                if not os.path.isdir(vr_folder):
                    os.makedirs(vr_folder)

                #Delete the previous visual representations...
                file_without_extension = os.path.join(vr_folder, blob_hash)
                list_of_visrep = glob.glob(file_without_extension+".*")
                for vr_to_delete in list_of_visrep:
                    os.remove(vr_to_delete)


                temp_path = create_tmp_file(vr_file, vr_folder)
                os.rename(temp_path, vr_path)
                self.create_thumbnail(vr_path)

            except Exception as ex:
                error_message = "Failure in upload_visual_representation --> {}".format(ex)
                self.logger.exception(error_message)
                data['status']= 'KO'
                data['message'] = error_message
                return json.dumps(data)

        return self.get_blobs_of_demo(demo_name)

    @cherrypy.expose
    @cherrypy.tools.accept(media="application/json")
    def demos_ws(self):
        """
        Web service used to have the list of demos from database

        :return: list of demos (dictionnary)
        :rtype: json format
        """
        dic = {}
        with DatabaseConnection(self.database_dir, self.database_name, self.logger) as data:
            cherrypy.response.headers['Content-Type'] = "application/json"

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
        dic = {}
        with DatabaseConnection(self.database_dir, self.database_name, self.logger) as data:
            cherrypy.response.headers['Content-Type'] = "application/json"

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
    def set_template_ws(self, demo_name, name):
        """
        Web service used to change the current template used by a demo
        demo

        :param demo_name: id demo
        :type demo_name: integer
        :param name: name of the templated demo selected
        :type name: string
        :return: "OK" if not error else "KO"
        :rtype: json format
        """
        dic = {}

        cherrypy.response.headers['Content-Type'] = "application/json"
        with DatabaseConnection(self.database_dir, self.database_name, self.logger) as data:
            try:
                print "Name:",name
                print "demo name:",demo_name
                template_id = data.demo_id(name)
                if name == 'None':
                    template_id = 0
                data.update_template(demo_name, template_id)
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
        demo_name = kwargs["demo[id]"]
        name_tmpl = kwargs["name_template"]

        data = {"demo_name": demo_name, "name": name_tmpl}

        use_web_service('/set_template_ws', data)

        return self.get_blobs_of_demo(demo_name)

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
        dic = {}
        with DatabaseConnection(self.database_dir, self.database_name, self.logger) as data:
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
        use_web_service('/add_demo_ws', data)

        return self.index()

    @cherrypy.expose
    @cherrypy.tools.accept(media="text/plain")
    def add_from_archive(self, **kwargs):
        """
        This function implements post request for /zip
        It corresponds to upload of the zip file

        :param blob:
        :type kwargs: dictionnary
        :return: mako templated html page refer to list.html
        :rtype: mako.lookup.TemplatedLookup
        """
        demo_name = kwargs['demo[id]']
        the_archive = kwargs['archive']

        filename, extension = os.path.splitext(the_archive.filename)
        assert isinstance(the_archive, cherrypy._cpreqbody.Part)

        tmp_directory = os.path.join(self.base_directory, self.tmp_dir)
        if not os.path.exists(tmp_directory):
            os.makedirs(tmp_directory)

        path = create_tmp_file(the_archive, tmp_directory)
        self.parse_archive(extension, path, tmp_directory, the_archive.filename, demo_name)

        return self.get_blobs_of_demo(demo_name)


    def remove_files_associated_to_a_blob(self, blob):
        """
        This function removes a blob, its thumbnail and 
        the visual representation (if exists)
        
        :param blob:
        :type hash and extension of the blob
        :return: "OK" if not error else "KO"
        :rtype: dictionnary 
        """

        hash_blob, extension = os.path.splitext(blob)

        main_blobs_folder = os.path.join(self.base_directory, self.final_dir)
        path_file, _ , _  = dispersed_path(main_blobs_folder, hash_blob, extension)

        try:
            os.remove(path_file)
        except OSError as ex:
            error_message = "Failure removing the blob {}. Error: {} ".format(blob,ex)
            self.logger.error(error_message)
            print error_message

        main_thumb_folder = os.path.join(self.base_directory, self.thumb_dir)
        path_thumb, _, _  = dispersed_path(main_thumb_folder, hash_blob, ".jpg", True)

        try:
            os.remove(path_thumb)
        except OSError as ex:
            error_message = "Failure removing the thumbnail of blob {}. Error: {} ".format(blob,ex)
            self.logger.error(error_message)
            print error_message

        try:
            #Delete the visual representation (if exists)
            visrep_folder = os.path.join(self.base_directory, self.vr_dir)
            _, vr_folder,_ = dispersed_path(visrep_folder, hash_blob, "dummy")
            visrep_without_extension = os.path.join(vr_folder, hash_blob)
            list_of_visrep = glob.glob(visrep_without_extension+".*")

            for vr_to_delete in list_of_visrep:
                os.remove(vr_to_delete)

        except Exception as ex:
            error_message = "Failure removing the visrep of blob {}. Error: {} ".format(blob,ex)
            self.logger.error(error_message)
            print error_message



    @cherrypy.expose
    @cherrypy.tools.accept(media="application/json")
    @cherrypy.tools.auth_basic(realm=REALM, checkpassword=validate_password)
    def delete_blob_ws(self, demo_name, blob_set, blob_id):
        """
        This functions implements web service associated to '/delete_blob'
        Delete blob from demo name and hash blob in database

        :param demo_name: id demo
        :type demo_name: integer
        :param blob_id: id blob
        :type blob_id: integer
        return: name of the blob if it is not associated to demo and
        "OK" if not error else "KO"
        :rtype: dictionnary
        """
        dic = {}
        dic["delete"] = ""
        # return json.dump(dic)
        # wait for the lock until timeout in seconds is reach
        # if it can lock, locks and returns True
        # otherwise returns False
        # code based on http://stackoverflow.com/questions/8392640/how-to-
        # implement-a-lock-with-a-timeout-in-python-2-7
        # another option is to use Queue:
        # http://stackoverflow.com/questions/35149889/lock-with-timeout-in-
        # python2-7
        def waitLock(lock, timeout):
            """
            This function start to acquire the given lock
            during timeout amount of time.
            """
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
        if waitLock(self.blobs_lock, 3):

            with DatabaseConnection(self.database_dir, self.database_name, self.logger) as data:

                try:
                    blob_name = data.get_blob_filename(blob_id)
                    has_no_demo = data.delete_blob_from_demo(demo_name, blob_set, blob_id)
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
            self.logger.error("Failed to acquire blobs lock")
            dic["status"] = "KO"

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
        dic = {}
        with DatabaseConnection(self.database_dir, self.database_name, self.logger) as data:
            cherrypy.response.headers['Content-Type'] = "application/json"

            try:
                data.add_tag_in_database(blob_id, tag)
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
        demo_name = kwargs['demo_name']
        pattern = re.compile(r"^\s+|\s*,\s*|\s+$")
        list_tag = [x for x in pattern.split(tag) if x]

        if not list_tag:
            list_tag = [""]

        data = {"blob_id": blob_id, "tag": list_tag}
        use_web_service("/add_tag_to_blob_ws", data)

        return self.edit_blob(blob_id, demo_name)

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
        dic = {}
        with DatabaseConnection(self.database_dir, self.database_name, self.logger) as data:
            cherrypy.response.headers['Content-Type'] = "application/json"
            try:
                data.delete_tag_from_blob(tag_id, blob_id)
                data.commit()
                dic["status"] = "OK"
            except DatabaseError:
                self.logger.exception("Cannot delete item in database")
                data.rollback()
                dic["status"] = "KO"

        return json.dumps(dic)

    @cherrypy.expose
    def op_remove_tag_from_blob(self, tag_id, blob_id, demo_name):
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
        use_web_service("/remove_tag_from_blob_ws", data)
        return self.edit_blob(blob_id, demo_name)

    @cherrypy.expose
    @cherrypy.tools.auth_basic(realm=REALM, checkpassword=validate_password)
    def op_remove_blob_from_demo(self, demo_name, blob_set, blob_id):
        """
        Delete one blob from demo

        :param demo_name: id demo
        :type demo_name: integer
        :param blob_id: id blob
        :type blob_id: integer
        :return: mako templated html page (refer to edit_demo_blobs.html)
        :rtype: mako.lookup.TemplatedLookup
        """
        data = {"demo_name": demo_name, "blob_set": blob_set, "blob_id": blob_id}
        res = use_web_service('/delete_blob_ws', data, 'authenticated')

        if res["status"] == "OK" and res["delete"]:
            self.remove_files_associated_to_a_blob(res["delete"])

        return self.get_blobs_of_demo(demo_name)


    #---------------------------------------------------------------------------
    def prepare_list_of_blobs(self, dic_blobs):
        """
        This function creates a list with the info that the ws: get_blobs_of_demo_by_name_ws
        and get_blobs_from_template_ws, require for returning hash, extension, subdirs 
        and if the visrep exists, it includes the visrep extension
        """
        list_of_blobs_corrected_with_vr = []
        for elements in dic_blobs:
            blob_set = []
            for element in elements:
               if 'hash' in element:
                  hash_of_blob      = element['hash']
                  extension_of_blob = element['extension']

                  visrep_main_folder = os.path.join(self.base_directory, self.vr_dir)
                  vr_path, vr_folder, subdirs = dispersed_path(visrep_main_folder, \
                                                                                  hash_of_blob, \
                                                                                  extension_of_blob)
                  ##The subdir is the same in the VR , the thumbnail and in the blob_directory
                  element['subdirs'] = subdirs + "/"

                  vr_extension = self.check_if_visrep_exists(vr_folder, hash_of_blob)
                  if vr_extension != "":
                      element['extension_visrep'] = vr_extension

               blob_set.append(element)

            list_of_blobs_corrected_with_vr.append(blob_set)

        return list_of_blobs_corrected_with_vr

    def check_if_visrep_exists(self, vr_folder, hash_of_blob):
        """
        This function check if a blob has a visrep associated.
        If the visrep exists, the function returns its extension
        if not, returns an empty string
        """
        vr_extension = ""
        if os.path.isdir(vr_folder):

            file_without_extension = os.path.join(vr_folder, hash_of_blob)
            visrep = glob.glob(file_without_extension+".*")

            if len(visrep)>0:
                _, vr_extension = os.path.splitext(visrep[0])

        return vr_extension

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

        with DatabaseConnection(self.database_dir, self.database_name, self.logger) as data:
            try:
                # template_id = data.demo_id(template)
                dic["blobs"] = data.get_blobs_of_demo(template)
                dic["blobs"] = self.prepare_list_of_blobs(dic['blobs'])
                dic["status"] = "OK"
            except DatabaseError:
                self.logger.exception("Cannot access to blob from template demo")
                dic["status"] = "KO"

        return json.dumps(dic)

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
        dic = {}
        cherrypy.response.headers['Content-Type'] = "application/json"
        dic["status"] = "KO"

        with DatabaseConnection(self.database_dir, self.database_name, self.logger) as data:
            try:
                dic = data.get_demo_info_from_name(demo_name)
                dic["use_template"] = data.demo_use_template(demo_name)
                dic_temp = data.get_blobs_of_demo(demo_name)

                dic["blobs"] = self.prepare_list_of_blobs(dic_temp)

                dic["url"] = '/api/blobs' + "/" + self.final_dir + "/"
                dic["url_thumb"] = '/api/blobs' + "/" + self.thumb_dir + "/"
                dic["url_visrep"] = '/api/blobs' + "/" + self.vr_dir + "/"

                dic["physical_location"] = self.final_dir
                dic["vr_location"] = self.vr_dir
                dic["status"] = "OK"

            except DatabaseError:
                self.logger.exception("Cannot access to blob from demo")

        return json.dumps(dic)


    #---------------------------------------------------------------------------
    def process_paths(self, blob_hash, extension):
        """
        """
        main_blobs_folder = os.path.join(self.base_directory, self.vr_dir)
        physical_location, _, _ = dispersed_path(main_blobs_folder, \
                                                                  blob_hash, \
                                                                  extension)

        url_blobs = os.path.join(self.server_address, self.final_dir)
        url_blobs, _, _ = dispersed_path(url_blobs, blob_hash, extension)

        url_thumb = os.path.join(self.server_address, self.thumb_dir)
        url_thumb, _, _ = dispersed_path(url_thumb, blob_hash, ".jpg", True)

        return physical_location, url_blobs, url_thumb



    @cherrypy.expose
    def get_blobs_of_demo(self, demo_name, blob_deleted_message=None):
        """
        Web page to show the blobs of the demo from id demo

        :param demo_name: demo_name
        :return: mako templated html page (refer to edit_demo_blobs.html)
        :rtype: mako.lookup.TemplatedLookup
        """
        demo_blobs = use_web_service('/get_blobs_of_demo_by_name_ws', {"demo_name": demo_name})
        template_list_res = use_web_service('/get_template_demo_ws', {})
        template_blobs = {}

        #--- if the demo uses a template, process its blobs
        if demo_blobs["use_template"]:
            template_blobs_res = use_web_service('/get_blobs_from_template_ws',
                                                 {"template": demo_blobs["use_template"]["name"]})

            template_blobs = template_blobs_res['blobs']
            for blob_set in template_blobs:
                blob_size = blob_set[0]['size']
                for idx in range(1, blob_size + 1):
                    b = blob_set[idx]
                    b["physical_location"], b['url'], b["url_thumb"] = self.process_paths(b["hash"],\
		                                                                  b['extension'])


        for blob_set in demo_blobs["blobs"]:
            blob_size = blob_set[0]['size']
            for idx in range(1, blob_size + 1):
                b = blob_set[idx]
                b["physical_location"], b['url'], b["url_thumb"] = self.process_paths(b["hash"],\
		                                                                  b['extension'])


        tmpl_lookup = TemplateLookup(directories=[self.html_dir])
        return tmpl_lookup.get_template("edit_demo_blobs.html").render(
            blobs_list=demo_blobs["blobs"],
            demo_name=demo_name,
            demo=demo_blobs,
            tmpl_list=template_list_res["template_list"],
            tmpl_blobs=template_blobs,
            blob_deleted_message=blob_deleted_message)

    @cherrypy.expose
    @cherrypy.tools.accept(media="application/json")
    def get_blobs_by_id(self, blob_ids):
        """
        Obtain blobs metadata from their IDs
        """

        blobs_ids_tuple = blob_ids if isinstance(blob_ids, list) else [int(blob_ids)]

        dic={}
        with DatabaseConnection(self.database_dir, self.database_name, self.logger) as data:
            try:
                list_with_blob_information = []
                dic_with_blob = {}
                for blob_id in blobs_ids_tuple:
                    dic_with_blob = data.get_blob(blob_id)

                    _, _, subdirs = dispersed_path(os.path.join(self.base_directory, self.final_dir), \
                                                                 dic_with_blob['hash'], \
                                                                 dic_with_blob['extension'])

                    dic_with_blob['subdirs'] = subdirs + "/"

                    list_with_blob_information.append(dic_with_blob)

                dic['list_of_blobs'] = list_with_blob_information
                dic["physical_location"] = self.final_dir
                dic["vr_location"] = self.vr_dir
                dic["status"] = "OK"
            except Exception:
                self.logger.exception("Cannot access to blob from its ID")
                dic["status"] = "KO"

        return json.dumps(dic)


    #---------------------------------------------------------------------------
    @cherrypy.expose
    def edit_blob(self, blob_id, demo_name):
        """
        HTML Page : show thumbnail of one blob, add tag or remove tag

        :param blob_id: id blob
        :type blob_id: integer
        :return: mako templated html page (refer to edit_blob.html)
        :rtype: mako.lookup.TemplatedLookup
        """
        data = {"blob_id": blob_id}
        res = use_web_service('/get_info_for_editing_a_blob_ws', data)

        if res["status"] == "OK":

            res["tags"] = use_web_service('/get_tags_ws', data)

            # process paths
            main_blobs_folder = os.path.join(self.base_directory, self.final_dir)
            res["physical_location"], _, _ = dispersed_path(main_blobs_folder, \
                                             res["hash"], \
                                             res["extension"])

            url_blobs = os.path.join(self.server_address, self.final_dir)
            res['url'], _, _ = dispersed_path(url_blobs, \
                                            res["hash"], \
                                            res["extension"])
            url_thumb = os.path.join(self.server_address, self.thumb_dir)

            res["url_thumb"], _, _ = dispersed_path(url_thumb, \
                                                    res["hash"], \
                                                    ".jpg", \
                                                    True)

        tmpl_lookup = TemplateLookup(directories=[self.html_dir])
        return tmpl_lookup.get_template("edit_blob.html").render(\
          blob_id=blob_id, blob_info=res, demo_id=demo_name)

    @cherrypy.expose
    @cherrypy.tools.accept(media="application/json")
    def get_info_for_editing_a_blob_ws(self, blob_id):
        """
        Web service used to get the set associated with a blob

        :param blob_id: id blob
        :type blob_id: integer
        :return: list of hash blob
        :rtype: json format list
        """
        dic = []
        cherrypy.response.headers['Content-Type'] = "application/json"

        with DatabaseConnection(self.database_dir, self.database_name, self.logger) as data:
            try:
	        dic = data.get_info_for_editing_a_blob(blob_id)
                dic["status"] = "OK"
            except DatabaseError:
                self.logger.exception("Cannot access to blob from its ID")
                dic["status"] = "KO"

        return json.dumps(dic)

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
        dic = {}
        with DatabaseConnection(self.database_dir, self.database_name, self.logger) as data:
            cherrypy.response.headers['Content-Type'] = "application/json"

            try:
                dic = data.get_blob(blob_id)
                dic["status"] = "OK"
            except DatabaseError:
                self.logger.exception("Cannot access to blob from its ID")
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

        with DatabaseConnection(self.database_dir, self.database_name, self.logger) as data:
            try:
                lis = data.get_tags_of_blob(blob_id)
            except DatabaseError:
                self.logger.exception("Cannot access tag from blob")
        return json.dumps(lis)

    #---------------------------------------------------------------------------
    @cherrypy.expose
    @cherrypy.tools.accept(media="application/json")
    @cherrypy.tools.auth_basic(realm=REALM, checkpassword=validate_password)
    def op_remove_demo_ws(self, demo_name):
        """
        Web service used to remove demo from id demo

        :param demo_name: demo name
        :return: "OK" if not error else "KO"
        :rtype: json format
        """
        cherrypy.response.headers['Content-Type'] = "application/json"

        dic = {}
        dic["status"] = "KO"
        with DatabaseConnection(self.database_dir, self.database_name, self.logger) as data:
            try:
                blobfilenames_to_delete = data.remove_demo(demo_name)
                data.commit()

                # remove from disk unused blobs
                for blob in blobfilenames_to_delete:
                    self.remove_files_associated_to_a_blob(blob)

                dic["status"] = "OK"

            except DatabaseError:
                self.logger.exception("Cannot delete demo")
                data.rollback()

        return json.dumps(dic)

    #---------------------------------------------------------------------------
    @cherrypy.expose
    @cherrypy.tools.auth_basic(realm=REALM, checkpassword=validate_password)
    def op_remove_demo(self, demo_name):
        """
        Web page used to remove a demo from id

        :param demo_name: id demo
        :type demo_name: integer
        :return: mako templated html page refer to list.html
        :rtype: mako.lookup.TemplatedLookup
        """
        data = {"demo_name": demo_name}
        use_web_service('/op_remove_demo_ws', data, 'authenticated')
        data = {}
        res = use_web_service('/demos_ws', data)

        tmpl_lookup = TemplateLookup(directories=[self.html_dir])
        return tmpl_lookup.get_template("demos.html").render(list_demos=res["list_demos"])

    #---------------------------------------------------------------------------
    def move_to_input_directory(self, path, blob_hash, extension):
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
        main_blobs_folder = os.path.join(self.base_directory, self.final_dir)

        file_dest, new_folder, _  = dispersed_path(main_blobs_folder, \
                                          blob_hash, \
                                          extension)

        if not os.path.exists(new_folder):
            os.makedirs(new_folder)

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
        main_thumb_folder = os.path.join(self.base_directory, self.thumb_dir)
        name = os.path.basename(src)
        blob_hash = os.path.splitext(name)[0]
        # force thumbnail extension to be .jpg
        file_dest, new_folder, _ = dispersed_path(main_thumb_folder, \
                                          blob_hash, \
                                          ".jpg", \
                                          True)
        
        if not os.path.exists(new_folder):
            os.makedirs(new_folder)
        
        fil_format = file_format(src)
        try:
            if fil_format == 'image':
                try:
                    image = PIL.Image.open(src)
                except Exception as _:
                    self.logger.exception("failed to open image file")
                    return
                image.thumbnail((256, 256))
                image.save(file_dest)
        except IOError:
            self.logger.exception("Cannot create thumbnail")

    #---------------------------------------------------------------------------
    def parse_archive(self, ext, path, tmp_directory, the_archive, demo_name):
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

                    file_id = list_file.index(_file)
                    if _file and _file in files:
                        title = buff.get(section, 'title')
                        try:
                            credit = buff.get(section, 'credit')
                        except Exception as dummy:
                            credit = ""
                        try:
                            tags = buff.get(section, 'tag')
                        except Exception as dummy:
                            tags = ""
                        src.extract(_file, path=tmp_directory)
                        tmp_path = os.path.join(tmp_directory, _file)
                        _, ext = os.path.splitext(tmp_path)


                        data = {"demo_name": demo_name, "path": tmp_path,
                                "tag":tags,
                                "ext": ext, "blob_set": section,
                                "blob_pos_in_set": file_id, "title": title,
                                "credit": credit}
                        res = use_web_service('/add_blob_ws/', data)

                        # add the tags

                        #res = use_web_service('/add_tag_to_blob_ws/', data)
                        the_hash = res["the_hash"]
                        if the_hash != -1 and res["status"] == "OK":
                            file_dest = self.move_to_input_directory(tmp_path,
                                                                     the_hash,
                                                                     ext)
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
    @cherrypy.tools.accept(media="application/json")
    @authenticate
    def update_demo_id(self, old_demo_id, new_demo_id):
        """
        Update the given old demo id by the given new demo id.
        """
        dic = {}
        with DatabaseConnection(self.database_dir, self.database_name, self.logger) as data:
            cherrypy.response.headers['Content-Type'] = "application/json"
            try:
                data.update_demo_id(old_demo_id, new_demo_id)
                data.commit()

                dic["status"] = "OK"

            except DatabaseError as ex:
                self.logger.exception("Cannot update demo id in database")
                data.rollback()
                dic["status"] = "KO"
                dic["error"] = "blobs update_demo_id error: {}".format(ex)

        return json.dumps(dic)

    #---------------------------------------------------------------------------

    @staticmethod
    @cherrypy.expose
    def ping():
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
    @authenticate
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
            self.logger.error("Failed to shutdown : " + ex)
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

def use_web_service(req, data, auth=None):
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
    request = urllib2.Request(url)
    if auth == 'authenticated':
        base64string = base64.encodestring('%s:%s' % (user_name, passwd)).replace('\n', '')
        request.add_header("Authorization", "Basic %s" % base64string)
    res = urllib2.urlopen(request)
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

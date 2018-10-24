#!/usr/bin/env python3
# -*- coding:utf-8 -*-

"""
DemoInfo: an information container module

All exposed WS return JSON with a status OK/KO, along with an error
description if that's the case.

To test the POST WS use the following:
        curl -d demo_id=1  -X POST 'http://127.0.0.1:9002/demo_get_authors_list'
        curl -d editorsdemoid=777 -d title='demo1' -d
            state=published -X POST 'http://127.0.0.1:9002/add_demo'
        or use Ffox plugin: Poster

"""

import configparser
import errno
import glob
import json
import logging
import os
import re
import shutil
import sqlite3 as lite
import sys
from collections import OrderedDict
from math import ceil
from sqlite3 import IntegrityError

import cherrypy
import magic

from model import (Author, AuthorDAO, Demo, DemoAuthorDAO, DemoDAO,
                   DemoDemoDescriptionDAO, DemoDescriptionDAO, DemoEditorDAO,
                   Editor, EditorDAO, initDb)
from tools import is_json

# GLOBAL VARS
LOGNAME = "demoinfo_log"


def authenticate(func):
    """
    Wrapper to authenticate before using an exposed function
    """

    def authenticate_and_call(*args, **kwargs):
        """
        Invokes the wrapped function if authenticated
        """
        if not is_authorized_ip(cherrypy.request.remote.ip) \
                and not ("X-Real-IP" in cherrypy.request.headers
                         and is_authorized_ip(cherrypy.request.headers["X-Real-IP"])):
            error = {"status": "KO", "error": "Authentication Failed"}
            return json.dumps(error).encode()
        return func(*args, **kwargs)

    def is_authorized_ip(ip):
        """
        Validates the given IP
        """
        demo_info = DemoInfo.get_instance()
        patterns = []
        # Creates the patterns  with regular expresions
        for authorized_pattern in demo_info.authorized_patterns:
            patterns.append(re.compile(authorized_pattern.replace(".", "\\.").replace("*", "[0-9]*")))

        # Compare the IP with the patterns
        for pattern in patterns:
            if pattern.match(ip) is not None:
                return True
        return False

    return authenticate_and_call


class DemoInfo():
    """
    Implement the demoinfo webservices.
    """

    instance = None

    @staticmethod
    def get_instance():
        """
        Singleton pattern
        """
        if DemoInfo.instance is None:
            DemoInfo.instance = DemoInfo()
        return DemoInfo.instance

    def __init__(self):
        """
        Constructor.
        """
        status = self.check_config()
        if not status:
            sys.exit(1)

        self.logs_dir = cherrypy.config.get("logs_dir")
        self.mkdir_p(self.logs_dir)
        self.logger = self.init_logging()

        self.dl_extras_dir = cherrypy.config.get("dl_extras_dir")
        self.mkdir_p(self.dl_extras_dir)
        self.config_common_dir = cherrypy.config.get("config_common_dir")

        

        # Security: authorized IPs
        self.authorized_patterns = self.read_authorized_patterns()

        # Database
        self.database_dir = cherrypy.config.get("database_dir")
        self.database_name = cherrypy.config.get("database_name")
        self.database_file = os.path.join(self.database_dir, self.database_name)
        if not self.create_database():
            sys.exit("Initialization of database failed. Check the logs.")

    def create_database(self):
        """
        Creates the database used by the module if it doesn't exist.
        If the file is empty, the system delete it and create a new one.
        """
        if os.path.isfile(self.database_file):

            file_info = os.stat(self.database_file)

            if file_info.st_size == 0:
                try:
                    os.remove(self.database_file)
                except Exception as ex:
                    self.logger.exception("init_database: {}".format(str(ex)))
                    return False

        if not os.path.isfile(self.database_file):
            try:
                conn = lite.connect(self.database_file)
                cursor_db = conn.cursor()

                sql_buffer = ""

                with open(self.database_dir + '/drop_create_db_schema.sql', 'r') as sql_file:
                    for line in sql_file:

                        sql_buffer += line
                        if lite.complete_statement(sql_buffer):
                            sql_buffer = sql_buffer.strip()
                            cursor_db.execute(sql_buffer)
                            sql_buffer = ""

                conn.commit()
                conn.close()
                # Initializes the DB
                initDb(self.database_file)
            except Exception as ex:
                self.logger.exception("init_database - {}".format(str(ex)))

                if os.path.isfile(self.database_file):
                    try:
                        os.remove(self.database_file)
                    except Exception as ex:
                        self.logger.exception("init_database - {}".format(str(ex)))
                        return False

        return True

    @staticmethod
    def mkdir_p(path):
        """
        Implement the UNIX shell command "mkdir -p"
        with given path as parameter.
        """
        try:
            os.makedirs(path)
        except OSError as exc:
            if exc.errno == errno.EEXIST and os.path.isdir(path):
                pass
            else:
                raise

    @staticmethod
    def check_config():
        """
        Check if needed datas exist correctly in the config of cherrypy.
        """
        if not ("database_dir" in cherrypy.config and "database_name" in cherrypy.config and "logs_dir" in cherrypy.config):
            print("Missing elements in configuration file.")
            return False
        return True

    def read_authorized_patterns(self):
        """
        Read from the IPs conf file
        """
        # Check if the config file exists
        authorized_patterns_path = os.path.join(self.config_common_dir, "authorized_patterns.conf")
        if not os.path.isfile(authorized_patterns_path):
            self.error_log("read_authorized_patterns",
                           "Can't open {}".format(authorized_patterns_path))
            return []

        # Read config file
        try:
            cfg = configparser.ConfigParser()
            cfg.read([authorized_patterns_path])
            patterns = []
            for item in cfg.items('Patterns'):
                patterns.append(item[1])
            return patterns
        except configparser.Error:
            self.logger.exception("Bad format in {}".format(authorized_patterns_path))
            return []

    def init_logging(self):
        """
        Initialize the error logs of the module.
        """
        logger = logging.getLogger(LOGNAME)
        logger.setLevel(logging.ERROR)
        handler = logging.FileHandler(os.path.join(self.logs_dir, 'error.log'))
        formatter = logging.Formatter('%(asctime)s ERROR in %(message)s',
                                      datefmt='%Y-%m-%d %H:%M:%S')
        handler.setFormatter(formatter)
        logger.addHandler(handler)
        return logger

    def error_log(self, function_name, error):
        """
        Write a message in the error log.
        """
        error_string = function_name + ": " + error
        self.logger.error(error_string)

    # DEMO
    @staticmethod
    @cherrypy.expose
    def default(attr):
        """
        Default method invoked when asked for a non-existing service.
        """
        data = {}
        data["status"] = "KO"
        data["message"] = "Unknown service '{}'".format(attr)
        return json.dumps(data).encode()

    def get_compressed_file_url(self, demo_id):
        """
        Get the URL of the demo's demoExtras
        """
        demoextras_folder = os.path.join(self.dl_extras_dir, demo_id)
        demoextras_file = glob.glob(demoextras_folder+"/*")
        
        if not demoextras_file:
            return None

        demoextras_name = os.path.basename(demoextras_file[0])
        return "http://{0}/api/demoinfo/{}/{}/{}".format(
          socket.getfqdn(),
          self.dl_extras_dir,
          demo_id,
          demoextras_name)


    @cherrypy.expose
    @authenticate
    def delete_demoextras(self, demo_id):
        """
        Delete the demoextras from the demo
        """
        data = {}
        data['status'] = "OK"

        try:
            demoextras_folder = os.path.join(self.dl_extras_dir, demo_id)
            shutil.rmtree(demoextras_folder)
        except Exception as ex:
            data['status'] = "KO"
            self.logger.exception(str(ex))
        return json.dumps(data).encode()

    @cherrypy.expose
    @authenticate
    def add_demoextras(self, demo_id, demoextras, demoextras_name):
        """
        Add a new demoextras file to a demo
        """
        data = {'status': 'KO'}
        try:
            conn = lite.connect(self.database_file)
            demo_dao = DemoDAO(conn)

            if not demo_dao.exist(demo_id):
                return json.dumps(data).encode()

            if demoextras is None:
                data['error_message'] = "File not found"
                return json.dumps(data).encode()

            mime_type = magic.from_buffer(demoextras.file.read(1024), mime=True)
            _, type_of_file = mime_type.split("/")
            type_of_file = type_of_file.lower()

            accepted_types = (
                "zip",
                "tar",
                "gzip",
                "x-tar",
                "x-bzip2"
            )

            if type_of_file not in accepted_types:
                data['error_message'] = "Unexpected type: {}.".format(mime_type)
                return json.dumps(data).encode()

            demoextras_folder = os.path.join(self.dl_extras_dir, demo_id)
            if os.path.exists(demoextras_folder):
                shutil.rmtree(demoextras_folder)

            os.makedirs(demoextras_folder)
            destination = os.path.join(demoextras_folder, demoextras_name)

            demoextras.file.seek(0)
            with open(destination, 'wb') as f:
                shutil.copyfileobj(demoextras.file, f)

            data['status'] = "OK"
            return json.dumps(data).encode()

        except Exception as ex:
            error_message = "Failure in 'add_demoextras' for demo '{}'. Error {}".format(demo_id, ex)
            self.logger.exception(error_message)
            data['error_message'] = error_message
            return json.dumps(data).encode()

    @cherrypy.expose
    def get_demo_extras_info(self, demo_id):
        """
        Return the date of creation, the size of the file and the demoExtras file if exists
        """
        data = {'status': 'KO'}
        try:
            demoExtras_url = self.get_compressed_file_url(demo_id)

            if demoExtras_url is None:
                # DemoInfo does not have any demoExtras
                return json.dumps({'status': 'OK'}).encode()

            demoextras_folder = os.path.join(self.dl_extras_dir, demo_id)
            demoExtras_path = glob.glob(demoextras_folder+"/*")[0]

            file_stats = os.stat(demoExtras_path)
            data['date'] = file_stats.st_mtime
            data['size'] = file_stats.st_size
            data['url'] = demoExtras_url
            data['status'] = 'OK'
            return json.dumps(data).encode()

        except Exception as ex:
            self.logger.exception("Failure in get_demo_extras_info")
            print("get_demo_extras_info. Error: {}".format(ex))
            return json.dumps(data).encode()

    # todo check its not usefull any more and delete...remeber deleting from test/demoinfotest.py
    @cherrypy.expose
    def demo_list(self):
        """
        Return the list of the demos of the module.
        """
        data = {}
        data["status"] = "KO"
        demo_list = list()
        try:
            conn = lite.connect(self.database_file)
            demo_dao = DemoDAO(conn)
            for d in demo_dao.list():
                # convert to Demo class to json
                demo_list.append(d.__dict__)
            data["demo_list"] = demo_list
            data["status"] = "OK"
            conn.close()
        except Exception as ex:
            error_string = "demoinfo demo_list error %s" % str(ex)
            print(error_string)
            self.logger.exception(error_string)
            try:
                conn.close()
            except Exception as ex:
                pass
            # raise Exception
            data["error"] = error_string

        return json.dumps(data).encode()

    @cherrypy.expose
    def demo_list_by_demoeditorid(self, demoeditorid_list):
        """
        return demo metainformation from list of demo editor id.
        """

        data = {}
        data["status"] = "KO"
        demo_list = list()

        # get json list into python object
        if is_json(demoeditorid_list):
            demoeditorid_list = json.loads(demoeditorid_list)
        else:
            print("demoeditorid_list is not a valid JSON")
            data["error"] = "demoeditorid_list is not a valid JSON"
            return json.dumps(data).encode()

        try:
            conn = lite.connect(self.database_file)
            demo_dao = DemoDAO(conn)
            for d in demo_dao.list():
                # convert to Demo class to json
                if d.editorsdemoid in demoeditorid_list:
                    demo_list.append(d.__dict__)

            data["demo_list"] = demo_list
            data["status"] = "OK"
            conn.close()
        except Exception as ex:
            error_string = "demoinfo demo_list_by_demoeditorid error %s" % str(ex)
            print(error_string)
            self.logger.exception(error_string)
            try:
                conn.close()
            except Exception as ex:
                pass
            # raise Exception
            data["error"] = error_string

        return json.dumps(data).encode()

    @cherrypy.expose
    def demo_list_pagination_and_filter(self, num_elements_page, page, qfilter=None):
        """
        return a paginated and filtered list of demos
        """
        data = {}
        data["status"] = "KO"
        demo_list = list()
        next_page_number = None
        previous_page_number = None

        try:
            # validate params
            num_elements_page = int(num_elements_page)
            page = int(page)

            conn = lite.connect(self.database_file)
            demo_dao = DemoDAO(conn)

            complete_demo_list = demo_dao.list()

            # filter or return all
            if qfilter:
                for demo in complete_demo_list:
                    if qfilter.lower() in demo.title.lower() or qfilter == str(demo.editorsdemoid):
                        demo_list.append(demo.__dict__)
            else:
                # convert to Demo class to json
                for demo in complete_demo_list:
                    demo_list.append(demo.__dict__)

            # if demos found, return pagination
            if demo_list:
                # [ToDo] Check if the first float cast r=float(.) is
                # really needed. It seems not, because the divisor is
                # already a float and thus the result must be a float.
                r = float(len(demo_list)) / float(num_elements_page)

                totalpages = int(ceil(r))

                if page is None:
                    page = 1
                else:
                    if page < 1:
                        page = 1
                    elif page > totalpages:
                        page = totalpages

                next_page_number = page + 1
                if next_page_number > totalpages:
                    next_page_number = None

                previous_page_number = page - 1
                if previous_page_number <= 0:
                    previous_page_number = None

                start_element = (page - 1) * num_elements_page

                demo_list = demo_list[start_element: start_element + num_elements_page]

            else:
                totalpages = None

            data["demo_list"] = demo_list
            data["next_page_number"] = next_page_number
            data["number"] = totalpages
            data["previous_page_number"] = previous_page_number
            data["status"] = "OK"
            conn.close()
        except Exception as ex:
            error_string = "demoinfo demo_list_pagination_and_filter error %s" % str(ex)
            print(error_string)
            self.logger.exception(error_string)
            try:
                conn.close()  # [ToDo] It seems that this should do in a
                # finally clause, not in a nested try. Check all similar
                # cases in this file.
            except Exception as ex:
                pass
            # raise Exception
            data["error"] = error_string
        return json.dumps(data).encode()

    @cherrypy.expose
    @authenticate
    def demo_get_authors_list(self, demo_id):
        """
        return the list of authors of a given demo.
        """
        data = {}
        data["status"] = "KO"
        author_list = list()
        try:
            conn = lite.connect(self.database_file)
            demo_dao = DemoDAO(conn)
            if not demo_dao.exist(demo_id):
                return json.dumps(data).encode()

            da_dao = DemoAuthorDAO(conn)

            for a in da_dao.read_demo_authors(int(demo_id)):
                # convert to Demo class to json
                author_list.append(a.__dict__)

            data["author_list"] = author_list
            data["status"] = "OK"
            conn.close()
        except Exception as ex:
            error_string = "demoinfo demo_get_authors_list error %s" % str(ex)
            print(error_string)
            self.logger.exception(error_string)
            try:
                conn.close()
            except Exception as ex:
                pass
            # raise Exception
            data["error"] = error_string
        return json.dumps(data).encode()

    @cherrypy.expose
    @authenticate
    def demo_get_available_authors_list(self, demo_id):
        """
        return the list of all authors that are not currently assigned to a given demo.
        """
        data = {}
        data["status"] = "KO"
        available_author_list = list()

        try:
            conn = lite.connect(self.database_file)

            # get all available authors
            a_dao = AuthorDAO(conn)
            list_of_all_authors = a_dao.list()

            # get the authors of this demo
            da_dao = DemoAuthorDAO(conn)
            list_of_authors_assigned_to_this_demo = da_dao.read_demo_authors(int(demo_id))

            for a in list_of_all_authors:
                if a not in list_of_authors_assigned_to_this_demo:
                    # convert to Demo class to json
                    available_author_list.append(a.__dict__)

            data["author_list"] = available_author_list
            data["status"] = "OK"
            conn.close()
        except Exception as ex:
            error_string = "demoinfo demo_get_available_authors_list error %s" % str(ex)
            print(error_string)
            self.logger.exception(error_string)
            try:
                conn.close()
            except Exception as ex:
                pass
            # raise Exception
            data["error"] = error_string
        return json.dumps(data).encode()

    @cherrypy.expose
    @authenticate
    def demo_get_editors_list(self, demo_id):
        """
        return the editors of a given demo.
        """
        data = {}
        data["status"] = "KO"
        editor_list = list()
        try:
            conn = lite.connect(self.database_file)
            demo_dao = DemoDAO(conn)

            if not demo_dao.exist(demo_id):
                return json.dumps(data).encode()

            de_dao = DemoEditorDAO(conn)

            for e in de_dao.read_demo_editors(int(demo_id)):
                # convert to Demo class to json
                editor_list.append(e.__dict__)

            data["editor_list"] = editor_list
            conn.close()
            data["status"] = "OK"
        except Exception as ex:
            error_string = "demoinfo demo_get_editors_list error %s" % str(ex)
            print(error_string)
            self.logger.exception(error_string)
            try:
                conn.close()
            except Exception as ex:
                pass
            # raise Exception
            data["error"] = error_string
        return json.dumps(data).encode()

    @cherrypy.expose
    @authenticate
    def demo_get_available_editors_list(self, demo_id):
        """
        return all editors that are not currently assigned to a given demo
        """
        data = {}
        data["status"] = "KO"
        available_editor_list = list()

        try:
            conn = lite.connect(self.database_file)

            # get all available editors
            a_dao = EditorDAO(conn)
            list_of_all_editors = a_dao.list()

            # get the editors of this demo
            da_dao = DemoEditorDAO(conn)
            list_of_editors_assigned_to_this_demo = da_dao.read_demo_editors(int(demo_id))

            for a in list_of_all_editors:
                if a not in list_of_editors_assigned_to_this_demo:
                    # convert to Demo class to json
                    available_editor_list.append(a.__dict__)

            data["editor_list"] = available_editor_list
            data["status"] = "OK"
            conn.close()
        except Exception as ex:
            error_string = "demoinfo demo_get_available_editors_list error %s" % str(ex)
            print(error_string)
            self.logger.exception(error_string)
            try:
                conn.close()
            except Exception as ex:
                pass
            # raise Exception
            data["error"] = error_string
        return json.dumps(data).encode()

    def read_demo(self, demoid):
        """
        Return DAO for given demo.
        """
        demo = None
        try:
            the_id = int(demoid)
            conn = lite.connect(self.database_file)
            dao = DemoDAO(conn)
            demo = dao.read(the_id)
            conn.close()

        except Exception as ex:
            error_string = ("read_demo  e:%s" % (str(ex)))
            print(error_string)
            conn.close()

        return demo

    def read_demo_by_editordemoid(self, editor_demo_id):
        """
        return the demo DAO from a given association between editor and demo.
        """
        demo = None
        try:
            editordemoid = int(editor_demo_id)
            conn = lite.connect(self.database_file)
            dao = DemoDAO(conn)
            demo = dao.read(editordemoid)
            conn.close()

        except Exception as ex:
            error_string = ("read_demo_by_editordemoid  e:%s" % (str(ex)))
            print(error_string)
            conn.close()

        return demo

    @cherrypy.expose
    def read_demo_metainfo(self, demoid):
        """
        return metainfo of given demo.
        """
        data = dict()
        data["status"] = "KO"
        try:

            demo = self.read_demo(demoid)
            if demo is None:
                data['error'] = "No demo retrieved for this id"
                print("No demo retrieved for this id")
                return json.dumps(data).encode()
            data["editorsdemoid"] = demo.editorsdemoid
            data["title"] = demo.title
            data["state"] = demo.state
            data["creation"] = demo.creation
            data["modification"] = demo.modification
            data["status"] = "OK"

        except Exception as ex:
            error_string = "demoinfo read_demo_metainfo error %s" % str(ex)
            print(error_string)
            self.logger.exception(error_string)
            # raise Exception
            data["error"] = error_string

        return json.dumps(data).encode()

    @cherrypy.expose
    @cherrypy.tools.allow(methods=['POST'])  # allow only post
    @authenticate
    def add_demo(self, editorsdemoid, title, state, ddl_id=None, ddl=None):
        """
        Create a demo
        """
        data = {"status": "KO"}
        conn = None
        try:
            conn = lite.connect(self.database_file)
            dao = DemoDAO(conn)

            editorsdemoid = int(editorsdemoid)

            # Check if the demo already exists
            # In that case, get out with an error
            if dao.exist(int(editorsdemoid)):
                return json.dumps({"status": "KO", "error": "Demo ID={} already exists".format(editorsdemoid)}).encode()

            if ddl:
                # creates a demodescription and asigns it to demo
                ddao = DemoDescriptionDAO(conn)
                ddl_id = ddao.add(ddl)
                d = Demo(int(editorsdemoid), title, state)
                editorsdemoid = dao.add(d)
                dddao = DemoDemoDescriptionDAO(conn)
                dddao.add(int(editorsdemoid), int(ddl_id))

            elif ddl_id:
                # asigns to demo an existing demodescription
                d = Demo(int(editorsdemoid), title, state)
                editorsdemoid = dao.add(d)
                ddddao = DemoDemoDescriptionDAO(conn)
                ddddao.add(int(editorsdemoid), int(ddl_id))

            else:
                # demo created without demodescription
                # careful with Demo init method's validation!
                d = Demo(editorsdemoid=int(editorsdemoid), title=title, state=str(state))

                demoid = dao.add(d)
                data["demoid"] = demoid

            conn.close()

            data["status"] = "OK"

        except IntegrityError as ex:
            if conn is not None:
                conn.close()
            data['error'] = str(ex)

        except Exception as ex:
            error_string = " demoinfo add_demo error %s" % str(ex)
            print(error_string)
            self.logger.exception(error_string)
            try:
                conn.close()
            except Exception as ex:
                pass
            data["error"] = error_string

        return json.dumps(data).encode()

    @cherrypy.expose
    @cherrypy.tools.allow(methods=['POST'])  # allow only post
    @authenticate
    def delete_demo(self, demo_id):
        """
        Delete the specified demo
        """
        data = {}
        data["status"] = "KO"

        try:

            conn = lite.connect(self.database_file)

            demo_dao = DemoDAO(conn)
            # read demo
            dd_dao = DemoDemoDescriptionDAO(conn)

            # delete demo decription history borra ddl id 3
            # d_dd con id 2 , y demoid=2, demodescpid 3 deberia no estar
            dd_dao.delete_all_demodescriptions_for_demo(int(demo_id))
            # delete demo, and delete on cascade demodemodescription
            demo_dao.delete(int(demo_id))
            data["status"] = "OK"
            conn.close()

        except Exception as ex:
            error_string = "demoinfo delete_demo error %s" % str(ex)
            print(error_string)
            self.logger.exception(error_string)
            try:
                conn.close()
            except Exception as ex:
                pass
            # raise Exception
            data["error"] = error_string

        return json.dumps(data).encode()

    @cherrypy.expose
    @cherrypy.tools.allow(methods=['POST'])  # allow only post
    @authenticate
    def update_demo(self, demo, old_editor_demoid):
        """
        Update the demo.
        """
        data = {"status": "KO"}

        demo_json = json.loads(demo)

        if 'creation' in demo_json:
            # Change creation date
            d = Demo(demo_json.get('editorsdemoid'), demo_json.get('title'), demo_json.get('state'),
                     demo_json.get('creation'))
        else:
            # update Demo
            d = Demo(demo_json.get('editorsdemoid'), demo_json.get('title'), demo_json.get('state'))

        try:
            old_editor_demoid = int(old_editor_demoid)
            d_editorsdemoid = int(d.editorsdemoid)

            conn = lite.connect(self.database_file)
            dao = DemoDAO(conn)
            dao.update(d, old_editor_demoid)
            conn.close()

            if old_editor_demoid != d_editorsdemoid \
                    and os.path.isdir(os.path.join(self.dl_extras_dir, str(old_editor_demoid))):
                if os.path.isdir(os.path.join(self.dl_extras_dir, str(d_editorsdemoid))):
                    # If the destination path exists, it should be removed
                    shutil.rmtree(os.path.join(self.dl_extras_dir, str(d_editorsdemoid)))

                if os.path.isdir(os.path.join(self.dl_extras_dir, str(old_editor_demoid))):
                    os.rename(os.path.join(self.dl_extras_dir, str(old_editor_demoid)),
                              os.path.join(self.dl_extras_dir, str(d_editorsdemoid)))

            data["status"] = "OK"
        except OSError as ex:
            data["error"] = "demoinfo update_demo error {}".format(ex)
        except Exception as ex:
            error_string = (" demoinfo update_demo error %s" % (str(ex)))
            print(error_string)
            try:
                conn.close()
            except Exception as ex:
                pass
            data["error"] = error_string

        return json.dumps(data).encode()

    # AUTHOR


    # todo check its not usefull any more and delete...
    @cherrypy.expose
    @authenticate
    def author_list(self):
        """
        Returns the list of authors.
        """
        data = {}
        data["status"] = "KO"
        author_list = list()
        try:
            conn = lite.connect(self.database_file)
            author_dao = AuthorDAO(conn)
            for a in author_dao.list():
                # convert to Demo class to json
                author_list.append(a.__dict__)

            data["author_list"] = author_list
            data["status"] = "OK"
            conn.close()
        except Exception as ex:
            error_string = "demoinfo author_list error %s" % str(ex)
            print(error_string)
            self.logger.exception(error_string)
            try:
                conn.close()
            except Exception as ex:
                pass
            # raise Exception
            data["error"] = error_string
        return json.dumps(data).encode()

    @cherrypy.expose
    @authenticate
    def author_list_pagination_and_filter(self, num_elements_page, page,
                                          qfilter=None):
        """
        Returns paginated and filtered list of authors.
        """
        data = {}
        data["status"] = "KO"
        author_list = list()
        next_page_number = None
        previous_page_number = None

        try:
            num_elements_page = int(num_elements_page)
            page = int(page)

            conn = lite.connect(self.database_file)
            author_dao = AuthorDAO(conn)

            complete_author_list = author_dao.list()

            # filter or return all
            if qfilter:
                for a in complete_author_list:
                    if qfilter.lower() in a.name.lower() or qfilter.lower() in a.mail.lower():
                        author_list.append(a.__dict__)
            else:
                # convert to Demo class to json
                for a in complete_author_list:
                    author_list.append(a.__dict__)

            # if demos found, return pagination
            if author_list:

                r = float(len(author_list)) / float(num_elements_page)

                totalpages = int(ceil(r))

                if page is None:
                    page = 1
                else:
                    if page < 1:
                        page = 1
                    elif page > totalpages:
                        page = totalpages

                next_page_number = page + 1
                if next_page_number > totalpages:
                    next_page_number = None

                previous_page_number = page - 1
                if previous_page_number <= 0:
                    previous_page_number = None

                start_element = (page - 1) * num_elements_page
                author_list = author_list[start_element: start_element + num_elements_page]
            else:
                totalpages = None

            data["author_list"] = author_list
            data["next_page_number"] = next_page_number
            data["number"] = totalpages
            data["previous_page_number"] = previous_page_number
            data["status"] = "OK"
            conn.close()
        except Exception as ex:
            error_string = "demoinfo author_list_pagination_and_filter error %s" % str(ex)
            print(error_string)
            self.logger.exception(error_string)
            try:
                conn.close()
            except Exception as ex:
                pass
            # raise Exception
            data["error"] = error_string

        return json.dumps(data).encode()

    @cherrypy.expose
    @authenticate
    def read_author(self, authorid):
        """
        Returns info of the author.
        """
        data = dict()
        data["status"] = "KO"

        try:

            author = None
            try:
                authorid = int(authorid)
                conn = lite.connect(self.database_file)
                dao = AuthorDAO(conn)
                author = dao.read(authorid)
                conn.close()
            except Exception as ex:
                error_string = ("read_author  e:%s" % (str(ex)))
                print(error_string)

            if author is None:
                print("No author retrieved for this id")
                return json.dumps(data).encode()

            data["id"] = author.id
            data["name"] = author.name
            data["mail"] = author.mail
            data["creation"] = author.creation
            data["status"] = "OK"

        except Exception as ex:
            error_string = "demoinfo read_author error %s" % str(ex)
            print(error_string)
            self.logger.exception(error_string)
            try:
                conn.close()
            except Exception as ex:
                pass
            # raise Exception
            data["error"] = error_string

        return json.dumps(data).encode()

    @cherrypy.expose
    def author_get_demos_list(self, author_id):
        """
        Returns the list of demos associated to a given author.
        """
        data = {}
        data["status"] = "KO"
        demo_list = list()
        try:
            conn = lite.connect(self.database_file)
            author_dao = AuthorDAO(conn)

            if not author_dao.exist(author_id):
                return json.dumps(data).encode()

            da_dao = DemoAuthorDAO(conn)

            for d in da_dao.read_author_demos(int(author_id)):
                # convert to Demo class to json
                demo_list.append(d.__dict__)

            data["demo_list"] = demo_list
            conn.close()
            data["status"] = "OK"

        except Exception as ex:
            error_string = "demoinfo author_get_demos_list error %s" % str(ex)
            print(error_string)
            self.logger.exception(error_string)
            try:
                conn.close()
            except Exception as ex:
                pass
            # raise Exception
            data["error"] = error_string
        return json.dumps(data).encode()

    @cherrypy.expose
    @cherrypy.tools.allow(methods=['POST', 'GET'])  # allow only post
    @authenticate
    def add_author(self, name, mail):
        """
        Add an author
        """
        data = {"status": "KO"}
        conn = None
        try:
            a = Author(name, mail)
            conn = lite.connect(self.database_file)
            dao = AuthorDAO(conn)
            the_id = dao.add(a)
            conn.close()
            data["status"] = "OK"
            data["authorid"] = the_id

        except IntegrityError as ex:
            print(ex)
            data['error'] = str(ex)
            if conn is not None:
                conn.close()
        except Exception as ex:
            error_string = "demoinfo add_author error %s" % str(ex)
            print(error_string)
            self.logger.exception(error_string)
            if conn is not None:
                conn.close()
            data["error"] = error_string
        return json.dumps(data).encode()

    @cherrypy.expose
    @cherrypy.tools.allow(methods=['POST'])  # allow only post
    @authenticate
    def add_author_to_demo(self, demo_id, author_id):
        """
        Add an author to a demo.
        """
        data = {}
        data["status"] = "KO"
        try:
            conn = lite.connect(self.database_file)
            demo_dao = DemoDAO(conn)
            author_dao = AuthorDAO(conn)

            if not demo_dao.exist(demo_id) or not author_dao.exist(author_id):
                return json.dumps(data).encode()

            dao = DemoAuthorDAO(conn)
            dao.add(int(demo_id), int(author_id))
            conn.close()
            data["status"] = "OK"
        except Exception as ex:
            error_string = "demoinfo add_author_to_demo error %s" % str(ex)
            print(error_string)
            self.logger.exception(error_string)
            try:
                conn.close()
            except Exception as ex:
                pass
            # raise Exception
            data["error"] = error_string
        return json.dumps(data).encode()

    @cherrypy.expose
    @cherrypy.tools.allow(methods=['POST'])  # allow only post
    @authenticate
    def remove_author_from_demo(self, demo_id, author_id):
        """
        Remove the given author from the demo.
        """
        data = {}
        data["status"] = "KO"
        try:
            conn = lite.connect(self.database_file)
            demo_dao = DemoDAO(conn)
            author_dao = AuthorDAO(conn)

            if not demo_dao.exist(demo_id) or not author_dao.exist(author_id):
                return json.dumps(data).encode()

            dao = DemoAuthorDAO(conn)
            dao.remove_author_from_demo(int(demo_id), int(author_id))
            conn.close()
            data["status"] = "OK"
        except Exception as ex:
            error_string = "demoinfo remove_author_from_demo error %s" % str(ex)
            print(error_string)
            self.logger.exception(error_string)
            try:
                conn.close()
            except Exception as ex:
                pass
            # raise Exception
            data["error"] = error_string
        return json.dumps(data).encode()

    @cherrypy.expose
    @cherrypy.tools.allow(methods=['POST'])  # allow only post
    @authenticate
    def remove_author(self, author_id):
        """
        deleting given author, and its relationship with demos
        """
        data = {}
        data["status"] = "KO"
        try:

            authorid = int(author_id)

            conn = lite.connect(self.database_file)
            dadao = DemoAuthorDAO(conn)
            # deletes the author relation with its demos
            demolist = dadao.read_author_demos(authorid)
            if demolist:
                # remove author from demos
                for demo in demolist:
                    dadao.remove_author_from_demo(demo.editorsdemoid, authorid)

            # deletes the author
            adao = AuthorDAO(conn)
            adao.delete(authorid)

            conn.close()
            data["status"] = "OK"
        except Exception as ex:
            error_string = "demoinfo remove_author error %s" % str(ex)
            print(error_string)
            self.logger.exception(error_string)
            try:
                conn.close()
            except Exception as ex:
                pass
            # raise Exception
            data["error"] = error_string
        return json.dumps(data).encode()

    @cherrypy.expose
    @cherrypy.tools.allow(methods=['POST'])  # allow only post
    @authenticate
    def update_author(self, author):
        """
        Update author
        """
        data = {"status": "KO"}

        json_author = json.loads(author)
        if 'creation' in json_author:
            a = Author(json_author.get('name'), json_author.get('mail'), json_author.get('id'),
                       json_author.get('creation'))
        else:
            a = Author(json_author.get('name'), json_author.get('mail'), json_author.get('id'))

        # update Author
        try:

            conn = lite.connect(self.database_file)
            dao = AuthorDAO(conn)

            if not dao.exist(a.id):
                return json.dumps(data).encode()

            dao.update(a)
            conn.close()
            data["status"] = "OK"
        except Exception as ex:
            error_string = "demoinfo update_author error %s" % str(ex)
            print(error_string)
            self.logger.exception(error_string)
            try:
                conn.close()
            except Exception as ex:
                pass
            # raise Exception
            data["error"] = error_string
        return json.dumps(data).encode()

    # EDITOR


    @cherrypy.expose
    @authenticate
    def editor_list(self):
        """
        Returns the editor list
        """
        data = {}
        data["status"] = "KO"
        editor_list = list()
        try:
            conn = lite.connect(self.database_file)
            editor_dao = EditorDAO(conn)
            for e in editor_dao.list():
                # convert to Demo class to json
                editor_list.append(e.__dict__)

            data["editor_list"] = editor_list
            data["status"] = "OK"
            conn.close()
        except Exception as ex:
            error_string = "demoinfo editor_list error %s" % str(ex)
            print(error_string)
            self.logger.exception(error_string)
            try:
                conn.close()
            except Exception as ex:
                pass
            # raise Exception
            data["error"] = error_string
        return json.dumps(data).encode()

    @cherrypy.expose
    @authenticate
    def editor_list_pagination_and_filter(self, num_elements_page, page,
                                          qfilter=None):
        """
        Returns paginated and filtered list of editor
        """
        data = {}
        data["status"] = "KO"
        editor_list = list()
        next_page_number = None
        previous_page_number = None

        try:
            num_elements_page = int(num_elements_page)
            page = int(page)

            conn = lite.connect(self.database_file)
            editor_dao = EditorDAO(conn)

            complete_editor_list = editor_dao.list()

            # filter or return all
            if qfilter:
                for a in complete_editor_list:
                    if qfilter.lower() in a.name.lower() or qfilter.lower() in a.mail.lower():
                        editor_list.append(a.__dict__)
            else:
                # convert to Demo class to json
                for a in complete_editor_list:
                    editor_list.append(a.__dict__)

            # if demos found, return pagination
            if editor_list:
                r = float(len(editor_list)) / float(num_elements_page)
                totalpages = int(ceil(r))

                if page is None:
                    page = 1
                else:
                    if page < 1:
                        page = 1
                    elif page > totalpages:
                        page = totalpages

                next_page_number = page + 1
                if next_page_number > totalpages:
                    next_page_number = None

                previous_page_number = page - 1
                if previous_page_number <= 0:
                    previous_page_number = None

                start_element = (page - 1) * num_elements_page
                editor_list = editor_list[start_element: start_element + num_elements_page]
            else:
                totalpages = None

            data["editor_list"] = editor_list
            data["next_page_number"] = next_page_number
            data["number"] = totalpages
            data["previous_page_number"] = previous_page_number
            data["status"] = "OK"
            conn.close()
        except Exception as ex:
            error_string = "demoinfo editor_list_pagination_and_filter error %s" % str(ex)
            print(error_string)
            self.logger.exception(error_string)
            try:
                conn.close()
            except Exception as ex:
                pass
            # raise Exception
            data["error"] = error_string

        return json.dumps(data).encode()

    @cherrypy.expose
    def editor_get_demos_list(self, editor_id):
        """
        Returns a list of demos associated to given editor.
        """
        data = {}
        data["status"] = "KO"
        demo_list = list()
        try:
            conn = lite.connect(self.database_file)
            editor_dao = EditorDAO(conn)

            if not editor_dao.exist(editor_id):
                return json.dumps(data).encode()

            de_dao = DemoEditorDAO(conn)

            for d in de_dao.read_editor_demos(int(editor_id)):
                # convert to Demo class to json
                demo_list.append(d.__dict__)

            data["demo_list"] = demo_list
            conn.close()
            data["status"] = "OK"
        except Exception as ex:
            error_string = "demoinfo editor_get_demos_list error %s" % str(ex)
            print(error_string)
            self.logger.exception(error_string)
            try:
                conn.close()
            except Exception as ex:
                pass
            # raise Exception
            data["error"] = error_string
        return json.dumps(data).encode()

    @cherrypy.expose
    @authenticate
    def read_editor(self, editorid):
        """
        Returns editor info.
        """
        data = dict()
        data["status"] = "KO"

        try:
            editor = None
            try:
                editorid = int(editorid)
                conn = lite.connect(self.database_file)
                dao = EditorDAO(conn)
                editor = dao.read(editorid)
                conn.close()
            except Exception as ex:
                error_string = ("read_editor  e:%s" % (str(ex)))
                print(error_string)

            if editor is None:
                print("No editor retrieved for this id")
                data['error'] = "No editor retrieved for this id"
                return json.dumps(data).encode()

            data["id"] = editor.id
            data["name"] = editor.name
            data["mail"] = editor.mail
            data["creation"] = editor.creation
            data["status"] = "OK"

        except Exception as ex:
            error_string = "demoinfo read_editor error %s" % str(ex)
            print(error_string)
            self.logger.exception(error_string)
            try:
                conn.close()
            except Exception as ex:
                pass
            # raise Exception
            data["error"] = error_string

        return json.dumps(data).encode()

    @cherrypy.expose
    @cherrypy.tools.allow(methods=['POST'])  # allow only post
    @authenticate
    def add_editor(self, name, mail):
        """
        Add editor.
        """
        data = {"status": "KO"}
        conn = None
        try:
            e = Editor(name, mail)
            conn = lite.connect(self.database_file)
            dao = EditorDAO(conn)
            the_id = dao.add(e)
            conn.close()
            data["status"] = "OK"
            data["editorid"] = the_id

        except IntegrityError as ex:
            print(ex)
            data['error'] = str(ex)
            if conn is not None:
                conn.close()
        except Exception as ex:
            error_string = "demoinfo add_editor error %s" % str(ex)
            print(error_string)
            self.logger.exception(error_string)
            if conn is not None:
                conn.close()

            data["error"] = error_string
        return json.dumps(data).encode()

    @cherrypy.expose
    @cherrypy.tools.allow(methods=['POST'])  # allow only post
    @authenticate
    def add_editor_to_demo(self, demo_id, editor_id):
        """
        Add the given editor to the given demo.
        """
        data = {}
        data["status"] = "KO"
        try:
            conn = lite.connect(self.database_file)
            demo_dao = DemoDAO(conn)
            editor_dao = EditorDAO(conn)

            if not demo_dao.exist(demo_id) or not editor_dao.exist(editor_id):
                return json.dumps(data).encode()

            dao = DemoEditorDAO(conn)
            dao.add(int(demo_id), int(editor_id))
            conn.close()
            data["status"] = "OK"
        except Exception as ex:
            error_string = "demoinfo add_editor_to_demo error %s" % str(ex)
            print(error_string)
            self.logger.exception(error_string)
            try:
                conn.close()
            except Exception as ex:
                pass
            # raise Exception
            data["error"] = error_string
        return json.dumps(data).encode()

    @cherrypy.expose
    @cherrypy.tools.allow(methods=['POST'])  # allow only post
    @authenticate
    def remove_editor_from_demo(self, demo_id, editor_id):
        """
        Remove the given editor from the given demo.
        """
        data = {}
        data["status"] = "KO"
        try:
            conn = lite.connect(self.database_file)
            demo_dao = DemoDAO(conn)
            editor_dao = EditorDAO(conn)

            if not demo_dao.exist(demo_id) or not editor_dao.exist(editor_id):
                return json.dumps(data).encode()

            dao = DemoEditorDAO(conn)
            dao.remove_editor_from_demo(int(demo_id), int(editor_id))
            conn.close()
            data["status"] = "OK"
        except Exception as ex:
            error_string = "demoinfo remove_editor_from_demo error %s" % str(ex)
            print(error_string)
            self.logger.exception(error_string)
            try:
                conn.close()
            except Exception as ex:
                pass
            # raise Exception
            data["error"] = error_string
        return json.dumps(data).encode()

    @cherrypy.expose
    @cherrypy.tools.allow(methods=['POST'])  # allow only post
    @authenticate
    def remove_editor(self, editor_id):
        """
        Delete editor
        """

        data = {}
        data["status"] = "KO"
        try:

            editorid = int(editor_id)
            conn = lite.connect(self.database_file)
            dedao = DemoEditorDAO(conn)
            # deletes the author relation with its demos
            demolist = dedao.read_editor_demos(editorid)
            if demolist:
                # remove editor from demos
                for demo in demolist:
                    dedao.remove_editor_from_demo(demo.editorsdemoid, editorid)
            # deletes the editor
            edao = EditorDAO(conn)
            edao.delete(editorid)
            conn.close()
            data["status"] = "OK"
        except Exception as ex:
            error_string = "demoinfo remove_editor error %s" % str(ex)
            print(error_string)
            self.logger.exception(error_string)
            try:
                conn.close()
            except Exception as ex:
                pass
            # raise Exception
            data["error"] = error_string
        return json.dumps(data).encode()

    @cherrypy.expose
    @cherrypy.tools.allow(methods=['POST'])  # allow only post
    @authenticate
    def update_editor(self, editor):
        """
        Update editor.
        """
        data = {"status": "KO"}

        json_editor = json.loads(editor)
        if 'creation' in json_editor:
            e = Editor(json_editor.get('name'), json_editor.get('mail'), json_editor.get('id'),
                       json_editor.get('creation'))
        else:
            e = Editor(json_editor.get('name'), json_editor.get('mail'), json_editor.get('id'))

        # update Editor
        try:
            conn = lite.connect(self.database_file)
            dao = EditorDAO(conn)

            if not dao.exist(e.id):
                return json.dumps(data).encode()

            dao.update(e)
            conn.close()
            data["status"] = "OK"
        except Exception as ex:
            error_string = "demoinfo update_editor error %s" % str(ex)
            print(error_string)
            self.logger.exception(error_string)
            try:
                conn.close()
            except Exception as ex:
                pass
            # raise Exception
            data["error"] = error_string
        return json.dumps(data).encode()

    # DDL


    @cherrypy.expose
    @authenticate
    def read_ddl(self, ddl_id):
        """
        Return the DDL.
        """
        data = {}
        data["status"] = "KO"
        data["demo_description"] = None
        try:
            ddl_id = int(ddl_id)
            conn = lite.connect(self.database_file)
            dao = DemoDescriptionDAO(conn)

            ddl = dao.read(ddl_id)
            ddl_str = str(ddl)

            data["demo_description"] = ddl_str
            conn.close()
            data["status"] = "OK"
        except Exception as ex:
            error_string = "demoinfo read_ddl error %s" % str(ex)
            print(error_string)
            self.logger.exception(error_string)
            try:
                conn.close()
            except Exception as ex:
                pass
            # raise Exception
            data["error"] = error_string

        return json.dumps(data).encode()

    @cherrypy.expose
    def get_interface_ddl(self, demo_id, sections=None):
        """
        Read the DDL of the specified demo without unneeded or private fields. Used by the website interface.
        """
        try:
            # Validate demo_id 
            try:
                demo_id = int(demo_id)
            except(TypeError, ValueError) as ex: 
                return json.dumps({'status': 'KO', 'error': "Invalid demo_id: {}".format(demo_id)}).encode()

            ddl = self.get_stored_ddl(demo_id)
            if not ddl:
                return json.dumps({'status': 'KO', 'error': "There isn't any DDL for the demo {}".format(demo_id)}).encode()

            ddl = json.loads(ddl.get("ddl"), object_pairs_hook=OrderedDict)
            # removing sections that shouldn't be obtained by the web interface
            if 'build' in ddl:
                del ddl['build']
            if 'run' in ddl:
                del ddl['run']
            # obtaining the sections given as a parameter
            if sections:
                ddl_sections = self.get_ddl_sections(ddl, sections)
                return json.dumps({'status': 'OK', 'last_demodescription': {"ddl": json.dumps(ddl_sections)}}).encode()
            return json.dumps({'status': 'OK', 'last_demodescription': {"ddl": json.dumps(ddl)}}).encode()
        except Exception as ex:
            error_string = "Failure in function get_interface_ddl with demo {}, Error = {}".format(demo_id, ex)
            print(error_string)
            self.logger.exception(error_string)
            return json.dumps({'status': 'KO', 'error': error_string}).encode()

    @staticmethod
    def get_ddl_sections(ddl, ddl_sections):
        """
        Returns DDL sections
        """
        sections = OrderedDict()
        for section in ddl_sections.split(','):
            if ddl.get(section):
                sections[str(section)] = ddl.get(section)
        return sections

    @cherrypy.expose
    @authenticate
    def get_ddl_history(self, demo_id):
        """
        Return a list with all the DDLs
        """
        ddl_history = []
        data = {'status':'KO'}
        try:
            conn = lite.connect(self.database_file)
            dd_dao = DemoDemoDescriptionDAO(conn)
            ddl_history = dd_dao.read_history(demo_id)
            if not ddl_history:
                data['error'] = "There isn't any DDL for demo {}".format(demo_id)
                return json.dumps(data).encode()
            data['ddl_history'] = ddl_history
            data['status'] = 'OK'
            return json.dumps(data).encode()
        except Exception as ex:
            error_msg = "Failure in function get_ddl_history. Error: {}".format(ex)
            self.logger.exception(error_msg)
            print(error_msg)
            data['error'] = error_msg
            return json.dumps(data).encode()

    @cherrypy.expose
    @authenticate
    def get_ddl(self, demo_id, sections=None):
        """
        Reads the current DDL of the demo
        """
        try:
            # Validate demo_id 
            try:
                demo_id = int(demo_id)
            except(TypeError, ValueError) as ex: 
                return json.dumps({'status': 'KO', 'error': "Invalid demo_id: {}".format(demo_id)}).encode()

            ddl = self.get_stored_ddl(demo_id)
            if not ddl:
                error = "There isn't any DDL for demo {}".format(demo_id)
                return json.dumps({'status': 'KO', 'error': error}).encode()
            if sections:
                ddl = json.loads(ddl.get("ddl"), object_pairs_hook=OrderedDict)
                ddl_sections = self.get_ddl_sections(ddl, sections)
                return json.dumps({'status': 'OK', 'last_demodescription': ddl_sections}).encode()
            return json.dumps({'status': 'OK', 'last_demodescription': ddl}).encode()
        except Exception as ex:
            error_string = "Failure in function get_ddl, Error = {}".format(ex)
            print(error_string)
            self.logger.exception(error_string)
            return json.dumps({'status': 'KO'}).encode()

    def get_stored_ddl(self, demo_id):
        """
        Method that gives the stored DDL given a demo_id
        """
        conn = lite.connect(self.database_file)
        dd_dao = DemoDemoDescriptionDAO(conn)
        last_demodescription = dd_dao.get_ddl(int(demo_id))
        conn.close()
        return last_demodescription

    @cherrypy.expose
    @cherrypy.tools.allow(methods=['POST'])  # allow only post
    @authenticate
    def save_ddl(self, demoid):
        """
        Save the DDL.
        """
        # def save_ddl(self, demoid):
        # recieves a valid json as a string AS POST DATA
        # stackoverflow.com/questions/3743769/how-to-receive-json-in-a-post-request-in-cherrypy

        data = {}
        data["status"] = "KO"
        cl = cherrypy.request.headers['Content-Length']
        ddl = cherrypy.request.body.read(int(cl)).decode()
        if not is_json(ddl):
            print("\n save_ddl ddl is not a valid json ")
            print("ddl: ", ddl)
            print("ddl type: ", type(ddl))
            data['error'] = "save_ddl ddl is not a valid json"
            return json.dumps(data).encode()
        try:
            conn = lite.connect(self.database_file)
            demo_dao = DemoDAO(conn)
            demo = demo_dao.read(int(demoid))
            if demo is None:
                data['error'] = 'There is no demo with that demoid'
                return json.dumps(data).encode()
            state = demo_dao.read(int(demoid)).state
            if state != "published":  # If the demo is not published the DDL is overwritten
                ddddao = DemoDemoDescriptionDAO(conn)
                demodescription = ddddao.get_ddl(int(demoid))
                dao = DemoDescriptionDAO(conn)

                if demodescription is None:  # Check if is a new demo
                    demodescription_id = dao.add(ddl)

                    dao = DemoDemoDescriptionDAO(conn)
                    dao.add(int(demoid), int(demodescription_id))
                else:
                    dao.update(ddl, demoid)

            else:  # Otherwise it's create a new one
                dao = DemoDescriptionDAO(conn)
                demodescription_id = dao.add(ddl)
                dao = DemoDemoDescriptionDAO(conn)
                dao.add(int(demoid), int(demodescription_id))

            data["added_to_demo_id"] = demoid

            conn.close()
            # return id
            data["status"] = "OK"

        except Exception as ex:
            error_string = "demoinfo save_ddl error %s" % str(ex)
            print(error_string)
            self.logger.exception(error_string)
            try:
                conn.close()
            except Exception as ex:
                pass
            # raise Exception
            data["error"] = error_string

        return json.dumps(data).encode()

    # MISCELLANEA

    @staticmethod
    @cherrypy.expose
    def index():
        """
        index of the module.
        """
        return "Welcome to IPOL demoInfo !"

    @staticmethod
    @cherrypy.expose
    def ping():
        """
        Ping service: answer with a PONG.
        """
        data = {}
        data["status"] = "OK"
        data["ping"] = "pong"
        return json.dumps(data).encode()

    @cherrypy.expose
    @authenticate
    def shutdown(self):
        """
        shutdown the module.
        """
        data = {}
        data["status"] = "KO"
        try:
            cherrypy.engine.exit()
            data["status"] = "OK"
        except Exception as ex:
            self.error_log("shutdown", str(ex))
        return json.dumps(data).encode()

    # todo hide sql
    @cherrypy.expose
    def stats(self):
        """
        Returns usage statistics.
        """
        data = {}
        data["status"] = "KO"
        try:
            conn = lite.connect(self.database_file)
            cursor_db = conn.cursor()
            cursor_db.execute("""
            SELECT COUNT(*) FROM demo""")
            data["nb_demos"] = cursor_db.fetchone()[0]
            cursor_db.execute("""
            SELECT COUNT(*) FROM author""")
            data["nb_authors"] = cursor_db.fetchone()[0]
            cursor_db.execute("""
            SELECT COUNT(*) FROM editor""")
            data["nb_editors"] = cursor_db.fetchone()[0]
            conn.close()
            data["status"] = "OK"
        except Exception as ex:
            error_string = "demoinfo stats error %s" % str(ex)
            print(error_string)
            self.logger.exception(error_string)
            try:
                conn.close()
            except Exception as ex:
                pass
            # raise Exception
            data["error"] = error_string
        return json.dumps(data).encode()

    # todo hide sql
    @cherrypy.expose
    def read_states(self):
        """
        Returns the list of defined demo states.
        """
        data = {}
        state_list = list()
        data["status"] = "KO"
        try:
            conn = lite.connect(self.database_file)
            cursor_db = conn.cursor()
            cursor_db.execute("""SELECT s.name FROM state as s """)
            conn.commit()
            for row in cursor_db.fetchall():
                s = (row[0], row[0])
                state_list.append(s)

            conn.close()

            data["status"] = "OK"
            data["state_list"] = state_list
        except Exception as ex:
            error_string = "demoinfo read_states error %s" % str(ex)
            print(error_string)
            self.logger.exception(error_string)
            try:
                conn.close()
            except Exception as ex:
                pass
            # raise Exception
            data["error"] = error_string
        return json.dumps(data).encode()

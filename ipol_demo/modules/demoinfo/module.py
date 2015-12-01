#!/usr/bin/python
# -*- coding:utf-8 -*-

"""
Demo Info metadata module
Provides a set of stateless JSON webservices

todo: secure webservices
todo: secure db access
"""

import sqlite3 as lite
import sys
import errno
import logging
import json
import cherrypy
import os
import os.path


from model import *


#GLOBAL VARS
LOGNAME = "demoinfo_log"
#todo This should not be hardcoded
CONFIGFILE = "./demoinfo.conf"



class DemoInfo(object):
    """
    This class implement an archive system for experiments and
    calculations done with the IPOL demo image system.
    """

    #####
    # initialization and static methods.
    #####

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

        :rtype: bool
        """
        if not (
                #cherrypy.config.has_key("blobs_dir") and
                cherrypy.config.has_key("database_dir") and
                cherrypy.config.has_key("database_name") and
                #cherrypy.config.has_key("blobs_thumbs_dir") and
                cherrypy.config.has_key("logs_dir") ):
                #cherrypy.config.has_key("url")):
            print "Missing elements in configuration file."
            return False
        else:
            return True


    def __init__(self, option):
        """
        Initialize Archive class.
        Attribute status should be checked after each initialisation.
        It is false if something went wrong.
        """
        thumbs_s = None
        cherrypy.config.update(CONFIGFILE)
        self.status = self.check_config()
        if not self.status:
            sys.exit(1)

        self.logs_dir = cherrypy.config.get("logs_dir")
        #self.url = cherrypy.config.get("url")
        self.mkdir_p(self.logs_dir)
        self.logger = self.init_logging()

        # Database
        self.database_dir = cherrypy.config.get("database_dir")
        self.database_name = cherrypy.config.get("database_name")
        self.database_file = os.path.join(self.database_dir, self.database_name)
        createDb(self.database_name)
        initDb(self.database_name)
        # db testing purposes only!
        testDb(self.database_name)




    def init_logging(self):
        """
        Initialize the error logs of the module.
        """
        logger = logging.getLogger(LOGNAME)
        logger.setLevel(logging.ERROR)
        handler = logging.FileHandler(os.path.join(self.logs_dir,
                                                   'error.log'))
        formatter = logging.Formatter('%(asctime)s ERROR in %(message)s',
                                      datefmt='%Y-%m-%d %H:%M:%S')
        handler.setFormatter(formatter)
        logger.addHandler(handler)
        return logger

    def error_log(self, function_name, error):
        """
        Write an error log in the logs_dir defined in archive.conf
        """
        error_string = function_name + ": " + error
        self.logger.error(error_string)
 

    @cherrypy.expose
    def index(self):
        return ("Welcome to IPOL demoInfo !")
    @cherrypy.expose
    def demo_list(self):
        data = {}
        data["status"] = "KO"
        demo_list=list()
        try:
            conn = lite.connect(self.database_file)
            demo_dao = DemoDAO(conn)
            for d in demo_dao.list():
                #convert to Demo class to json
                demo_list.append(d.__dict__)


            data["demo_list"] = demo_list
            data["status"] = "OK"
        except Exception as ex:
            print str(ex)
            self.error_log("demo_list",str(ex))
            try:
                conn.close()
            except Exception as ex:
                print str(ex)
        return json.dumps(data)

    @cherrypy.expose
    def author_list(self):
        data = {}
        data["status"] = "KO"
        author_list=list()
        try:
            conn = lite.connect(self.database_file)
            author_dao = AuthorDAO(conn)
            for a in author_dao.list():
                #convert to Demo class to json
                author_list.append(a.__dict__)


            data["author_list"] = author_list
            data["status"] = "OK"
        except Exception as ex:
            print str(ex)
            self.error_log("author_list",str(ex))
            try:
                conn.close()
            except Exception as ex:
                print str(ex)
        return json.dumps(data)

    @cherrypy.expose
    def editor_list(self):
        data = {}
        data["status"] = "KO"
        editor_list=list()
        try:
            conn = lite.connect(self.database_file)
            editor_dao = EditorDAO(conn)
            for e in editor_dao.list():
                #convert to Demo class to json
                editor_list.append(e.__dict__)


            data["editor_list"] = editor_list
            data["status"] = "OK"
        except Exception as ex:
            print str(ex)
            self.error_log("editor_list",str(ex))
            try:
                conn.close()
            except Exception as ex:
                print str(ex)
        return json.dumps(data)

    @cherrypy.expose
    def demo_get_authors_list(self,demo_id):
        data = {}
        data["status"] = "KO"
        author_list=list()
        try:
            conn = lite.connect(self.database_file)
            da_dao = DemoAuthorDAO(conn)

            for a in da_dao.read_demo_authors(int(demo_id)):
                #convert to Demo class to json
                author_list.append(a.__dict__)


            data["author_list"] = author_list
            data["status"] = "OK"
        except Exception as ex:
            print str(ex)
            self.error_log("demo_get_authors_list",str(ex))
            try:
                conn.close()
            except Exception as ex:
                print str(ex)
        return json.dumps(data)

    @cherrypy.expose
    def author_get_demos_list(self,author_id):
        data = {}
        data["status"] = "KO"
        demo_list=list()
        try:
            conn = lite.connect(self.database_file)
            da_dao = DemoAuthorDAO(conn)

            for d in da_dao.read_author_demos(int(author_id)):
                #convert to Demo class to json
                demo_list.append(d.__dict__)


            data["demo_list"] = demo_list
            data["status"] = "OK"
        except Exception as ex:
            print str(ex)
            self.error_log("author_get_demos_list",str(ex))
            try:
                conn.close()
            except Exception as ex:
                print str(ex)
        return json.dumps(data)

    @cherrypy.expose
    def demo_get_editors_list(self,demo_id):
        data = {}
        data["status"] = "KO"
        editor_list=list()
        try:
            conn = lite.connect(self.database_file)
            de_dao = DemoEditorDAO(conn)

            for e in de_dao.read_demo_editors(int(demo_id)):
                #convert to Demo class to json
                editor_list.append(e.__dict__)


            data["editor_list"] = editor_list
            data["status"] = "OK"
        except Exception as ex:
            print str(ex)
            self.error_log("demo_get_authors_list",str(ex))
            try:
                conn.close()
            except Exception as ex:
                print str(ex)
        return json.dumps(data)

    @cherrypy.expose
    def editor_get_demos_list(self,editor_id):
        data = {}
        data["status"] = "KO"
        demo_list = list()
        try:
            conn = lite.connect(self.database_file)
            de_dao = DemoEditorDAO(conn)

            for d in de_dao.read_editor_demos(int(editor_id)):
                #convert to Demo class to json
                demo_list.append(d.__dict__)


            data["demo_list"] = demo_list
            data["status"] = "OK"
        except Exception as ex:
            print str(ex)
            self.error_log("author_get_demos_list",str(ex))
            try:
                conn.close()
            except Exception as ex:
                print str(ex)
        return json.dumps(data)

        
    @cherrypy.tools.allow(methods=['POST']) #allow only post
    def add_demo(self):
        pass

    @cherrypy.expose   
    #@cherrypy.tools.allow(methods=['POST']) #allow only post 
    def add_author(self):
        pass

    #@cherrypy.tools.allow(methods=['POST']) #allow only post
    def add_editor(self):
        pass
    #@cherrypy.tools.allow(methods=['POST']) #allow only post
    def add_author_to_demo(self):
        pass
    #@cherrypy.tools.allow(methods=['POST']) #allow only post
    def add_editor_to_demo(self):
        pass


    @cherrypy.expose
    def ping(self):
        data = {}
        data["status"] = "OK"
        data["ping"] = "pong"
        return json.dumps(data)

    @cherrypy.expose
    def shutdown(self):
        data = {}
        data["status"] = "KO"
        try:
            cherrypy.engine.exit()
            data["status"] = "OK"
        except Exception as ex:
            self.error_log("shutdown", str(ex))
        return json.dumps(data)

    @cherrypy.expose
    def stats(self):
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
            self.error_log("stats", str(ex))
            try:
                conn.close()
            except Exception as ex:
                pass
        return json.dumps(data)

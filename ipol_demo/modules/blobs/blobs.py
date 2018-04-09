#!/usr/bin/env python
# -*- coding:utf-8 -*-

"""
This file implements the system core of the server
It implements Blob object and web service
"""
import hashlib
import json
import os
import sys
import logging
import glob
import mimetypes

import operator
import ConfigParser
import re
import shutil
from threading import Lock
import sqlite3 as lite
from sqlite3 import IntegrityError
import magic
import cherrypy
import ipolutils


import database
from errors import IPOLBlobsDataBaseError
from errors import IPOLBlobsTemplateError
from errors import IPOLBlobsThumbnailError
from errors import IPOLRemoveDirError


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
            return json.dumps(error)
        return func(*args, **kwargs)

    def is_authorized_ip(ip):
        """
        Validates the given IP
        """
        blobs = Blobs.get_instance()
        patterns = []
        # Creates the patterns  with regular expressions
        for authorized_pattern in blobs.authorized_patterns:
            patterns.append(re.compile(authorized_pattern.replace(".", "\\.").replace("*", "[0-9]*")))
        # Compare the IP with the patterns
        for pattern in patterns:
            if pattern.match(ip) is not None:
                return True
        return False

    return authenticate_and_call


class Blobs(object):
    """
    Blobs module
    """
    instance = None

    @staticmethod
    def get_instance():
        """
        Singleton pattern.
        """
        if Blobs.instance is None:
            Blobs.instance = Blobs()
        return Blobs.instance

    def __init__(self):
        """
        Constructor.
        """

        # Paths
        self.blob_dir = cherrypy.config['final.dir']
        self.thumb_dir = cherrypy.config['thumbnail.dir']
        self.vr_dir = cherrypy.config['visual_representation.dir']
        self.config_common_dir = cherrypy.config.get("config_common.dir")
        self.module_dir = cherrypy.config.get("module.dir")
        self.host_name = cherrypy.config['server.socket_host']

        # Logs
        self.logs_dir = cherrypy.config.get("logs_dir")
        try:
            if not os.path.exists(self.logs_dir):
                os.makedirs(self.logs_dir)
            self.logger = self.init_logging()
        except Exception as ex:
            print "Failed to create log dir. Error: {}".format(ex)

        # Lock
        self.lock = Lock()

        # Security: authorized IPs
        self.authorized_patterns = self.read_authorized_patterns()

        # Database
        self.database_dir = cherrypy.config.get("database_dir")
        self.database_name = cherrypy.config.get("database_name")
        self.database_file = os.path.join(self.database_dir, self.database_name)
        if not self.init_database():
            sys.exit("Initialization of database failed. Check the logs.")

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

    def error_log(self, function_name, error):
        """
        Write an error log in the logs_dir defined in demo.conf
        """
        error_string = function_name + ": " + error
        self.logger.error(error_string)

    def init_database(self):
        """
        Initialize the database used by the module if it doesn't exist.
        If the file is empty, the system delete it and create a new one.
        """

        if os.path.isfile(self.database_file):

            file_info = os.stat(self.database_file)

            if file_info.st_size == 0:
                try:
                    os.remove(self.database_file)
                except Exception as ex:
                    self.logger.exception("init_database: {}".format(ex))
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

            except Exception as ex:
                self.logger.exception("init_database: {}".format(ex))

                if os.path.isfile(self.database_file):
                    try:
                        os.remove(self.database_file)
                    except Exception as ex:
                        self.logger.exception("init_database: {}".format(ex))
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
            cfg = ConfigParser.ConfigParser()
            cfg.read([authorized_patterns_path])
            patterns = []
            for item in cfg.items('Patterns'):
                patterns.append(item[1])
            return patterns
        except ConfigParser.Error:
            self.logger.exception("Bad format in {}".format(authorized_patterns_path))
            return []

    @staticmethod
    @cherrypy.expose
    def index():
        """
        index of the module.
        """
        return "Blobs module"

    @staticmethod
    @cherrypy.expose
    def default(attr):
        """
        Default method invoked when asked for non-existing service.
        """
        data = {"status": "KO", "message": "Unknown service '{}'".format(attr)}
        return json.dumps(data)

    @staticmethod
    @cherrypy.expose
    def ping():
        """
        Ping service: answer with a PONG.
        """
        data = {"status": "OK", "ping": "pong"}
        return json.dumps(data)

    @cherrypy.expose
    @authenticate
    def shutdown(self):
        """
        Shutdown the module.
        """
        data = {"status": "KO"}
        try:
            cherrypy.engine.exit()
            data["status"] = "OK"
        except Exception as ex:
            self.logger.error("Failed to shutdown : {}".format(ex))
            sys.exit(1)
        return json.dumps(data)

    def add_blob(self, blob, tags, blob_set, pos_set, title, credit, dest, blob_vr):
        """
        Copies the blob and store it in the DB
        """
        res = False
        conn = None
        try:
            conn = lite.connect(self.database_file)
            mime = self.get_blob_mime(blob.file)

            blob_format, ext = self.get_format_and_extension(mime)
            # ext = "." + ext

            blob_hash = self.get_hash(blob.file)
            blob_id = self.store_blob(conn, blob.file, credit, blob_hash, ext, blob_format)

            try:
                if blob_vr is not None:
                    _, vr_ext = self.get_format_and_extension(self.get_blob_mime(blob_vr.file))
                    blob_file = self.copy_blob(blob_vr.file, blob_hash, vr_ext, self.vr_dir)
                    self.create_thumbnail(blob_file, blob_hash)
                else:
                    blob_file = os.path.join(self.blob_dir, self.get_subdir(blob_hash))
                    blob_file = os.path.join(blob_file, blob_hash + ext)
                    self.create_thumbnail(blob_file, blob_hash)
            except IPOLBlobsThumbnailError as ex:
                # An error in the creation of the thumbnail doesn't stop the execution of the method
                self.logger.exception("Error creating the thumbnail")
                print "Couldn't create the thumbnail. Error: {}".format(ex)

            self.associate_tags_to_blob(conn, blob_id, tags)

            # If the set is empty the module generates an unique set name
            if blob_set is None:
                blob_set = self.generate_set_name(blob_id)
                pos_set = 0

            if dest["dest"] == "demo":
                demo_id = dest["demo_id"]
                # Check if the pos is empty
                if database.is_pos_occupied_in_demo_set(conn, demo_id, blob_set, pos_set):
                    pos_set = database.get_max_pos_in_demo_set(conn, demo_id, blob_set) + 1

                self.do_add_blob_to_demo(conn, demo_id, blob_id, blob_set, pos_set, title)
                res = True
            elif dest["dest"] == "template":
                template_name = dest["name"]
                # Check if the pos is empty
                if database.is_pos_occupied_in_template_set(conn, template_name, blob_set, pos_set):
                    pos_set = database.get_max_pos_in_template_set(conn, template_name, blob_set) + 1

                self.do_add_blob_to_template(conn, template_name, blob_id, blob_set, pos_set, title)
                res = True
            else:
                self.logger.error("Failed to add the blob in add_blob. Unknown dest: {}".format(dest["dest"]))

        except IntegrityError as ex:
            print 'IntegrityError', ex
        except IOError as ex:
            self.logger.exception("Error copying uploaded blob")
            print "Couldn't copy uploaded blob. Error: {}".format(ex)
        except IPOLBlobsDataBaseError as ex:
            self.logger.exception("Error adding blob info to DB")
            print "Couldn't add blob info to DB. Error: {}".format(ex)
        except IPOLBlobsTemplateError as ex:
            print "Couldn't add blob to template. blob. Template doesn't exists. Error: {}".format(ex)
        except Exception as ex:
            self.logger.exception("*** Unhandled exception while adding the blob")
            print "*** Unhandled exception while adding the blob. Error: {}".format(ex)
        finally:
            if conn is not None:
                conn.close()

        return res

    @cherrypy.expose
    @authenticate
    def add_blob_to_demo(self, blob=None, demo_id=None, tags=None, blob_set=None, pos_set=None, title=None,
                         credit=None, blob_vr=None):
        """
        Adds a new blob to a demo
        """
        dest = {"dest": "demo", "demo_id": demo_id}
        if self.add_blob(blob, tags, blob_set, pos_set, title, credit, dest, blob_vr):
            return json.dumps({"status": "OK"})

        return json.dumps({"status": "KO"})

    @cherrypy.expose
    @authenticate
    def add_blob_to_template(self, blob=None, template_name=None, tags=None, blob_set=None, pos_set=None, title=None,
                             credit=None, blob_vr=None):
        """
        Adds a new blob to a template
        """
        dest = {"dest": "template", "name": template_name}

        if self.add_blob(blob, tags, blob_set, pos_set, title, credit, dest, blob_vr):
            return json.dumps({"status": "OK"})
        return json.dumps({"status": "KO"})

    def store_blob(self, conn, blob, credit, blob_hash, ext, blob_format):
        """
        Stores the blob info in the DB, copy it in the file system and returns the blob_id and blob_file
        """
        blob_id = database.get_blob_id(conn, blob_hash)
        if blob_id is not None:
            # If the DB already have the hash there is no need to store the blob
            return blob_id

        try:
            self.copy_blob(blob, blob_hash, ext, self.blob_dir)
            blob_id = database.store_blob(conn, blob_hash, blob_format, ext, credit)
            conn.commit()
            return blob_id
        except (IPOLBlobsDataBaseError, IntegrityError):
            conn.rollback()
            raise

    @staticmethod
    def get_blob_mime(blob):
        """
        Return format from blob
        """
        mime = magic.Magic(mime=True)
        blob.seek(0)
        blob_format = mime.from_buffer(blob.read())
        return blob_format

    @staticmethod
    def get_format_and_extension(mime):
        """
        get format and extension from mime
        """
        mime_format = mime.split('/')[0]
        ext = mimetypes.guess_extension(mime)
        return mime_format, ext

    @staticmethod
    def get_hash(blob):
        """
        Return the sha1 hash from blob
        """
        blob.seek(0)
        return hashlib.sha1(blob.read()).hexdigest()

    def copy_blob(self, blob, blob_hash, ext, dst_dir):
        """
        Stores the blob in the file system, returns the dest path
        """
        dst_path = os.path.join(dst_dir, self.get_subdir(blob_hash))
        if not os.path.isdir(dst_path):
            os.makedirs(dst_path)
        dst_path = os.path.join(dst_path, blob_hash + ext)
        blob.seek(0)
        with open(dst_path, 'wb') as f:
            shutil.copyfileobj(blob, f)
        return dst_path

    @staticmethod
    def get_subdir(blob_hash):
        """
        Returns the subdirectory from the blob hash
        """
        return os.path.join(blob_hash[0], blob_hash[1])

    @staticmethod
    def do_add_blob_to_demo(conn, demo_id, blob_id, pos_set, blob_set, blob_title):
        """
        Associates the blob to a demo in the DB
        """
        try:
            if not database.demo_exist(conn, demo_id):
                database.create_demo(conn, demo_id)
            database.add_blob_to_demo(conn, demo_id, blob_id, pos_set, blob_set, blob_title)
            conn.commit()
        except (IPOLBlobsDataBaseError, IntegrityError):
            conn.rollback()
            raise

    @staticmethod
    def do_add_blob_to_template(conn, template_name, blob_id, blob_set, pos_set, blob_title):
        """
        Associates the template to a demo in the DB
        """
        try:
            if not database.template_exist(conn, template_name):
                raise IPOLBlobsTemplateError("Template doesn't exist")

            database.add_blob_to_template(conn, template_name, blob_id, pos_set, blob_set, blob_title)
            conn.commit()
        except (IPOLBlobsDataBaseError, IntegrityError):
            conn.rollback()
            raise

    def create_thumbnail(self, src_file, blob_hash):
        """
        Creates a thumbnail for blob_file.
        """
        src_file = os.path.realpath(src_file)
        thumb_height = 256
        dst_path = os.path.join(self.thumb_dir, self.get_subdir(blob_hash))
        dst_file = os.path.join(dst_path, blob_hash + ".jpg")
        try:
            ipolutils.thumbnail(src_file, height=thumb_height, dst_file=dst_file)
        except Exception as ex:
            raise IPOLBlobsThumbnailError("File '{}', thumbnail error. {}".format(src_file, ex))

    def associate_tags_to_blob(self, conn, blob_id, tags):
        """
        Creates the tags and associate them to the blob
        """
        tag_list = set(map(str.strip, str(tags).split(",")))
        try:
            with self.lock:
                database.create_tags(conn, tag_list)
            database.add_tags_to_blob(conn, tag_list, blob_id)
            conn.commit()
        except (IPOLBlobsDataBaseError, IntegrityError):
            conn.rollback()
            raise

    @cherrypy.expose
    @authenticate
    def create_template(self, template_name):
        """
        Creates a new empty template
        """

        status = {"status": "KO"}
        conn = None
        try:
            conn = lite.connect(self.database_file)
            database.create_template(conn, template_name)
            conn.commit()
            status = {"status": "OK"}

        except IntegrityError as ex:
            print 'IntegrityError', ex
        except IPOLBlobsDataBaseError as ex:
            if conn is not None:
                conn.rollback()
            self.logger.exception("Fail creating template {}".format(template_name))
            print "Couldn't create the template {}. Error: {}".format(template_name, ex)
        except Exception as ex:
            if conn is not None:
                conn.rollback()
            self.logger.exception("*** Unhandled exception while creating the template {}".format(template_name))
            print "*** Unhandled exception while creating the template {}. Error: {}".format(template_name, ex)

        finally:
            if conn is not None:
                conn.close()
        return json.dumps(status)

    @cherrypy.expose
    @authenticate
    def add_templates_to_demo(self, demo_id, template_names):
        """
        Associates the demo to the list of templates
        """
        template_names_list = set(map(str.strip, str(template_names).split(",")))
        status = {"status": "KO"}
        conn = None
        try:
            conn = lite.connect(self.database_file)

            if not database.all_templates_exist(conn, template_names_list):
                raise IPOLBlobsTemplateError("Not all the templates exist")

            if not database.demo_exist(conn, demo_id):
                database.create_demo(conn, demo_id)

            database.add_templates_to_demo(conn, template_names_list, demo_id)
            conn.commit()
            status = {"status": "OK"}

        except IntegrityError as ex:
            print 'IntegrityError', ex
        except IPOLBlobsDataBaseError as ex:
            if conn is not None:
                conn.rollback()
            self.logger.exception("Fails linking templates {} to the demo #{}".format(template_names, demo_id))
            print "Couldn't link templates {} to the demo #{}. Error: {}".format(template_names, demo_id, ex)
        except IPOLBlobsTemplateError as ex:
            if conn is not None:
                conn.rollback()
            print "Some of the templates {} does not exist. Error: {}".format(template_names, ex)
        except Exception as ex:
            if conn is not None:
                conn.rollback()
            self.logger.exception("*** Unhandled exception while linking the templates {} to the demo #{}"
                                  .format(template_names, demo_id))
            print "*** Unhandled exception while linking the templates {} to the demo #{}. Error:{}" \
                .format(template_names, demo_id, ex)
        finally:
            if conn is not None:
                conn.close()
        return json.dumps(status)

    @cherrypy.expose
    def get_blobs(self, demo_id):
        """
        Get all the blobs of the demo, from owned blobs and templates
        """
        data = {"status": "KO"}
        conn = None
        try:
            conn = lite.connect(self.database_file)

            demo_blobs = database.get_demo_owned_blobs(conn, demo_id)
            templates = database.get_demo_templates(conn, demo_id)
            sets = self.prepare_list(demo_blobs)
            for template in templates:
                sets += self.prepare_list(database.get_template_blobs(conn, template))

            data["sets"] = sets
            data["status"] = "OK"

        except IntegrityError as ex:
            print 'IntegrityError', ex
        except IPOLBlobsDataBaseError as ex:
            self.logger.exception("Fails obtaining all the blobs from demo #{}".format(demo_id))
            print "Couldn't obtain all the blobs from demo #{}. Error: {}".format(demo_id, ex)
        except Exception as ex:
            self.logger.exception("*** Unhandled exception while obtaining all the blobs from demo #{}"
                                  .format(demo_id))
            print "*** Unhandled exception while obtaining all the blobs from demo #{}. Error: {}" \
                .format(demo_id, ex)
        finally:
            if conn is not None:
                conn.close()
        return json.dumps(data)

    def prepare_list(self, blobs):
        """
        Prepare the output list of blobs
        """
        sets = {}
        for blob in blobs:
            blob_set = blob["blob_set"]
            if blob_set in sets:
                sets[blob_set].append(self.get_blob_info(blob))
            else:
                sets[blob_set] = [self.get_blob_info(blob)]

        sorted_sets = sorted(sets.items(), key=operator.itemgetter(0))
        result = []
        for blob_set in sorted_sets:
            dic = {}
            for blob in blob_set[1]:
                position = blob['pos_set']
                del blob['pos_set']
                dic[position] = blob

            result.append({"name": blob_set[0], "blobs": dic})
        return result

    @cherrypy.expose
    def get_template_blobs(self, template_name):
        """
        Get the list of blobs for the template
        """
        data = {"status": "KO"}
        conn = None
        try:
            conn = lite.connect(self.database_file)

            if not database.template_exist(conn, template_name):
                # If the requested template doesn't exist the method will return a KO
                return json.dumps(data)

            sets = self.prepare_list(database.get_template_blobs(conn, template_name))

            data["sets"] = sets
            data["status"] = "OK"

        except IntegrityError as ex:
            print 'IntegrityError', ex
        except IPOLBlobsDataBaseError as ex:
            self.logger.exception("Fails obtaining the owned blobs from template '{}'".format(template_name))
            print "Couldn't obtain owned blobs from template '{}'. Error: {}".format(template_name, ex)
        except Exception as ex:
            self.logger.exception("*** Unhandled exception while obtaining the owned blobs from template '{}'"
                                  .format(template_name))
            print "*** Unhandled exception while obtaining the owned blobs from template '{}'. Error: {}" \
                .format(template_name, ex)
        finally:
            if conn is not None:
                conn.close()
        return json.dumps(data)

    @cherrypy.expose
    def get_demo_owned_blobs(self, demo_id):
        """
        Get the list of owned blobs for the demo
        """
        data = {"status": "KO"}
        conn = None
        try:
            conn = lite.connect(self.database_file)

            blobs = database.get_demo_owned_blobs(conn, demo_id)
            sets = self.prepare_list(blobs)
            data["sets"] = sets
            data["status"] = "OK"

        except IntegrityError as ex:
            print 'IntegrityError', ex
        except IPOLBlobsDataBaseError as ex:
            self.logger.exception("Fails obtaining the owned blobs from demo #{}".format(demo_id))
            print "Couldn't obtain owned blobs from demo #{}. Error: {}".format(demo_id, ex)
        except Exception as ex:
            self.logger.exception("*** Unhandled exception while obtaining the owned blobs from demo #{}"
                                  .format(demo_id))
            print "*** Unhandled exception while obtaining the owned blobs from demo #{}. Error: {}" \
                .format(demo_id, ex)
        finally:
            if conn is not None:
                conn.close()
        return json.dumps(data)

    def get_blob_info(self, blob):
        """
        Return the required information from the blob
        """
        subdir = self.get_subdir(blob['hash'])
        vr_physical_dir = os.path.join(self.vr_dir, subdir)
        thumb_physical_dir = os.path.join(self.thumb_dir, subdir)
        blob_physical_dir = os.path.join(self.blob_dir, subdir)

        vr_url = os.path.join('/api', 'blobs', vr_physical_dir)
        thumbnail_url = os.path.join('/api', 'blobs', thumb_physical_dir)
        blob_url = os.path.join('/api', 'blobs', blob_physical_dir)

        blob_info = {'id': blob['id'],
                     'title': blob['title'],
                     'blob': os.path.join(blob_url, blob['hash'] + blob['extension']),
                     'format': blob['format'],
                     'credit': blob['credit'],
                     'tags': blob['tags'],
                     'pos_set': blob['pos_set']}

        if os.path.isfile(os.path.join(self.module_dir, thumb_physical_dir, blob['hash'] + '.jpg')):
            blob_info['thumbnail'] = os.path.join(self.module_dir, thumbnail_url, blob['hash'] + '.jpg')

        vr_extension = self.get_vr_extension(os.path.join(self.module_dir, vr_physical_dir), blob['hash'])
        if vr_extension is not None:
            blob_info['vr'] = os.path.join(vr_url, blob['hash'] + vr_extension)

        return blob_info

    @staticmethod
    def get_vr_extension(vr_dir, blob_hash):
        """
        If the visual representation exists, the function returns its extension
        if not, returns None
        """
        vr_extension = None
        if os.path.isdir(vr_dir):

            file_without_extension = os.path.join(vr_dir, blob_hash)
            vr = glob.glob(file_without_extension + ".*")
            if vr:
                _, vr_extension = os.path.splitext(vr[0])

        return vr_extension

    @cherrypy.expose
    def get_demo_templates(self, demo_id):
        """
        Get the list of templates used by the demo
        """
        data = {"status": "KO"}
        conn = None
        try:
            conn = lite.connect(self.database_file)

            db_response = database.get_demo_templates(conn, demo_id)
            data["templates"] = db_response
            data["status"] = "OK"

        except IntegrityError as ex:
            print 'IntegrityError', ex
        except IPOLBlobsDataBaseError as ex:
            self.logger.exception("Fails obtaining the owned templates from demo #{}".format(demo_id))
            print "Couldn't obtain owned templates from demo #{}. Error: {}".format(demo_id, ex)
        except Exception as ex:
            self.logger.exception("*** Unhandled exception while obtaining the owned templates from demo #{}"
                                  .format(demo_id))
            print "*** Unhandled exception while obtaining the owned templates from demo #{}. Error: {}" \
                .format(demo_id, ex)
        finally:
            if conn is not None:
                conn.close()
        return json.dumps(data)

    @cherrypy.expose
    @authenticate
    def add_tags_to_blob(self, tags, blob_id):
        """
        Add a new to tag to the blob
        """
        data = {'status': 'KO'}
        conn = None
        try:
            conn = lite.connect(self.database_file)
            self.associate_tags_to_blob(conn, blob_id, tags)
            data['status'] = 'OK'

        except IntegrityError as ex:
            print 'IntegrityError', ex
        except IPOLBlobsDataBaseError as ex:
            self.logger.exception("Failed to add the tags to blob")
            print "Failed to add the tags to blob. DB Error: {}".format(ex)
        except Exception as ex:
            self.logger.exception("*** Unhandled exception while adding the tags to blob")
            print "*** Unhandled exception while adding the tags to blob. Error: {}" \
                .format(ex)
        finally:
            if conn is not None:
                conn.close()
        return json.dumps(data)

    def remove_blob(self, blob_set, pos_set, dest):
        """
        Remove the blob
        """
        res = False
        conn = None
        try:
            conn = lite.connect(self.database_file)
            if dest["dest"] == "demo":
                demo_id = dest["demo_id"]
                blob_data = database.get_blob_data_from_demo(conn, demo_id, blob_set, pos_set)
                database.remove_blob_from_demo(conn, demo_id, blob_set, pos_set)
            elif dest["dest"] == "template":
                template_name = dest["name"]
                blob_data = database.get_blob_data_from_template(conn, template_name, blob_set, pos_set)
                database.remove_blob_from_template(conn, template_name, blob_set, pos_set)
            else:
                self.logger.error("Failed to remove blob. Unknown dest: {}".format(dest["dest"]))
                return res

            if blob_data is None:
                return res

            blob_hash = blob_data.get('hash')
            blob_id = blob_data.get('id')
            if not database.is_blob_used(conn, blob_id):
                database.remove_blob(conn, blob_id)
                self.remove_files_associated_to_a_blob(blob_hash)
            conn.commit()
            res = True
        except IntegrityError as ex:
            print 'IntegrityError', ex
        except IPOLBlobsDataBaseError as ex:
            conn.rollback()
            self.logger.exception("DB error while removing blob")
            print "Failed to remove blob from DB. Error: {}".format(ex)
        except OSError as ex:
            conn.rollback()
            self.logger.exception("OS error while deleting blob file")
            print "Failed to remove blob from file system. Error: {}".format(ex)
        except IPOLRemoveDirError as ex:
            # There is no need to do a rollback if the problem was deleting directories
            self.logger.exception("Failed to remove directories")
            print "Failed to remove directories. Error: {}".format(ex)
        except Exception as ex:
            conn.rollback()
            self.logger.exception("*** Unhandled exception while removing the blob")
            print "*** Unhandled exception while removing the blob. Error: {}".format(ex)
        finally:
            if conn is not None:
                conn.close()
        return res

    @cherrypy.expose
    @authenticate
    def remove_blob_from_demo(self, demo_id, blob_set, pos_set):
        """
        Remove a blob from the demo
        """
        dest = {"dest": "demo", "demo_id": demo_id}
        if self.remove_blob(blob_set, pos_set, dest):
            return json.dumps({"status": "OK"})
        return json.dumps({"status": "KO"})

    @cherrypy.expose
    @authenticate
    def remove_blob_from_template(self, template_name, blob_set, pos_set):
        """
        Remove a blob from the template
        """
        dest = {"dest": "template", "name": template_name}
        if self.remove_blob(blob_set, pos_set, dest):
            return json.dumps({"status": "OK"})
        return json.dumps({"status": "KO"})

    def delete_blob_container(self, dest):
        """
        Remove the demo or template and all the blobs only used by them
        """
        res = False
        conn = None
        try:
            conn = lite.connect(self.database_file)
            if dest["dest"] == "demo":
                demo_id = dest["demo_id"]
                blobs = database.get_demo_owned_blobs(conn, demo_id)
                database.remove_demo_blobs_association(conn, demo_id)
                database.remove_demo(conn, demo_id)
            elif dest["dest"] == "template":
                template_name = dest["name"]
                blobs = database.get_template_blobs(conn, template_name)
                database.remove_template_blobs_association(conn, template_name)
                database.remove_template(conn, template_name)
            else:
                self.logger.error("Failed to remove blob. Unknown dest: {}".format(dest["dest"]))
                return res
            for blob in blobs:
                if not database.is_blob_used(conn, blob['id']):
                    database.remove_blob(conn, blob['id'])
                    self.remove_files_associated_to_a_blob(blob['hash'])

            conn.commit()
            res = True
        except OSError as ex:
            conn.rollback()
            self.logger.exception("OS error while deleting blob file")
            print "Failed to remove blob from file system. Error: {}".format(ex)
        except IPOLRemoveDirError as ex:
            # There is no need to do a rollback if the problem was deleting directories
            self.logger.exception("Failed to remove directories")
            print "Failed to remove directories. Error: {}".format(ex)
        except IntegrityError as ex:
            print 'IntegrityError', ex
        except IPOLBlobsDataBaseError as ex:
            conn.rollback()
            self.logger.exception("DB error while removing the demo/template")
            print "Failed to remove the demo/template. Error: {}".format(ex)
        except Exception as ex:
            conn.rollback()
            self.logger.exception("*** Unhandled exception while removing the demo/template")
            print "*** Unhandled exception while removing the demo/template. Error: {}".format(ex)
        finally:
            if conn is not None:
                conn.close()
        return res

    @cherrypy.expose
    @authenticate
    def delete_demo(self, demo_id):
        """
        Remove the demo
        """
        dest = {"dest": "demo", "demo_id": demo_id}
        if self.delete_blob_container(dest):
            return json.dumps({"status": "OK"})
        return json.dumps({"status": "KO"})

    @cherrypy.expose
    @authenticate
    def delete_template(self, template_name):
        """
        Remove the template
        """
        dest = {"dest": "template", "name": template_name}
        if self.delete_blob_container(dest):
            return json.dumps({"status": "OK"})
        return json.dumps({"status": "KO"})

    @cherrypy.expose
    @authenticate
    def remove_template_from_demo(self, demo_id, template_name):
        """
        Remove the template from the demo
        """
        data = {'status': 'KO'}
        conn = None
        try:
            conn = lite.connect(self.database_file)
            if database.remove_template_from_demo(conn, demo_id, template_name):
                conn.commit()
                data['status'] = 'OK'
        except IntegrityError as ex:
            print 'IntegrityError', ex
        except IPOLBlobsDataBaseError as ex:
            conn.rollback()
            self.logger.exception("DB error while removing the template from the demo")
            print "Failed to remove the template from the demo. Error: {}".format(ex)
        except Exception as ex:
            conn.rollback()
            self.logger.exception("*** Unhandled exception while removing the template from the demo")
            print "*** Unhandled exception while removing the template from the demo. Error: {}".format(ex)
        finally:
            if conn is not None:
                conn.close()
        return json.dumps(data)

    @cherrypy.expose
    @authenticate
    def remove_tag_from_blob(self, tag, blob_id):
        """
        Remove the tag from the blob
        """
        data = {'status': 'KO'}
        conn = None
        try:
            conn = lite.connect(self.database_file)
            database.remove_tag_from_blob(conn, tag, blob_id)
            conn.commit()
            data['status'] = 'OK'

        except IntegrityError as ex:
            print 'IntegrityError', ex
        except IPOLBlobsDataBaseError as ex:
            conn.rollback()
            self.logger.exception("DB error while removing the demo/template")
            print "Failed to remove the demo/template. Error: {}".format(ex)
        except Exception as ex:
            conn.rollback()
            self.logger.exception("*** Unhandled exception while removing the demo/template")
            print "*** Unhandled exception while removing the demo/template. Error: {}".format(ex)
        finally:
            if conn is not None:
                conn.close()
        return json.dumps(data)

    def remove_files_associated_to_a_blob(self, blob_hash):
        """
        This function removes the blob, the thumbnail and
        the visual representation from the hash given
        """
        subdir = self.get_subdir(blob_hash)

        blob_folder = os.path.join(self.module_dir, self.blob_dir, subdir)
        thumb_folder = os.path.join(self.module_dir, self.thumb_dir, subdir)
        vr_folder = os.path.join(self.module_dir, self.vr_dir, subdir)

        blob_file = glob.glob(os.path.join(blob_folder, blob_hash + ".*"))
        thumb_file = glob.glob(os.path.join(thumb_folder, blob_hash + ".*"))
        vr_file = glob.glob(os.path.join(vr_folder, blob_hash + ".*"))

        # remove blob and its folder if necessary
        if blob_file:
            os.remove(blob_file[0])
            self.remove_dirs(blob_folder)

        # remove thumbnail and its folder if necessary
        if thumb_file:
            os.remove(thumb_file[0])
            self.remove_dirs(thumb_folder)

        # remove visual representation and its folder if necessary
        if vr_file:
            os.remove(vr_file[0])
            self.remove_dirs(vr_folder)

    def remove_dirs(self, blob_folder):
        """
        Remove all the empty directories
        """
        try:
            if not os.listdir(blob_folder):
                os.rmdir(blob_folder)
                self.remove_dirs(os.path.dirname(blob_folder))
        except Exception as ex:
            raise IPOLRemoveDirError(ex)

    @staticmethod
    def generate_set_name(blob_id):
        """
        Generate a unique set name for the given blob id
        """
        return "__" + str(blob_id)

    @cherrypy.expose
    @authenticate
    def edit_blob_from_demo(self, demo_id=None, tags=None, blob_set=None, new_blob_set=None, pos_set=None,
                            new_pos_set=None, title=None, credit=None, vr=None):
        """
        Edit blob information in a demo
        """
        dest = {"dest": "demo", "demo_id": demo_id}
        if self.edit_blob(tags, blob_set, new_blob_set, pos_set, new_pos_set, title, credit, vr, dest):
            return json.dumps({"status": "OK"})
        return json.dumps({"status": "KO"})

    @cherrypy.expose
    @authenticate
    def edit_blob_from_template(self, template_name=None, tags=None, blob_set=None, new_blob_set=None, pos_set=None,
                                new_pos_set=None, title=None, credit=None, vr=None):
        """
        Edit blob information in a template
        """
        dest = {"dest": "template", "name": template_name}
        if self.edit_blob(tags, blob_set, new_blob_set, pos_set, new_pos_set, title, credit, vr, dest):
            return json.dumps({"status": "OK"})
        return json.dumps({"status": "KO"})

    def edit_blob(self, tags, blob_set, new_blob_set, pos_set, new_pos_set, title, credit, blob_vr, dest):
        """
        Edit blob information
        """
        res = False
        conn = None
        try:
            conn = lite.connect(self.database_file)
            if dest["dest"] == "demo":
                demo_id = dest["demo_id"]

                if new_pos_set != pos_set and \
                        database.is_pos_occupied_in_demo_set(conn, demo_id, blob_set, new_pos_set):
                    new_pos_set = database.get_max_pos_in_demo_set(conn, demo_id, blob_set) + 1

                database.edit_blob_from_demo(conn, demo_id, blob_set, new_blob_set, pos_set, new_pos_set, title, credit)
                blob_data = database.get_blob_data_from_demo(conn, demo_id, new_blob_set, new_pos_set)
            elif dest["dest"] == "template":
                template_name = dest["name"]

                if new_pos_set != pos_set and \
                        database.is_pos_occupied_in_template_set(conn, template_name, blob_set, new_pos_set):
                    new_pos_set = database.get_max_pos_in_template_set(conn, template_name, blob_set) + 1

                database.edit_blob_from_template(conn, template_name, blob_set, new_blob_set, pos_set, new_pos_set,
                                                 title, credit)
                blob_data = database.get_blob_data_from_template(conn, template_name, new_blob_set, new_pos_set)
            else:
                self.logger.error("Failed to edit blob. Unknown dest: {}".format(dest["dest"]))
                return res

            if blob_data is None:
                return res

            blob_hash = blob_data.get('hash')
            blob_id = blob_data.get('id')
            self.set_tags(conn, blob_id, tags)

            if blob_vr is not None:
                _, vr_ext = self.get_format_and_extension(self.get_blob_mime(blob_vr.file))

                blob_file = self.copy_blob(blob_vr.file, blob_hash, vr_ext, self.vr_dir)
                try:
                    self.create_thumbnail(blob_file, blob_hash)
                except IPOLBlobsThumbnailError as ex:
                    self.logger.exception("Error creating the thumbnail")
                    print "Couldn't create the thumbnail. Error: {}".format(ex)
            conn.commit()
            res = True

        except IntegrityError as ex:
            print 'IntegrityError', ex
        except IPOLBlobsDataBaseError as ex:
            conn.rollback()
            self.logger.exception("DB error while editing the blob")
            print "Failed editing the blob. Error: {}".format(ex)
        except Exception as ex:
            conn.rollback()
            self.logger.exception("*** Unhandled exception while editing the blob")
            print "*** Unhandled exception while editing the blob. Error: {}".format(ex)
        finally:
            if conn is not None:
                conn.close()
        return res

    def set_tags(self, conn, blob_id, tags):
        """
        Remove old tags and add the new ones
        """
        for tag in database.get_blob_tags(conn, blob_id):
            database.remove_tag(conn, tag)

        self.associate_tags_to_blob(conn, blob_id, tags)

    @cherrypy.expose
    def get_all_templates(self):
        """
        Return a list with all the templates
        """
        conn = None
        data = {'status': 'KO'}
        try:
            conn = lite.connect(self.database_file)
            data['templates'] = database.get_all_templates(conn)
            data['status'] = 'OK'
        except IntegrityError as ex:
            print 'IntegrityError', ex
        except IPOLBlobsDataBaseError as ex:
            self.logger.exception("DB error while reading all the templates")
            print "Failed reading all the templates. Error: {}".format(ex)
        except Exception as ex:
            self.logger.exception("*** Unhandled exception while reading all the templates")
            print "*** Unhandled exception while reading all the templates. Error: {}".format(ex)
        finally:
            if conn is not None:
                conn.close()
        return json.dumps(data)

    @cherrypy.expose
    @authenticate
    def delete_vr_from_blob(self, blob_id):
        """
        Remove the visual representation of the blob (in all the demos and templates)
        """
        data = {'status': 'KO'}
        conn = None
        try:
            conn = lite.connect(self.database_file)
            blob_data = database.get_blob_data(conn, blob_id)
            if blob_data is None:
                return json.dumps(data)

            blob_hash = blob_data.get('hash')
            subdir = self.get_subdir(blob_hash)

            # Delete VR
            vr_folder = os.path.join(self.vr_dir, subdir)
            if os.path.isdir(vr_folder):
                files_in_dir = glob.glob(os.path.join(vr_folder, blob_hash + ".*"))
                if files_in_dir:
                    os.remove(files_in_dir[0])
                    self.remove_dirs(vr_folder)

            # Delete old thumbnail
            thumb_folder = os.path.join(self.module_dir, self.thumb_dir, subdir)
            if os.path.isdir(thumb_folder):
                thumb_files_in_dir = glob.glob(os.path.join(thumb_folder, blob_hash + ".*"))
                if thumb_files_in_dir:
                    os.remove(thumb_files_in_dir[0])
                    self.remove_dirs(thumb_folder)

            # Creates the new thumbnail with the blob (if it is possible)
            try:
                blob_folder = os.path.join(self.blob_dir, subdir)
                if os.path.isdir(blob_folder):
                    blobs_in_dir = glob.glob(os.path.join(blob_folder, blob_hash + ".*"))
                    if blobs_in_dir:
                        self.create_thumbnail(blobs_in_dir[0], blob_hash)
            except IPOLBlobsThumbnailError as ex:
                self.logger.exception("Error creating the thumbnail")
                print "Couldn't create the thumbnail. Error: {}".format(ex)

        except IntegrityError as ex:
            print 'IntegrityError', ex
        except IPOLBlobsDataBaseError as ex:
            self.logger.exception("DB error while removing the visual representation")
            print "Failed removing the visual representation. Error: {}".format(ex)
        except Exception as ex:
            mess = "*** Unhandled exception while removing the visual representation."
            self.logger.exception(mess)
            print "{} Error: {}".format(mess, ex)
        finally:
            if conn is not None:
                conn.close()

        data['status'] = 'OK'
        return json.dumps(data)

    @cherrypy.expose
    @authenticate
    def update_demo_id(self, old_demo_id, new_demo_id):
        """
        Update the given old demo id by the given new demo id.
        """
        conn = None
        data = {'status': 'KO'}
        try:
            conn = lite.connect(self.database_file)
            database.update_demo_id(conn, old_demo_id, new_demo_id)
            data['status'] = 'OK'
            conn.commit()
        except IntegrityError as ex:
            print 'IntegrityError', ex
        except IPOLBlobsDataBaseError as ex:
            conn.rollback()
            self.logger.exception("DB error while updating demo id")
            print "Failed while updating demo id. Error: {}".format(ex)
        except Exception as ex:
            conn.rollback()
            self.logger.exception("*** Unhandled exception while updating demo id")
            print "*** Unhandled exception while updating demo id. Error: {}".format(ex)
        finally:
            if conn is not None:
                conn.close()
        return json.dumps(data)

    @cherrypy.expose
    def get_blobs_location(self, blobs_ids):
        """
        Return the physical location of the blobs
        """
        conn = None
        data = {'status': 'KO'}
        try:
            conn = lite.connect(self.database_file)
            blobs_ids_list = blobs_ids if isinstance(blobs_ids, list) else [int(blobs_ids)]
            physical_locations = []

            for blob_id in blobs_ids_list:
                blob = database.get_blob_data(conn, blob_id)
                subdir = self.get_subdir(blob['hash'])
                blob_physical_dir = os.path.join(self.blob_dir, subdir)
                physical_locations.append(os.path.join(blob_physical_dir, blob['hash'] + blob['extension']))

            data['physical_locations'] = physical_locations
            data['status'] = 'OK'
        except IntegrityError as ex:
            print 'IntegrityError', ex
        except IPOLBlobsDataBaseError as ex:
            self.logger.exception("DB operation failed while getting blob location")
            print "DB operation failed while getting blob location. Error: {}".format(ex)
        except Exception as ex:
            conn.rollback()
            self.logger.exception("*** Unhandled exception while getting blob location")
            print "*** Unhandled exception while getting blob location. Error: {}".format(ex)
        finally:
            if conn is not None:
                conn.close()
        return json.dumps(data)

    @cherrypy.expose
    def get_demos_using_the_template(self, template_name):
        """
        Return the list of demos that use the given template
        """
        conn = None
        data = {'status': 'KO'}
        try:
            conn = lite.connect(self.database_file)
            data['demos'] = database.get_demos_using_the_template(conn, template_name)
            data['status'] = 'OK'
        except IntegrityError as ex:
            print 'IntegrityError', ex
        except IPOLBlobsDataBaseError as ex:
            self.logger.exception("DB operation failed while getting the list of demos that uses the template")
            print "DB operation failed while getting the list of demos that uses the template. Error: {}".format(ex)
        except Exception as ex:
            conn.rollback()
            self.logger.exception("*** Unhandled exception while getting the list of demos that uses the template")
            print "*** Unhandled exception while getting the list of demos that uses the template. Error: {}".format(ex)
        finally:
            if conn is not None:
                conn.close()
        return json.dumps(data)

    @cherrypy.expose
    def stats(self):
        """
        Return module stats
        """
        conn = None
        data = {'status': 'KO'}
        try:
            conn = lite.connect(self.database_file)
            data['nb_templates'] = len(database.get_all_templates(conn))
            data['nb_blobs'] = database.get_nb_of_blobs(conn)
            data['nb_tags'] = database.get_nb_of_tags(conn)
            data['status'] = 'OK'
        except Exception as ex:
            self.logger.exception("*** Unhandled exception while getting the blobs stats")
            print "*** Unhandled exception while getting the blobs stats. Error: {}".format(ex)
        finally:
            if conn is not None:
                conn.close()
        return json.dumps(data)

    # ----------- DEPRECATED FUNCTIONS ---------------
    # This functions are for the OLD web interface and
    # they shouldn't be called by new methods.
    # [TODO] Get rid of these functions

    @cherrypy.expose
    def get_blobs_deprecated(self, demo_name):
        """
        DEPRECATED - Return all demo blobs for the old interface
        """
        data = {"status": "KO"}
        conn = None
        try:
            conn = lite.connect(self.database_file)
            demo_blobs = database.get_demo_owned_blobs(conn, demo_name)
            templates = database.get_demo_templates(conn, demo_name)
            sets = self.prepare_list_deprecated(demo_blobs)
            for template in templates:
                sets += self.prepare_list_deprecated(database.get_template_blobs(conn, template))

            data["blobs"] = sets
            data["status"] = "OK"
            data["url"] = "/api/blobs/staticData/blob_directory/"
            data['url_visrep'] = "/api/blobs/staticData/visrep/"
            data["vr_location"] = "staticData/visrep"
            data[demo_name] = {'is_template': 0, 'name': str(demo_name), 'template_id': 0}
            data['use_template'] = {}
            data["url_thumb"] = "/api/blobs/staticData/thumbnail/"
            data['physical_location'] = "staticData/blob_directory"

        except IntegrityError as ex:
            print 'IntegrityError', ex
        except IPOLBlobsDataBaseError as ex:
            self.logger.exception("Fails obtaining the blobs from demo #{}".format(demo_name))
            print "Couldn't obtain the blobs from demo #{}. Error: {}".format(demo_name, ex)
        except Exception as ex:
            self.logger.exception("*** Unhandled exception while obtaining the blobs from demo #{}"
                                  .format(demo_name))
            print "*** Unhandled exception while obtaining the blobs from demo #{}. Error: {}" \
                .format(demo_name, ex)
        finally:
            if conn is not None:
                conn.close()
        return json.dumps(data)

    def prepare_list_deprecated(self, blobs):
        """
        DEPRECATED - Prepare the output list of blobs
        """
        sets = {}
        for blob in blobs:
            blob_set = blob["blob_set"]
            if blob_set in sets:
                sets[blob_set].append(self.get_blob_info_deprecated(blob))
            else:
                sets[blob_set] = [self.get_blob_info_deprecated(blob)]

        sorted_sets = sorted(sets.items(), key=operator.itemgetter(0))
        result = []
        for element in sorted_sets:
            blob_set = [{'set_name': element[0], 'size': len(element[1])}]

            for blob in element[1]:
                dic = {
                    'credit': blob['credit'],
                    'tag': ','.join(blob['tags']),
                    'hash': blob['hash'],
                    'extension': blob['extension'],
                    'pos_in_set': blob['pos_set'],
                    'format': blob['format'],
                    'title': blob['title'],
                    'id': blob['id'],
                    'subdirs': blob['subdir'],

                }
                if 'vr' in blob:
                    dic['extension_visrep'] = blob['vr']
                blob_set.append(dic)

            result.append(blob_set)
        return result

    def get_blob_info_deprecated(self, blob):
        """
        DEPRECATED - Return the required information from the blob
        """
        subdir = self.get_subdir(blob['hash'])
        vr_physical_dir = os.path.join(self.vr_dir, subdir)

        blob_info = {'title': blob['title'],
                     'hash': blob['hash'],
                     'extension': blob['extension'],
                     'format': blob['format'],
                     'credit': blob['credit'],
                     'tags': blob['tags'],
                     'subdir': subdir + "/",
                     'id': blob['id'],
                     'pos_set': blob['pos_set']}

        vr_extension = self.get_vr_extension(os.path.join(self.module_dir, vr_physical_dir), blob['hash'])
        if vr_extension is not None:
            blob_info['vr'] = vr_extension

        return blob_info

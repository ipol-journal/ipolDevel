#!/usr/bin/python
# -*- coding:utf-8 -*-

# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.

"""
This microservices stores the experiments made with data uploaded by
the users.
"""
from collections import OrderedDict
import sqlite3 as lite
import sys
import errno
import hashlib
import logging
import json
import os
import os.path
import shutil
import ConfigParser
import re
import magic
import cherrypy

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
        archive = Archive.get_instance()
        patterns = []
        # Creates the patterns  with regular expresions
        for authorized_pattern in archive.authorized_patterns:
            patterns.append(re.compile(authorized_pattern.replace(".", "\\.").replace("*", "[0-9]*")))
        # Compare the IP with the patterns
        for pattern in patterns:
            if pattern.match(ip) is not None:
                return True
        return False

    return authenticate_and_call


class Archive(object):
    """
    This class implement an archive system for experiments and
    calculations done with the IPOL demo image system.
    """
    #####
    # initialization and static methods.
    #####

    instance = None

    @staticmethod
    def get_instance():
        """
        Singleton pattern
        """
        if Archive.instance is None:
            Archive.instance = Archive()
        return Archive.instance

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
        if not (cherrypy.config.has_key("blobs_dir")
                and cherrypy.config.has_key("database_dir")
                and cherrypy.config.has_key("blobs_thumbs_dir")
                and cherrypy.config.has_key("logs_dir")
                and cherrypy.config.has_key("url")):
            print "Missing elements in configuration file."
            return False
        return True

    @staticmethod
    def get_hash_blob(path):
        """
        Return sha1 hash of given blob
        """
        with open(path, 'rb') as the_file:
            return hashlib.sha1(the_file.read()).hexdigest()

    @staticmethod
    def file_format(the_file):
        """
        Return format of the file
        """
        mime = magic.Magic(mime=True)
        fileformat = mime.from_file(the_file)
        fileformat = fileformat.split('/')[0]
        return fileformat

    def __init__(self):
        """
        Initialize Archive class.
        Attribute status should be checked after each initialisation.
        It is false if something went wrong.
        """

        if not self.check_config():
            sys.exit(1)

        self.blobs_dir = cherrypy.config.get("blobs_dir")
        self.blobs_thumbs_dir = cherrypy.config.get("blobs_thumbs_dir")
        self.database_dir = cherrypy.config.get("database_dir")

        self.logs_dir = cherrypy.config.get("logs_dir")
        self.url = cherrypy.config.get("url")
        self.config_common_dir = cherrypy.config.get("config_common_dir")

        try:
            self.number_of_experiments_by_pages = \
                int(cherrypy.config.get("number_of_experiments_by_pages"))
        except Exception:
            self.number_of_experiments_by_pages = 10

        self.mkdir_p(self.database_dir)
        self.mkdir_p(self.blobs_dir)
        self.mkdir_p(self.blobs_thumbs_dir)

        # Logs
        try:
            if not os.path.exists(self.logs_dir):
                os.makedirs(self.logs_dir)
            self.logger = self.init_logging()
        except Exception as ex:
            print "Failed to create log dir. Error: {}".format(ex)

        # Security: authorized IPs
        self.authorized_patterns = self.read_authorized_patterns()

        try:
            self.database_name = cherrypy.config.get("database_name")
        except Exception:
            self.database_name = "archive.db"

        self.database_file = os.path.join(self.database_dir, self.database_name)

        if not self.init_database():
            sys.exit("Initialization of database failed. Check the logs.")

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

    def init_logging(self):
        """
        Initialize the error logs of the module.
        """
        logger = logging.getLogger("archive_log")
        logger.setLevel(logging.ERROR)
        handler = logging.FileHandler(os.path.join(self.logs_dir, 'error.log'))
        formatter = logging.Formatter('%(asctime)s ERROR in %(message)s', datefmt='%Y-%m-%d %H:%M:%S')
        handler.setFormatter(formatter)
        logger.addHandler(handler)
        return logger

    def error_log(self, function_name, error):
        """
        Write an error log in the logs_dir defined in archive.conf
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
                print str(self.database_file) + ' is empty. Removing the file...'
                try:
                    self.error_log("init_database", 'Database file was empty')
                    os.remove(self.database_file)
                except Exception as ex:
                    message = "Error in init_database. Error = {}".format(ex)
                    self.logger.exception(message)
                    return False

                print "Creating a correct new database"

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
                message = "Error in init_database. Error = {}".format(ex)
                self.logger.exception(message)
                if os.path.isfile(self.database_file):
                    try:
                        os.remove(self.database_file)
                    except Exception as ex:
                        message = "Error in init_database. Error = {}".format(ex)
                        self.logger.exception(message)
                        return False

        return True

    #####
    # adding an experiment to the archive database
    #####

    @staticmethod
    def get_new_path(main_directory, hash_name, file_extension, depth=2):
        """
        This method creates a new fullpath to store the blobs in the archive,
        where new directories are created for each 'depth' first letters
        of the hash, for example:
        input  is /tmp/abvddff.png
        output is /tmp/a/b/abvddff.png
        where the full path /tmp/a/b/ has been created
        returns this new_path and the subdirectory (a/b/) if depth = 2
        """
        l = min(len(hash_name), depth)

        subdirs = '/'.join(list(hash_name[:l]))
        new_directory_name = main_directory + subdirs + '/'

        if not os.path.isdir(new_directory_name):
            os.makedirs(new_directory_name)

        new_path = new_directory_name + hash_name + "." + file_extension

        return new_path, subdirs

    def copy_file_in_folder(self, original_path, main_dir, hash_file, extension):
        """
        Write a file in its respective folder
        """
        try:
            final_path, _ = self.get_new_path(main_dir, hash_file, extension)
            shutil.copyfile(original_path, final_path)
            return final_path
        except Exception as ex:
            message = "Failure in copy_file_in_folder. Error={}".format(ex)
            self.logger.exception(message)
            print message
            raise

    def add_blob_in_the_database(self, conn, hash_file, type_file, format_file):
        """
        check if a blob already exists in the database. If not, we include it
        return the id of the blob
        """
        try:
            cursor_db = conn.cursor()
            #First, we check if the blob is already in the database
            query = cursor_db.execute("""
                SELECT id FROM blobs WHERE hash = ?
                """, (hash_file,))
            row = query.fetchone()
            if row is not None:
                return int(row[0])

            cursor_db.execute("""
                INSERT INTO blobs(hash, type, format) VALUES(?, ?, ?)
                """, (hash_file, type_file, format_file,))
            # get id of the blob previously inserted
            return int(str(cursor_db.lastrowid))
        except Exception as ex:
            message = "Failure in add_blob_in_the_database. Error = {}".format(ex)
            self.logger.exception(message)
            raise

    def add_blob(self, conn, blob_dict, copied_files_list):
        """
        This function checks if a blob exists in the table. If it exists,
        the id is returned. If not, the blob is added, then the id is returned.
        """
        # List of copied files. Useful to delete them if an exception is thrown
        # copied_files = []
        try:
            thumb_key = list(key for key, value in blob_dict.iteritems() if 'thumbnail' in key)
            if thumb_key:
                blob_thumbnail_name = thumb_key[0]
                blob_thumbnail_path = blob_dict[blob_thumbnail_name]
                del blob_dict[blob_thumbnail_name]

            blob_name = blob_dict.keys()[0]
            blob_path = blob_dict.values()[0]

            # If the file doesn't exist, just return None
            if not os.path.isfile(blob_path):
                return None, None

            hash_file = self.get_hash_blob(blob_path)
            format_file = self.file_format(blob_path)

            _, type_file = os.path.splitext(blob_path)
            type_file = type_file.split('.')[1]
            type_file.lower()

            id_blob = self.add_blob_in_the_database(conn, hash_file, type_file, format_file)
            #copy the files in their respective folders
            path_new_blob = self.copy_file_in_folder(blob_path, self.blobs_dir, hash_file, type_file)
            copied_files_list.append(path_new_blob)
            if thumb_key:
                path_new_thumbnail = self.copy_file_in_folder(blob_thumbnail_path, self.blobs_thumbs_dir, hash_file, "jpeg")
                copied_files_list.append(path_new_thumbnail)

            return id_blob, blob_name
        except Exception as ex:
            message = "Failure in add_blob. Error = {}".format(ex)
            self.logger.exception(message)
            print message
            raise

    @staticmethod
    def update_exp_table(conn, demo_id, parameters, execution):
        """
        This function update the experiment table
        """
        cursor_db = conn.cursor()
        cursor_db.execute("""
        INSERT INTO
        experiments (id_demo, params, execution, timestamp)
        VALUES (?, ?, ?,datetime(CURRENT_TIMESTAMP, 'localtime'))""", (demo_id, parameters, execution))
        return int(cursor_db.lastrowid)


    def update_blob(self, conn, blobs, copied_files_list):
        """
        This function updates the blobs table.
        It return a dictionary of data to be added to the correspondences table.
        """
        try:
            id_blob = int()
            dict_blobs = json.loads(blobs)
            dict_corresp = []

            for blob_element in dict_blobs:
                id_blob, blob_name = self.add_blob(conn, blob_element, copied_files_list)
                dict_corresp.append({'blob_id': id_blob, 'blob_name': blob_name})

        except Exception as ex:
            self.logger.exception("update_blob. Error {}".format(ex))
            raise

        return dict_corresp

    @staticmethod
    def update_correspondence_table(conn, id_experiment, dict_corresp):
        """
        This function update the correspondence table, associating
                blobs, experiments, and descriptions of blobs.
        """
        cursor_db = conn.cursor()
        for order_exp, item in enumerate(dict_corresp):
            cursor_db.execute("""
            INSERT INTO
            correspondence (id_experiment, id_blob, name, order_exp)
            VALUES (?, ?, ?, ?)""", (id_experiment, item['blob_id'], item['blob_name'], order_exp))

    @cherrypy.expose
    @authenticate
    def add_experiment(self, demo_id, blobs, parameters, execution=None):
        """
        This function adds an experiment with all its data to the archive.
        """
        data = {"status": "OK"}
        # initialize list of copied files, to delete them in case of exception
        copied_files_list = []
        try:
            demo_id = int(demo_id)
            conn = lite.connect(self.database_file)
            id_experiment = self.update_exp_table(conn, demo_id, parameters, execution)
            data["id_experiment"] = id_experiment
            dict_corresp = {}
            dict_corresp = self.update_blob(conn, blobs, copied_files_list)
            self.update_correspondence_table(conn, id_experiment, dict_corresp)
            conn.commit()
            conn.close()
        except Exception as ex:
            message = "Failure in add_experiment. Error = {}".format(ex)
            self.logger.exception(message)
            data["status"] = "KO"
            try:
                # Execute database rollback
                conn.rollback()
                conn.close()

                # Execute deletion of copied files
                for copied_file in copied_files_list:
                    os.remove(copied_file)

            except Exception:
                pass

        return json.dumps(data)

    #####
    # displaying a single experiment of archive
    #####

    @cherrypy.expose
    def get_experiment(self, experiment_id):
        """
        Get requested experiment
        """
        # id_demo = int(demo_id)
        experiment_id = int(experiment_id)

        data = {"status": "OK"}
        conn = None
        try:
            conn = lite.connect(self.database_file)
            cursor_db = conn.cursor()
            cursor_db.execute("""SELECT params, execution, timestamp
                FROM experiments WHERE id = ?""", (experiment_id,))
            row = cursor_db.fetchone()
            data['experiment'] = self.get_data_experiment(conn, experiment_id, row[0], row[1], row[2])
            conn.close()
        except Exception as ex:
            data["status"] = "KO"
            self.error_log("get_experiment", str(ex))

            if conn is not None:
                conn.close()

        return json.dumps(data)

    #####
    # displaying a page of archive
    #####
    def get_meta_info(self, conn, id_demo):
        """
        This function return the number of archive pages to be displayed
        for a given demo, and the number of experiments done with
        this demo.
        """
        meta_info = {}

        meta_info["number_of_experiments_in_a_page"] = self.number_of_experiments_by_pages

        cursor_db = conn.cursor()

        cursor_db.execute("""
        SELECT COUNT(*) FROM experiments WHERE id_demo = ?""", (id_demo,))

        number_of_experiments = cursor_db.fetchone()[0]
        meta_info["number_of_experiments"] = number_of_experiments

        if number_of_experiments == 0:
            meta_info["first_date_of_an_experiment"] = 'never'
            meta_info["number_of_pages"] = 0
            return meta_info

        cursor_db.execute("""
        SELECT timestamp
        FROM experiments WHERE id_demo = ?
        ORDER BY timestamp """, (id_demo,))

        first_date_of_an_experiment = cursor_db.fetchone()[0]

        if number_of_experiments % self.number_of_experiments_by_pages != 0:
            pages_to_add = 1
        else:
            pages_to_add = 0

        number_of_pages = \
            (number_of_experiments / self.number_of_experiments_by_pages) + \
            pages_to_add

        meta_info["first_date_of_an_experiment"] = first_date_of_an_experiment
        meta_info["number_of_pages"] = number_of_pages

        return meta_info

    def get_dict_file(self, path_file, path_thumb, name, id_blob):
        """
        Build a dict containing the path to the file, the path to the thumb
                and the name of the file.
        """
        dict_file = {}
        dict_file["url"] = self.url + path_file
        dict_file["name"] = name
        dict_file["id"] = id_blob

        if os.path.exists(path_thumb):
            dict_file["url_thumb"] = self.url + path_thumb

        return dict_file

    def get_data_experiment(self, conn, id_exp, parameters, execution, date):
        """
        Build a dictionnary containing all the datas needed on a given
                experiment for building the archive page.
        """
        dict_exp = {}
        list_files = []
        path_file = str()
        path_thumb = str()

        try:
            cursor_db = conn.cursor()
            cursor_db.execute("""
                SELECT blb.hash, blb.type, cor.name, blb.id FROM blobs blb
                INNER JOIN correspondence cor ON blb.id=cor.id_blob
                INNER JOIN experiments exp ON cor.id_experiment=exp.id
                WHERE id_experiment = ? ORDER by cor.order_exp """, (id_exp,))

            all_rows = cursor_db.fetchall()

            for row in all_rows:
                path_file, subdirs = self.get_new_path(self.blobs_dir, row[0], row[1])
                thumb_dir = '{}/{}'.format(self.blobs_thumbs_dir, subdirs)
                thumb_name = '{}.jpeg'.format(row[0])
                path_thumb = os.path.join(thumb_dir, thumb_name)
                list_files.append(self.get_dict_file(path_file, path_thumb, row[2], row[3]))

            dict_exp["id"] = id_exp
            dict_exp["date"] = date
            dict_exp["parameters"] = json.loads(parameters, object_pairs_hook=OrderedDict)
            dict_exp["execution"] = execution
            dict_exp["files"] = list_files
            return dict_exp
        except Exception as ex:
            message = "Failure in get_data_experiment. Error = {}".format(ex)
            print message
            self.logger.exception(message)
            raise

    def get_experiment_page(self, conn, id_demo, page):
        """
        This function return a list of dicts with all the informations needed
                for displaying the experiments on a given page.
        """
        data_exp = []
        cursor_db = conn.cursor()
        starting_index = ((page - 1) * self.number_of_experiments_by_pages)

        cursor_db.execute("""
        SELECT id, params, execution, timestamp
        FROM experiments WHERE id_demo = ?
        ORDER BY timestamp
        LIMIT ? OFFSET ?""", (id_demo, self.number_of_experiments_by_pages, starting_index,))

        all_rows = cursor_db.fetchall()

        for row in all_rows:
            data_exp.append(self.get_data_experiment(conn, row[0], row[1], row[2], row[3]))

        return data_exp

    @cherrypy.expose
    def get_page(self, demo_id, page='1'):
        """
        This function return all the information needed
        to build the given page for the given demo.
        if the page number is not in the range [1,number_of_pages],
        the last page is used
        """
        id_demo = int(demo_id)
        page = int(page)
        data = {}
        data["status"] = "OK"
        try:
            conn = lite.connect(self.database_file)

            meta_info = self.get_meta_info(conn, id_demo)
            meta_info["id_demo"] = id_demo

            if meta_info["number_of_experiments"] == 0:
                data["meta"] = meta_info
                data["experiments"] = {}
                data["status"] = "OK"
                return json.dumps(data)

            if page > meta_info["number_of_pages"] or page <= 0:
                page = meta_info["number_of_pages"]
                experiments = self.get_experiment_page(conn, id_demo, page)

            else:
                experiments = self.get_experiment_page(conn, id_demo, page)

            data["meta"] = meta_info
            data["experiments"] = experiments

            conn.close()

        except Exception as ex:
            data["status"] = "KO"
            self.error_log("get_page", str(ex))
            try:
                conn.close()
            except Exception:
                pass

        return json.dumps(data)

    #####
    # deleting an experiment
    #####

    def delete_blob(self, conn, id_blob):
        """
        This function delete the given id_blob, in the database and physically.
        """
        cursor_db = conn.cursor()
        cursor_db.execute("SELECT * FROM blobs WHERE id = ?", (id_blob,))
        tmp = cursor_db.fetchone()

        # get the new path of the blob and thumbnail
        path_blob = None
        path_thumb = None
        if tmp is not None:
            path_blob, _ = self.get_new_path(self.blobs_dir, tmp[1], tmp[2])
            path_thumb, _ = self.get_new_path(self.blobs_thumbs_dir, tmp[1], 'jpeg')

        cursor_db.execute("DELETE FROM blobs WHERE id = ?", (id_blob,))

        # delete the files of this blob
        try:
            os.remove(path_blob)
            os.remove(path_thumb)
        except Exception:
            pass

    def purge_unique_blobs(self, conn, ids_blobs, experiment_id):
        """
        This function checks if the blobs are used only in this experiment.
                If this is the case, they are deleted both in the database
                and physically.
        """
        cursor_db = conn.cursor()

        for blob in ids_blobs:
            cursor_db.execute("""SELECT COUNT(*) FROM correspondence WHERE id_blob = ? AND id_experiment <> ?""",
                              (blob, experiment_id,))
            if cursor_db.fetchone()[0] == 0:
                self.delete_blob(conn, blob)

    def delete_exp_w_deps(self, conn, experiment_id):
        """
        This function remove, in the database, an experiment from
                the experiments table, and its dependencies in the correspondence
                table. If the blobs are used only by this experiment, they will be
                removed too.
        """
        ids_blobs = []
        cursor_db = conn.cursor()
        cursor_db.execute("""
        PRAGMA foreign_keys=ON""")

        # save a list of blobs used by the experiment
        for row in cursor_db.execute("SELECT * FROM correspondence where id_experiment = ?", (experiment_id,)):
            ids_blobs.append(row[2])

        self.purge_unique_blobs(conn, ids_blobs, experiment_id)

        cursor_db.execute("DELETE FROM experiments WHERE id = ?", (experiment_id,))
        n_changes = cursor_db.rowcount
        cursor_db.execute("DELETE FROM correspondence WHERE id_experiment = ?", (experiment_id,))

        return n_changes

    @cherrypy.expose
    @authenticate
    def delete_experiment(self, experiment_id):
        """
        Remove an experiment
        """
        status = {"status": "KO"}
        try:
            conn = lite.connect(self.database_file)
            if self.delete_exp_w_deps(conn, experiment_id) > 0:
                conn.commit()
                conn.close()
                status["status"] = "OK"

        except Exception as ex:
            self.error_log("delete_experiment", str(ex))
            print traceback.format_exc()
            try:
                conn.rollback()
                conn.close()
            except Exception as ex:
                pass

        return json.dumps(status)

    #####
    # deleting a blob
    #####

    @cherrypy.expose
    @authenticate
    def delete_blob_w_deps(self, id_blob):
        """
        Remove a blob
        """
        status = {"status": "KO"}
        try:
            conn = lite.connect(self.database_file)
            cursor_db = conn.cursor()
            list_tmp = []

            for row in cursor_db.execute("""
SELECT id_experiment FROM correspondence WHERE id_blob = ?""", \
                                         (id_blob,)):
                tmp = unicode(str(row[0]), "utf-8")
                list_tmp.append(tmp)

            for value in list_tmp:
                self.delete_exp_w_deps(conn, value)

            conn.commit()
            conn.close()
            status["status"] = "OK"
        except Exception as ex:
            self.error_log("delete_blob_w_deps", str(ex))
            try:
                conn.rollback()
                conn.close()
            except Exception as ex:
                pass
        return json.dumps(status)

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
        """
        return the stats of the module.
        """
        data = {}
        data["status"] = "KO"
        conn = None
        try:
            conn = lite.connect(self.database_file)
            cursor_db = conn.cursor()

            cursor_db.execute("""
                SELECT
                (SELECT COUNT(*) FROM experiments),
                (SELECT COUNT(*) FROM blobs)
             """)
            results = cursor_db.fetchall()
            data["nb_experiments"] = results[0][0]
            data["nb_blobs"] = results[0][1]
            data["status"] = "OK"

        except Exception as ex:
            message = "Failure in stats function. Error: {}".format(ex)
            print message
            self.logger.exception(message)
        finally:
            if conn is not None:
                conn.close()

        return json.dumps(data)

    @cherrypy.expose
    @staticmethod
    def index():
        """
        Small index for the archive.
        """
        return "This is the IPOL Archive module"

    @cherrypy.expose
    @staticmethod
    def default(attr):
        """
        Default method invoked when asked for non-existing service.
        """
        data = {}
        data["status"] = "KO"
        data["message"] = "Unknown service '{}'".format(attr)
        return json.dumps(data)


    @cherrypy.expose
    def demo_list(self):
        """
        return the list of demos with experiments.
        """
        data = {"status": "KO"}
        demo_list = list()

        try:
            conn = lite.connect(self.database_file)
            cursor_db = conn.cursor()
            cursor_db.execute("""
            SELECT DISTINCT id_demo FROM experiments""")

            for row in cursor_db.fetchall():
                demoid = row[0]
                demo_list.append(demoid)

            data["demo_list"] = demo_list
            data["status"] = "OK"
        except Exception as ex:
            message = "Failure in demo_list. Error = {}".format(ex)
            self.logger.exception(message)
            data["error"] = message
            try:
                conn.close()
            except Exception as ex:
                pass
        return json.dumps(data)

    @cherrypy.expose
    @authenticate
    def delete_demo(self, demo_id):
        """
        Delete the demo from the archive.
        """
        status = {"status": "KO"}
        try:
            # Get all experiments for this demo
            conn = lite.connect(self.database_file)
            cursor_db = conn.cursor()
            cursor_db.execute("SELECT DISTINCT id FROM experiments WHERE id_demo = ?", (demo_id,))

            experiment_id_list = cursor_db.fetchall()

            if not experiment_id_list:
                return json.dumps(status)

            # Delete experiments and files
            for experiment_id in experiment_id_list:
                self.delete_exp_w_deps(conn, experiment_id[0])

            conn.commit()
            conn.close()
            status["status"] = "OK"

        except Exception as ex:
            self.error_log("delete_demo", str(ex))
            try:
                conn.rollback()
                conn.close()
            except Exception as ex:
                pass

        return json.dumps(status)

    @cherrypy.expose
    def update_demo_id(self, old_demo_id, new_demo_id):
        """
        Change the given old demo id by the new demo id.
        """

        conn = None
        try:
            conn = lite.connect(self.database_file)
            cursor_db = conn.cursor()

            cursor_db.execute("""
            UPDATE experiments
            SET id_demo = ?
            WHERE id_demo = ?
            """, (new_demo_id, old_demo_id))

            conn.commit()
            conn.close()
            status = {"status": "OK"}

            return json.dumps(status)

        except Exception as ex:
            status = {"status": "KO"}
            status = {"error": "blobs update_demo_id error: {}".format(ex)}
            self.error_log("update_demo_id", str(ex))
            if conn is not None:
                conn.rollback()
                conn.close()

            return json.dumps(status)

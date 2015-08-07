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

# Module written by Alexis Mongin. Contact : alexis.mongin #~AT~# outlook.com

"""
This module is an archive system
for calculations and experiments done with IPOL.
"""

import sqlite3 as lite
import errno
import hashlib
import logging
import json
import cherrypy
import os
import os.path
import magic
import shutil
import Image

class Archive(object):
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

        :param path: path to be made, with all the parents directories
        :type path: string
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
        if not (cherrypy.config.has_key("blobs_dir") and
                cherrypy.config.has_key("database_dir") and
                cherrypy.config.has_key("blobs_thumbs_dir") and
                cherrypy.config.has_key("logs_dir")):
            print "Missing elements in configuration file."
            return False
        else:
            return True

    @staticmethod
    def get_extension(path):
        """
        Return the extension of a file using its magic number.

        :param path: path to the file
        :type path: string
        :return: the extension of the file
        :rtype: string
        """
        return magic.from_file(path).split(' ', 1)[0].lower()

    @staticmethod
    def get_hash_blob(path):
        """
        Return sha1 hash of given blob

        :param path: path file
        :type path: string
        :return: sha1 of the blob
        :rtype: string
        """
        with open(path, 'rb') as the_file:
            return hashlib.sha1(the_file.read()).hexdigest()

    @staticmethod
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

    def __init__(self):
        """
        Initialize Archive class.
        Attribute status should be checked after each initialisation.
        It is false if something went wrong.
        """
        thumbs_s = int()
        cherrypy.config.update("./archive.conf")
        self.status = self.check_config()
        if not self.status:
            return
        self.blobs_dir = cherrypy.config.get("blobs_dir")
        self.blobs_thumbs_dir = cherrypy.config.get("blobs_thumbs_dir")
        self.database_dir = cherrypy.config.get("database_dir")
        self.logs_dir = cherrypy.config.get("logs_dir")
        try:
            thumbs_s = int(cherrypy.config.get("thumbs_size"))
        except Exception:
            thumbs_s = 256
        try:
            self.nb_exp_by_pages = int(cherrypy.config.get("nb_exp_by_pages"))
        except Exception:
            self.nb_exp_by_pages = 12
        self.thumbs_size = (thumbs_s, thumbs_s)
        try:
            self.mkdir_p(self.logs_dir)
            self.mkdir_p(self.database_dir)
            self.mkdir_p(self.blobs_dir)
            self.mkdir_p(self.blobs_thumbs_dir)
        except Exception as ex:
            print "Error : " + str(ex)
            return
        self.logger = self.init_logging()
        self.database_file = os.path.join(self.database_dir, "archive.db")
        self.status = self.init_database()

    def init_logging(self):
        """
        Initialize the error logs of the module.
        """
        logger = logging.getLogger("archive_log")
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

        :param function_name: name of the function calling error_log for
            locating the error
        :type function_name: string
        :param error: string of the error description.
        :type error: string
        """
        error_string = function_name + ": " + error
        self.logger.error(error_string)

    def init_database(self):
        """
        Initialize the database used by the module if it doesn't exist.

        :return: False if there was an error. True otherwise.
        :rtype: bool
        """
        status = True
        if not os.path.isfile(self.database_file):
            try:
                conn = lite.connect(self.database_file)
                cursor_db = conn.cursor()
                cursor_db.execute("""
                PRAGMA foreign_keys=ON""")
                cursor_db.execute("""
                CREATE TABLE IF NOT EXISTS experiments(
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                id_demo INTEGER NULL,
                params TEXT NULL,
                timestamp TIMESTAMP
                DEFAULT CURRENT_TIMESTAMP)
                """)
                cursor_db.execute("""
                CREATE TABLE IF NOT EXISTS blobs(
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                hash TEXT NULL,
                type TEXT NULL,
                format TEXT NULL)
                """)
                cursor_db.execute("""
                CREATE TABLE IF NOT EXISTS correspondence(
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                id_experiment INTEGER NULL,
                id_blob INTEGER NULL,
                name TEXT NULL,
                FOREIGN KEY(id_experiment) REFERENCES experiments(id)
                ON DELETE CASCADE)
                """)
                conn.commit()
                conn.close()
            except Exception as ex:
                self.error_log("init_database", (str(ex)))
                if os.path.isfile(self.database_file):
                    try:
                        os.remove(self.database_file)
                    except Exception as ex:
                        self.error_log("init_database", str(ex))
                status = False
        return status

#####
# adding an experiment to the archive database
#####

    def make_thumbnail(self, path, name):
        """
        This function make a thumbnail of path.

        :param path: path to the file.
        :type path: string.
        :param name: name of the file without extension..
        :type name: string.
        """
        img = Image.open(path)
        img.thumbnail(self.thumbs_size, Image.ANTIALIAS)
        img.save(os.path.join(self.blobs_thumbs_dir, name) + ".jpeg", "JPEG")

    def add_to_blob_table(self, conn, path):
        """
        This function check if an blob exist in the table. If it exist,
            the id is returned. If not, the blob is added, then the id
            is returned.

        :param conn: connection to the database.
        :type conn: sqlite3 connection
        :param path: path to the temporary file.
        :type path: string.
        :return: id of the blob in the database.
        :rtype: integer.
        """
        id_blob = int()
        path_new_file = str()
        tmp = tuple()
        hash_file = self.get_hash_blob(path)
        type_file = self.get_extension(path)
        format_file = self.file_format(path)
        cursor_db = conn.cursor()
        cursor_db.execute('''
        SELECT * FROM blobs WHERE hash = ?
        ''', (hash_file,))
        tmp = cursor_db.fetchone()
        if not tmp:
            cursor_db.execute('''
            INSERT INTO blobs(hash, type, format) VALUES(?, ?, ?)
            ''', (hash_file, type_file, format_file,))
            path_new_file = os.path.join(self.blobs_dir,
                                         hash_file) + '.' + type_file
            shutil.copyfile(path, path_new_file)
            self.make_thumbnail(path_new_file, hash_file)
            cursor_db.execute('''
            SELECT * FROM blobs WHERE hash = ?
            ''', (hash_file,))
            tmp = cursor_db.fetchone()
        id_blob = int(tmp[0])
        return id_blob

    def update_exp_table(self, conn, demo_id, parameters):
        """
        This function update the experiment table.

        :param conn: connection to the database.
        :type conn: sqlite3 connection
        :param demo_id: id of the demo used for the experiment.
        :type demo_id: integer.
        :param blobs: blobs locations and their given names in the experiment
            as keys/values encoded in JSON.
        :type blobs: JSON formatted string.
        :param parameters: parameters used as keys/values encoded in JSON.
        :type parameters: JSON formatted string.
        :return: Return the id of the newly created experiment in the database.
        :rtype: integer.
        """
        cursor_db = conn.cursor()
        cursor_db.execute('''
        INSERT INTO
        experiments (id_demo, params)
        VALUES (?, ?)''', (demo_id, parameters))
        cursor_db.execute("SELECT MAX(id) FROM experiments")
        id_experiment = int(cursor_db.fetchone()[0])
        return id_experiment

    def update_blob_table(self, conn, blobs):
        """
        This function update the blob table.
            It return a dictionary of data to be added
            to the correspondence table.

        :param conn: connection to the database.
        :type conn: sqlite3 connection
        :param blobs: blobs locations and their given names in the experiment
            as keys/values encoded in JSON.
        :type blobs: JSON formatted string.
        :return: a dictionary of data to be added to the correspondence table.
        :rtype: dict
        """
        id_blob = int()
        dict_blobs = json.loads(blobs)
        dict_corresp = {}
        for keys, values in dict_blobs.items():
            id_blob = self.add_to_blob_table(conn, keys)
            dict_corresp[id_blob] = values
        return dict_corresp

    def update_correspondence_table(self, conn, id_experiment, dict_corresp):
        """
        This function update the correspondence table, associating
            blobs, experiments, and descriptions of blobs.

        :param conn: connection to the database.
        :type conn: sqlite3 connection
        :param id_experiment: Id of the experiment in the database.
        :type id_experiment: integer
        :param dict_corresp: dict with blob ids as keys and the description
            of their blobs as values.
        :type dict_corresp: dict
        """
        cursor_db = conn.cursor()
        for keys, values in dict_corresp.items():
            cursor_db.execute('''
            INSERT INTO
            correspondence (id_experiment, id_blob, name)
            VALUES (?, ?, ?)''', (id_experiment, keys, values))

    def add_experiment(self, demo_id, blobs, parameters):
        """
        This function add an experiment with all its datas to the archive.
            In case of failure, False will be returned.

        :param demo_id: id of the demo used for the experiment.
        :type demo_id: integer.
        :param blobs: blobs locations and their given names in the experiment
            as keys/values encoded in JSON.
        :type blobs: JSON formatted string.
        :param parameters: parameters used as keys/values encoded in JSON.
        :type parameters: JSON formatted string.
        :return: status of the operation
        :rtype: bool
        """
        status = True
        try:
            conn = lite.connect(self.database_file)
            id_experiment = self.update_exp_table(conn, demo_id, parameters)
            dict_corresp = self.update_blob_table(conn, blobs)
            self.update_correspondence_table(conn, id_experiment, dict_corresp)
            conn.commit()
            conn.close()
        except Exception as ex:
            self.error_log("add_experiment", str(ex))
            status = False
            try:
                conn.rollback()
                conn.close()
            except Exception as ex:
                pass
        return status

#####
# displaying a page of archive
#####

    def count_pages(self, conn, id_demo):
        """
        This function return the number of archive pages to be displayed
            for a given demo, and the number of experiments done with this
            demo.

        :param conn: connection to the database.
        :type conn: sqlite3 connection
        :param id_demo: id of the demo.
        :type id_demo: integer.
        :return: a dict with the number and pages and the number of experiments
        :rtype: dict
        """
        dict_pages = {}
        cursor_db = conn.cursor()
        cursor_db.execute("""
        SELECT COUNT(*) FROM experiments WHERE id_demo = ?""", (id_demo,))
        nb_exp = cursor_db.fetchone()[0]
        dict_pages["nb_exp"] = nb_exp
        if nb_exp % self.nb_exp_by_pages != 0:
            pages_to_add = 1
        else:
            pages_to_add = 0
        nb_pages = (nb_exp / self.nb_exp_by_pages) + pages_to_add
        dict_pages["nb_pages"] = nb_pages
        return dict_pages

    def get_dict_file(self, path_file, path_thumb, name):
        """
        Build a dict containing the path to the file, the path to the thumb
            and the name of the file.

        :param path_file: path to the file
        :type path_file: string
        :param path_thumb: path to the thumb
        :type path_thumb: string
        :param name: name of the file
        :type nape: string
        :rtype: dict
        """
        dict_file = {}
        dict_file["url"] = "http://127.0.0.1:7777/" + path_file
        dict_file["url_thumb"] = "http://127.0.0.1:7777/" + path_thumb
        dict_file["name"] = name
        return dict_file

    def get_data_experiment(self, conn, id_exp, parameters, date):
        """
        Build a dictionnary containing all the datas needed on a given
            experiment for building the archive page.

        :param conn: connection to the database.
        :type conn: sqlite3 connection
        :param id_exp: id of the experiment.
        :type id_exp: integer
        :param parameters: json formatted strings with the params of the exp.
        :type parameters: string
        :return: dictionnary with infos on the given experiment.
        :rtype: dict
        """
        dict_exp = {}
        list_files = []
        path_file = str()
        path_thumb = str()
        cursor_db = conn.cursor()
        for row in cursor_db.execute("""
        SELECT img.hash, img.type, cor.name FROM blobs img
        INNER JOIN correspondence cor ON img.id=cor.id_blob
        INNER JOIN experiments exp ON cor.id_experiment=exp.id
        WHERE id_experiment = ?""", (id_exp,)):
            path_file = os.path.join(self.blobs_dir, (row[0] + '.' + row[1]))
            path_thumb = os.path.join(self.blobs_thumbs_dir, row[0] + '.jpeg')
            list_files.append(self.get_dict_file(path_file,
                                                 path_thumb,
                                                 row[2]))
        dict_exp["id"] = id_exp
        dict_exp["date"] = date
        dict_exp["parameters"] = json.loads(parameters)
        dict_exp["files"] = list_files
        return dict_exp

    def get_experiment_page(self, conn, id_demo, page, dict_pages):
        """
        This function return a list of dicts with all the informations needed
            for displaying the experiments on a given page.

        :param conn: connection to the database.
        :type conn: sqlite3 connection
        :param id_demo: id of the demo
        :type id_demo: integer
        :param page: number of the page to be built
        :type page: integer
        :param dict_pages: dict created with count_pages
        :type dict_pages: dict
        :return: list with infos on experiments
        :rtype: list
        """
        data_exp = []
        cursor_db = conn.cursor()
        starting_index = ((page - 1) * self.nb_exp_by_pages)
        for row in cursor_db.execute("""
        SELECT id, params, timestamp
        FROM experiments WHERE id_demo = ?
        ORDER BY timestamp
        LIMIT ? OFFSET ?""", (id_demo, self.nb_exp_by_pages, starting_index,)):
            data_exp.append(self.get_data_experiment(conn,
                                                     row[0],
                                                     row[1],
                                                     row[2]))
        return data_exp

    def echo_page(self, id_demo, page):
        """
        This function return a JSON string with all the informations needed
            to build the given page for the given demo.

        :param id_demo: id of the demo
        :type id_demo: integer
        :param page: number of the page to be built
        :type page: integer
        :return: JSON string
        :rtype: string
        """
        data = {}
        data["status"] = "KO"
        try:
            conn = lite.connect(self.database_file)
            dict_pages = self.count_pages(conn, id_demo)
            if page > dict_pages["nb_pages"] or page < 0:
                raise ValueError("Page requested don't exist.")
            elif page == 0:
                page = 1
            data["id_demo"] = id_demo
            data["nb_pages"] = dict_pages["nb_pages"]
            data["experiments"] = self.get_experiment_page(conn,
                                                          id_demo,
                                                          page,
                                                          dict_pages)
            conn.close()
            data["status"] = "OK"
        except Exception as ex:
            self.error_log("echo_page", str(ex))
            try:
                conn.close()
            except Exception:
                pass
        return data

    @cherrypy.expose
    def page(self, demo_id, page='1'):
        """
        Return a JSON string with all the infos on a given pave of archive
            for a given id.

        :param demo_id: number of the demo
        :type demo_id: string
        :param page: number of page
        :type page: string
        :rtype: JSON formatted string
        """
        self.echo_database()
        return json.dumps(self.echo_page(int(demo_id), int(page)))

#####
# deleting an experiment
#####

    def delete_blob(self, conn, id_blob):
        """
        This function delete the given id_blob, in the database and physically.

        :param conn: connection to the database.
        :type conn: sqlite3 connection
        :param id_blob: id of the blob to be removed.
        :type id_blob: integer
        """
        cursor_db = conn.cursor()
        cursor_db.execute("""
        SELECT * FROM blobs WHERE id = ?""", (id_blob,))
        tmp = cursor_db.fetchone()
        path_blob = self.blobs_dir + tmp[1] + '.' + tmp[2]
        path_thumb = self.blobs_thumbs_dir + tmp[1] + '.' + 'jpeg'
        os.remove(path_blob)
        os.remove(path_thumb)
        cursor_db.execute("""
        DELETE FROM blobs WHERE id = ?""", (id_blob,))

    def purge_unique_blobs(self, conn, ids_blobs):
        """
        This function check if the blobs are use in only one experiment.
            If this is the case, they are deleted both in the database
            and physically.

        :param conn: connection to the database.
        :type conn: sqlite3 connection
        :param ids_blobs: ids of the blobs to be checked and removed.
        :type ids_blobs: list
        """
        cursor_db = conn.cursor()
        for blob in ids_blobs:
            cursor_db.execute("""
            SELECT COUNT(*) FROM correspondence WHERE id_blob = ?""",
            (blob,))
            if cursor_db.fetchone()[0] == 1:
                self.delete_blob(conn, blob)

    @cherrypy.expose
    def delete_experiment(self, experiment_id):
        """
        This function remove, in the database, an experiment,
            from the experiment table, and its dependencies
            in the correspondence table.
            If the blobs are used only in this experiment, they will be
            removed too.

        :param experiment_id: id of the experiment to be removed.
        :type experiment_id: integer
        """
        status = {"status" : "KO"}
        try:
            ids_blobs = []
            conn = lite.connect(self.database_file)
            cursor_db = conn.cursor()
            cursor_db.execute("""
            PRAGMA foreign_keys=ON""")
            for row in cursor_db.execute("""
            SELECT * FROM correspondence where id_experiment = ?""",
            (experiment_id,)):
                ids_blobs.append(row[2])
            self.purge_unique_blobs(conn, ids_blobs)
            cursor_db.execute("""
            DELETE FROM experiments WHERE id = ?
            """, (experiment_id,))
            cursor_db.execute("""
            DELETE FROM correspondence WHERE id_experiment = ?
            """, (experiment_id))
            cursor_db.execute("VACUUM")
            conn.commit()
            conn.close()
            status["status"] = "OK"
        except Exception as ex:
            self.error_log("delete_experiment", str(ex))
            try:
                conn.rollback()
                conn.close()
            except Exception as ex:
                pass
        return json.dumps(status)

#####
# deleting a blob v1
#####

    # def delete_deps(self, conn, id_blob):
    #     """
    #     Remove depencies of a blob in the database.

    #     :param conn: connection to the database.
    #     :type conn: sqlite3 connection
    #     :param id_blob: id of the blob
    #     :type id_blob: integer
    #     """
    #     cursor_db = conn.cursor()
    #     print "k"
    #     list_tmp = []
    #     for row in cursor_db.execute("""
    #     SELECT id_experiment FROM correspondence WHERE id_blob = ?""",
    #     (id_blob,)):
    #         list_tmp.append(row[0])
    #     str_tmp = '('
    #     str_tmp += ' OR '.join(('id = ' + str(n) for n in list_tmp))
    #     str_tmp += ')'
    #     cursor_db.execute("""DELETE FROM experiments WHERE ?""",
    #     (str_tmp,))
    #     cursor_db.execute("""
    #     DELETE FROM correspondence WHERE id_experiment = ?""", (id_blob))
    #     cursor_db.execute("VACUUM")

    # @cherrypy.expose
    # def delete_blob_w_deps(self, id_blob):
    #     """
    #     Remove a blob, both physically and in the database,
    #         with all its dependencies.

    #     :param id_blob: id of the blob in the database.
    #     :type id_blob: integer
    #     :return: status of experiment
    #     :rtype: json formatted string
    #     """
    #     status = {"status" : "KO"}
    #     try:
    #         conn = lite.connect(self.database_file)
    #         self.delete_blob(conn, id_blob)
    #         self.delete_deps(conn, id_blob)
    #         conn.commit()
    #         conn.close()
    #         status["status"] = "OK"
    #     except Exception as ex:
    #         self.error_log("delete_blob_w_deps", str(ex))
    #         try:
    #             conn.rollback()
    #             conn.close()
    #         except Exception as ex:
    #             pass
    #     return json.dumps(status)

#####
# deleting a blob v2
#####

    @cherrypy.expose
    def delete_blob_w_deps(self, id_blob):
        """
        Remove a blob, both physically and in the database,
            with all its dependencies.

        :param id_blob: id of the blob in the database.
        :type id_blob: integer
        :return: status of experiment
        :rtype: json formatted string
        """
        status = {"status" : "KO"}
        try:
            conn = lite.connect(self.database_file)
            cursor_db = conn.cursor()
            list_tmp = []
            for row in cursor_db.execute("""
            SELECT id_experiment FROM correspondence WHERE id_blob = ?""",
            (id_blob,)):
                tmp = unicode(str(row[0]), "utf-8")
                list_tmp.append(tmp)
            conn.close()
        except Exception as ex:
            self.error_log("delete_blob_w_deps", str(ex))
            try:
                conn.close()
            except Exception as ex:
                pass
        for value in list_tmp:
            tmp = self.delete_experiment(value)
            if tmp["status"] != "OK":
                return json.dumps(status)
        status["status"] = "OK"
        return json.dumps(status)

#####
#below it that's test
#####

    def echo_database(self):
        """
        Print the database content on stdout.
        """
        try:
            conn = lite.connect(self.database_file)
            cursor_db = conn.cursor()
            print "Archive Database :"
            print "table experiments (id, id_demo, parameters) :"
            for row in cursor_db.execute("""
            SELECT * FROM experiments ORDER BY id"""):
                print row
            print "table blobs (id, hash, type, format) :"
            for row in cursor_db.execute("""
            SELECT * FROM blobs ORDER BY id"""):
                print row
            print "table correspondence (id, id_exp, id_blob, name, time):"
            for row in cursor_db.execute("""
            SELECT * FROM correspondence ORDER BY id"""):
                print row
            conn.close()
        except Exception as ex:
            self.error_log("echo_database", str(ex))
            try:
                conn.close()
            except Exception as ex:
                pass

    @cherrypy.expose
    def add_exp_test(self):
        """
        Test for adding an experiment to the database.
        """
        tmp_dir = "blobs_tmp"
        dict_blobs = {os.path.join(tmp_dir, "charmander") : "input",
                       os.path.join(tmp_dir, "squirtle") : "water"}
        str_blobs = json.dumps(dict_blobs)
        str_test = json.dumps("test")
        demo_id = 42
        test = self.add_experiment(demo_id, str_blobs, str_test)
        self.echo_database()
        return str(test)

    @cherrypy.expose
    def echo(self):
        """
        test for displaying database.
        """
        self.echo_database()

cherrypy.quickstart(Archive(), config="archive.conf")

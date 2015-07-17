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
                                      datefmt = '%Y-%m-%d %H:%M:%S')
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
                CREATE TABLE IF NOT EXISTS images(
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                hash TEXT NULL,
                type TEXT NULL)
                """)
                cursor_db.execute("""
                CREATE TABLE IF NOT EXISTS correspondence(
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                id_experiment INTEGER NULL,
                id_image INTEGER NULL,
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

    def add_to_image_table(self, conn, path):
        """
        This function check if an image exist in the table. If it exist,
            the id is returned. If not, the image is added, then the id
            is returned.

        :param conn: connection to the database.
        :type conn: sqlite3 connection
        :param path: path to the temporary file.
        :type path: string.
        :return: id of the image in the database.
        :rtype: integer.
        """
        id_image = int()
        path_new_file = str()
        tmp = tuple()
        hash_file = self.get_hash_blob(path)
        type_file = self.get_extension(path)
        cursor_db = conn.cursor()
        cursor_db.execute('''
        SELECT * FROM images WHERE hash = ?
        ''', (hash_file,))
        tmp = cursor_db.fetchone()
        if not tmp:
            cursor_db.execute('''
            INSERT INTO images(hash, type) VALUES(?, ?)
            ''', (hash_file, type_file,))
            path_new_file = os.path.join(self.blobs_dir,
                                         hash_file) + '.' + type_file
            shutil.copyfile(path, path_new_file)
            self.make_thumbnail(path_new_file, hash_file)
            cursor_db.execute('''
            SELECT * FROM IMAGES WHERE hash = ?
            ''', (hash_file,))
            tmp = cursor_db.fetchone()
        id_image = int(tmp[0])
        return id_image

    def update_exp_table(self, conn, demo_id, parameters):
        """
        This function update the experiment table.

        :param conn: connection to the database.
        :type conn: sqlite3 connection
        :param demo_id: id of the demo used for the experiment.
        :type demo_id: integer.
        :param images: images locations and their given names in the experiment
            as keys/values encoded in JSON.
        :type images: JSON formatted string.
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

    def update_image_table(self, conn, images):
        """
        This function update the image table.
            It return a dictionary of data to be added
            to the correspondence table.

        :param conn: connection to the database.
        :type conn: sqlite3 connection
        :param images: images locations and their given names in the experiment
            as keys/values encoded in JSON.
        :type images: JSON formatted string.
        :return: a dictionary of data to be added to the correspondence table.
        :rtype: dict
        """
        id_image = int()
        dict_images = json.loads(images)
        dict_corresp = {}
        for keys, values in dict_images.items():
            id_image = self.add_to_image_table(conn, keys)
            dict_corresp[id_image] = values
        return dict_corresp

    def update_correspondence_table(self, conn, id_experiment, dict_corresp):
        """
        This function update the correspondence table, associating
            images, experiments, and descriptions of images.

        :param conn: connection to the database.
        :type conn: sqlite3 connection
        :param id_experiment: Id of the experiment in the database.
        :type id_experiment: integer
        :param dict_corresp: dict with image ids as keys and the description
            of their images as values.
        :type dict_corresp: dict
        """
        cursor_db = conn.cursor()
        for keys, values in dict_corresp.items():
            cursor_db.execute('''
            INSERT INTO
            correspondence (id_experiment, id_image, name)
            VALUES (?, ?, ?)''', (id_experiment, keys, values))

    def add_experiment(self, demo_id, images, parameters):
        """
        This function add an experiment with all its datas to the archive.
            In case of failure, False will be returned.

        :param demo_id: id of the demo used for the experiment.
        :type demo_id: integer.
        :param images: images locations and their given names in the experiment
            as keys/values encoded in JSON.
        :type images: JSON formatted string.
        :param parameters: parameters used as keys/values encoded in JSON.
        :type parameters: JSON formatted string.
        :return: status of the operation
        :rtype: bool
        """
        status = True
        try:
            conn = lite.connect(self.database_file)
            id_experiment = self.update_exp_table(conn, demo_id, parameters)
            dict_corresp = self.update_image_table(conn, images)
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
        dict_img = {}
        dict_files = {}
        path_file = str()
        path_thumb = str()
        cursor_db = conn.cursor()
        for row in cursor_db.execute("""
        SELECT * FROM correspondence WHERE id_experiment = ?""", (id_exp,)):
            dict_img[row[2]] = row[3]
        for key, value in dict_img.items():
            cursor_db.execute("""
            SELECT * FROM images WHERE id = ?""", (key,))
            tmp = cursor_db.fetchone()
            if value == 'input':
                dict_exp["key"] = tmp[1]
            path_file = os.path.join(self.blobs_dir, (tmp[1] + '.' + tmp[2]))
            path_thumb = os.path.join(self.blobs_thumbs_dir, tmp[1] + '.jpeg')
            dict_files[path_file] = path_thumb
        dict_exp["date"] = date
        dict_exp["parameters"] = json.loads(parameters)
        dict_exp["files"] = dict_files
        return dict_exp

    def get_experiment_page(self, conn, id_demo, id_page, dict_pages):
        """
        This function return a list of dicts with all the informations needed
            for displaying the experiments on a given page.

        :param conn: connection to the database.
        :type conn: sqlite3 connection
        :param id_demo: id of the demo
        :type id_demo: integer
        :param id_page: number of the page to be built
        :type id_page: integer
        :param dict_pages: dict created with count_pages
        :type dict_pages: dict
        :return: list with infos on experiments
        :rtype: list
        """
        data_exp = []
        cursor_db = conn.cursor()
        if id_page == 1:
            nb_exp_on_page = dict_pages["nb_exp"] % self.nb_exp_by_pages
            starting_index = 0
            if nb_exp_on_page == 0:
                nb_exp_on_page = self.nb_exp_by_pages
        else:
            nb_exp_on_page = self.nb_exp_by_pages
            starting_index = (dict_pages["nb_exp"] % self.nb_exp_by_pages)
            if starting_index == 0:
                starting_index = self.nb_exp_by_pages
            starting_index += ((id_page - 2) * self.nb_exp_by_pages)
        for row in cursor_db.execute("""
        SELECT * FROM experiments WHERE id_demo = ?
        LIMIT ? OFFSET ?""", (id_demo, nb_exp_on_page, starting_index,)):
            data_exp.append(self.get_data_experiment(conn,
                                                     row[0],
                                                     row[2],
                                                     row[3]))
        return data_exp

    def echo_page(self, id_demo, id_page):
        """
        This function return a JSON string with all the informations needed
            to build the given page for the given demo.

        :param id_demo: id of the demo
        :type id_demo: integer
        :param id_page: number of the page to be built
        :type id_page: integer
        :return: JSON string
        :rtype: string
        """
        data = {}
        data["status"] = "KO"
        try:
            conn = lite.connect(self.database_file)
            dict_pages = self.count_pages(conn, id_demo)
            if (id_page > dict_pages["nb_pages"] or id_page <= 0):
                raise ValueError("Page requested don't exist.")
            data["id_demo"] = id_demo
            data["nb_pages"] = dict_pages["nb_pages"]
            data["experiments"] = self.get_experiment_page(conn,
                                                          id_demo,
                                                          id_page,
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

    def delete_image(self, conn, image):
        """
        This function delete the given image, in the database and physically.

        :param conn: connection to the database.
        :type conn: sqlite3 connection
        :param image: id of the image to be removed.
        :type image: integer
        """
        cursor_db = conn.cursor()
        cursor_db.execute("""
        SELECT * FROM images WHERE id = ?""", (image,))
        tmp = cursor_db.fetchone()
        path_img = self.blobs_dir + tmp[1] + '.' + tmp[2]
        path_thumb = self.blobs_thumbs_dir + tmp[1] + '.' + 'jpeg'
        os.remove(path_img)
        os.remove(path_thumb)
        cursor_db.execute("""
        DELETE FROM images WHERE id = ?""", (image,))

    def purge_unique_images(self, conn, ids_images):
        """
        This function check if the images are use in only one experiment.
            If this is the case, they are deleted both in the database
            and physically.

        :param conn: connection to the database.
        :type conn: sqlite3 connection
        :param ids_images: ids of the images to be checked and removed.
        :type ids_images: list
        """
        cursor_db = conn.cursor()
        for image in ids_images:
            cursor_db.execute("""
            SELECT COUNT(*) FROM correspondence WHERE id_image = ?""",
            (image,))
            if cursor_db.fetchone()[0] == 1:
                self.delete_image(conn, image)

    def delete_experiment(self, experiment_id):
        """
        This function remove, in the database, an experiment,
            from the experiment table, and its dependencies
            in the correspondence table.
            If the images are used only in this experiment, they will be
            removed too.

        :param experiment_id: id of the experiment to be removed.
        :type experiment_id: integer
        """
        try:
            ids_images = []
            conn = lite.connect(self.database_file)
            cursor_db = conn.cursor()
            cursor_db.execute("""
            PRAGMA foreign_keys=ON""")
            for row in cursor_db.execute("""
            SELECT * FROM correspondence where id_experiment = ?""",
            (experiment_id,)):
                ids_images.append(row[2])
            self.purge_unique_images(conn, ids_images)
            cursor_db.execute("""
            DELETE FROM experiments WHERE id = ?
            """, (experiment_id,))
            cursor_db.execute("VACUUM")
            conn.commit()
            conn.close()
        except Exception as ex:
            self.error_log("delete_experiment", str(ex))
            try:
                conn.rollback()
                conn.close()
            except Exception as ex:
                pass

    def echo_database(self):
        """
        Print the database content on stdout.
        """
        try:
            conn = lite.connect(self.database_file)
            cursor_db = conn.cursor()
            print "Archive Database :"
            print "table experiment (id, id_demo, parameters) :"
            for row in cursor_db.execute("""
            SELECT * FROM experiments ORDER BY id"""):
                print row
            print "table images (id, hash, type) :"
            for row in cursor_db.execute("""
            SELECT * FROM images ORDER BY id"""):
                print row
            print "table correspondence (id, id_exp, id_image, name, time):"
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
    def test(self):
        """
        Test for the webservice.
        """
        tmp_dir = "blobs_tmp"
        dict_images = {os.path.join(tmp_dir, "charmander") : "input",
                       os.path.join(tmp_dir, "squirtle") : "result"}
        str_images = json.dumps(dict_images)
        str_test = "test"
        demo_id = 42
        tmp = str(self.add_experiment(demo_id, str_images,
                                      json.dumps(str_test)))
        # return (json.dumps(self.echo_page(demo_id, 2),
        #                    indent=4,
        #                    separators=(',', ': ')))
        self.echo_database()
        status = {"status" : "OK" if tmp == "True" else "KO"}
        return json.dumps(status)

cherrypy.quickstart(Archive(), config="archive.conf")



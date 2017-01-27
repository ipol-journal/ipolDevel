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

import sqlite3 as lite
import sys
import errno
import hashlib
import logging
import json
import os
import os.path
import shutil
import cherrypy
import magic
from mako.template import Template


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
                cherrypy.config.has_key("logs_dir") and
                cherrypy.config.has_key("url")):
            print "Missing elements in configuration file."
            return False
        else:
            return True

    @staticmethod
    def get_hash_blob(path):
        """
        Return sha1 hash of given blob
        :return: sha1 of the blob
        :rtype: string
        """
        with open(path, 'rb') as the_file:
            return hashlib.sha1(the_file.read()).hexdigest()

    @staticmethod
    def file_format(the_file):
        """
        Return format of the file
        :return: format of file (audio, image or video)
        :rtype: string
        """
        mime = magic.Magic(mime=True)
        fileformat = mime.from_file(the_file)
        extension = fileformat.split('/')
        return extension[0]


    def __init__(self, option, conf_file):
        """
        Initialize Archive class.
        Attribute status should be checked after each initialisation.
        It is false if something went wrong.
        """
        thumbs_s = None
        cherrypy.config.update(conf_file)
        # [ToDo][Miguel] Why self.status as an object variable if
        # if it's used just in this contructor???
        self.status = self.check_config()
        if not self.status:
            sys.exit(1)

        self.blobs_dir = cherrypy.config.get("blobs_dir")
        self.blobs_thumbs_dir = cherrypy.config.get("blobs_thumbs_dir")

        if option == "test":
            self.database_dir = "test"
        else:
            self.database_dir = cherrypy.config.get("database_dir")

        self.logs_dir = cherrypy.config.get("logs_dir")
        self.url = cherrypy.config.get("url")

        try:
            thumbs_s = int(cherrypy.config.get("thumbs_size"))
        except Exception:
            thumbs_s = 256

        try:
            self.number_of_experiments_by_pages = \
              int(cherrypy.config.get("number_of_experiments_by_pages"))
        except Exception:
            self.number_of_experiments_by_pages = 12

        self.thumbs_size = (thumbs_s, thumbs_s)

        self.mkdir_p(self.logs_dir)
        self.mkdir_p(self.database_dir)
        self.mkdir_p(self.blobs_dir)
        self.mkdir_p(self.blobs_thumbs_dir)

        self.logger = self.init_logging()

        try:
            self.database_name = cherrypy.config.get("database_name")
        except Exception:
            self.database_name = "archive.db"

        self.database_file = os.path.join(self.database_dir, self.database_name)

        self.status = self.init_database()
        if not self.status:
            sys.exit("Initialization of database failed. Check the logs.")


    def init_logging(self):
        """
        Initialize the error logs of the module.
        """
        logger = logging.getLogger("archive_log")
        logger.setLevel(logging.ERROR)
        handler = logging.FileHandler(os.path.join(\
          self.logs_dir, 'error.log'))
        formatter = logging.Formatter(\
          '%(asctime)s ERROR in %(message)s',\
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
                print str(self.database_file) + ' is empty. Removing the file...'
                try:
                    self.error_log("init_database", 'Database file was empty')
                    os.remove(self.database_file)
                except Exception as ex:
                    self.error_log("init_database", str(ex))
                    status = False
                    return status

                print "Creating a correct new database"

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


    def get_new_path(self, main_directory, hash_name, file_extension, depth=2):
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



    def add_to_blob_table(self, conn, blob_dict):
        """
        This function check if an blob exist in the table. If it exist,
        the id is returned. If not, the blob is added, then the id is returned.
        :return: id of the blob in the database.
        :rtype: integer.
        """

        # len = 1 --> Non-image
        # len = 2 --> Image and thumbnail

        if len(blob_dict) == 1:
            for key, value in blob_dict.items():
                blob_name = key
                blob_path = value

            copy_thumbnail = False

        else:
            blob, blob_thumbnail = blob_dict.items()
            blob_name = blob[0]
            blob_path = blob[1]
            blob_thumbnail_name = blob_thumbnail[0]
            blob_thumbnail_path = blob_thumbnail[1]
            copy_thumbnail = True

            # The dictionary can be unordered.
            # We need to ensure that the thumbnail is the second value.
            #If not, we must order it correctly
            if blob_thumbnail_name.find('_thumbnail') == -1:
                # We correct the routes and the names.
                blob_name = blob_thumbnail_name
                blob_path_aux = blob_thumbnail_path
                blob_thumbnail_path = blob_path
                blob_path = blob_path_aux


        id_blob = int()
        path_new_file = str()
        tmp = tuple()

        hash_file = self.get_hash_blob(blob_path)
        format_file = self.file_format(blob_path)

        _, type_file = os.path.splitext(blob_path)
        extension = type_file.split('.')
        type_file = extension[1]
        type_file.lower()

        cursor_db = conn.cursor()
        cursor_db.execute('''
        SELECT * FROM blobs WHERE hash = ?
        ''', (hash_file,))

        if not tmp:

            path_new_file, _ = self.get_new_path(self.blobs_dir, hash_file, type_file)

            cursor_db.execute('''
            INSERT INTO blobs(hash, type, format) VALUES(?, ?, ?)
            ''', (hash_file, type_file, format_file,))

            shutil.copyfile(blob_path, path_new_file)

            if copy_thumbnail:

                path_new_thumbnail, _ = self.get_new_path(\
                  self.blobs_thumbs_dir, hash_file, "jpeg")
                shutil.copyfile(blob_thumbnail_path, path_new_thumbnail)

        id_blob = int(cursor_db.lastrowid)
        return id_blob, blob_name

    def update_exp_table(self, conn, demo_id, parameters):
        """
        This function update the experiment table.
        :return: Return the id of the newly created experiment in the database.
        :rtype: integer.
        """
        cursor_db = conn.cursor()
        cursor_db.execute('''
        INSERT INTO
        experiments (id_demo, params)
        VALUES (?, ?)''', (demo_id, parameters))

        return int(cursor_db.lastrowid)

    def update_blob_table(self, conn, blobs):
        """
        This function update the blob table.
                It return a dictionary of data to be added
                to the correspondence table.
        :return: a dictionary of data to be added to the correspondence table.
        :rtype: dict
        """
        id_blob = int()
        dict_blobs = json.loads(blobs)
        dict_corresp = {}

        for blob_element in dict_blobs:
            id_blob, blob_name = self.add_to_blob_table(conn, blob_element)
            dict_corresp[id_blob] = blob_name

        return dict_corresp

    def update_correspondence_table(self, conn, id_experiment, dict_corresp):
        """
        This function update the correspondence table, associating
                blobs, experiments, and descriptions of blobs.
        """
        cursor_db = conn.cursor()

        for keys, values in dict_corresp.items():
            cursor_db.execute('''
            INSERT INTO
            correspondence (id_experiment, id_blob, name)
            VALUES (?, ?, ?)''', (id_experiment, keys, values))

    @cherrypy.expose
    def add_experiment(self, demo_id, blobs, parameters):
        """
        This function add an experiment with all its datas to the archive.
                In case of failure, False will be returned.
        :return: status of the operation
        :rtype: JSON formatted string.
        """
        data = {}
        data["status"] = "OK"
        try:
            demo_id = int(demo_id)
            conn = lite.connect(self.database_file)
            id_experiment = self.update_exp_table(conn, demo_id, parameters)
            dict_corresp = self.update_blob_table(conn, blobs)
            self.update_correspondence_table(conn, id_experiment, dict_corresp)
            conn.commit()
            conn.close()
            data["id_experiment"] = id_experiment

        except Exception as ex:
            self.error_log("add_experiment", str(ex))
            data["status"] = "KO"

            try:
                conn.rollback()
                conn.close()
            except Exception as ex:
                pass
        return json.dumps(data)

#####
# displaying a single experiment of archive
#####

    # [Miguel] Missing docstring!
    @cherrypy.expose
    def get_experiment(self, experiment_id):

        #id_demo = int(demo_id)
        experiment_id = int(experiment_id)

        data = {}
        data["status"] = "OK"
        try:
            conn = lite.connect(self.database_file)

            cursor_db = conn.cursor()

            cursor_db.execute('''SELECT params, timestamp
                FROM experiments WHERE id = ?''', (experiment_id, ))

            row = cursor_db.fetchone()
            data['experiment'] = self.get_data_experiment(conn, experiment_id, row[0], row[1])

            conn.close()

        except Exception as ex:

            data["status"] = "KO"
            self.error_log("get_experiment", str(ex))

            try:
                conn.close()
            except Exception:
                pass


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

        number_of_pages =\
        (number_of_experiments/self.number_of_experiments_by_pages) +\
        pages_to_add

        meta_info["first_date_of_an_experiment"] = first_date_of_an_experiment
        meta_info["number_of_pages"] = number_of_pages

        return meta_info

    def get_dict_file(self, path_file, path_thumb, name, id_blob):
        """
        Build a dict containing the path to the file, the path to the thumb
                and the name of the file.
        :rtype: dict
        """
        dict_file = {}
        dict_file["url"] = self.url + path_file
        dict_file["url_thumb"] = self.url + path_thumb
        dict_file["name"] = name
        dict_file["id"] = id_blob
        return dict_file

    def get_data_experiment(self, conn, id_exp, parameters, date):
        """
        Build a dictionnary containing all the datas needed on a given
                experiment for building the archive page.
        :return: dictionnary with infos on the given experiment.
        :rtype: dict
        """

        dict_exp = {}
        list_files = []
        path_file = str()
        path_thumb = str()
        cursor_db = conn.cursor()

        cursor_db.execute("""
            SELECT blb.hash, blb.type, cor.name, blb.id FROM blobs blb
            INNER JOIN correspondence cor ON blb.id=cor.id_blob
            INNER JOIN experiments exp ON cor.id_experiment=exp.id
            WHERE id_experiment = ?""", (id_exp,))

        all_rows = cursor_db.fetchall()

        for row in all_rows:

            path_file, subdirs = self.get_new_path(self.blobs_dir, row[0], row[1])
            path_thumb = os.path.join((self.blobs_thumbs_dir + '/' + subdirs), row[0] + '.jpeg')
            list_files.append(self.get_dict_file(path_file, path_thumb, row[2], row[3]))

        dict_exp["id"] = id_exp
        dict_exp["date"] = date
        dict_exp["parameters"] = json.loads(parameters)
        dict_exp["files"] = list_files

        return dict_exp

    def get_experiment_page(self, conn, id_demo, page):
        """
        This function return a list of dicts with all the informations needed
                for displaying the experiments on a given page.
        :return: list with infos on experiments
        :rtype: list
        """
        data_exp = []
        cursor_db = conn.cursor()
        starting_index = ((page - 1) * self.number_of_experiments_by_pages)



        cursor_db.execute("""
        SELECT id, params, timestamp
        FROM experiments WHERE id_demo = ?
        ORDER BY timestamp
        LIMIT ? OFFSET ?""", (id_demo, self.number_of_experiments_by_pages, starting_index,))

        all_rows = cursor_db.fetchall()

        for row in all_rows:
            data_exp.append(self.get_data_experiment(conn, row[0], row[1], row[2]))

        return data_exp

    @cherrypy.expose
    def get_page(self, demo_id, page='1'):
        """
        This function return a JSON string with all the informations needed
                to build the given page for the given demo.
                if the page number is not in the range [1,number_of_pages],
                the last page is used
        :return: JSON string
        :rtype: string
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

            if page > meta_info["number_of_pages"] or page < 0:
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
        """
        cursor_db = conn.cursor()

        for blob in ids_blobs:
            cursor_db.execute("""
            SELECT COUNT(*) FROM correspondence WHERE id_blob = ?""",\
            (blob,))

            if cursor_db.fetchone()[0] == 1:
                self.delete_blob(conn, blob)

    def delete_exp_w_deps(self, conn, experiment_id):
        """
        This function remove, in the database, an experiment from
                the experiment table, and its dependencies in the correspondence
                table. If the blobs are used only in this experiment, they will be
                removed too.
        """
        ids_blobs = []
        cursor_db = conn.cursor()
        cursor_db.execute("""
        PRAGMA foreign_keys=ON""")

        for row in cursor_db.execute("""
        SELECT * FROM correspondence where id_experiment = ?""",\
        (experiment_id,)):
            ids_blobs.append(row[2])

        self.purge_unique_blobs(conn, ids_blobs)
        cursor_db.execute("""
        DELETE FROM experiments WHERE id = ?
        """, (experiment_id,))
        cursor_db.execute("""
        DELETE FROM correspondence WHERE id_experiment = ?
        """, (experiment_id,))
        cursor_db.execute("VACUUM")

    @cherrypy.expose
    def delete_experiment(self, experiment_id):
        """
        Encapsulation of the delete_exp_w_deps function for removing an
                experiment.
        :rtype: JSON formatted string
        """
        status = {"status" : "KO"}
        try:
            conn = lite.connect(self.database_file)
            self.delete_exp_w_deps(conn, experiment_id)
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
# deleting a blob
#####

    @cherrypy.expose
    def delete_blob_w_deps(self, id_blob):
        """
        Remove a blob, both physically and in the database,
                with all its dependencies.
        Encapsulation of the delete_exp_w_deps function for removing a blob.
        :return: status of experiment
        :rtype: JSON formatted string
        """
        status = {"status" : "KO"}
        try:
            conn = lite.connect(self.database_file)
            cursor_db = conn.cursor()
            list_tmp = []

            for row in cursor_db.execute("""
SELECT id_experiment FROM correspondence WHERE id_blob = ?""",\
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

#####
# admin mode for removing blobs
#####

    @cherrypy.expose
    def archive_admin(self, demo_id, page):
        """
        Implement the administrator interface for removing blobs.
        """
        try:
            demo_id = int(demo_id)
            page = int(page)
            test_json = self.echo_page(demo_id, page)
            template = Template(filename='archive_admin_tmp.html')

            return template.render(demo=demo_id,
                                   test=test_json,
                                   num_page=page,
                                   url=self.url,
                                   func_name="archive_admin")
        except Exception:
            template = Template(filename='error.html')
            return template.render()

    @cherrypy.expose
    def delete_blob_w_deps_web(self, id_blob, demo_id):
        """
        HTML rendering for deleting blobs.
        """
        status = json.loads(self.delete_blob_w_deps(id_blob))
        if status["status"] != "OK":
            template = Template(filename='error.html')
            return template.render()
        else:
            return self.archive_admin(demo_id, 0)

    @cherrypy.expose
    def delete_experiment_web(self, experiment_id, demo_id):
        """
        HTML rendering for deleting experiments.
        """
        status = json.loads(self.delete_experiment(experiment_id))
        if status["status"] != "OK":
            template = Template(filename='error.html')
            return template.render()
        else:
            return self.archive_admin(demo_id, 0)

#####
# web utilities
#####

    @cherrypy.expose
    def ping(self):
        """
        Ping pong.
        :rtype: JSON formatted string
        """
        data = {}
        data["status"] = "OK"
        data["ping"] = "pong"
        return json.dumps(data)

    @cherrypy.expose
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
        :rtype: json formatted string
        """
        data = {}
        data["status"] = "KO"
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

            conn.close()
            data["status"] = "OK"

        except Exception as ex:
            self.error_log("stats", str(ex))
            try:
                conn.close()
            except Exception as ex:
                pass
        return json.dumps(data)

    @cherrypy.expose
    def index(self):
        """
        Small index for the archive.
        """
        return "This is the IPOL Archive module"

    @cherrypy.expose
    def default(self, attr):
        """
        Default method invoked when asked for non-existing service.
        """
        data = {}
        data["status"] = "KO"
        data["message"] = "Unknown service '{}'".format(attr)
        return json.dumps(data)


    @cherrypy.expose
    def add_exp_test(self):
        """
        Test for adding an experiment to the database.
        """
        tmp_dir = "blobs_tmp"
        dict_blobs = {os.path.join(tmp_dir, "charmander") : "input",\
                      os.path.join(tmp_dir, "squirtle") : "water"}
        str_blobs = json.dumps(dict_blobs)
        str_test = json.dumps("test")
        demo_id = -1
        test = self.add_experiment(unicode(demo_id), unicode(str_blobs), unicode(str_test))
        return str(test)


    @cherrypy.expose
    def demo_list(self):
        """
        return the demo_list of the module.
        :rtype: json formatted string
        {status: "OK",demo_list: [{demo_id: -1}]}
        """
        data = {}
        data["status"] = "KO"
        demo_list = list()

        try:
            conn = lite.connect(self.database_file)
            cursor_db = conn.cursor()
            cursor_db.execute("""
            SELECT DISTINCT id_demo FROM experiments""")

            for row in cursor_db.fetchall():
                print "loop"
                demoid = row[0]
                demo_list.append({'demo_id':demoid})
            data["demo_list"] = demo_list
            data["status"] = "OK"
        except Exception as ex:
            self.error_log("demo_list", str(ex))
            data["error"] = str(ex)
            try:
                conn.close()
            except Exception as ex:
                pass
        return json.dumps(data)

    @cherrypy.expose
    def delete_demo_w_deps(self, demo_id):
        """
        Encapsulation of the delete_exp_w_deps function for removing an
                experiment.
        :rtype: JSON formatted string status:OK/KO
        """
        # [ToDo][Miguel] demo_id is not used!!!
        # This functions is clearly wrong.

        status = {"status" : "KO"}
        try:

            # Get all experiments of this demo
            conn = lite.connect(self.database_file)
            cursor_db = conn.cursor()
            cursor_db.execute("""
            SELECT DISTINCT id FROM experiments""")
            experiment_id_list = list()
            wd = True
            while wd:
                try:
                    demoid = cursor_db.fetchone()[0]
                    experiment_id_list.append(demoid)
                # [ToDo][Miguel] Too broad Exception class! Use the
                # right (specific) type.
                except Exception, e:
                    wd = False


            # Delete all demo experiments info from db
            for experiment_id in experiment_id_list:
                print experiment_id
                self.delete_exp_w_deps(conn, experiment_id)
                # files removed?


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

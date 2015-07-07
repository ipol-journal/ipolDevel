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

import errno
import hashlib
import logging
import json
import cherrypy
import sqlite3 as lite
import os
import os.path

class Archive(object):
    """
    This class implement an archive system for experiments and
    calculations done with the IPOL demo image system.
    """
    
    def init_logging(self):
        """
        Initialize the error logs of the module.
        """
        logging.basicConfig(format='%(asctime)s ERROR : %(message)s',
                            datefmt='%Y-%m-%d %H:%M:%S',
                            filename= os.path.join(self.logs_dir, 'error.log'),
                            level=logging.ERROR)

    @staticmethod
    def mkdir_p(path):
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
                cherrypy.config.has_key("logs_dir")):
            print "Missing elements in configuration file."
            return False
        else:
            return True

    def __init__(self):
        """
        Initialize Archive class.
        Attribute status should be checked after each initialisation.
        It is false if something went wrong.
        """
        cherrypy.config.update("./archive.conf")
        self.status = self.check_config()
        if not self.status:
            return
        self.blobs_dir = cherrypy.config.get("blobs_dir")
        self.database_dir = cherrypy.config.get("database_dir")
        self.logs_dir = cherrypy.config.get("logs_dir")
        try:
            self.mkdir_p(self.logs_dir)
            self.mkdir_p(self.database_dir)
            self.mkdir_p(self.blobs_dir)
        except Exception as ex:
            print "Error : " + str(ex)
            return
        self.database_file = os.path.join(self.database_dir, "archive.db")
        self.init_logging()

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
                CREATE TABLE IF NOT EXISTS experiments(
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                id_demo INTEGER NULL,
                params TEXT NULL)
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
                name TEXT NULL)
                """)
                conn.commit()
                conn.close()
            except Exception as ex:
                logging.error(str(ex))
                if os.path.isfile(self.database_file):
                    try:
                        os.remove(self.database_file)
                    except Exception as ex:
                        logging.error(str(ex))
                status = False
        return status

def main():
    archive = Archive()
    archive.init_logging()
    print archive.init_database()

main()

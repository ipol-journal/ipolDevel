#!/usr/bin/env python
# -*- coding:utf-8 -*-

"""
This file implements database class
"""

import inspect
import sqlite3 as lite
from error import DatabaseInsertError, DatabaseSelectError, \
DatabaseDeleteError, DatabaseError

class   Database(object):
    """
    This class implements database management
    The database architecture is defined in file /db/blob.sql
    """
    def __init__(self, name):
        """
        Initialize database class
        Connect to databse

        :param ptr: database name
        :type ptr: string
        """
        self.formats = ('audio', 'image', 'video')
        self.database = lite.connect(name, check_same_thread=False)
        self.database.isolation_level = None
        self.cursor = self.database.cursor()
        self.init_tags_column()

    def add_demo_in_database(self, demo):
        """
        Add name demo in demo column in database

        :param demo: name demo
        :type demo: string
        :return: id demo in database
        :rtype: integer (primary key autoincrement)
        """
        try:
            self.cursor.execute("INSERT INTO demo(name) VALUES(?)", (demo,))
        except self.database.Error:
            raise DatabaseInsertError(inspect.currentframe().f_code.co_name)
        return self.cursor.lastrowid

    def add_blob_in_database(self, demoid, hash_blob, fileformat,
                             tags, blobid=-1):
        """
        Add hash blob content and format blob in blob column in database
        Add blob and demo ids in column blob_demo in database
        (necesary for many to many in DBMS)
        Add also tags in database : call addTagsInDatabase function

        :param demoid: demo id in database
        :type demoid: integer (primary key autoincrement)
        :param hash_blob: hash content blob
        :type hash_blob: string
        :param fileformat: type format of blob
        :type fileformat: string
        :param tags: name tag
        :type tags: string
        :param blobid: if blobid is omitted (= -1), then add blob
        (hash and format) to database esle not add
        :type blobid: integer
        """
        if blobid == -1:
            try:
                self.cursor.execute('''
                INSERT INTO blob(hash, format)
                VALUES(?, ?)''', \
                (hash_blob, fileformat,))
                blobid = self.cursor.lastrowid
            except self.database.Error:
                raise DatabaseInsertError(inspect.currentframe().f_code.co_name)

        try:
            self.cursor.execute(
                '''INSERT OR REPLACE INTO
                blob_demo(id_blob, id_demo)
                VALUES(?, ?)''', \
                (blobid, demoid,))

        except self.database.Error:
            raise DatabaseInsertError(inspect.currentframe().f_code.co_name)

        tagsid = -1
        if self.tags_is_in_database(tags):
            tagsid = self.id_tags(tags)

        self.add_tags_in_database(blobid, tags, tagsid)

    def add_tags_in_database(self, blobid, tags, tagsid=-1):
        """
        Add a new tagin tags columnin database if it's necessary
        Add blob and tag idsin blob_tagsin database

        :param blobid: blob idin database
        :type blobid:integer (primary key autoincrement)
        :param tags: name tag
        :type tags: string
        :param tagsid: if blobid is omitted (= -1), then add tag to database
        else not add
        :type tagsid:integer
        """
        if tagsid == -1:
            try:
                self.cursor.execute("INSERT INTO tags(tags) VALUES(?)", (tags,))
                tagsid = self.cursor.lastrowid
            except self.database.Error:
                raise DatabaseInsertError(inspect.currentframe().f_code.co_name)

        try:
            self.cursor.execute('''
            INSERT OR REPLACE INTO
            blob_tags(id_blob, id_tags)
            VALUES(?, ?)''', \
            (blobid, tagsid,))
        except self.database.Error:
            raise DatabaseInsertError(inspect.currentframe().f_code.co_name)

    def demo_is_in_database(self, demo):
        """
        Check if demo isin database,in column demo

        :param demo: name demo
        :type demo: string
        :return: name demo if it isin database else None
        :rtype: string
        """
        try:
            self.cursor.execute("SELECT name FROM demo WHERE name=?", (demo,))
            something = self.cursor.fetchone()
        except self.database.Error:
            raise DatabaseSelectError(inspect.currentframe().f_code.co_name)
        return something is not None

    def blob_is_in_database(self, hash_blob):
        """
        Check if hash blob isin database,in column blob

        :param hash_blob: hash blob content
        :type who: string
        :return: hash if it isin database else None
        :rtype: string
        """
        try:
            self.cursor.execute('''
            SELECT hash FROM blob WHERE hash=?''',
            (hash_blob,))
            something = self.cursor.fetchone()
        except self.database.Error:
            raise DatabaseSelectError(inspect.currentframe().f_code.co_name)
        return something is not None

    def tags_is_in_database(self, tag):
        """
        Check if tags isin database,in column tags

        :param tag: name tag
        :type tag: string
        :return: tag name if it isin database else None
        :rtype: string
        """
        something = None
        try:
            self.cursor.execute("SELECT tags FROM tags WHERE tags=?", (tag,))
            something = self.cursor.fetchone()
        except self.database.Error:
            raise DatabaseSelectError(inspect.currentframe().f_code.co_name)
        return something is not None

    def format_is_good(self, fileformat):
        """
        Check format file comparing the fileformat returned by python-magic
        with extension list (self.formats)

        :param fileformat: format file
        :type fileformat: string
        :return: True if the extension matches with the value given
        in paramater (check) else False
        :rtype: bool
        """
        return any(fileformat in s for s in self.formats)

    def id_blob(self, hash_blob):
        """
        Get id blob from hash blob

        :param hash_blob: hash content blob
        :type hash_blob: string
        :return: first case of tuple returned by request SQL
        :rtype:integer (primary key autoincrement)
        """
        try:
            self.cursor.execute('''
            SELECT id_blob FROM blob_demo
            JOIN blob ON id_blob=id WHERE hash=?''',\
            (hash_blob,))
            something = self.cursor.fetchone()
        except self.database.Error:
            raise DatabaseSelectError(inspect.currentframe().f_code.co_name)
        return None if something is None else something[0]


    def id_demo(self, demo):
        """
        Get id demo from name demo

        :param demo: name demo
        :type demo: string
        :return: first case of tuple returned by request SQL
        :rtype:integer (primary key autoincrement)
        """
        try:
            self.cursor.execute('''
            SELECT id_demo FROM blob_demo
            JOIN demo ON id_demo=id
            WHERE name=?''', (demo,))
            something = self.cursor.fetchone()
        except self.database.Error:
            raise DatabaseSelectError(inspect.currentframe().f_code.co_name)
        return None if something is None else something[0]


    def id_tags(self, tag):
        """
        Get id tags from name tag

        :param tag: name tag
        :type tag: string
        :return: fist case of tuple returned by request SQL
        :rtype:integer (primary key autoincrement)
        """
        try:
            self.cursor.execute("SELECT id FROM tags WHERE tags=?", (tag,))
            something = self.cursor.fetchone()
        except self.database.Error:
            raise DatabaseSelectError(inspect.currentframe().f_code.co_name)
        return None if something is None else something[0]

    def delete_demo(self, demoid):
        """
        Delete row (name, iddemo) corresponding to id demo

        :param demoid: id demo
        :type demoid:integer (primary key autoincrement)
        """
        try:
            self.cursor.execute("DELETE FROM demo WHERE id=?", (demoid,))
        except self.database.Error:
            raise DatabaseDeleteError(inspect.currentframe().f_code.co_name)

    def return_list(self):
        """
        Return tuple list of name demo and hash blob

        :return: list tuple [(name, hash_blob)]
        :rtype: list
        """
        try:
            something = self.cursor.execute('''
            SELECT name, hash FROM demo
            JOIN blob_demo ON demo.id=id_demo
            JOIN blob ON id_blob=blob.id''')
        except self.database.Error:
            raise DatabaseSelectError(inspect.currentframe().f_code.co_name)

        lis = []
        for item in something:
            lis.append((item[0], item[1]))

        return lis

    def get_demo_of_hash(self, hash_blob):
        """
        Return list of demo associated with hash blob

        :param demo: hash blob
        :type demo: string
        :return: list of demos
        :rtype: list
        """
        try:
            something = self.cursor.execute('''
            SELECT name FROM demo
            JOIN blob_demo ON demo.id=id_demo
            JOIN blob ON id_blob=blob.id
            WHERE hash=?''', \
            (hash_blob,))
        except self.database.Error:
            raise DatabaseSelectError(inspect.currentframe().f_code.co_name)

        lis = []
        for item in something:
            lis.append(item[0])
        return lis

    def get_hash_of_demo(self, demo):
        """
        Return list of hash blob associated with demo

        :param demo: name demo
        :type demo: string
        :return: list of hash blobs
        :rtype: list
        """
        try:
            something = self.cursor.execute('''
            SELECT hash FROM blob
            JOIN blob_demo ON blob.id=id_blob
            JOIN demo ON id_demo=demo.id
            WHERE name=?''', \
            (demo,))
        except self.database.Error:
            raise DatabaseSelectError(inspect.currentframe().f_code.co_name)

        lis = []
        for item in something:
            lis.append(item[0])
        return lis

    def get_blob_of_tags(self, tag):
        """
        Return list of blob associated with tag

        :param tag: name tag
        :type tag: string
        :return: list of hash blobs
        :rtype: list
        """
        try:
            something = self.cursor.execute('''
            SELECT hash FROM blob
            JOIN blob_tags ON blob.id=id_blob
            JOIN tags ON id_tags=tags.id
            WHERE tags=?''', \
            (tag,))
        except self.database.Error:
            raise DatabaseSelectError(inspect.currentframe().f_code.co_name)

        lis = []
        for item in something:
            lis.append(item[0])
        return lis

    def get_tags_of_blob(self, hash_blob):
        """
        Return list of tag associated with hash blob

        :param hash_blob: hash blob
        :type hash_blob: string
        :return: list of tags
        :rtype: list
        """
        try:
            something = self.cursor.execute('''
            SELECT tags FROM tags
            JOIN blob_tags ON tags.id=id_tags
            JOIN blob ON id_blob=blob.id
            WHERE hash=?''', \
            (hash_blob,))
        except self.database.Error:
            raise DatabaseSelectError(inspect.currentframe().f_code.co_name)

        lis = []
        for item in something:
            lis.append(item[0])
        return lis

    def demo_is_empty(self, demo):
        """
        Check if demo is not associated with a blob
        If it's empty, delete row correspondingin demo column

        :param name: name demo
        :type name: string
        """
        try:
            self.cursor.execute('''
            SELECT COUNT(*) FROM blob_demo
            JOIN demo ON id_demo=id
            WHERE name=?''', \
            (demo,))
            something2 = self.cursor.fetchone()
        except self.database.Error:
            raise DatabaseSelectError(inspect.currentframe().f_code.co_name)

        if something2[0] == 0:
            try:
                self.cursor.execute("DELETE FROM demo WHERE name=?", (demo,))
            except self.database.Error:
                raise DatabaseDeleteError(inspect.currentframe().f_code.co_name)

    def blob_is_empty(self, hash_blob):
        """
        Check if blob named by hash is not associated with a demo
        If it's empty delete row correspondingin blob column

        :param hash_blob: hash blob
        :type hash_blob: string
        :return: number of blob assigned by hash
        :rtype:integer
        """
        try:
            self.cursor.execute('''
            SELECT COUNT(*) FROM blob_demo
            JOIN blob ON id_blob=id
            WHERE hash=?''', \
            (hash_blob,))
            something = self.cursor.fetchone()
        except self.database.Error:
            raise DatabaseSelectError(inspect.currentframe().f_code.co_name)

        if something[0] == 0:
            try:
                self.cursor.execute('''
                DELETE FROM blob
                WHERE hash=?''', \
                (hash_blob,))
            except self.database.Error:
                raise DatabaseDeleteError(inspect.currentframe().f_code.co_name)
        return None if not something[0] else something[0]

    def delete_from_blob_demo(self, demo, hash_blob):
        """
        Delete link between demo and hash blob from blob_demo columnin database
        Delete demo row named by name demo if demo has no blob
        Delete blob row named by hash blob if blob has no demo

        :param demo: name demo
        :type demo: string
        :param hash_blob: hash blob
        :type hash_blob: string
        :return: True if blob named by hash hasn't demo associated else False
        :rtype: bool
        """
        try:
            something = self.cursor.execute('''
            SELECT id_blob, id_demo FROM blob_demo
            JOIN demo ON id_demo=demo.id
            JOIN blob ON id_blob=blob.id
            WHERE name=? AND hash=?''',\
            (demo, hash_blob,))
        except self.database.Error:
            raise DatabaseSelectError(inspect.currentframe().f_code.co_name)

        value = ()
        for item in something:
            value = (item[0], item[1])

        if value:
            try:
                self.cursor.execute('''
                DELETE FROM blob_demo
                WHERE id_blob=? AND id_demo=?''',\
                (value[0], value[1],))
            except self.database.Error:
                raise DatabaseDeleteError(inspect.currentframe().f_code.co_name)

        try:
            something = self.cursor.execute('''
            SELECT id_blob, id_tags FROM blob_tags
            JOIN blob ON id_blob=blob.id AND hash=?''',\
            (hash_blob,))
        except self.database.Error:
            raise DatabaseSelectError(inspect.currentframe().f_code.co_name)

        value = ()
        for item in something:
            value = (item[0], item[1])

        if value:
            try:
                self.cursor.execute('''
                DELETE FROM blob_tags
                WHERE id_blob=? AND id_tags=?''',\
                (value[0], value[1],))
            except self.database.Error:
                raise DatabaseDeleteError(inspect.currentframe().f_code.co_name)

        self.demo_is_empty(demo)
        return self.blob_is_empty(hash_blob)

    def init_tags_column(self):
        """
       insertin tags column defaults tags
        """
        try:
            if not self.tags_is_in_database("BW"):

                self.cursor.execute("INSERT INTO tags(tags) VALUES(?)",
                                    ("BW",))
                self.cursor.execute("INSERT INTO tags(tags) VALUES(?)",
                                    ("Textured",))
                self.cursor.execute("INSERT INTO tags(tags) VALUES(?)",
                                    ("Coloured",))
                self.cursor.execute("INSERT INTO tags(tags) VALUES(?)",
                                    ("Classic",))

        except (self.database.Error, DatabaseError):
            raise DatabaseInsertError(inspect.currentframe().f_code.co_name)

    def commit(self):
        """
        Commit instruction(SELECT, DELETE or INSERT INTO) to database
        """
        self.database.commit()

    def start_transaction(self):
        """
        This instruction allows to start changes on database
        End Transaction is called by commit function
        """
        self.cursor.execute("BEGIN")

    def rollback(self):
        """
        Call rollback functionnality database
        This function is called when exception is caught
        """
        self.database.rollback()


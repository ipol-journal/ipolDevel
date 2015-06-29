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
        self.init_tag_column()

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
                             ext, tag, blobid=-1):
        """
        Add hash blob content and format blob in blob column in database
        Add blob and demo ids in column blob_demo in database
        (necesary for many to many in DBMS)
        Add also tag in database : call addTagInDatabase function

        :param demoid: demo id in database
        :type demoid: integer (primary key autoincrement)
        :param hash_blob: hash content blob
        :type hash_blob: string
        :param fileformat: type format of blob
        :type fileformat: string
        :param ext: extension of blob
        :type ext: string
        :param tag: name tag
        :type tag: string
        :param blobid: if blobid is omitted (= -1), then add blob
        (hash and format) to database esle not add
        :type blobid: integer
        """
        if blobid == -1:
            try:
                self.cursor.execute('''
                INSERT INTO blob(hash, format, extension)
                VALUES(?, ?, ?)''', \
                (hash_blob, fileformat, ext,))
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

        tagid = -1
        if self.tag_is_in_database(tag):
            tagid = self.id_tag(tag)

        self.add_tag_in_database(blobid, tag, tagid)

    def add_tag_in_database(self, blobid, tag, tagid=-1):
        """
        Add a new tagin tag columnin database if it's necessary
        Add blob and tag idsin blob_tagin database

        :param blobid: blob idin database
        :type blobid:integer (primary key autoincrement)
        :param tag: name tag
        :type tag: string
        :param tagid: if blobid is omitted (= -1), then add tag to database
        else not add
        :type tagid:integer
        """
        if tagid == -1:
            try:
                self.cursor.execute("INSERT INTO tag(name) VALUES(?)", (tag,))
                tagid = self.cursor.lastrowid
            except self.database.Error:
                raise DatabaseInsertError(inspect.currentframe().f_code.co_name)

        try:
            self.cursor.execute('''
            INSERT OR REPLACE INTO
            blob_tag(id_blob, id_tag)
            VALUES(?, ?)''', \
            (blobid, tagid,))
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

    def tag_is_in_database(self, tag):
        """
        Check if tag isin database,in column tag

        :param tag: name tag
        :type tag: string
        :return: tag name if it isin database else None
        :rtype: string
        """
        something = None
        try:
            self.cursor.execute("SELECT name FROM tag WHERE name=?", (tag,))
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
            INNER JOIN blob ON blob_demo.id_blob=blob.id WHERE blob.hash=?''',\
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
            INNER JOIN demo ON blob_demo.id_demo=demo.id
            WHERE demo.name=?''', (demo,))
            something = self.cursor.fetchone()
        except self.database.Error:
            raise DatabaseSelectError(inspect.currentframe().f_code.co_name)
        return None if something is None else something[0]


    def id_tag(self, tag):
        """
        Get id tag from name tag

        :param tag: name tag
        :type tag: string
        :return: fist case of tuple returned by request SQL
        :rtype:integer (primary key autoincrement)
        """
        try:
            self.cursor.execute("SELECT id FROM tag WHERE name=?", (tag,))
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
            INNER JOIN blob_demo ON demo.id=blob_demo.id_demo
            INNER JOIN blob ON blob_demo.id_blob=blob.id''')
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
            INNER JOIN blob_demo ON demo.id=blob_demo.id_demo
            INNER JOIN blob ON blob_demo.id_blob=blob.id
            WHERE blob.hash=?''', \
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
            INNER JOIN blob_demo ON blob.id=blob_demo.id_blob
            INNER JOIN demo ON blob_demo.id_demo=demo.id
            WHERE demo.name=?''', \
            (demo,))
        except self.database.Error:
            raise DatabaseSelectError(inspect.currentframe().f_code.co_name)

        lis = []
        for item in something:
            lis.append(item[0])
        return lis

    def get_blob_of_tag(self, tag):
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
            INNER JOIN blob_tag ON blob.id=blob_tag.id_blob
            INNER JOIN tag ON blob_tag.id_tag=tag.id
            WHERE tag.name=?''', \
            (tag,))
        except self.database.Error:
            raise DatabaseSelectError(inspect.currentframe().f_code.co_name)

        lis = []
        for item in something:
            lis.append(item[0])
        return lis

    def get_tag_of_blob(self, hash_blob):
        """
        Return list of tag associated with hash blob

        :param hash_blob: hash blob
        :type hash_blob: string
        :return: list of tag
        :rtype: list
        """
        try:
            something = self.cursor.execute('''
            SELECT name FROM tag
            INNER JOIN blob_tag ON tag.id=blob_tag.id_tag
            INNER JOIN blob ON blob_tag.id_blob=blob.id
            WHERE blob.hash=?''', \
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

        :param demo: name demo
        :type demo: string
        :return: number of demo present in database
        :rtype: tuple of integer or None
        """
        something = None
        try:
            self.cursor.execute('''
            SELECT COUNT(*) FROM blob_demo
            INNER JOIN demo ON id_demo=demo.id
            WHERE demo.name=?''', \
            (demo,))
            something = self.cursor.fetchone()
        except self.database.Error:
            raise DatabaseSelectError(inspect.currentframe().f_code.co_name)
        return None if not something else something

    def delete_demo(self, demo, demo_is_reducible):
        """
        If demo is empty, delete row correspondingin demo column

        :param demo: name demo
        :type demo: string
        :param demo_is_reducible: tuple of integer
        :type demo_is_reducible: tuple or None
        """
        if demo_is_reducible[0] == 0:
            try:
                self.cursor.execute("DELETE FROM demo WHERE name=?", (demo,))
            except self.database.Error:
                raise DatabaseDeleteError(inspect.currentframe().f_code.co_name)

    def blob_is_empty(self, hash_blob):
        """
        Check if blob named by hash is not associated with a demo

        :param hash_blob: hash blob
        :type hash_blob: string
        :return: number of blob present in database
        :rtype: tuple of integer
        """
        something = None
        try:
            self.cursor.execute('''
            SELECT COUNT(*) FROM blob_demo
            INNER JOIN blob ON id_blob=blob.id
            WHERE blob.hash=?''', \
            (hash_blob,))
            something = self.cursor.fetchone()
        except self.database.Error:
            raise DatabaseSelectError(inspect.currentframe().f_code.co_name)
        return None if not something else something

    def delete_blob(self, hash_blob, blob_is_reducible):
        """
        If blob is empty delete row correspondingin blob column

        :param hash_blob: hash blob
        :type hash_blob: string
        :param blob_is_reducible: tuple of integer
        :type blob_is_reducible: tuple or None
        """
        if blob_is_reducible[0] == 0:
            try:
                self.cursor.execute('''
                DELETE FROM blob
                WHERE hash=?''', \
                (hash_blob,))
            except self.database.Error:
                raise DatabaseDeleteError(inspect.currentframe().f_code.co_name)

    def delete_blob_from_demo(self, demo, hash_blob):
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
            INNER JOIN demo ON blob_demo.id_demo=demo.id
            INNER JOIN blob ON blob_demo.id_blob=blob.id
            WHERE demo.name=? AND blob.hash=?''',\
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
            SELECT id_blob, id_tag FROM blob_tag
            INNER JOIN blob ON blob_tag.id_blob=blob.id AND blob.hash=?''',\
            (hash_blob,))
        except self.database.Error:
            raise DatabaseSelectError(inspect.currentframe().f_code.co_name)

        value = ()
        for item in something:
            value = (item[0], item[1])

        if value:
            try:
                self.cursor.execute('''
                DELETE FROM blob_tag
                WHERE id_blob=? AND id_tag=?''',\
                (value[0], value[1],))
            except self.database.Error:
                raise DatabaseDeleteError(inspect.currentframe().f_code.co_name)

        demo_is_reducible = self.demo_is_empty(demo)
        self.delete_demo(demo, demo_is_reducible)
        blob_is_reducible = self.blob_is_empty(hash_blob)
        self.delete_blob(hash_blob, blob_is_reducible)
        return None if not blob_is_reducible[0] else blob_is_reducible[0]

    def init_tag_column(self):
        """
       insertin tag column defaults tag
        """
        try:
            if not self.tag_is_in_database("BW"):

                self.cursor.execute("INSERT INTO tag(name) VALUES(?)",
                                    ("BW",))
                self.cursor.execute("INSERT INTO tag(name) VALUES(?)",
                                    ("Textured",))
                self.cursor.execute("INSERT INTO tag(name) VALUES(?)",
                                    ("Coloured",))
                self.cursor.execute("INSERT INTO tag(name) VALUES(?)",
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


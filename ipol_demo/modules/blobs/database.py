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
    One instance of this object represents one connection to the database
    """
    def __init__(self, name):
        """
        Initialize database class
        Connect to databse

        :param name: database name
        :type name: string
        """
        self.formats = ('audio', 'image', 'video')
        self.name = name
        self.database = lite.connect(name, check_same_thread=False)
        self.cursor = self.database.cursor()
        self.init_tag_column()

    def __del__(self):
        """
        Destructor: Close the connection
        """
        self.database.close()

    def add_demo_in_database(self, demo, is_template, id_template):
        """
        Add name demo in demo column in database

        :param demo: name demo
        :type demo: string
        :param is_template: if demo is template equal 1 else 0
        :type is_template: boolean cast in integer
        :param id_template: id templated demo used
        :type id_template: integer
        """
        try:
            if not self.demo_is_in_database(demo):
                if is_template == '0':
                    if id_template == None:
                        self.cursor.execute('''
                        INSERT INTO demo(name)
                        VALUES(?)''', (demo,))
                    else:
                        self.cursor.execute('''
                        INSERT INTO demo(name, id_template)
                        VALUES(?, ?)''', (demo, id_template,))
                else:
                    self.cursor.execute('''
                    INSERT INTO demo(name, is_template) VALUES(?, ?)''', (demo, is_template,))
        except self.database.Error:
            raise DatabaseInsertError(inspect.currentframe().f_code.co_name)

    def add_blob_in_database(self, demoid, hash_blob, fileformat,
                             ext, tag, the_set,
                             title, credit, blobid=-1):
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
        :param the_set: set of blob
        :type the_set: string
        :param title: title blob
        :type title: string
        :param credit: credit blob
        :type credit: string
        :param blobid: if blobid is omitted (= -1), then add blob
        (hash and format) to database esle not add
        :type blobid: integer
        """
        if blobid == -1:
            try:
                self.cursor.execute('''
                INSERT INTO blob(hash, format, extension, title, credit)
                VALUES(?, ?, ?, ?, ?)''', \
                (hash_blob, fileformat, ext, title, credit,))
                blobid = self.cursor.lastrowid
            except self.database.Error:
                raise DatabaseInsertError(inspect.currentframe().f_code.co_name)

        try:
            self.cursor.execute(
                '''INSERT OR REPLACE INTO
                blob_demo(id_blob, id_demo, set_blob)
                VALUES(?, ?, ?)''', \
                (blobid, demoid, the_set,))

        except self.database.Error:
            raise DatabaseInsertError(inspect.currentframe().f_code.co_name)

        self.add_tag_in_database(blobid, tag)

    def add_tag_in_database(self, blobid, tag):
        """
        Add a new tag in tag columnin database if it's necessary
        Add blob and tag idsin blob_tagin database

        :param blobid: blob idin database
        :type blobid:integer (primary key autoincrement)
        :param tag: name tag
        :type tag: string
        :param tagid: if blobid is omitted (= -1), then add tag to database
        else not add
        :type tagid:integer
        """
        if type(tag) == unicode and tag:
            try:
                tagid = -1
                if self.tag_is_in_database(tag):
                    tagid = self.id_tag(tag)

                if tagid == -1:
                    self.cursor.execute("INSERT INTO tag(name) VALUES(?)", \
                                        (tag,))
                    tagid = self.cursor.lastrowid
            except self.database.Error, DatabaseError:
                raise DatabaseInsertError(inspect.currentframe().f_code.co_name)

            try:
                self.cursor.execute('''
                INSERT OR REPLACE INTO
                blob_tag(id_blob, id_tag)
                VALUES(?, ?)''', \
                (blobid, tagid,))
            except self.database.Error:
                raise DatabaseInsertError(inspect.currentframe().f_code.co_name)

        else:
            for item in tag:
                tagid = -1
                if self.tag_is_in_database(item):
                    tagid = self.id_tag(item)

                if tagid == -1:
                    try:
                        self.cursor.execute("INSERT INTO tag(name) VALUES(?)", \
                                            (item,))
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
        Check if demo is in database,in column demo

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
            SELECT demo.id FROM demo
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

    def delete_demo_existed(self, demoid):
        """
        Delete row (name, id, is_template, id_template) corresponding to id demo

        :param demoid: id demo
        :type demoid:integer (primary key autoincrement)
        """
        try:
            self.cursor.execute("DELETE FROM demo WHERE id=?", (demoid,))
        except self.database.Error:
            raise DatabaseDeleteError(inspect.currentframe().f_code.co_name)

    def get_blobs_of_demo(self, demo_id):
        """
        Return list of hash blob associated with demo

        :param demo_id: id demo
        :type demo_id: integer
        :return: blob infos associated to demo
        :rtype: list of dictionnary
        """
        try:
            something = self.cursor.execute('''
            SELECT blob.id, blob.hash, blob.extension, blob.format FROM blob
            INNER JOIN blob_demo ON blob.id=blob_demo.id_blob
            INNER JOIN demo ON blob_demo.id_demo=demo.id
            WHERE demo.id=?''', \
            (demo_id,))
        except self.database.Error:
            raise DatabaseSelectError(inspect.currentframe().f_code.co_name)

        lis = []
        for item in something:
            lis.append({"id": item[0], "hash" : item[1], "extension": item[2],
                        "format": item[3]})
        return lis

    def get_demo_name_from_id(self, demo_id):
        """
        Return name of the demo from id

        :param demo_id: id demo
        ::type demo_id: integer
        :return: name, is template, id template
        :rtype: dictionnary
        """
        dic = {}
        try:
            self.cursor.execute('''
            SELECT id, name, is_template, id_template
            FROM demo
            WHERE demo.id=?''',\
            (demo_id,))
            something = self.cursor.fetchone()
            dic[something[0]] = {"name": something[1], "is_template": something[2],
                                 "id_template": something[3]}

        except self.database.Error:
            raise DatabaseSelectError(inspect.currentframe().f_code.co_name)

        return dic

    def get_blob_of_tag(self, tag):
        """
        Return list of blob associated with list of tag

        :param tag: list name tag
        :type tag: list of string
        :return: list of hash blobs
        :rtype: list
        """
        try:
            something = self.cursor.execute('''
            SELECT hash FROM blob
            INNER JOIN blob_tag ON blob.id=blob_tag.id_blob
            INNER JOIN tag ON blob_tag.id_tag=tag.id
            WHERE tag.name IN (%s)''' % \
            ("?," * len(tag))[:-1], tag)
        except self.database.Error:
            raise DatabaseSelectError(inspect.currentframe().f_code.co_name)

        lis = []
        for item in something:
            lis.append(item[0])
        return lis

    def get_tags_of_blob(self, blob_id):
        """
        Return list of tag associated with hash blob

        :param blob_id: id blob
        :type blob_id: integer
        :return: list of tag
        :rtype: dictionnary
        """
        try:
            something = self.cursor.execute('''
            SELECT tag.id, tag.name FROM tag
            INNER JOIN blob_tag ON tag.id=blob_tag.id_tag
            INNER JOIN blob ON blob_tag.id_blob=blob.id
            WHERE blob.id=?''', \
            (blob_id,))
        except self.database.Error:
            raise DatabaseSelectError(inspect.currentframe().f_code.co_name)

        lis = {}
        for item in something:
            lis[item[0]] = item[1]
        return lis

    def demo_is_empty(self, demo_id):
        """
        Check if demo is not associated with a blob

        :param demo_id: id demo
        :type demo_id: integer
        :return: number of demo present in database
        :rtype: tuple of integer or None
        """
        something = None
        try:
            self.cursor.execute('''
            SELECT COUNT(*) FROM blob_demo
            INNER JOIN demo ON id_demo=demo.id
            WHERE demo.id=?''', \
            (demo_id,))
            something = self.cursor.fetchone()
        except self.database.Error:
            raise DatabaseSelectError(inspect.currentframe().f_code.co_name)
        return None if not something else something


    def delete_demo(self, demo_id, demo_is_reducible):
        """
        If demo is empty, delete row corresponding in demo column

        :param demo_id: id demo
        :type demo_id: integer
        :param demo_is_reducible: tuple of integer
        :type demo_is_reducible: tuple or None
        """
        if demo_is_reducible[0] == 0:
            try:
                self.cursor.execute("DELETE FROM demo WHERE demo.id=?", (demo_id,))
            except self.database.Error:
                raise DatabaseDeleteError(inspect.currentframe().f_code.co_name)

    def blob_is_empty(self, blob_id):
        """
        Check if blob named by hash is not associated with a demo

        :param blob_id: id blob
        :type blob_id: string
        :return: number of blob present in database
        :rtype: tuple of integer
        """
        something = None
        try:
            self.cursor.execute('''
            SELECT COUNT(*) FROM blob_demo
            INNER JOIN blob ON id_blob=blob.id
            WHERE blob.id=?''', \
            (blob_id,))
            something = self.cursor.fetchone()
        except self.database.Error:
            raise DatabaseSelectError(inspect.currentframe().f_code.co_name)
        return None if not something else something

    def delete_blob(self, blob_id, blob_is_reducible):
        """
        If blob is empty delete row corresponding in blob column

        :param blob_id: id blob
        :type blob_id: integer
        :param blob_is_reducible: tuple of integer
        :type blob_is_reducible: tuple or None
        """
        if blob_is_reducible[0] == 0:
            try:
                self.cursor.execute('''
                DELETE FROM blob
                WHERE blob.id=?''', \
                (blob_id,))
            except self.database.Error:
                raise DatabaseDeleteError(inspect.currentframe().f_code.co_name)

    def tag_is_empty(self, tag_id):
        """
        Check if tag is not associated with a blob

        :param tag_id: id tag
        :type tag_id: integer
        :return: number of tag present in database
        :rtype: tuple of integer or None
        """
        something = None
        try:
            self.cursor.execute('''
            SELECT COUNT(*) FROM blob_tag
            INNER JOIN tag ON id_tag=tag.id
            WHERE tag.id=?''',\
            (tag_id,))
            something = self.cursor.fetchone()
        except self.database.Error:
            raise DatabaseSelectError(inspect.currentframe().f_code.co_name)
        return None if not something else something

    def delete_tag(self, tag_id, tag_is_reducible):
        """
        If tag is empty, delete row corresponding in tag column

        :param tag_id: id tag
        :type tag_id: integer
        :param tag_is_reducible: tag is empty (not associated to any blob)
        :type tag_is_reducible: integer
        """
        if tag_is_reducible[0] == 0:
            try:
                self.cursor.execute('''
                DELETE FROM tag
                WHERE tag.id=?''',\
                (tag_id,))
            except self.database.Error:
                raise DatabaseDeleteError(inspect.currentframe().f_code.co_name)

    def delete_blob_from_demo(self, demo_id, blob_id):
        """
        Delete link between demo and hash blob from blob_demo column in database
        Delete link between blob and tag from blob_tag column in database
        Delete demo row named by name demo if demo has no blob
        Delete tag row associated to blob if tag has no blob
        Delete blob row named by hash blob if blob has no demo

        :param demo_id: id demo
        :type demo_id: integer
        :param blob_id: id blob
        :type blob_id: integer
        :return: True if blob named by id hasn't demo associated else False
        :rtype: bool
        """
        try:
            something = self.cursor.execute('''
            SELECT id_blob, id_demo FROM blob_demo
            INNER JOIN demo ON blob_demo.id_demo=demo.id
            INNER JOIN blob ON blob_demo.id_blob=blob.id
            WHERE demo.id=? AND blob.id=?''',\
            (demo_id, blob_id,))
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
            INNER JOIN blob ON blob_tag.id_blob=blob.id AND blob.id=?''',\
            (blob_id,))
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

        self.delete_all_tag(blob_id)
        blob_is_reducible = self.blob_is_empty(blob_id)
        self.delete_blob(blob_id, blob_is_reducible)
        return None if not blob_is_reducible[0] else blob_is_reducible[0]

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

    def get_list_tags(self):
        """
        Return the list of tag present in database

        :return: list of name tag
        :rtype: list of string
        """
        something = self.cursor.execute("SELECT name FROM tag")
        lis = []
        for item in something:
            lis.append(item[0])
        return lis

    def init_tag_column(self):
        """
        Inserting tag column defaults tag
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
        except self.database.Error, DatabaseError:
            raise DatabaseInsertError(inspect.currentframe().f_code.co_name)


    def list_of_demos(self):
        """
        Return the name list of demos

        :return: name demos
        :rtype: dictionnary
        """
        try:
            something = self.cursor.execute('''
            SELECT id, name, is_template, id_template
            FROM demo''')
        except self.database.Error:
            raise DatabaseSelectError(inspect.currentframe().f_code.co_name)

        lis = {}
        for item in something:
            lis[item[0]] = {"name": item[1], "is_template": item[2], "id_template": item[3]}
        return lis

    def get_name_blob(self, blob_id):
        """
        Return the name of the blob from id

        :param blob_id: id blob
        :type blob_id: integer
        :return: hash of the blob with extension
        :rtype: string
        """
        try:
            something = self.cursor.execute('''
            SELECT hash, extension FROM blob
            WHERE blob.id=?''', \
            (blob_id,))
        except self.database.Error:
            raise DatabaseSelectError(inspect.currentframe().f_code.co_name)

        value = ()
        for item in something:
            value = (item[0], item[1])

        return value[0] + value[1] if value else value

    def get_blob(self, blob_id):
        """
        Return the infos blob from id blob

        :param blob_id: id blob
        :type blob_id: integer
        :return: id, hash, extension and credit of blob
        :rtype: dictionnary
        """
        dic = {}
        try:
            self.cursor.execute('''
            SELECT id, hash, extension, credit FROM blob
            WHERE blob.id=?''', \
            (blob_id,))
            something = self.cursor.fetchone()
            dic = {"id": something[0], "hash": something[1], "extension": something[2],
               "credit": something[3]}
        except self.database.Error:
            raise DatabaseSelectError(inspect.currentframe().f_code.co_name)

        return dic

    def delete_tag_from_blob(self, tag_id, blob_id):
        """
        Delete link between tag and blob
        Delete tag if it is not associated to blob

        :param tag_id: id tag
        :type tag_id: integer
        :param blob_id: id blob
        :type blob_id: integer
        """
        try:
            self.cursor.execute('''
            DELETE FROM blob_tag
            WHERE id_tag=? AND id_blob=?''',
            (tag_id, blob_id))
        except self.database.Error:
            raise DatabaseDeleteError(inspect.currentframe().f_code.co_name)

        demo_is_reducible = self.tag_is_empty(tag_id)
        self.delete_tag(tag_id, demo_is_reducible)


    def delete_all_tag(self, blob_id):
        """
        Delete all tags from the blob because blob is delete

        :param blob_id: id blob
        :type blob_id: integer
        """
        something = None
        try:
            self.cursor.execute('''
            SELECT tag.id FROM tag
            INNER JOIN blob_tag ON tag.id=id_tag
            INNER JOIN blob ON id_blob=blob.id
            WHERE blob.id=?''',\
            (blob_id,))
            something = self.cursor.fetchone()
            if something:
                for item in something:
                    self.delete_tag_from_blob(item, blob_id)

        except self.database.Error, DatabaseDeleteError:
            raise DatabaseSelectError(inspect.currentframe().f_code.co_name)


    def list_of_template(self):
        """
        Return the list templated demo

        :return: list of templated demo
        :type: dictionnary
        """
        try:
            something = self.cursor.execute('''
            SELECT id, name
            FROM demo
            WHERE is_template=1''')
        except self.database.Error:
            raise DatabaseSelectError(inspect.currentframe().f_code.co_name)

        lis = {}
        for item in something:
            lis[item[0]] = {"name": item[1]}
        return lis


    def remove_demo(self, demo_id):
        """
        Remove demo of the database, and blob and tag associated

        :param demo_id: id demo
        :type demo_id: integer
        """
        try:
            self.list_templated_demo_using_from_demo(demo_id)
            something = self.cursor.execute('''
            SELECT blob.id FROM blob
            INNER JOIN blob_demo ON blob.id=blob_demo.id_blob
            INNER JOIN demo ON blob_demo.id_demo=demo.id
            WHERE demo.id=?''', \
            (demo_id,))
            lis = []
            for item in something:
                lis.append(item[0])

            for item in lis:
                self.delete_blob_from_demo(demo_id, item)
            demo_is_reducible = self.demo_is_empty(demo_id)
            self.delete_demo(demo_id, demo_is_reducible)
        except self.database.Error, DatabaseSelectError:
            raise DatabaseDeleteError(inspect.currentframe().f_code.co_name)


    def demo_use_template(self, demo_id):
        """
        Return the name of the templated demo used by another demo

        :param demo_id: id demo
        :type demo_id: integer
        :return: name of templated demo used
        :rtype: dictionnary
        """
        dic = {}
        try:
            self.cursor.execute('''
            SELECT is_template, id_template
            FROM demo
            WHERE demo.id=?''',\
            (demo_id,))
            something = self.cursor.fetchone()
            if something[0] == 0 and something[1] != 0:
                dic = self.get_demo_name_from_id(something[1])[something[1]]
        except DatabaseError, DatabaseSelectError:
            raise DatabaseSelectError(inspect.currentframe().f_code.co_name)

        return dic


    def update_template(self, demo_id, id_template):
        """
        Update the template used by another demo

        :param demo_id: id demo (current demo)
        :type demo_id: integer
        :param id_template: id demo templated used by current demo
        :type id_template: integer
        """
        try:
            self.cursor.execute('''
            UPDATE demo SET id_template=?
            WHERE demo.id=?''', \
            (id_template, demo_id,))
        except DatabaseError:
            raise DatabaseUpdateError(inspect.currentframe().f_code.co_name)

    def list_templated_demo_using_from_demo(self, id_demo):
        """
        Update id template of demo using templated demo defined by id

        :param id_demo: id demo
        :type id_demo: integer
        """
        try:
            self.cursor.execute('''
            UPDATE demo SET id_template=0
            WHERE id_template=?''',\
            (id_demo,))
        except DatabaseError:
            raise DatabaseUpdateError(inspect.currentframe().f_code.co_name)

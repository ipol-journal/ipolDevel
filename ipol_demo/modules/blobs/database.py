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

    def add_demo_in_database(self, demo, is_template, template_id):
        """
        Add name demo in demo column in database

        :param demo: name demo
        :type demo: string
        :param is_template: if demo is template equal 1 else 0
        :type is_template: boolean cast in integer
        :param template_id: id templated demo used
        :type template_id: integer
        """
        try:
            if not self.demo_is_in_database(demo):
                if is_template == '0':
                    if template_id == None:
                        self.cursor.execute('''
                        INSERT INTO demo(name)
                        VALUES(?)''', (demo,))
                    else:
                        self.cursor.execute('''
                        INSERT INTO demo(name, template_id)
                        VALUES(?, ?)''', (demo, template_id,))
                else:
                    self.cursor.execute('''
                    INSERT INTO demo(name, is_template) VALUES(?, ?)''', (demo, is_template,))
        except self.database.Error:
            raise DatabaseInsertError(inspect.currentframe().f_code.co_name)

    def add_blob_in_database(self, demoid, hash_blob, fileformat,
                             ext, tag, blob_set, blob_id_in_set,
                             title, credit, blobid=-1):
        """
        Add hash blob content and format blob in blob column in database
        Add blob and demo ids in column demo_blob in database
        (necesary for many to many in DBMS)
        Add also tag in database : call addTagInDatabase function

        :param demoid: demo id in database integer (primary key autoincrement)
        :param hash_blob: hash content blob string
        :param fileformat: type format of blob string
        :param ext: extension of blob string
        :param tag: name tag string
        :param blob_set: set  blob string
        :param blob_id_in_set: set  blob id in its set
        :param title: title blob string
        :param credit: credit blob string
        :param blobid: if blobid is omitted (= -1), then add blob
        (hash and format) to database else do not add, integer
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
                demo_blob(blob_id, demo_id, blob_set,blob_id_in_set)
                VALUES(?, ?, ?, ?)''', \
                (blobid, demoid, blob_set,blob_id_in_set,))

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
                    tagid = self.tag_id(tag)

                if tagid == -1:
                    self.cursor.execute("INSERT INTO tag(name) VALUES(?)", \
                                        (tag,))
                    tagid = self.cursor.lastrowid
            except self.database.Error, DatabaseError:
                raise DatabaseInsertError(inspect.currentframe().f_code.co_name)

            try:
                self.cursor.execute('''
                INSERT OR REPLACE INTO
                blob_tag(blob_id, tag_id)
                VALUES(?, ?)''', \
                (blobid, tagid,))
            except self.database.Error:
                raise DatabaseInsertError(inspect.currentframe().f_code.co_name)

        else:
            for item in tag:
                tagid = -1
                if self.tag_is_in_database(item):
                    tagid = self.tag_id(item)

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
                    blob_tag(blob_id, tag_id)
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

    def blob_id(self, hash_blob):
        """
        Get id blob from hash blob

        :param hash_blob: hash content blob
        :type hash_blob: string
        :return: first case of tuple returned by request SQL
        :rtype:integer (primary key autoincrement)
        """
        try:
            self.cursor.execute('''
            SELECT blob_id FROM demo_blob
            INNER JOIN blob ON demo_blob.blob_id=blob.id WHERE blob.hash=?''',\
            (hash_blob,))
            something = self.cursor.fetchone()
        except self.database.Error:
            raise DatabaseSelectError(inspect.currentframe().f_code.co_name)
        return None if something is None else something[0]

    def demo_id(self, demo):
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

    def tag_id(self, tag):
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
        Delete row (name, id, is_template, template_id) corresponding to id demo

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
        :return: blob infos (id, hash, extension, format, title, credit) associated to demo
        :rtype: list of dictionnary
        """
        print "Database.get_blobs_of_demo({0})".format(demo_id)
        
        # 
        try:
          self.cursor.execute('''
            SELECT  blob_set, GROUP_CONCAT(blob_id)  FROM demo_blob
            INNER JOIN demo ON demo_blob.demo_id=demo.id
            INNER JOIN blob ON demo_blob.blob_id=blob.id
            WHERE demo.id=? GROUP BY blob_set ''', (demo_id,))
        except self.database.Error:
          print "exception"
          raise DatabaseSelectError(inspect.currentframe().f_code.co_name)

        blobsets_list = self.cursor.fetchall()
        
        blobset_list = []
        for blobset in blobsets_list:
          try:
            self.cursor.execute('''
              SELECT  blob.id, demo_blob.blob_id_in_set,
                      blob.hash, blob.extension, blob.format, 
                      blob.title, blob.credit FROM demo_blob
              INNER JOIN demo ON demo_blob.demo_id=demo.id
              INNER JOIN blob ON demo_blob.blob_id=blob.id
              WHERE demo.id=? AND blob_set=?''', (demo_id,blobset[0],))
          except self.database.Error:
            print "exception"
            raise DatabaseSelectError(inspect.currentframe().f_code.co_name)
          
          blobset_blobs = self.cursor.fetchall()
          blob_list = [{ 'set_name':blobset[0], 'size':len(blobset_blobs) } ]
          for b in  blobset_blobs:
            # get blob tags
            tags = self.get_tags_of_blob( b[0])
            
            tag_str = ''
            print "tags = ",tags
            for tid in tags:
                tag_str += ", "+tags[tid]

            # now get blobs of each set
            blob_list.append(
                        { "id": b[0], "id_in_set": b[1], "hash" : b[2], "extension": b[3],
                          "format": b[4], "title":b[5], "credit":b[6], 'tag':tag_str }
                      )
          blobset_list.append(blob_list)
        
        #print blobset_list
        return blobset_list

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
            SELECT id, name, is_template, template_id
            FROM demo
            WHERE demo.id=?''',\
            (demo_id,))
            something = self.cursor.fetchone()
            dic[something[0]] = {"name": something[1], "is_template": something[2],
                                 "template_id": something[3]}

        except self.database.Error:
            raise DatabaseSelectError(inspect.currentframe().f_code.co_name)

        return dic

    def get_demo_info_from_name(self, demo_name):
        """
        Return name of the demo info: name, is_template, template_id from the 
        demo name

        :param demo_name: demo name
        ::type demo_name: string
        :return: name, is template, id template
        :rtype: dictionnary
        """
        dic = {}
        try:
            self.cursor.execute('''
            SELECT id, name, is_template, template_id
            FROM demo
            WHERE demo.name=?''',\
            (demo_name,))
            something = self.cursor.fetchone()
            dic[something[0]] = {"name": something[1], "is_template": something[2],
                                 "template_id": something[3]}

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
            INNER JOIN blob_tag ON blob.id=blob_tag.blob_id
            INNER JOIN tag ON blob_tag.tag_id=tag.id
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
            INNER JOIN blob_tag ON tag.id=blob_tag.tag_id
            INNER JOIN blob ON blob_tag.blob_id=blob.id
            WHERE blob.id=?''', \
            (blob_id,))
        except self.database.Error:
            raise DatabaseSelectError(inspect.currentframe().f_code.co_name)

        lis = {}
        for item in something:
            lis[item[0]] = item[1]
        return lis

    def get_tag_name(self, tag_id):
        """
        Return tag name associated to tag id

        """
        try:
            tagname = self.cursor.execute('''
            SELECT  tag.name FROM tag
            WHERE tag.id=?''', \
            (tag_id,))
        except self.database.Error:
            raise DatabaseSelectError(inspect.currentframe().f_code.co_name)

        return tagname

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
            SELECT COUNT(*) FROM demo_blob
            INNER JOIN demo ON demo_id=demo.id
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

    #---------------------------------------------------------------------------
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
            SELECT COUNT(*) FROM demo_blob
            INNER JOIN blob ON blob_id=blob.id
            WHERE blob.id=?''', \
            (blob_id,))
            something = self.cursor.fetchone()
        except self.database.Error:
            raise DatabaseSelectError(inspect.currentframe().f_code.co_name)
        return None if not something else something

    #---------------------------------------------------------------------------
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

    #---------------------------------------------------------------------------
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
            INNER JOIN tag ON tag_id=tag.id
            WHERE tag.id=?''',\
            (tag_id,))
            something = self.cursor.fetchone()
        except self.database.Error:
            raise DatabaseSelectError(inspect.currentframe().f_code.co_name)
        return None if not something else something

    #---------------------------------------------------------------------------
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


    #---------------------------------------------------------------------------
    def delete_blobset_from_demo(self, demo_id, blobset):
        """
        Delete link between demo and hash blob from demo_blob column in database
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
            result = self.cursor.execute('''
            SELECT blob_id, demo_id FROM demo_blob
            INNER JOIN demo ON demo_blob.demo_id=demo.id
            INNER JOIN blob ON demo_blob.blob_id=blob.id
            WHERE demo.id=? AND blob.id=?''',\
            (demo_id, blob_id,))
        except self.database.Error:
            raise DatabaseSelectError(inspect.currentframe().f_code.co_name)

        value = ()
        for item in result:
            value = (item[0], item[1])

        if value:
            try:
                self.cursor.execute('''
                DELETE FROM demo_blob
                WHERE blob_id=? AND demo_id=?''',\
                (value[0], value[1],))
            except self.database.Error:
                raise DatabaseDeleteError(inspect.currentframe().f_code.co_name)

        try:
            result = self.cursor.execute('''
            SELECT blob_id, tag_id FROM blob_tag
            INNER JOIN blob ON blob_tag.blob_id=blob.id AND blob.id=?''',\
            (blob_id,))
        except self.database.Error:
            raise DatabaseSelectError(inspect.currentframe().f_code.co_name)

        value = ()
        for item in result:
            value = (item[0], item[1])

        if value:
            try:
                self.cursor.execute('''
                DELETE FROM blob_tag
                WHERE blob_id=? AND tag_id=?''',\
                (value[0], value[1],))
            except self.database.Error:
                raise DatabaseDeleteError(inspect.currentframe().f_code.co_name)

        self.delete_all_tag(blob_id)
        blob_is_reducible = self.blob_is_empty(blob_id)
        self.delete_blob(blob_id, blob_is_reducible)
        return None if not blob_is_reducible[0] else blob_is_reducible[0]


    #---------------------------------------------------------------------------
    def delete_blob_from_demo(self, demo_id, blobset, blob_id):
        """
        Delete link between demo and hash blob from demo_blob column in database
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
            result = self.cursor.execute('''
            SELECT blob_id, demo_id, blob_set FROM demo_blob
            INNER JOIN demo ON demo_blob.demo_id=demo.id
            INNER JOIN blob ON demo_blob.blob_id=blob.id
            WHERE demo.id=? AND blob.id=? AND demo_blob.blob_set=? ''',\
            (demo_id, blob_id,blobset))
        except self.database.Error:
            raise DatabaseSelectError(inspect.currentframe().f_code.co_name)

        value = ()
        for item in result:
            value = (item[0], item[1], item[2])

        if value:
            try:
                self.cursor.execute('''
                DELETE FROM demo_blob
                WHERE blob_id=? AND demo_id=? AND blob_set=? ''',\
                (value[0], value[1],value[2]))
            except self.database.Error:
                raise DatabaseDeleteError(inspect.currentframe().f_code.co_name)

        try:
            result = self.cursor.execute('''
            SELECT blob_id, tag_id FROM blob_tag
            INNER JOIN blob ON blob_tag.blob_id=blob.id AND blob.id=?''',\
            (blob_id,))
        except self.database.Error:
            raise DatabaseSelectError(inspect.currentframe().f_code.co_name)

        value = ()
        for item in result:
            value = (item[0], item[1])

        if value:
            try:
                self.cursor.execute('''
                DELETE FROM blob_tag
                WHERE blob_id=? AND tag_id=?''',\
                (value[0], value[1],))
            except self.database.Error:
                raise DatabaseDeleteError(inspect.currentframe().f_code.co_name)

        self.delete_all_tag(blob_id)
        blob_is_reducible = self.blob_is_empty(blob_id)
        self.delete_blob(blob_id, blob_is_reducible)
        return None if not blob_is_reducible[0] else blob_is_reducible[0]

    #---------------------------------------------------------------------------
    def commit(self):
        """
        Commit instruction(SELECT, DELETE or INSERT INTO) to database
        """
        self.database.commit()

    #---------------------------------------------------------------------------
    def start_transaction(self):
        """
        This instruction allows to start changes on database
        End Transaction is called by commit function
        """
        self.cursor.execute("BEGIN")

    #---------------------------------------------------------------------------
    def rollback(self):
        """
        Call rollback functionnality database
        This function is called when exception is caught
        """
        self.database.rollback()

    #---------------------------------------------------------------------------
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

    #---------------------------------------------------------------------------
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


    #---------------------------------------------------------------------------
    def list_of_demos(self):
        """
        Return the name list of demos

        :return: name demos
        :rtype: dictionnary
        """
        try:
            self.cursor.execute('''
            SELECT id, name, is_template, template_id
            FROM demo''')
        except self.database.Error:
            raise DatabaseSelectError(inspect.currentframe().f_code.co_name)

        #jak
        #todo  change json schema, avoun int keys
        #lis = {}
        #for item in something:
        #    lis[item[0]] = {"name": item[1], "is_template": item[2], "template_id": item[3]}

        demos_info = self.cursor.fetchall()

        lis = list()
        for item in demos_info:
            try:
                blob_sets = self.cursor.execute('''
                    SELECT  blob_set  FROM demo_blob
                    INNER JOIN demo ON demo_blob.demo_id=demo.id
                    INNER JOIN blob ON demo_blob.blob_id=blob.id
                    WHERE demo.id=? GROUP BY blob_set ''', (item[0],))
            except self.database.Error:
                print "exception"
                raise DatabaseSelectError(inspect.currentframe().f_code.co_name)

            #blobsets_list = self.cursor.fetchall()
            print item[0]
            #print blobsets_list
            length= len(blob_sets.fetchall())
            
            lis.append({"id": item[0], "name": item[1], "is_template": item[2], "template_id": item[3], "length": length } ) 
        return lis

    def get_blob_name(self, blob_id):
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
            WHERE tag_id=? AND blob_id=?''',
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
            INNER JOIN blob_tag ON tag.id=tag_id
            INNER JOIN blob ON blob_id=blob.id
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
            INNER JOIN demo_blob ON blob.id=demo_blob.blob_id
            INNER JOIN demo ON demo_blob.demo_id=demo.id
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
            SELECT is_template, template_id
            FROM demo
            WHERE demo.id=?''',\
            (demo_id,))
            something = self.cursor.fetchone()
            if something[0] == 0 and something[1] != 0:
                dic = self.get_demo_name_from_id(something[1])[something[1]]
        except DatabaseError, DatabaseSelectError:
            raise DatabaseSelectError(inspect.currentframe().f_code.co_name)

        return dic


    def update_template(self, demo_id, template_id):
        """
        Update the template used by another demo

        :param demo_id: id demo (current demo)
        :type demo_id: integer
        :param template_id: id demo templated used by current demo
        :type template_id: integer
        """
        try:
            self.cursor.execute('''
            UPDATE demo SET template_id=?
            WHERE demo.id=?''', \
            (template_id, demo_id,))
        except DatabaseError:
            raise DatabaseUpdateError(inspect.currentframe().f_code.co_name)

    def list_templated_demo_using_from_demo(self, demo_id):
        """
        Update id template of demo using templated demo defined by id

        :param demo_id: id demo
        :type demo_id: integer
        """
        try:
            self.cursor.execute('''
            UPDATE demo SET template_id=0
            WHERE template_id=?''',\
            (demo_id,))
        except DatabaseError:
            raise DatabaseUpdateError(inspect.currentframe().f_code.co_name)

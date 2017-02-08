#!/usr/bin/env python
# -*- coding:utf-8 -*-

"""
This file implements database class
"""

import os
import os.path
import sys

import sqlite3 as lite
from error import DatabaseInsertError, DatabaseSelectError, \
DatabaseDeleteError, DatabaseError, DatabaseUpdateError

class   Database(object):
    """
    This class implements database management
    The database architecture is defined in file /db/blob.sql
    One instance of this object represents one connection to the database
    """
    def __init__(self, database_dir, database_name, logger):
        """
        Initialize database class
        Connect to databse

        :param name: database name
        :type name: string
        """
        self.logger = logger
        self.formats = ('audio', 'image', 'video')

        self.database_dir = database_dir

        self.database_file = os.path.join(database_dir, database_name)
        self.status = self.init_database()
        if not self.status:
            sys.exit("Initialisation of database failed. Check the logs.")

        self.database = lite.connect(self.database_file, check_same_thread=False)
        self.cursor = self.database.cursor()
        self.init_tag_column()

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
                self.logger.warning(str(self.database_file) + \
                                    ' is empty. Removing the file...')
                try:
                    self.logger.warning('Database file was empty')
                    os.remove(self.database_file)
                except Exception as ex:
                    self.logger.exception(str(ex))
                    status = False
                    return status

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
                self.logger.exception(str(ex))

                if os.path.isfile(self.database_file):
                    try:
                        os.remove(self.database_file)
                    except Exception as ex:
                        self.logger.exception(str(ex))
                        status = False

        return status

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
                    if template_id is None:
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
        except self.database.Error as e:
            raise DatabaseInsertError(e)

    def add_blob_in_database(self, demo_name, hash_blob, fileformat,
                             ext, tag, blob_set, blob_pos_in_set,
                             title, credit, blobid=-1):
        """
        Add hash blob content and format blob in blob column in database
        Add blob and demo ids in column demo_blob in database
        (necesary for many to many in DBMS)
        Add also tag in database : call addTagInDatabase function

        :param demo_name: demo_name in database
        :param hash_blob: hash content blob string
        :param fileformat: type format of blob string
        :param ext: extension of blob string
        :param tag: name tag string
        :param blob_set: set  blob string
        :param blob_pos_in_set: set  blob id in its set
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
            except self.database.Error as e:
                raise DatabaseInsertError(e)

        try:
            self.cursor.execute(
                '''SELECT id
                FROM demo
                WHERE name=?
                ''',(demo_name,));
            demoid = self.cursor.fetchone()[0]
            self.cursor.execute(
                '''INSERT OR REPLACE INTO
                demo_blob(blob_id, demo_id, blob_set,blob_pos_in_set)
                VALUES(?, ?, ?, ?)''', \
                (blobid, demoid, blob_set, blob_pos_in_set,))

        except self.database.Error as e:
            raise DatabaseInsertError(e)

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
            except self.database.Error as e:
                raise DatabaseInsertError(e)

            try:
                self.cursor.execute('''
                INSERT OR REPLACE INTO
                blob_tag(blob_id, tag_id)
                VALUES(?, ?)''', \
                (blobid, tagid,))
            except self.database.Error as e:
                raise DatabaseInsertError(e)

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
                    except self.database.Error as e:
                        raise DatabaseInsertError(e)

                try:
                    self.cursor.execute('''
                    INSERT OR REPLACE INTO
                    blob_tag(blob_id, tag_id)
                    VALUES(?, ?)''', \
                    (blobid, tagid,))
                except self.database.Error as e:
                    raise DatabaseInsertError(e)


    def edit_blob_in_database(self, blob_id, blob_set, blob_pos_in_set,
                                    title, credit):
        """
        Edit a blob that already exists in the database
        
        :param blob_set: set  blob string
        :param blob_pos_in_set: set  blob id in its set
        :param title: title blob string
        :param credit: credit blob string
        """
        try:
            self.cursor.execute('''
                UPDATE blob SET title=?, credit=?
                WHERE blob.id=?''', \
                (title, credit, blob_id,))
        except self.database.Error as e:
            raise DatabaseInsertError(e)

        try:
            self.cursor.execute('''
                UPDATE demo_blob SET blob_set=?, blob_pos_in_set=?
                WHERE demo_blob.blob_id=?''', \
                (blob_set, blob_pos_in_set, blob_id,))
        except self.database.Error as e:
            raise DatabaseInsertError(e)

    #---------------------------------------------------------------------------
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
            row = self.cursor.fetchone()
        except self.database.Error as e:
            raise DatabaseSelectError(e)
        return row is not None

    #---------------------------------------------------------------------------
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
            row = self.cursor.fetchone()
        except self.database.Error as e:
            raise DatabaseSelectError(e)
        return row is not None

    #---------------------------------------------------------------------------
    def tag_is_in_database(self, tag):
        """
        Check if tag isin database,in column tag

        :param tag: name tag
        :type tag: string
        :return: tag name if it isin database else None
        :rtype: string
        """
        row = None
        try:
            self.cursor.execute("SELECT name FROM tag WHERE name=?", (tag,))
            row = self.cursor.fetchone()
        except self.database.Error as e:
            raise DatabaseSelectError(e)
        return row is not None

    #---------------------------------------------------------------------------
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

    #---------------------------------------------------------------------------
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
            row = self.cursor.fetchone()
        except self.database.Error as e:
            raise DatabaseSelectError(e)
        return None if row is None else row[0]

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
            row = self.cursor.fetchone()
        except self.database.Error as e:
            raise DatabaseSelectError(e)
        return None if row is None else row[0]

    #---------------------------------------------------------------------------
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
            row = self.cursor.fetchone()
        except self.database.Error as e:
            raise DatabaseSelectError(e)
        return None if row is None else row[0]

    #---------------------------------------------------------------------------
    def get_blobs_of_demo(self, demo_name):
        """
        Return list of hash blob associated with demo

        :param demo_name: demo name
        :return: blob infos (id, hash, extension, format, title, credit) associated to demo
        :rtype: list of dictionnary
        """
        #
        try:
            self.cursor.execute('''
            SELECT  blob_set, GROUP_CONCAT(blob_id)  FROM demo_blob
            INNER JOIN demo ON demo_blob.demo_id=demo.id
            INNER JOIN blob ON demo_blob.blob_id=blob.id
            WHERE demo.name=? GROUP BY blob_set ''', (demo_name,))
        except self.database.Error as e:
            raise DatabaseSelectError(e)

        blobsets_list = self.cursor.fetchall()

        blobset_list = []
        for blobset in blobsets_list:
            try:
                self.cursor.execute('''
                SELECT  blob.id, demo_blob.blob_pos_in_set,
                blob.hash, blob.extension, blob.format,
                blob.title, blob.credit FROM demo_blob
                INNER JOIN demo ON demo_blob.demo_id=demo.id
                INNER JOIN blob ON demo_blob.blob_id=blob.id
                WHERE demo.name=? AND blob_set=?''', (demo_name, blobset[0],))
            except self.database.Error as e:
                raise DatabaseSelectError(e)

            blobset_blobs = self.cursor.fetchall()
            blob_list = [{'set_name': blobset[0], 'size': len(blobset_blobs)}]
            for b in  blobset_blobs:
                # get blob tags
                tags = self.get_tags_of_blob(b[0])

                tag_str = ''
                for tid in tags:
                    tag_str += ", "+tags[tid]

                # now get blobs of each set
                blob_list.append(
                    {"id": b[0], "pos_in_set": b[1], "hash" : b[2], "extension": b[3],
                     "format": b[4], "title": b[5], "credit": b[6], 'tag': tag_str}
                )
            blobset_list.append(blob_list)

        return blobset_list

    def get_demo_metadata_by_PK_id(self, demo_id):
        """
        Return name of the demo from the PK id

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

            row = self.cursor.fetchone()

            if row is None or len(row) == 0:
                return None # No results

            dic[row[0]] = {"name": row[1], "is_template": row[2],
                                 "template_id": row[3]}
        except self.database.Error as e:
            raise DatabaseSelectError(e)

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
            SELECT name, is_template, template_id
            FROM demo
            WHERE demo.name=?''',\
            (demo_name,))
            
            row = self.cursor.fetchone()
            if row is None or len(row) == 0:
                return {} # No results
            
            dic[row[0]] = {"name": row[0], "is_template": row[1],
                                 "template_id": row[2]}
        except self.database.Error as e:
            self.logger.exception("get_demo_info_from_name --> The \
            database does not have the demo ({0})".format(demo_name))
            raise DatabaseSelectError(e)

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
            row = self.cursor.execute('''
            SELECT hash FROM blob
            INNER JOIN blob_tag ON blob.id=blob_tag.blob_id
            INNER JOIN tag ON blob_tag.tag_id=tag.id
            WHERE tag.name IN (%s)''' % \
            ("?," * len(tag))[:-1], tag)
        except self.database.Error as e:
            raise DatabaseSelectError(e)

        lis = []
        for item in row:
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
            row = self.cursor.execute('''
            SELECT tag.id, tag.name FROM tag
            INNER JOIN blob_tag ON tag.id=blob_tag.tag_id
            INNER JOIN blob ON blob_tag.blob_id=blob.id
            WHERE blob.id=?''', \
            (blob_id,))
        except self.database.Error as e:
            raise DatabaseSelectError(e)

        lis = {}
        for item in row:
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
        except self.database.Error as e:
            raise DatabaseSelectError(e)

        return tagname

    def get_info_for_editing_a_blob(self, blob_id):
        """
        Return the set where the blob with this blod_id belongs.
        """
        try:
           self.cursor.execute('''
           SELECT demo_blob.blob_set, demo_blob.blob_pos_in_set,
           blob.hash, blob.extension, blob.format, blob.title, blob.credit, blob.id 
           FROM demo_blob INNER JOIN blob ON blob.id=?
           WHERE demo_blob.blob_id=?''', (blob_id, blob_id,))
          
        except self.database.Error as e:
            raise DatabaseSelectError(e)

        blob_info = self.cursor.fetchall()
        dic = {}
        dic['blob_set'] = blob_info[0][0]
        dic['blob_pos_in_set'] = blob_info[0][1]
        dic['hash'] = blob_info[0][2]
        dic['extension'] = blob_info[0][3]
        dic['format'] = blob_info[0][4]
        dic['title'] = blob_info[0][5]
        dic['credit'] = blob_info[0][6]
        dic['id'] = blob_info[0][7]
        
        return dic

    #---------------------------------------------------------------------------
    def blobcount(self, demo_name):
        """
        Check if demo is not associated with a blob

        :param demo_name: demo name
        :return: number of demo present in database
        :rtype: tuple of integer or None
        """
        count = 0
        try:
            self.cursor.execute('''
            SELECT COUNT(*) FROM demo_blob
            INNER JOIN demo ON demo_id=demo.id
            WHERE demo.name=?''', \
            (demo_name,))
            count = self.cursor.fetchone()
            if count is None:
                return 0
            else:
                return count[0]
        except self.database.Error as e:
            raise DatabaseSelectError(e)

        return count

    #---------------------------------------------------------------------------
    def remove_demo_from_database(self, demo_name):
        """
        If demo is empty, delete row corresponding in demo column

        :param demo_name: demo name
        :param demo_blobcount: tuple of integer
        :type demo_blobcount: tuple or None
        """

        try:
            self.cursor.execute("DELETE FROM demo WHERE demo.name=?", (demo_name,))
        except self.database.Error as e:
            raise DatabaseDeleteError(e)

    #---------------------------------------------------------------------------
    def blob_democount(self, blob_id):
        """
        Count the number of demos that use the given blob

        :param blob_id: id blob
        :type blob_id: string
        :return: number of blob present in database
        :rtype: tuple of integer
        """
        democount = None
        try:
            self.cursor.execute('''
            SELECT COUNT(*) FROM demo_blob
            INNER JOIN blob ON blob_id=blob.id
            WHERE blob.id=?''', \
            (blob_id,))
            democount = self.cursor.fetchone()
            if democount is None:
                democount = 0
            else:
                democount = democount[0]
        except self.database.Error as e:
            raise DatabaseSelectError(e)
        if democount is None:
            democount = 0
        return democount

    #---------------------------------------------------------------------------
    def delete_blob(self, blob_id, blob_demo_count):
        """
        If blob is empty delete row corresponding in blob column

        :param blob_id: id blob
        :type blob_id: integer
        :param blob_demo_count: tuple of integer
        :type blob_demo_count: tuple or None
        """

        if blob_demo_count == 0:
            try:
                self.cursor.execute('''
                DELETE FROM blob
                WHERE blob.id=?''', \
                (blob_id,))
            except self.database.Error as e:
                raise DatabaseDeleteError(e)

    #---------------------------------------------------------------------------
    def tag_is_empty(self, tag_id):
        """
        Check if tag is not associated with a blob

        :param tag_id: id tag
        :type tag_id: integer
        :return: number of tag present in database
        :rtype: tuple of integer or None
        """
        row = None
        try:
            self.cursor.execute('''
            SELECT COUNT(*) FROM blob_tag
            INNER JOIN tag ON tag_id=tag.id
            WHERE tag.id=?''',\
            (tag_id,))
            row = self.cursor.fetchone()
        except self.database.Error as e:
            raise DatabaseSelectError(e)
        return None if not row else row

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
            except self.database.Error as e:
                raise DatabaseDeleteError(e)


    #---------------------------------------------------------------------------
    def delete_blob_from_demo(self, demo_name, blobset, blob_id):
        """
        Delete link between demo and hash blob from demo_blob column in database
        Delete link between blob and tag from blob_tag column in database
        Delete demo row named by name demo if demo has no blob
        Delete tag row associated to blob if tag has no blob
        Delete blob row named by hash blob if blob has no demo

        :param demo_name: demo_name
        :param blob_id: id blob
        :type blob_id: integer
        :return: true if and only if the blob is not used anymore
        :rtype: boolean
        """
        try:
            self.cursor.execute(
                '''SELECT id
                FROM demo
                WHERE name=?
                ''', (demo_name,));
            demo_id = self.cursor.fetchone()[0]
        except self.database.Error as e:
            raise DatabaseSelectError(e)

        try:
            result = self.cursor.execute('''
            SELECT blob_id, demo_id, blob_set FROM demo_blob
            INNER JOIN demo ON demo_blob.demo_id=demo.id
            INNER JOIN blob ON demo_blob.blob_id=blob.id
            WHERE demo.id=? AND blob.id=? AND demo_blob.blob_set=? ''',\
            (demo_id, blob_id, blobset))
        except self.database.Error as e:
            raise DatabaseSelectError(e)

        value = ()
        for item in result:
            value = (item[0], item[1], item[2])
            if value:
                try:
                    self.cursor.execute('''
                    DELETE FROM demo_blob
                    WHERE demo_blob.blob_id=? AND demo_blob.demo_id=? AND demo_blob.blob_set=? ''',\
                    (value[0], value[1], value[2]))
                except self.database.Error as e:
                    raise DatabaseDeleteError(e)

        # recompute blob positions in set
        try:
            print "recompute blob positions"
            result = self.cursor.execute('''
            SELECT blob_id, blob_pos_in_set, demo_blob.id FROM demo_blob
            INNER JOIN demo ON demo_blob.demo_id=demo.id
            INNER JOIN blob ON demo_blob.blob_id=blob.id
            WHERE demo_blob.demo_id=? AND demo_blob.blob_set=? ''',\
            (demo_id, blobset))
        except self.database.Error as e:
            raise DatabaseSelectError(e)
        values = []
        for item in result:
            values.append((item[0], item[1], item[2]))
        values = sorted(values, key=lambda b: b[1])
        blobpos = 0
        idx = 0
        prev_pos = 0
        for val in values:
            if blobpos != 0 and prev_pos != val[1]:
                idx = idx + 1
            try:
                result = self.cursor.execute('''
                    UPDATE demo_blob SET blob_pos_in_set=?
                    WHERE demo_blob.id=? ''',\
                    (idx, val[2]))
            except self.database.Error as e:
                raise DatabaseSelectError(e)
            prev_pos = val[1]
            blobpos = blobpos + 1


        #---- here
        self.delete_all_tag(blob_id)
        blob_demo_count = self.blob_democount(blob_id)
        self.delete_blob(blob_id, blob_demo_count)
        return blob_demo_count == 0

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
    def close(self):
        """
        Close the connection.
        """
        self.database.close()

    #---------------------------------------------------------------------------
    def get_list_tags(self):
        """
        Return the list of tag present in database

        :return: list of name tag
        :rtype: list of string
        """
        row = self.cursor.execute("SELECT name FROM tag")
        lis = []
        for item in row:
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
        except self.database.Error as e:
            raise DatabaseInsertError(e)


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
        except self.database.Error as e:
            raise DatabaseSelectError(e)

        #jak
        #todo  change json schema, avoun int keys
        #lis = {}
        #for item in row:
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
            except self.database.Error as e:
                raise DatabaseSelectError(e)

            #blobsets_list = self.cursor.fetchall()
            #print item[0]
            #print blobsets_list
            length = len(blob_sets.fetchall())

            lis.append({"id": item[0], "name": item[1], "is_template": item[2],
                        "template_id": item[3], "length": length})
        return lis

    #---------------------------------------------------------------------------
    def get_blob_filename(self, blob_id):
        """
        Return the name of the blob from id

        :param blob_id: id blob
        :type blob_id: integer
        :return: hash of the blob with extension
        :rtype: string
        """
        try:
            row = self.cursor.execute('''
            SELECT hash, extension FROM blob
            WHERE blob.id=?''', \
            (blob_id,))
        except self.database.Error as e:
            raise DatabaseSelectError(e)

        value = ()
        for item in row:
            value = (item[0], item[1])

        return value[0] + value[1] if value else value

    #---------------------------------------------------------------------------
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
            row = self.cursor.fetchone()
            dic = {"id": row[0], "hash": row[1], "extension": row[2],
                   "credit": row[3]}
        except self.database.Error as e:
            raise DatabaseSelectError(e)

        return dic

    #---------------------------------------------------------------------------
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
        except self.database.Error as e:
            raise DatabaseDeleteError(e)

        tag_is_reducible = self.tag_is_empty(tag_id)
        self.delete_tag(tag_id, tag_is_reducible)


    #---------------------------------------------------------------------------
    def delete_all_tag(self, blob_id):
        """
        Delete all tags from the blob because blob is delete

        :param blob_id: id blob
        :type blob_id: integer
        """

        row = None
        try:
            self.cursor.execute('''
            SELECT tag.id FROM tag
            INNER JOIN blob_tag ON tag.id=tag_id
            INNER JOIN blob ON blob_id=blob.id
            WHERE blob.id=?''',\
            (blob_id,))
            row = self.cursor.fetchone()
            if row:
                for item in row:
                    self.delete_tag_from_blob(item, blob_id)

        except self.database.Error, e:
            raise DatabaseSelectError(e)


    #---------------------------------------------------------------------------
    def list_of_template(self):
        """
        Return the list templated demo

        :return: list of templated demo
        :type: dictionnary
        """
        try:
            row = self.cursor.execute('''
            SELECT id, name
            FROM demo
            WHERE is_template=1''')
        except self.database.Error, e:
            raise DatabaseSelectError(e)

        lis = {}
        for item in row:
            lis[item[0]] = {"name": item[1]}
        return lis


    #---------------------------------------------------------------------------
    def remove_demo(self, demo_name):
        """
        Remove demo of the database, and blob and tag associated

        :param demo_name: demo name
        """

        print "database remove_demo({0})".format(demo_name)
        try:
            # use get_blobs_of_demo() to simplify the code
            demo_blobsets = self.get_blobs_of_demo(demo_name)
            print "demo_blobsets=", demo_blobsets
            blobfilenames_to_delete = []
            for blobs in demo_blobsets:
                blobset_id = blobs[0]["set_name"]
                print "removing blobset '{0}'".format(blobset_id)
                for i in range(blobs[0]["size"]):
                    can_delete = self.delete_blob_from_demo(demo_name, blobset_id, blobs[i + 1]["id"])
                    if can_delete:
                        blobfilenames_to_delete.append(blobs[i+1]["hash"]+blobs[i+1]["extension"])
            demo_blobcount = self.blobcount(demo_name)
            print "demo blobcount = ", demo_blobcount
            if demo_blobcount == 0:
                self.remove_demo_from_database(demo_name)
        except self.database.Error, e:
            raise DatabaseDeleteError(e)
        return blobfilenames_to_delete


    #---------------------------------------------------------------------------
    def demo_use_template(self, demo_name):
        """
        Return the name of the template of demo with the given name
        """
        dic = {}
        try:
            self.cursor.execute('''
            SELECT is_template, template_id
            FROM demo
            WHERE demo.name=?''',\
            (demo_name,))
            
            row = self.cursor.fetchone()
            if row is None or len(row) == 0:
                return {}
            
            is_template, template_id = row
            
            if is_template == 0 and template_id != 0:
                demo_metadata = self.get_demo_metadata_by_PK_id(template_id)
                if demo_metadata is None:
                    return {}
                
                dic = demo_metadata[template_id]
        except DatabaseError, e:
            raise DatabaseSelectError(e)

        return dic


    #---------------------------------------------------------------------------
    def update_template(self, demo_name, template_id):
        """
        Update the template used by another demo

        :param demo_name: id demo (current demo)
        :param template_id: id demo templated used by current demo
        :type template_id: integer
        """
        try:
            self.cursor.execute('''
            UPDATE demo SET template_id=?
            WHERE demo.name=?''', \
            (template_id, demo_name,))
        except DatabaseError as e:
            raise DatabaseUpdateError(e)

#!/usr/bin/env python
# -*- coding:utf-8 -*-

"""
This file implements database class
"""

import sqlite3 as lite

class   Database(object):
    """
    This class implements database management
    The database architecture is defined in file /db/blob.sql
    """
    def __init__(self, ptr):
        """
        Initialize database class
        Connect to databse

        :param ptr: database name
        :type ptr: string
        """
        self.formats = ('audio', 'image', 'video')
        self.db = lite.connect(ptr, check_same_thread=False)
        self.cursor = self.db.cursor()
        self.initTagsColumn()

    def addAppInDatabase(self, app):
        """
        Add name app in app column in database

        :param app: name app
        :type app: string
        :return: id app in database
        :rtype: integer (primary key autoincrement)
        """
        self.cursor.execute("INSERT INTO app(name) VALUES(?)", (app,))
        return self.cursor.lastrowid

    def addBlobInDatabase(self, appid, hash_blob, fileformat, tags, blobid=-1):
        """
        Add hash blob content and format blob in blob column in database
        Add blob and app ids in column blob_app in database
        (necesary for many to many in DBMS)
        Add also tags in database : call addTagsInDatabase function

        :param appid: app id in database
        :type appid: integer (primary key autoincrement)
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
            self.cursor.execute("INSERT INTO blob(hash, format) VALUES(?, ?)",
                                (hash_blob, fileformat,))
            blobid = self.cursor.lastrowid

        self.cursor.execute("INSERT OR REPLACE INTO blob_app(id_blob, id_app) VALUES(?, ?)",
                            (blobid, appid,))

        tagsid = -1
        if self.tagsIsInDatabase(tags):
            tagsid = self.idTags(tags)

        self.addTagsInDatabase(blobid, tags, tagsid)

    def addTagsInDatabase(self, blobid, tags, tagsid=-1):
        """
        Add a new tag in tags column in database if it's necessary
        Add blob and tag ids in blob_tags in database

        :param blobid: blob id in database
        :type blobid: integer (primary key autoincrement)
        :param tags: name tag
        :type tags: string
        :param tagsid: if blobid is omitted (= -1), then add tag to database
        else not add
        :type tagsid: integer
        """
        if tagsid == -1:
            self.cursor.execute("INSERT INTO tags(tags) VALUES(?)", (tags,))
            tagsid = self.cursor.lastrowid

        self.cursor.execute("INSERT INTO blob_tags(id_blob, id_tags) VALUES(?, ?)", (blobid, tagsid,))

    def appIsInDatabase(self, app):
        """
        Check if app is in database, in column app

        :param app: name app
        :type app: string
        :return: name app if it is in database else None
        :rtype: string
        """
        self.cursor.execute("SELECT name FROM app WHERE name=?", (app,))
        something = self.cursor.fetchone()
        return something is not None

    def blobIsInDatabase(self, hash_blob):
        """
        Check if hash blob is in database, in column blob

        :param hash_blob: hash blob content
        :type who: string
        :return: hash if it is in database else None
        :rtype: string
        """
        self.cursor.execute("SELECT hash FROM blob WHERE hash=?", (hash_blob,))
        something = self.cursor.fetchone()
        return something is not None

    def tagsIsInDatabase(self, tag):
        """
        Check if tags is in database, in column tags

        :param tag: name tag
        :type tag: string
        :return: tag name if it is in database else None
        :rtype: string
        """
        self.cursor.execute("SELECT tags FROM tags WHERE tags=?", (tag,))
        something = self.cursor.fetchone()
        return something is not None

    def formatIsGood(self, fileformat):
        """
        Check format file comparing the fileformat returned by imghdr.what()
        with extension list (self.formats)

        :param fileformat: format file
        :type fileformat: string
        :return: True if the extension matches with the value given in paramater (check) else False
        :rtype: bool
        """
        return any(fileformat in s for s in self.formats)

    def idBlob(self, hash_blob):
        """
        Get id blob from hash blob

        :param hash_blob: hash content blob
        :type hash_blob: string
        :return: first case of tuple returned by request SQL
        :rtype: integer (primary key autoincrement)
        """
        self.cursor.execute("SELECT id_blob FROM blob_app JOIN blob ON id_blob=id WHERE hash=?", (hash_blob,))
        something = self.cursor.fetchone()
        return None if something is None else something[0]


    def idApp(self, app):
        """
        Get id app from name app

        :param app: name app
        :type app: string
        :return: first case of tuple returned by request SQL
        :rtype: integer (primary key autoincrement)
        """
        self.cursor.execute("SELECT id_app FROM blob_app JOIN app ON id_app=id WHERE name=?", (app,))
        something = self.cursor.fetchone()
        return None if something is None else something[0]


    def idTags(self, tag):
        """
        Get id tags from name tag

        :param tag: name tag
        :type tag: string
        :return: fist case of tuple returned by request SQL
        :rtype: integer (primary key autoincrement)
        """
        self.cursor.execute("SELECT id FROM tags WHERE tags=?", (tag,))
        something = self.cursor.fetchone()
        return None if something is None else something[0]

    def deleteApp(self, appid):
        """
        Delete row (name, idapp) corresponding to id app

        :param appid: id app
        :type appid: integer (primary key autoincrement)
        """
        self.cursor.execute("DELETE FROM app WHERE id=?", (appid,))


    def commit(self):
        """
        Commit instruction(SELECT, DELETE or INSERT INTO) to database
        """
        self.db.commit()

    def returnList(self):
        """
        Return tuple list of name app and hash blob

        :return: list tuple [(name, hash_blob)]
        :rtype: list
        """
        something = self.cursor.execute("SELECT name, hash FROM app JOIN blob_app ON app.id=id_app JOIN blob ON id_blob=blob.id")

        lis = []
        for item in something:
            lis.append((item[0], item[1]))

        return lis

    def getAppOfHash(self, hash_blob):
        """
        Return list of app associated with hash blob

        :param app: hash blob
        :type app: string
        :return: list of apps
        :rtype: list
        """
        something = self.cursor.execute("SELECT name FROM app JOIN blob_app ON app.id=id_app JOIN blob ON id_blob=blob.id WHERE hash=?", (hash_blob,))

        lis = []
        for item in something:
            lis.append(item[0])
        return lis

    def getHashOfApp(self, app):
        """
        Return list of hash blob associated with app

        :param app: name app
        :type app: string
        :return: list of hash blobs
        :rtype: list
        """
        something = self.cursor.execute("SELECT hash FROM blob JOIN blob_app ON blob.id=id_blob JOIN app ON id_app=app.id WHERE name=?", (app,))

        lis = []
        for item in something:
            lis.append(item[0])
        return lis

    def getBlobOfTags(self, tag):
        """
        Return list of blob associated with tag

        :param tag: name tag
        :type tag: string
        :return: list of hash blobs
        :rtype: list
        """
        something = self.cursor.execute("SELECT hash FROM blob JOIN blob_tags ON blob.id=id_blob JOIN tags ON id_tags=tags.id WHERE tags=?", (tag,))

        lis = []
        for item in something:
            lis.append(item[0])
        return lis

    def getTagsOfBlob(self, hash_blob):
        """
        Return list of tag associated with hash blob

        :param hash_blob: hash blob
        :type hash_blob: string
        :return: list of tags
        :rtype: list
        """
        something = self.cursor.execute("SELECT tags FROM tags JOIN blob_tags ON tags.id=id_tags JOIN blob ON id_blob=blob.id WHERE hash=?", (hash_blob,))

        lis = []
        for item in something:
            lis.append(item[0])
        return lis

    def appIsEmpty(self, app):
        """
        Check if app is not associated with a blob
        If it's empty, delete row corresponding in app column

        :param name: name app
        :type name: string
        """
        self.cursor.execute("SELECT COUNT(*) FROM blob_app JOIN app ON id_app=id WHERE name=?", ((app,)))
        something2 = self.cursor.fetchone()

        if something2[0] == 0:
            self.cursor.execute("DELETE FROM app WHERE name=?", ((app,)))

    def blobIsEmpty(self, hash_blob):
        """
        Check if blob named by hash is not associated with an app
        If it's empty delete row corresponding in blob column

        :param hash_blob: hash blob
        :type hash_blob: string
        :return: number of blob assigned by hash
        :rtype: integer
        """
        self.cursor.execute("SELECT COUNT(*) FROM blob WHERE hash=?", ((hash_blob,)))
        something = self.cursor.fetchone()

        self.cursor.execute("SELECT COUNT(*) FROM blob_app JOIN blob ON id_blob=id WHERE hash=?", ((hash_blob,)))
        something2 = self.cursor.fetchone()

        if something2[0] == 0:
            self.cursor.execute("DELETE FROM blob WHERE hash=?", ((hash_blob,)))
        return True if something[0] == 0 else False

    def deleteFromBlobApp(self, app, hash_blob):
        """
        Delete link between app and hash blob from blob_app column in database
        Delete app row named by name app if app has no blob
        Delete blob row named by hash blob if blob has no app

        :param app: name app
        :type app: string
        :param hash_blob: hash blob
        :type hash_blob: string
        :return: True if blob named by hash hasn't app associated else False
        :rtype: bool
        """
        something = self.cursor.execute("SELECT id_blob, id_app FROM blob_app JOIN app ON id_app=app.id JOIN blob ON id_blob=blob.id WHERE name=? AND hash=?", (app, hash_blob,))

        value = ()
        for item in something:
            value = (item[0], item[1])

        if value:
            self.cursor.execute("DELETE FROM blob_app WHERE id_blob=? AND id_app=?", (value[0], value[1],))

        something = self.cursor.execute("SELECT id_blob, id_tags FROM blob_tags JOIN blob ON id_blob=blob.id AND hash=?", (hash_blob,))

        value = ()
        for item in something:
            value = (item[0], item[1])

        if value:
            self.cursor.execute("DELETE FROM blob_tags WHERE id_blob=? AND id_tags=?", (value[0], value[1],))

        self.appIsEmpty(app)
        return self.blobIsEmpty(hash_blob)

    def initTagsColumn(self):
        """
        Insert in tags column defaults tags
        """
        if not self.tagsIsInDatabase("BW"):
            self.cursor.execute("INSERT INTO tags(tags) VALUES(?)", ("BW",))
            self.cursor.execute("INSERT INTO tags(tags) VALUES(?)", ("Textured",))
            self.cursor.execute("INSERT INTO tags(tags) VALUES(?)", ("Coloured",))
            self.cursor.execute("INSERT INTO tags(tags) VALUES(?)", ("Classic",))
            self.commit()

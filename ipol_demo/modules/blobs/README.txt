BLOB (Binary Large OBject) module

Introduction:

In the context of IPOL project, this module aims to create a new system of management file
for demo.

This module is divided in three parts following MVC pattern:
     - Database
     - Web page
     - Web service

Database was designed by mysql-workbench (see the file '/db/blob.mwb') then SQL file was
exported. Thereof architects the database.

Web page is called when client is connected to server with adress and port
(see blob.conf) using Mako Template Library.

Web service is called by web page and manages the database.

Requirements:
 - Python2.7
 - Python-magic (package)
 - Sqlite3
 - Mako Template Library
 - Cherrypy

Features:
 - Upload file (audio, image, video)
 - Add uploaded file in directory defined in blobs conf file
 - Add in database what file was uploaded with which demo associated
 - Add in database what file was uploaded with which tags associated
 - Delete one file with his hash and his demo associated
 - Get file from name of the demo
 - Get demo from name of the file
 - Get file from name of the tag
 - Get tags from name of the file

Usage: python main.py blobs.conf

Blobs configuration file allows to set adress and port to server.
It allows also to set name of the temporary directory, where uploaded file are temporary put, and
final directory, where files are stored.

The shell script init allows to reset an empty database and to remove temporary
and final directories.

Usage of this script: ./init [-g] blobs.conf

      -g (git option)
		remove blob.db file


For launch test program. Test program will test only the web service, so
the management of the database (ADD, DELETE, GET).

Usage: python test.py blobs.conf

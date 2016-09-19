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
 - Upload zip contents file
 - Created demo (templated, using templated demo or normal demo)
 - Add file for this demo from uploaded file
 - Add tag for these file
 - Delete demo with his id
 - Delete one file with his id and his id demo associated
 - Delete tag with id file associated
 - Add uploaded file in directory defined in blobs conf file
 - Created thumbnail of uploaded file in directory defined in blobs conf file

Usage: python main.py blobs.conf

Blobs configuration file allows to set adress and port to server.
It allows also to set name of the temporary directory, where uploaded file are temporary put, and
final directory, where files are stored.


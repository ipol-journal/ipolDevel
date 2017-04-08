# -*- coding:utf-8 -*-

"""
DATA MODEL

This module will encapsulate all the DB operations
It has the creation scrript,  DAOs to encapsulte sql and ,
a few helper clases that represent the objects modeld
in the DB that will be used by the webservices,
this way I can work with python objects not with queries.

It would be nice to replace all this by orm ,security etc...for example see:
https://groups.google.com/forum/#!topic/cherrypy-users/mpi58-AbBJU
But it has been decided not to use one because of the small scope of the problem

"""

import os
import sqlite3 as lite
import datetime
from validoot import validates, inst, typ, between, And, Or, email_address


#####################
#  helper clases    #
#####################

class Demo(object):

    """
    Class representing a demo.
    """

    editorsdemoid = None
    title = None
    abstract = None
    zipURL = None
    state = None
    creation = None
    modification = None

    @validates(editorsdemoid=typ(int),
               title=inst(basestring),
               abstract=inst(basestring),
               #zipurl=type(url),
               zipurl=inst(basestring),
               stateid=typ(str),
               creation=Or(typ(datetime.datetime), inst(basestring)),
               modification=Or(typ(datetime.datetime), inst(basestring))
              )
    def __init__(self, editorsdemoid, title, abstract, zipurl,
                 state, creation=None, modification=None):
        """
        Constructor.
        """

        self.editorsdemoid = editorsdemoid
        self.title = title
        self.abstract = abstract
        self.zipURL = zipurl
        self.state = state

        if creation:
            self.creation = creation
        else:
            self.creation = datetime.datetime.now()
        if modification:
            self.modification = modification
        else:
            self.modification = datetime.datetime.now()

    def __eq__(self, other):
        """
        Equality operator overloading.
        """
        return self.__dict__ == other.__dict__

class Author(object):
    """
    Object representing an author.
    """
    id = None
    name = None
    mail = None
    creation = None
    # And(inst(basestring),len_between(4,100)),
    @validates(
        name=inst(basestring),
        #mail=regex("[^@]+@[^@]+\.[^@]+"),
        mail=type(email_address),
        the_id=Or(typ(int), inst(basestring)),
        creation=Or(typ(datetime.datetime), inst(basestring))
        )
    def __init__(self, name, mail, the_id=None, creation=None):
        """
        Constructor.
        """
        self.id = the_id
        self.name = name
        self.mail = mail
        if creation:
            self.creation = creation
        else:
            self.creation = datetime.datetime.now()


    def __eq__(self, other):
        """
        Equality operator overloading.
        """
        # print "eq"
        # print self.__dict__
        # print other.__dict__
        return self.__dict__ == other.__dict__

class Editor(object):
    """
    Object representing an editor.
    """
    id = None
    name = None
    mail = None
    creation = None

    @validates(
        name=inst(basestring),
        #mail=regex("[^@]+@[^@]+\.[^@]+"),
        mail=type(email_address),
        the_id=Or(typ(int), inst(basestring)),
        creation=Or(typ(datetime.datetime), inst(basestring))
        )
    def __init__(self, name, mail, the_id=None, creation=None):
        """
        Constructor.
        """
        self.name = name
        self.mail = mail
        self.id = the_id
        if creation:
            self.creation = creation
        else:
            self.creation = datetime.datetime.now()

    def __eq__(self, other):
        """
        Equality operator overloading.
        """
        return self.__dict__ == other.__dict__

##########################
#  DAO (data access obj) #
##########################

class DemoDescriptionDAO(object):
    """
    DAO for demodescription table.
    """
    def __init__(self, conn):
        """
        Constructor.
        """
        self.conn = conn
        self.cursor = conn.cursor()
        self.cursor.execute(""" PRAGMA foreign_keys=ON""")

    def __del__(self):
        """
        Destructor.
        """
        pass

    # conn.close()

    #@validates(inst(Demo))
    def add(self, demojson, inproduction=None):
        """
        Add description for the given demo.
        """
        try:
            if inproduction is None:
                self.cursor.execute('''INSERT INTO demodescription (json) VALUES(?)''', (demojson,))
            else:
                self.cursor.execute('''INSERT INTO demodescription (json,inproduction) VALUES(?,?)''',
                                    (demojson, int(inproduction)))
                self.conn.commit()
            return self.cursor.lastrowid
        except Exception as ex:
            error_string = ("add demo_description  e:%s" % (str(ex)))
            print error_string
            raise Exception(error_string)


    @validates(typ(int))
    def delete(self, demo_description_id):
        """
        delete description for the given demo.
        """
        try:
            self.cursor.execute("DELETE FROM demodescription WHERE id=?", (int(demo_description_id),))
            self.conn.commit()
        except Exception as ex:
            error_string = ("delete_demo_description  e:%s" % (str(ex)))
            print error_string
            raise Exception(error_string)


    #@validates(inst(Demo))
    def update(self, demo_description_id, demojson):
        """
        update description for given demo.
        """
        # demojson is a json str (json.dumps(jsonpythondict))
        # carefull doubly-encoding JSON strings
        try:
            self.cursor.execute('''UPDATE demodescription SET json=? WHERE id=?''', (demojson, demo_description_id))
            self.conn.commit()
        except Exception as ex:
            error_string = ("update demo_description  e:%s" % (str(ex)))
            print error_string
            raise Exception(error_string)

    @validates(typ(int))
    def read(self, demo_description_id):
        """
        read description for given demo.
        """
        result = None
        try:
            self.cursor.execute('''SELECT  json,inproduction  FROM demodescription WHERE id=?''',
                                (int(demo_description_id),))
            self.conn.commit()
            row = self.cursor.fetchone()
            if row:
                result = (row[0], row[1])
        except Exception as ex:
            error_string = ("read demo_description  e:%s" % (str(ex)))
            print error_string
        return result


class DemoDAO(object):
    """
    DAO for the demo table.
    """

    def __init__(self, conn):
        """
        Constructor.
        """
        self.conn = conn
        self.cursor = conn.cursor()
        self.cursor.execute(""" PRAGMA foreign_keys=ON""")

    def __del__(self):
        """
        Destructor.
        """
        pass

    # conn.close()

    @validates(inst(Demo))
    def add(self, demo):
        """
        Add a demo.
        """
        try:

            # print 'demo.editorsdemoid: ',demo.editorsdemoid
            # print 'demo.title: ',demo.title
            # print 'demo.abstract: ',demo.abstract
            # print 'demo.zipURL: ',demo.zipURL
            # print 'demo.state: ',demo.state
            # print 'demo.demodescriptionID: ',demo.demodescriptionID
            self.cursor.execute('''SELECT ID
                                FROM state
                                WHERE state.name=?''', (demo.state,))
            self.conn.commit()
            state_id = self.cursor.fetchone()[0]
            print state_id
            self.cursor.execute('''
            INSERT INTO demo(editor_demo_id, title, abstract, zipURL, stateID)
            VALUES(?,?,?,?,?)''', (demo.editorsdemoid, demo.title, demo.abstract,
                                     demo.zipURL, state_id,))
            self.conn.commit()
            return demo.editorsdemoid
        except Exception as ex:
            error_string = (" DAO add_demo e:%s" % (str(ex)))
            print error_string
            raise ValueError(error_string)

    @validates(typ(int))
    def delete(self, editor_demo_id):
        """
        delete a demo.
        """
        try:
            self.cursor.execute("DELETE FROM demo WHERE demo.editor_demo_id=?", (int(editor_demo_id),))
            self.conn.commit()
        except Exception as ex:
            error_string = ("delete_demo  e:%s" % (str(ex)))
            print error_string
            raise Exception(error_string)


    @validates(inst(Demo), And(typ(int)))
    def update(self, demo, old_editor_demo_id):
        """
        update a demo.
        """
        try:

            nowtmstmp = datetime.datetime.now()
            # print nowtmstmp
            # #nowtmstmp =datetime.datetime.strptime(nowtmstmp, '%Y-%m-%d %H:%M:%S.%fZ')
            # #print nowtmstmp
            # from django.core.serializers.json import json, DjangoJSONEncoder
            # nowtmstmp=json.dumps(nowtmstmp, cls=DjangoJSONEncoder)
            # print nowtmstmp
            # nowtmstmp=demo.creation
            # print nowtmstmp
            # datetime.strptime('2015-02-25T12:58:01.548Z', '%Y-%m-%dT%H:%M:%S.%fZ')
            self.cursor.execute('''SELECT ID
                                FROM state
                                WHERE state.name=?''',(demo.state,))
            self.conn.commit()
            state_id = self.cursor.fetchone()[0]

            if demo.creation:

                self.cursor.execute('''
                UPDATE demo SET editor_demo_id=?,title=?, abstract=?, zipURL=?,
                stateID=?,modification=?,creation=? WHERE demo.editor_demo_id=?''',
                                    (demo.editorsdemoid, demo.title, demo.abstract,
                                     demo.zipURL, state_id, nowtmstmp,
                                     demo.creation, old_editor_demo_id))

            else:
                self.cursor.execute('''
                UPDATE demo SET editor_demo_id=?,title=?, abstract=?, zipURL=?,
                stateID=?,modification=?,creation=? WHERE demo.editor_demo_id=?''',
                                    (demo.editorsdemoid, demo.title, demo.abstract,
                                     demo.zipURL, state_id, nowtmstmp,
                                     demo.creation, old_editor_demo_id))
            self.conn.commit()
        except Exception as ex:
            error_string = ("update_demo  e:%s" % (str(ex)))
            print error_string
            raise Exception(error_string)

    @validates(typ(int))
    def read(self, editor_demo_id):
        """
        Return a description of the demo.
        """
        result = None
        try:
            self.cursor.execute('''SELECT  d.editor_demo_id, d.title, d.abstract, d.zipURL, s.name, d.creation, d.modification
                                FROM demo as d, state as s
                                WHERE d.editor_demo_id=?
                                AND d.stateID = s.ID''', (int(editor_demo_id),))

            self.conn.commit()
            row = self.cursor.fetchone()
            if row:
                d = Demo(row[0], row[1], row[2], row[3], row[4], row[5], row[6])
                result = d
        except Exception as ex:
            error_string = ("read_demo  e:%s" % (str(ex)))
            print error_string
        return result

    @validates(typ(int))
    def read_by_editordemoid(self, editor_demo_id):
        """
        Same as read, deprecated.
        """
        #All calls to this function must be changed to read(editor_demo_id)
        self.read(editor_demo_id)

    def list(self):
        """
        Return a list of demos.
        """
        demo_list = list()
        try:

            self.cursor.execute('''SELECT d.editor_demo_id, d.title, d.abstract, d.zipURL, s.name, d.creation, d.modification
                                FROM demo as d, state as s
                                WHERE d.stateID = s.ID
                                ORDER BY d.editor_demo_id DESC ''')

            self.conn.commit()
            for row in self.cursor.fetchall():
                d = Demo(row[0], row[1], row[2], row[3], row[4], row[5], row[6])
                demo_list.append(d)

        except Exception as ex:
            error_string = ("list_demos  e:%s" % (str(ex)))
            print error_string
        return demo_list


class DemoDemoDescriptionDAO(object):
    """
    DAO for the demo_demodescription junction table.
    """
    def __init__(self, conn):
        """
        Constructor.
        """
        self.conn = conn
        self.cursor = conn.cursor()
        self.cursor.execute(""" PRAGMA foreign_keys=ON""")

    def __del__(self):
        """
        destructor
        """
        pass

    # conn.close()

    @validates(typ(int), typ(int))
    def add(self, editorsdemoid, demodescriptionid):
        """
        Add an entry in the table.
        """
        try:
            self.cursor.execute('''
            INSERT INTO demo_demodescription(demodescriptionID,demoID)
            VALUES(?,(SELECT ID
                FROM demo
                WHERE demo.editor_demo_id=?))''', (int(demodescriptionid), int(editorsdemoid),))
            self.conn.commit()

        except Exception as ex:
            error_string = ("add_demo_demodescription  e:%s" % (str(ex)))
            print error_string
            raise Exception(error_string)

    @validates(typ(int))
    def delete(self, editorsdemoid):
        """
        Remove an entry.
        """
        try:
            self.cursor.execute('''
            DELETE
            FROM demo_demodescription
            WHERE id=(SELECT ID
                FROM demo
                where demo.editor_demo_id=?)''', (int(editorsdemoid),))
            self.conn.commit()
        except Exception as ex:
            error_string = ("delete_demo_demodescription  e:%s" % (str(ex)))
            print error_string
            raise Exception(error_string)

    @validates(typ(int))
    def delete_all_demodescriptions_for_demo(self, editorsdemoid):
        """
        remove all entries for a demo.
        """
        try:
            #self.cursor.execute("DELETE FROM demo_demodescription WHERE demoID=?", (int(demoid),))
            #self.cursor.execute("DELETE FROM demodescription WHERE demoID=?", (int(demoid),))

            self.cursor.execute('''
            DELETE
            FROM demodescription
            WHERE ID in (SELECT demodescriptionid
                    FROM demo_demodescription
                    WHERE demoID=(SELECT ID
                            FROM demo
                            WHERE demo.editor_demo_id=?))''', (int(editorsdemoid),))
            self.conn.commit()
        except Exception as ex:
            error_string = ("delete_all_demodescriptions_for_demo  e:%s" % (str(ex)))
            print error_string
            raise Exception(error_string)


    @validates(typ(int), typ(int))
    def remove_demodescription_from_demo(self, editorsdemoid, demodescriptionid):
        """
        remove editor from demo.
        """
        try:
            self.cursor.execute('''
            DELETE
            FROM demo_demodescription
            WHERE demodescriptionID=?
            AND demoID=(SELECT ID
                    FROM demo
                    WHERE demo.editor_demo_id =?)''', (int(demodescriptionid), int(editorsdemoid),))
            self.conn.commit()
        except Exception as ex:
            error_string = ("remove_editor_from_demo  e:%s" % (str(ex)))
            print error_string
            raise Exception(error_string)


    @validates(typ(int))
    def read(self, editorsdemoid):
        """
        Get the editor from a demo.
        """
        result = None
        try:
            self.cursor.execute('''
            SELECT demo.editor_demo_id,demodescriptionID
            FROM demo_demodescription , demo
            WHERE demo.ID=demo_demodescription.demoID
            AND demo.editor_demo_id=?''', (int(editorsdemoid),))
            self.conn.commit()
            row = self.cursor.fetchone()
            if row:
                result = {'editorsDemoID': row[0], 'editorId': row[1]}

        except Exception as ex:
            error_string = ("read_demo_editor  e:%s" % (str(ex)))
            print error_string
        return result


    @validates(typ(int))
    def get_ddl(self, editorsdemoid):
        """
        return last demo description entered for editorsdemoid.
        """
        result = None
        # print
        # print "   +++++++ get_ddl +++++++++"
        try:

            self.cursor.execute('''SELECT ddl.inproduction,ddl.creation,ddl.JSON, ddl.id
                 FROM demodescription as ddl
                 INNER JOIN demo_demodescription AS dd ON dd.demodescriptionId = ddl.ID
                 INNER JOIN demo ON  demo.ID = dd.demoId
                 WHERE editor_demo_id = ?
                 ORDER BY ddl.creation DESC LIMIT 1''', (int(editorsdemoid),))
            self.conn.commit()
            row = self.cursor.fetchone()
            if row:
                result = {'inproduction': row[0], 'creation': row[1],
                          'json': row[2], 'demodescriptionId': row[3]}

        except Exception as ex:
            error_string = ("get_ddl  e:%s" % (str(ex)))
            print error_string
        return result


    @validates(typ(int))
    def read_demo_demodescriptions(self, editorsdemoid, returnjsons=None):
        """
        return list of demo descriptions from given editor.
        """
        #returns ordered list, by default does not return jsons

        demodescription_list = list()
        try:
            if returnjsons is True or returnjsons == 'True':
                self.cursor.execute('''
                SELECT ddl.ID,ddl.inproduction,ddl.creation,ddl.JSON
                FROM demo_demodescription as dd, demodescription as ddl, demo as d
                WHERE  dd.demodescriptionID=ddl.ID
                AND dd.demoID= d.ID
                AND d.editor_demo_id=?
                ORDER BY ddl.ID DESC''', (int(editorsdemoid),))
                self.conn.commit()
                for row in self.cursor.fetchall():
                    ddl = (row[0], row[1], row[2], row[3])
                    demodescription_list.append(ddl)
            else:
                self.cursor.execute('''
                SELECT ddl.ID,ddl.inproduction,ddl.creation
                FROM demo_demodescription as dd, demodescription as ddl, demo as d
                WHERE  dd.demodescriptionID=ddl.ID
                AND dd.demoID= d.ID
                AND d.editor_demo_id=?
                ORDER BY ddl.ID DESC''', (int(editorsdemoid),))
                self.conn.commit()
                for row in self.cursor.fetchall():
                    ddl = (row[0], row[1], row[2])
                    demodescription_list.append(ddl)
        except Exception as ex:
            error_string = ("read_demo_demodescriptions  e:%s" % (str(ex)))
            print "read_demo_demodescriptions e: ", error_string
        return demodescription_list


class AuthorDAO(object):
    """
    DAO for the author table.
    """
    def __init__(self, conn):
        """
        Constructor.
        """
        self.conn = conn
        self.cursor = conn.cursor()
        self.cursor.execute(""" PRAGMA foreign_keys=ON""")

    def __del__(self):
        """
        Destructor.
        """
        pass

    # conn.close()

    @validates(inst(Author))
    def add(self, author):
        """
        add an author to the db.
        """
        try:
            # todo validate user input
            self.cursor.execute('''
            INSERT INTO author(name, mail) VALUES(?,?)''', (author.name, author.mail,))
            self.conn.commit()
            return self.cursor.lastrowid

        except Exception as ex:
            error_string = ("add_author,  %s " % (str(ex)))
            print error_string
            raise Exception(error_string)

    @validates(typ(int))
    def delete(self, the_id):
        """
        delete an author from the db.
        """
        try:
            self.cursor.execute("DELETE FROM author WHERE id=?", (int(the_id),))
            self.conn.commit()
        except Exception as ex:
            error_string = ("delete_author  e:%s" % (str(ex)))
            print error_string
            raise Exception(error_string)

    @validates(inst(Author))
    def update(self, author):
        """
        update an author entry.
        """
        try:

            # todo validate user input
            if author.creation:
                self.cursor.execute('''
                UPDATE author SET name=?, mail=?,creation=? WHERE id=?''',
                                    (author.name, author.mail, author.creation, author.id))
            else:
                self.cursor.execute('''
                UPDATE author SET name=?, mail=? WHERE id=?''', (author.name, author.mail, author.id))

            self.conn.commit()

        except Exception as ex:
            error_string = ("update_author  e:%s" % (str(ex)))
            print error_string
            raise Exception(error_string)

    @validates(typ(int))
    def read(self, the_id):
        """
        get the author info from their id.
        """
        result = None
        try:
            self.cursor.execute('''SELECT  name, mail,id, creation FROM author WHERE id=?''', (int(the_id),))
            self.conn.commit()
            row = self.cursor.fetchone()
            if row:
                a = Author(row[0], row[1], row[2], row[3])
                result = a
        except Exception as ex:
            error_string = ("read_author  e:%s" % (str(ex)))
            print error_string
        return result

    def list(self):
        """
        get a list of all the authors of the database.
        """
        author_list = list()
        try:
            self.cursor.execute('''SELECT name, mail,id, creation FROM author ORDER BY id DESC ''')
            self.conn.commit()
            for row in self.cursor.fetchall():
                a = Author(row[0], row[1], row[2], row[3])
                author_list.append(a)

        except Exception as ex:
            error_string = ("list_author  e:%s" % (str(ex)))
            print error_string
        return author_list


class DemoAuthorDAO(object):
    """
    DAO for the author/demo junction table.
    """

    def __init__(self, conn):
        """
        Constructor.
        """
        self.conn = conn
        self.cursor = conn.cursor()
        self.cursor.execute(""" PRAGMA foreign_keys=ON""")

    def __del__(self):
        """
        destructor.
        """
        pass

    # conn.close()

    @validates(typ(int), typ(int))
    def add(self, editorsdemoid, authorid):
        """
        add an entry to the table.
        """
        try:
            self.cursor.execute('''
            INSERT INTO demo_author(authorId,demoID)
            VALUES(?,(SELECT ID
                FROM demo
                WHERE demo.editor_demo_id=?))''', (int(authorid), int(editorsdemoid),))
            self.conn.commit()

        except Exception as ex:
            error_string = ("add_demo_author  e:%s" % (str(ex)))
            print error_string
            raise Exception(error_string)

    @validates(typ(int))
    def delete(self, the_id):
        """
        delete an entry from the table.
        """
        try:
            self.cursor.execute("DELETE FROM demo_author WHERE id=?", (int(the_id),))
            self.conn.commit()
        except Exception as ex:
            error_string = ("delete_demo_author  e:%s" % (str(ex)))
            print error_string
            raise Exception(error_string)

    @validates(typ(int))
    def delete_all_authors_for_demo(self, editorsdemoid):
        """
        delete all authors for a demo.
        """
        try:
            self.cursor.execute('''
            DELETE
            FROM demo_author
            WHERE demoID=(SELECT ID
                    FROM demo
                    WHERE demo.editor_demo_id=?)''', (int(editorsdemoid),))
            self.conn.commit()
        except Exception as ex:
            error_string = ("delete_all_authors_for_demo  e:%s" % (str(ex)))
            print error_string
            raise Exception(error_string)

    @validates(typ(int), typ(int))
    def remove_author_from_demo(self, editorsdemoid, authorid):
        """
        remove all the authors for a given demo.
        """
        try:

            self.cursor.execute('''DELETE
            FROM demo_author
            where demo_author.authorId=?
            AND demo_author.demoID IN ( SELECT ID
            FROM demo
            WHERE demo.editor_demo_id = ?)''', (int(authorid), int(editorsdemoid),))
            self.conn.commit()
        except Exception as ex:
            error_string = ("remove_author_from_demo  e:%s" % (str(ex)))
            print error_string
            raise Exception(error_string)

    @validates(typ(int))
    def read(self, the_id):
        """
        return information on a given author/demo association.
        """
        result = None
        try:
            self.cursor.execute('''
            SELECT demo.editor_demo_id, demo_author.ID, demo_author.authorId
            FROM demo_author, demo
            WHERE demo.ID = demo_author.demoID
            AND demo_author.id=?''', (int(the_id),))
            self.conn.commit()
            row = self.cursor.fetchone()
            if row:
                result = {'id': row[0], 'editorsDemoID': row[1], 'authorId': row[2]}

        except Exception as ex:
            error_string = ("read_demo_author  e:%s" % (str(ex)))
            print error_string
        return result

    @validates(typ(int))
    def read_author_demos(self, authorid):
        """
        Get a list of the demos realised by a given author.
        """
        demo_list = list()
        try:
            self.cursor.execute('''SELECT d.editor_demo_id, d.title, d.abstract, d.zipURL, s.name , d.creation, d.modification
                                FROM demo as d, demo_author as da, state as s
                                WHERE d.id=da.demoId
                                AND d.stateID = s.ID
                                AND da.authorId=?''', (int(authorid),))
            self.conn.commit()
            for row in self.cursor.fetchall():
                d = Demo(row[0], row[1], row[2], row[3], row[4], row[5], row[6])
                demo_list.append(d)

        except Exception as ex:
            error_string = ("read_author_demos  e:%s" % (str(ex)))
            print error_string
        return demo_list

    @validates(typ(int))
    def read_demo_authors(self, editordemoid):
        """
        Get a list of the authors of the demos edited by a given editor.
        """
        author_list = list()
        try:
            self.cursor.execute('''
            SELECT a.name, a.mail,a.id, a.creation
            FROM author as a, demo_author as da , demo as d
            WHERE a.id=da.authorId
            AND da.demoID= d.ID
            AND d.editor_demo_id=?''', (int(editordemoid),))
            self.conn.commit()
            for row in self.cursor.fetchall():
                a = Author(row[0], row[1], row[2], row[3])
                author_list.append(a)

        except Exception as ex:
            error_string = ("read_demo_authors  e:%s" % (str(ex)))
            print error_string
        return author_list


class EditorDAO(object):
    """
    DAO for the editor table.
    """
    def __init__(self, conn):
        """
        Constructor.
        """

        self.conn = conn
        self.cursor = conn.cursor()
        self.cursor.execute(""" PRAGMA foreign_keys=ON""")

    def __del__(self):
        """
        Destructor.
        """
        pass

    # conn.close()

    @validates(inst(Editor))
    def add(self, editor):
        """
        Add an editor.
        """
        try:
            # todo validate user input
            self.cursor.execute('''
            INSERT INTO editor(name, mail) VALUES(?,?)''', (editor.name, editor.mail,))
            self.conn.commit()
            return self.cursor.lastrowid
        except Exception as ex:
            error_string = ("add_editor  e:%s" % (str(ex)))
            print error_string
            raise Exception(error_string)

    @validates(typ(int))
    def delete(self, the_id):
        """
        delete an editor.
        """
        try:
            self.cursor.execute("DELETE FROM editor WHERE id=?", (int(the_id),))
            self.conn.commit()
        except Exception as ex:
            error_string = ("delete_editor  e:%s" % (str(ex)))
            print error_string
            raise Exception(error_string)

    @validates(inst(Editor))
    def update(self, editor):
        """
        update an editor.
        """
        try:

            # todo validate user input
            if editor.creation:
                self.cursor.execute('''
                UPDATE editor SET name=?, mail=?,creation=? WHERE id=?''',
                                    (editor.name, editor.mail,
                                     editor.creation, editor.id))
            else:
                self.cursor.execute('''
                UPDATE editor SET name=?, mail=? WHERE id=?''',
                                    (editor.name, editor.mail, editor.id))

            self.conn.commit()

        except Exception as ex:
            error_string = ("update_editor  e:%s" % (str(ex)))
            print error_string
            raise Exception(error_string)

    @validates(typ(int))
    def read(self, the_id):
        """
        get an editor from its ID.
        """
        try:
            self.cursor.execute('''SELECT name, mail, id, creation
            FROM editor WHERE id=?''', (int(the_id),))
            # name, mail, id=None,creation=None):
            self.conn.commit()
            row = self.cursor.fetchone()

        except Exception as ex:
            error_string = ("read_editor  e:%s" % (str(ex)))
            print error_string
        return Editor(row[0], row[1], row[2], row[3])

    def list(self):
        """
        get the list of editors.
        """
        editor_list = list()
        try:
            # name, mail, id=None, creation=
            self.cursor.execute('''SELECT  name, mail,  id, creation
            FROM editor ORDER BY id DESC ''')
            self.conn.commit()
            for row in self.cursor.fetchall():
                e = Editor(row[0], row[1], row[2], row[3])
                # print 'editor list'
                # print e.__dict__
                editor_list.append(e)

        except Exception as ex:
            error_string = ("list_editor  e:%s" % (str(ex)))
            print error_string
        return editor_list


class DemoEditorDAO(object):
    """
    DAO for the demo_editor junction table.
    """
    def __init__(self, conn):
        """
        Constructor.
        """
        self.conn = conn
        self.cursor = conn.cursor()
        self.cursor.execute(""" PRAGMA foreign_keys=ON""")

    def __del__(self):
        """
        destructor.
        """
        pass

    # conn.close()

    @validates(typ(int), typ(int))
    def add(self, editorsdemoid, editorid):
        """
        Add an entry to the demo_editor table.
        """
        try:
            self.cursor.execute('''
            INSERT INTO demo_editor(editorId,demoID)
            VALUES(?,(SELECT ID
                FROM demo
                WHERE demo.editor_demo_id=?))''', (int(editorid), int(editorsdemoid),))
            self.conn.commit()

        except Exception as ex:
            error_string = ("add_demo_editor  e:%s" % (str(ex)))
            print error_string
            raise Exception(error_string)

    @validates(typ(int))
    def delete(self, the_id):
        """
        delete an entry from id.
        """
        try:
            self.cursor.execute("DELETE FROM demo_editor WHERE id=?", (int(the_id),))
            self.conn.commit()
        except Exception as ex:
            error_string = ("delete_demo_editor  e:%s" % (str(ex)))
            print error_string
            raise Exception(error_string)

    @validates(typ(int))
    def delete_all_editors_for_demo(self, editorsdemoid):
        """
        remove editor from demos/editor correspondence.
        """
        try:
            self.cursor.execute('''
            DELETE
            FROM demo_editor
            WHERE demoID=(SELECT ID
                    FROM demo
                    WHERE demo.editor_demo_id=?)''', (int(editorsdemoid),))
            self.conn.commit()
        except Exception as ex:
            error_string = ("delete_all_editors_for_demo  e:%s" % (str(ex)))
            print error_string
            raise Exception(error_string)

    @validates(typ(int), typ(int))
    def remove_editor_from_demo(self, editorsdemoid, editorid):
        """
        remove editor from demos/editor correspondence and editor id.
        """
        try:
            self.cursor.execute('''
            DELETE
            FROM demo_editor
            WHERE editorId=?
            AND demoID=(SELECT ID
                    FROM demo
                    WHERE demo.editor_demo_id=?)''', (int(editorid), int(editorsdemoid),))
            self.conn.commit()
        except Exception as ex:
            error_string = ("remove_editor_from_demo  e:%s" % (str(ex)))
            print error_string
            raise Exception(error_string)

    @validates(typ(int))
    def read(self, the_id):
        """
        get editor from id.
        """
        result = None
        try:
            self.cursor.execute('''
            SELECT demo_editor.ID,demo.editor_demo_id, demo_editor.editorId
            FROM demo_editor , demo
            WHERE demo_editor.demoID=demo.ID
            AND demo_editor.ID=?''', (int(the_id),))
            self.conn.commit()
            row = self.cursor.fetchone()
            if row:
                result = {'id': row[0], 'editorDemoID': row[1], 'editorId': row[2]}

        except Exception as ex:
            error_string = ("read_demo_editor  e:%s" % (str(ex)))
            print error_string
        return result

    @validates(typ(int))
    def read_editor_demos(self, editorid):
        """
        get list of demos from an editor id.
        """
        demo_list = list()
        try:
            self.cursor.execute('''SELECT d.editor_demo_id, d.title, d.abstract, d.zipURL, s.name, d.id, d.creation, d.modification
                                FROM demo as d, demo_editor as de, state as s
                                WHERE d.id=de.demoId
                                AND d.stateID = s.ID
                                AND de.editorId=?''', (int(editorid),))
            self.conn.commit()
            for row in self.cursor.fetchall():
                d = Demo(row[0], row[1], row[2], row[3], row[4], row[5], row[6])
                demo_list.append(d)

        except Exception as ex:
            error_string = ("read_editor_demos  e:%s" % (str(ex)))
            print error_string
        return demo_list

    @validates(typ(int))
    def read_demo_editors(self, editordemoid):
        """
        get list of editors from an editor-demo correspondence.
        """
        editor_list = list()
        try:
            # self.cursor.execute('''SELECT id,demoID,
            # editorId FROM demo_editor WHERE demoID=?''', (int(demoid),))
            self.cursor.execute('''
                SELECT e.name, e.mail,e.id,e.creation
                FROM editor as e, demo_editor as de , demo as d
                WHERE e.id=de.editorId
                AND de.demoID= d.ID
                AND d.editor_demo_id=?''', (int(editordemoid),))
            self.conn.commit()
            for row in self.cursor.fetchall():
                e = Editor(row[0], row[1], row[2], row[3])
                editor_list.append(e)

        except Exception as ex:
            error_string = ("read_demo_editors  e:%s" % (str(ex)))
            print error_string
        return editor_list


###########################
#    DB setup functions   #
###########################

def createDb(database_name):
    """
    Initialize the database used by the module if it doesn't exist.
    """
    status = True
    dbname = database_name

    if not os.path.isfile(dbname):

        try:
            conn = lite.connect(dbname)
            cursor_db = conn.cursor()
            cursor_db.execute(""" PRAGMA foreign_keys=ON""")

            cursor_db.execute(
                """CREATE TABLE IF NOT EXISTS "state" (
                ID INTEGER PRIMARY KEY AUTOINCREMENT,
                name VARCHAR(500) UNIQUE,
                description TEXT,
                creation TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                );"""
            )
            cursor_db.execute(
                """CREATE TABLE IF NOT EXISTS "demodescription" (
                ID INTEGER PRIMARY KEY AUTOINCREMENT,
                creation TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                inproduction INTEGER(1) DEFAULT 1,
                JSON BLOB
                );"""
            )
            cursor_db.execute(
                """CREATE TABLE IF NOT EXISTS "demo" (
                ID INTEGER PRIMARY KEY AUTOINCREMENT,
                editor_demo_id INTEGER UNIQUE NOT NULL,
                title VARCHAR UNIQUE NOT NULL,
                abstract TEXT,
                zipURL VARCHAR,
                creation TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                modification TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                stateID INTEGER,
                FOREIGN KEY(stateID) REFERENCES state(id)


                );"""
            )

            cursor_db.execute(
                """CREATE TABLE IF NOT EXISTS "demo_demodescription" (
                ID INTEGER PRIMARY KEY AUTOINCREMENT,
                demoID INTEGER NOT NULL,
                demodescriptionId INTEGER NOT NULL,
                FOREIGN KEY(demodescriptionId) REFERENCES demodescription(id) ON DELETE CASCADE,
                FOREIGN KEY(demoID) REFERENCES demo(id) ON DELETE CASCADE
                );"""
            )


            cursor_db.execute(
                """CREATE TABLE IF NOT EXISTS "author" (
                ID INTEGER PRIMARY KEY AUTOINCREMENT,
                name VARCHAR ,
                mail VARCHAR(320) UNIQUE,
                creation TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                );"""
            )
            cursor_db.execute(
                """CREATE TABLE IF NOT EXISTS "editor" (
                ID INTEGER PRIMARY KEY AUTOINCREMENT,
                name VARCHAR ,
                mail VARCHAR(320) UNIQUE,
                creation TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                );"""
            )
            cursor_db.execute(
                """CREATE TABLE IF NOT EXISTS "demo_author" (
                ID INTEGER PRIMARY KEY AUTOINCREMENT,
                demoID INTEGER NOT NULL,
                authorId INTEGER NOT NULL,
                FOREIGN KEY(authorId) REFERENCES author(id) ON DELETE CASCADE,
                FOREIGN KEY(demoID) REFERENCES demo(id) ON DELETE CASCADE,
                UNIQUE(demoID, authorId)

                );"""
            )
            cursor_db.execute(
                """CREATE TABLE IF NOT EXISTS "demo_editor" (
                ID INTEGER PRIMARY KEY AUTOINCREMENT,
                demoID INTEGER,
                editorId INTEGER,
                FOREIGN KEY(editorId) REFERENCES editor(id) ON DELETE CASCADE,
                FOREIGN KEY(demoID) REFERENCES demo(id) ON DELETE CASCADE,
                UNIQUE(demoID, editorId)
                );"""
            )

            conn.commit()
            conn.close()
        except Exception as ex:

            error_string = ("createDb e:%s" % (str(ex)))
            print error_string

            if os.path.isfile(dbname):
                try:
                    os.remove(dbname)
                except Exception as ex:
                    error_string = ("createDb remove e:%s" % (str(ex)))
                    print error_string
                    status = False

        print "DB Created"
    else:
        print "Create DB pass"
    return status


def initDb(database_name):
    """
    Initialize the database (could be replaced by SOUTH migrations)
    """
    status = True
    dbname = database_name



    try:
        conn = lite.connect(dbname)
        cursor_db = conn.cursor()
        cursor_db.execute(""" PRAGMA foreign_keys=ON""")

        # init state test, workshop, preprint, published
        cursor_db.execute('''INSERT INTO state (name,description) VALUES(?, ?)''',
                          ('published', 'published',))
        cursor_db.execute('''INSERT INTO state (name,description) VALUES(?, ?)''',
                          ('preprint', 'preprint',))
        cursor_db.execute('''INSERT INTO state (name,description) VALUES(?, ?)''',
                          ('workshop', 'workshop',))
        cursor_db.execute('''INSERT INTO state (name,description) VALUES(?, ?)''',
                          ('test', 'test',))

        conn.commit()
        conn.close()

    except Exception as ex:

        error_string = ("initDb e:%s" % (str(ex)))
        print error_string
        status = False

    print "DB Initialized"



    return status


def testDb(database_name):
    """
    Initialize the database for TESTING PURPOSES!
    (South migrations should be used instead od scripts)
    """
    status = True
    dbname = database_name
    print
    print "STARTING DB TESTS"

    try:
        conn = lite.connect(dbname)
        cursor_db = conn.cursor()
        cursor_db.execute(""" PRAGMA foreign_keys=ON""")

        # demo
        print "* DB DemoDAO"
        demo_dao = DemoDAO(conn)
        editorsdemoid = 24
        title = 'Demo TEST Title'
        abstract = 'Demo Abstract'
        zipURL = 'https://www.sqlite.org/lang_createtable.html'
        stateID = 1
        d = Demo(editorsdemoid, title, abstract, zipURL, stateID)
        demo_dao.add(d)
        print d.__dict__

        d = demo_dao.read(1)
        d.zipURL = 'https://www.sqlite.org'
        d.state = 2
        demo_dao.update(d)
        # demo.delete(1)
        d = demo_dao.read(1)
        print d.__dict__

        editorsdemoid = 43
        title = 'Demo 2 TEST Title'
        abstract = 'Demo2 Abstract'
        zipURL = 'https://www.sqlite.org/demo2'
        stateID = 1
        d2 = Demo(editorsdemoid, title, abstract, zipURL, stateID)
        demo_dao.add(d2)


        # author
        print "* DB AuthorDAO"
        author_dao = AuthorDAO(conn)
        name = 'jose Arrecio Kubon'
        mail = 'jak@gmail.com'
        a = Author(name, mail)
        author_dao.add(a)
        a = author_dao.read(1)
        a.name = 'Pepe Arrecio Kubon'
        author_dao.update(a)
        # author.delete(1)
        a = author_dao.read(1)
        print a.__dict__

        # demo-author
        print '* DB demo-author'
        da_dao = DemoAuthorDAO(conn)
        print a.id, d.id
        da_dao.add(d.id, a.id)
        da_dao.add(2, a.id)
        print da_dao.read_author_demos(a.id)
        print da_dao.read_demo_authors(d.id)
        print da_dao.read(1)

        # editor
        print "* DB EditorDAO"
        editor_dao = EditorDAO(conn)
        name = 'Editor1'
        mail = 'editor1@gmail.com'
        e = Editor(name, mail)
        editor_dao.add(e)
        e = editor_dao.read(1)
        e.name = 'Editor2'
        editor_dao.update(e)
        # editor.delete(1)
        e = editor_dao.read(1)
        print e.__dict__

        # demo-editor
        print '* DB demo-editor'
        de_dao = DemoEditorDAO(conn)
        print e.id, e.id
        de_dao.add(e.id, e.id)
        de_dao.add(2, e.id)
        print de_dao.read_editor_demos(e.id)
        print de_dao.read_demo_editors(d.id)
        print de_dao.read(3)
        print de_dao.read(1)

        conn.commit()
        conn.close()

    except Exception as ex:

        error_string = ("testDb e:%s" % (str(ex)))
        print error_string
        status = False

    print "DB test ok"
    return status

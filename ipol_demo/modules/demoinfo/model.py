# -*- coding:utf-8 -*-

"""
DATA MODEL

This module will encapsulate all the DB operations
It has the creation scrript,  DAOs to encapsulte sql and ,
a few helper clases that represent the objects modeld
in the DB that will be used by the webservices,

"""

import datetime
import sqlite3 as lite

#####################
#  helper clases    #
#####################

class Demo():
    """
    Class representing a demo.
    """

    editorsdemoid = None
    title = None
    state = None
    creation = None
    modification = None

    def __init__(self,
            editorsdemoid,
            title,
            state,
            creation=None,
            modification=None):
        """
        Constructor.
        """

        self.editorsdemoid = editorsdemoid
        self.title = title
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


class Author():
    """
    Object representing an author.
    """
    id = None
    name = None
    mail = None
    creation = None

    # And(inst(basestring),len_between(4,100)),
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


class Editor():
    """
    Object representing an editor.
    """
    id = None
    name = None
    mail = None
    creation = None

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

class DemoDescriptionDAO():
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

    # conn.close()

    def add(self, ddl):
        """
        Add description for the given demo.
        """
        self.cursor.execute('''INSERT INTO demodescription (creation, DDL)
                               VALUES(datetime(CURRENT_TIMESTAMP, 'localtime'),?)''', (ddl,))
        self.conn.commit()
        return self.cursor.lastrowid

    def delete(self, demo_description_id):
        """
        delete description for the given demo.
        """
        self.cursor.execute("DELETE FROM demodescription WHERE id=?", (int(demo_description_id),))
        self.conn.commit()

    def update(self, ddl, demo_id):
        """
        update description for a given demo.
        """
        self.cursor.execute("""
            UPDATE demodescription
            SET ddl = ?, creation = datetime(CURRENT_TIMESTAMP, 'localtime')
            WHERE id = (SELECT  dd.id
                        FROM demo_demodescription AS ddd, demodescription AS dd, demo AS d
                        WHERE dd.id = ddd.demodescriptionid AND ddd.demoid = d.id AND d.editor_demo_id = ?
                        ORDER by dd.creation DESC LIMIT 1
                       )
            """, (ddl, demo_id))
        nowtmstmp = datetime.datetime.now()
        self.cursor.execute('''UPDATE demo SET modification=? WHERE editor_demo_id=?''', (nowtmstmp, demo_id))

        if self.cursor.rowcount == 0:
            error_string = ("Demo %s not updated in DemoDescriptionDAO" % (str(demo_id)))
            print(error_string)
            raise Exception(error_string)

        self.conn.commit()

    def read(self, demo_description_id):
        """
        read description for given demo.
        """
        result = None
        self.cursor.execute('''SELECT  ddl  FROM demodescription WHERE id=?''',
                            (int(demo_description_id),))
        self.conn.commit()
        row = self.cursor.fetchone()
        if row:
            result = (row[0], row[1])
        return result


class DemoDAO():
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

    # conn.close()

    def add(self, demo):
        """
        Add a demo.
        """
        self.cursor.execute('''SELECT ID
                            FROM state
                            WHERE state.name=?''', (demo.state,))
        self.conn.commit()
        state_id = self.cursor.fetchone()[0]
        self.cursor.execute('''
        INSERT INTO demo(editor_demo_id, title, creation, modification, stateID)
        VALUES(?, ?, datetime(CURRENT_TIMESTAMP, 'localtime'), datetime(CURRENT_TIMESTAMP, 'localtime'),?)''',
                            (demo.editorsdemoid, demo.title, state_id,))
        self.conn.commit()
        return demo.editorsdemoid

    def delete(self, editor_demo_id):
        """
        delete a demo.
        """
        self.cursor.execute("DELETE FROM demo WHERE demo.editor_demo_id=?", (int(editor_demo_id),))
        self.conn.commit()

    def update(self, demo, old_editor_demo_id):
        """
        update a demo.
        """

        nowtmstmp = datetime.datetime.now()
        self.cursor.execute('''SELECT ID
                            FROM state
                            WHERE state.name=?''', (demo.state,))
        self.conn.commit()
        state_id = self.cursor.fetchone()[0]

        if demo.creation:

            self.cursor.execute('''
            UPDATE demo SET editor_demo_id=?,title=?,
            stateID=?,modification=?,creation=? WHERE demo.editor_demo_id=?''',
                                (demo.editorsdemoid, demo.title, state_id, nowtmstmp,
                                 demo.creation, old_editor_demo_id))

        else:
            self.cursor.execute('''
            UPDATE demo SET editor_demo_id=?,title=?,
            stateID=?,modification=?,creation=? WHERE demo.editor_demo_id=?''',
                                (demo.editorsdemoid, demo.title, state_id, nowtmstmp,
                                 demo.creation, old_editor_demo_id))
        self.conn.commit()

    def read(self, editor_demo_id):
        """
        Return a description of the demo.
        """
        result = None
        self.cursor.execute('''SELECT  d.editor_demo_id, d.title, s.name, d.creation, d.modification
                            FROM demo as d, state as s
                            WHERE d.editor_demo_id=?
                            AND d.stateID = s.ID''', (int(editor_demo_id),))

        self.conn.commit()
        row = self.cursor.fetchone()
        if row:
            d = Demo(row[0], row[1], row[2], row[3], row[4])
            result = d
        return result

    def list(self):
        """
        Return a list of demos.
        """
        demo_list = list()

        self.cursor.execute('''SELECT d.editor_demo_id, d.title, s.name, d.creation, d.modification
                            FROM demo as d, state as s
                            WHERE d.stateID = s.ID
                            ORDER BY d.editor_demo_id DESC ''')

        self.conn.commit()
        for row in self.cursor.fetchall():
            d = Demo(row[0], row[1], row[2], row[3], row[4])
            demo_list.append(d)
        return demo_list

    def exist(self, editor_demo_id):
        """
        Returns whether the demo exists or not
        """
        self.cursor.execute("""
        SELECT EXISTS(SELECT *
                    FROM demo
                    WHERE editor_demo_id=?);
        """, (editor_demo_id,))

        return self.cursor.fetchone()[0] == 1

    def has_ssh_key(self, editor_demo_id):
        """
        Returns whether the demo has an ssh key
        """
        self.cursor.execute("""
        SELECT EXISTS(SELECT *
                    FROM demo
                    WHERE editor_demo_id=? and ssh_pubkey is not null);
        """, (editor_demo_id,))

        return self.cursor.fetchone()[0] == 1

    def get_ssh_key(self, editor_demo_id):
        self.cursor.execute("""
        SELECT ssh_pubkey, ssh_privkey
        FROM demo
        WHERE editor_demo_id=?;
        """, (editor_demo_id,))
        return self.cursor.fetchone()

    def set_ssh_key(self, editor_demo_id, pubkey, privkey):
        self.cursor.execute("""
        UPDATE demo
        SET ssh_pubkey=?, ssh_privkey=?
        WHERE editor_demo_id=?;
        """, (pubkey, privkey, editor_demo_id))
        self.conn.commit()


class DemoDemoDescriptionDAO():
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

    def add(self, editorsdemoid, demodescriptionid):
        """
        Add an entry in the table.
        """
        self.cursor.execute('''
        INSERT INTO demo_demodescription(demodescriptionID,demoID)
        VALUES(?,(SELECT ID
            FROM demo
            WHERE demo.editor_demo_id=?))''', (int(demodescriptionid), int(editorsdemoid),))
        nowtmstmp = datetime.datetime.now()
        self.cursor.execute('''UPDATE demo SET modification=? WHERE editor_demo_id=?''', (nowtmstmp, editorsdemoid))
        self.conn.commit()

    def delete(self, editorsdemoid):
        """
        Remove an entry.
        """
        self.cursor.execute('''
        DELETE
        FROM demo_demodescription
        WHERE id=(SELECT ID
            FROM demo
            where demo.editor_demo_id=?)''', (int(editorsdemoid),))
        self.conn.commit()

    def delete_all_demodescriptions_for_demo(self, editorsdemoid):
        """
        remove all entries for a demo.
        """
        self.cursor.execute('''
        DELETE
        FROM demodescription
        WHERE ID in (SELECT demodescriptionid
                FROM demo_demodescription
                WHERE demoID=(SELECT ID
                        FROM demo
                        WHERE demo.editor_demo_id=?))''', (int(editorsdemoid),))
        self.conn.commit()

    def remove_demodescription_from_demo(self, editorsdemoid, demodescriptionid):
        """
        remove editor from demo.
        """
        self.cursor.execute('''
        DELETE
        FROM demo_demodescription
        WHERE demodescriptionID=?
        AND demoID=(SELECT ID
                FROM demo
                WHERE demo.editor_demo_id =?)''', (int(demodescriptionid), int(editorsdemoid),))
        self.conn.commit()

    def read(self, editorsdemoid):
        """
        Get the editor from a demo.
        """
        result = None
        self.cursor.execute('''
        SELECT demo.editor_demo_id,demodescriptionID
        FROM demo_demodescription , demo
        WHERE demo.ID=demo_demodescription.demoID
        AND demo.editor_demo_id=?''', (int(editorsdemoid),))
        self.conn.commit()
        row = self.cursor.fetchone()
        if row:
            result = {'editorsDemoID': row[0], 'editorId': row[1]}

        return result

    def get_ddl(self, editorsdemoid):
        """
        return last demo description entered for editorsdemoid.
        """
        self.cursor.execute('''SELECT ddl.DDL
             FROM demodescription as ddl
             INNER JOIN demo_demodescription AS dd ON dd.demodescriptionId = ddl.ID
             INNER JOIN demo ON  demo.ID = dd.demoId
             WHERE editor_demo_id = ?
             ORDER BY ddl.creation DESC LIMIT 1''', (int(editorsdemoid),))

        self.conn.commit()
        row = self.cursor.fetchone()
        if row:
            return {'ddl': row[0]}
        return None

    def read_demo_demodescriptions(self, editorsdemoid):
        """
        Return list of demo descriptions from given editor.
        """

        demodescription_list = list()
        self.cursor.execute('''
            SELECT ddl.ID,ddl.creation,ddl.DDL
            FROM demo_demodescription as dd, demodescription as ddl, demo as d
            WHERE  dd.demodescriptionID=ddl.ID
            AND dd.demoID= d.ID
            AND d.editor_demo_id=?
            ORDER BY ddl.ID DESC''', (int(editorsdemoid),))
        self.conn.commit()
        for row in self.cursor.fetchall():
            ddl = (row[0], row[1], row[2])
            demodescription_list.append(ddl)

        return demodescription_list

    def read_history(self, demo_id):
        """
        Read the DDl history for the given demo
        """
        self.cursor.execute('''
        SELECT  ddl , creation
        FROM demodescription
        WHERE id in (SELECT demodescriptionId
                    FROM demo_demodescription, demo
                    WHERE demoID = demo.id
                    AND demo.editor_demo_id = ?)
        ''', (int(demo_id),))
        history = []
        for row in self.cursor.fetchall():
            history.append({"ddl": row[0], "creation": row[1]})

        return history


class AuthorDAO():
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

    def add(self, author):
        """
        add an author to the db.
        """
        self.cursor.execute('''
        INSERT INTO author(name, mail, creation)
        VALUES(?,?,datetime(CURRENT_TIMESTAMP, 'localtime'))''', (author.name, author.mail,))
        self.conn.commit()
        return self.cursor.lastrowid

    def delete(self, the_id):
        """
        delete an author from the db.
        """
        self.cursor.execute("DELETE FROM author WHERE id=?", (int(the_id),))
        self.conn.commit()

    def update(self, author):
        """
        update an author entry.
        """
        if author.creation:
            self.cursor.execute('''
            UPDATE author SET name=?, mail=?,creation=? WHERE id=?''',
                                (author.name, author.mail, author.creation, author.id))
        else:
            self.cursor.execute('''
            UPDATE author SET name=?, mail=? WHERE id=?''', (author.name, author.mail, author.id))

        self.conn.commit()

    def read(self, the_id):
        """
        get the author info from their id.
        """
        result = None
        self.cursor.execute('''SELECT  name, mail,id, creation FROM author WHERE id=?''', (int(the_id),))
        self.conn.commit()
        row = self.cursor.fetchone()
        if row:
            a = Author(row[0], row[1], row[2], row[3])
            result = a
        return result

    def list(self):
        """
        get a list of all the authors of the database.
        """
        author_list = list()
        self.cursor.execute('''SELECT name, mail,id, creation FROM author ORDER BY id DESC ''')
        self.conn.commit()
        for row in self.cursor.fetchall():
            a = Author(row[0], row[1], row[2], row[3])
            author_list.append(a)

        return author_list

    def exist(self, author_id):
        """
        Returns whether the author exists or not
        """
        self.cursor.execute("""
        SELECT EXISTS(SELECT *
                    FROM author
                    WHERE id=?);
        """, (author_id,))

        return self.cursor.fetchone()[0] == 1


class DemoAuthorDAO():
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
            print(error_string)
            raise Exception(error_string)

    def delete(self, the_id):
        """
        delete an entry from the table.
        """
        try:
            self.cursor.execute("DELETE FROM demo_author WHERE id=?", (int(the_id),))
            self.conn.commit()
        except Exception as ex:
            error_string = ("delete_demo_author  e:%s" % (str(ex)))
            print(error_string)
            raise Exception(error_string)

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
            print(error_string)
            raise Exception(error_string)

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
            print(error_string)
            raise Exception(error_string)

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
            print(error_string)
        return result

    def read_author_demos(self, authorid):
        """
        Get a list of the demos realised by a given author.
        """
        demo_list = list()
        try:
            self.cursor.execute('''SELECT d.editor_demo_id, d.title, s.name , d.creation, d.modification
                                FROM demo as d, demo_author as da, state as s
                                WHERE d.id=da.demoId
                                AND d.stateID = s.ID
                                AND da.authorId=?''', (int(authorid),))
            self.conn.commit()
            for row in self.cursor.fetchall():
                d = Demo(row[0], row[1], row[2], row[3], row[4])
                demo_list.append(d)

        except Exception as ex:
            error_string = ("read_author_demos  e:%s" % (str(ex)))
            print(error_string)
        return demo_list

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
            print(error_string)
        return author_list


class EditorDAO():
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

    def add(self, editor):
        """
        Add an editor.
        """
        self.cursor.execute('''
        INSERT INTO editor(name, mail, creation)
        VALUES(?,?, datetime(CURRENT_TIMESTAMP, 'localtime'))''', (editor.name, editor.mail,))
        self.conn.commit()
        return self.cursor.lastrowid

    def delete(self, the_id):
        """
        delete an editor.
        """
        self.cursor.execute("DELETE FROM editor WHERE id=?", (int(the_id),))
        self.conn.commit()

    def update(self, editor):
        """
        update an editor.
        """

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

    def read(self, the_id):
        """
        get an editor from its ID.
        """
        self.cursor.execute('''SELECT name, mail, id, creation
        FROM editor WHERE id=?''', (int(the_id),))
        # name, mail, id=None,creation=None):
        self.conn.commit()
        row = self.cursor.fetchone()

        return Editor(row[0], row[1], row[2], row[3])

    def list(self):
        """
        get the list of editors.
        """
        editor_list = list()
        # name, mail, id=None, creation=
        self.cursor.execute('''SELECT  name, mail,  id, creation
        FROM editor ORDER BY id DESC ''')
        self.conn.commit()
        for row in self.cursor.fetchall():
            e = Editor(row[0], row[1], row[2], row[3])
            # print 'editor list'
            # print e.__dict__
            editor_list.append(e)

        return editor_list

    def exist(self, editor_id):
        """
        Returns whether the editor exists or not
        """
        self.cursor.execute("""
        SELECT EXISTS(SELECT *
                    FROM editor
                    WHERE id=?);
        """, (editor_id,))

        return self.cursor.fetchone()[0] == 1


class DemoEditorDAO():
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

    def add(self, editorsdemoid, editorid):
        """
        Add an entry to the demo_editor table.
        """
        self.cursor.execute('''
        INSERT INTO demo_editor(editorId,demoID)
        VALUES(?,(SELECT ID
            FROM demo
            WHERE demo.editor_demo_id=?))''', (int(editorid), int(editorsdemoid),))
        self.conn.commit()

    def delete(self, the_id):
        """
        delete an entry from id.
        """
        self.cursor.execute("DELETE FROM demo_editor WHERE id=?", (int(the_id),))
        self.conn.commit()

    def delete_all_editors_for_demo(self, editorsdemoid):
        """
        remove editor from demos/editor correspondence.
        """
        self.cursor.execute('''
        DELETE
        FROM demo_editor
        WHERE demoID=(SELECT ID
                FROM demo
                WHERE demo.editor_demo_id=?)''', (int(editorsdemoid),))
        self.conn.commit()

    def remove_editor_from_demo(self, editorsdemoid, editorid):
        """
        remove editor from demos/editor correspondence and editor id.
        """
        self.cursor.execute('''
        DELETE
        FROM demo_editor
        WHERE editorId=?
        AND demoID=(SELECT ID
                FROM demo
                WHERE demo.editor_demo_id=?)''', (int(editorid), int(editorsdemoid),))
        self.conn.commit()

    def read(self, the_id):
        """
        get editor from id.
        """
        result = None
        self.cursor.execute('''
        SELECT demo_editor.ID,demo.editor_demo_id, demo_editor.editorId
        FROM demo_editor , demo
        WHERE demo_editor.demoID=demo.ID
        AND demo_editor.ID=?''', (int(the_id),))
        self.conn.commit()
        row = self.cursor.fetchone()
        if row:
            result = {'id': row[0], 'editorDemoID': row[1], 'editorId': row[2]}

        return result

    def read_editor_demos(self, editorid):
        """
        get list of demos from an editor id.
        """
        demo_list = list()
        self.cursor.execute('''SELECT d.editor_demo_id, d.title, s.name, d.id, d.creation, d.modification
                            FROM demo as d, demo_editor as de, state as s
                            WHERE d.id=de.demoId
                            AND d.stateID = s.ID
                            AND de.editorId=?''', (int(editorid),))
        self.conn.commit()
        for row in self.cursor.fetchall():
            d = Demo(row[0], row[1], row[2], row[3], row[4])
            demo_list.append(d)
        return demo_list

    def read_demo_editors(self, editordemoid):
        """
        get list of editors from an editor-demo correspondence.
        """
        editor_list = list()
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

        return editor_list


###########################
#    DB setup functions   #
###########################


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
        print(error_string)
        status = False

    print("DB Initialized")

    return status

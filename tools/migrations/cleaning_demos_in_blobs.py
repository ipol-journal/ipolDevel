#!/usr/bin/python

import sqlite3 as lite
import os


def connect_to_db(db_dir, db_name):
    try:
        return lite.connect(os.path.join(db_dir, db_name))
    except Exception as ex:
        print "Couldn't connect to the DB {}. Error: {}".format(os.path.join(db_dir, db_name), ex)
        raise


def main():
    blobs_db_dir = "../../ipol_demo/modules/blobs/db/"
    di_db_dir = "../../ipol_demo/modules/demoinfo/"
    blobs_db_name = "blobs.db"
    di_db_name = "demoinfo.db"
    di_conn = None
    blobs_conn = None
    try:
        blobs_conn = connect_to_db(blobs_db_dir, blobs_db_name)
        di_conn = connect_to_db(di_db_dir, di_db_name)
        blobs_cursor = blobs_conn.cursor()
        di_cursor = di_conn.cursor()

        blobs_demo_list = get_demos_from_blob(blobs_cursor)
        demoinfo_demo_list = get_demos_from_demoinfo(di_cursor)

        unused_demos = []
        for blobs_demo in blobs_demo_list:
            found = False
            for demoinfo_demo in demoinfo_demo_list:
                if demoinfo_demo == blobs_demo:
                    found = True
                    break
            if not found:
                unused_demos.append(blobs_demo)

        if len(unused_demos) > 0:
            print "There are {} unused demos: \n{}".format(len(unused_demos), unused_demos)
            delete_unused_demos(blobs_cursor, unused_demos)
            blobs_conn.commit()

    except Exception as ex:
        print "Failure in the migration. Error: {}".format(ex)
        blobs_conn.rollback()

    finally:
        if di_conn is not None:
            di_conn.close()
        if blobs_conn is not None:
            blobs_conn.close()


def get_demos_from_blob(blobs_cursor):
    blobs_cursor.execute("""
        SELECT editor_demo_id
        FROM demos
        """)
    demo_list = []
    for demo in blobs_cursor.fetchall():
        demo_list.append(demo[0])
    return demo_list


def get_demos_from_demoinfo(demoinfo_cursor):
    demoinfo_cursor.execute("""
        SELECT editor_demo_id
        FROM demo
        """)
    demo_list = []
    for demo in demoinfo_cursor.fetchall():
        demo_list.append(demo[0])
    return demo_list


def delete_unused_demos(cursor, unused_demos):
    cursor.execute("""PRAGMA FOREIGN_KEYS = ON""")
    for demo in unused_demos:
        print "deleting: ",demo
        cursor.execute("""
                    DELETE
                    FROM demos
                    WHERE editor_demo_id = ?
                    """, (demo,))


main()

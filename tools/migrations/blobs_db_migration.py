#!/usr/bin/python
# -*- coding: utf-8 -*-

# GNU General Public Licence (GPL)
#
# This program is free software; you can redistribute it and/or modify it under
# the terms of the GNU General Public License as published by the Free Software
# Foundation; either version 2 of the License, or (at your option) any later
# version.
# This program is distributed in the hope that it will be useful, but WITHOUT
# ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS
# FOR A PARTICULAR PURPOSE.  See the GNU General Public License for more
# details.
# You should have received a copy of the GNU General Public License along with
# this program; if not, write to the Free Software Foundation, Inc., 59 Temple
# Place, Suite 330, Boston, MA  02111-1307  USA
#

import sqlite3 as lite
import os


def connect_to_db(db_dir, db_name):
    try:
        return lite.connect(os.path.join(db_dir, db_name))
    except Exception as ex:
        print "Couldn't connect to the DB {}. Error: {}".format(os.path.join(db_dir, db_name), ex)
        raise


def main():
    db_dir = "../../ipol_demo/modules/blobs/db/"
    db_name = "blobs.db"
    conn = None
    try:
        conn = connect_to_db(db_dir, db_name)
        cursor = conn.cursor()

        # Remove duplicated values
        # In integration there are 2 demos with id 125 and
        # 17 blobs with duplicated (demo_id, blob_set, pos_in_set)
        # In order to migrate to the new DB these items should be deleted
        remove_duplicated_demos(cursor)
        remove_duplicated_demos_blobs(cursor)

        # SELECTS
        blobs = get_blobs(cursor)
        demos, templates = get_demos_and_templates(cursor)
        tags = get_tags(cursor)

        blobs_tags = get_blob_tag_join_table(cursor)
        demos_blobs = get_demo_blob_join_table(cursor)
        templates_blobs = get_template_blob_join_table(cursor)

        # Creates a backup of the old DB
        os.rename(os.path.join(db_dir, db_name), os.path.join(db_dir, "old_blobs.db"))
        # Creates the new DB and connect to it
        create_new_db(db_dir, db_name)

        conn = connect_to_db(db_dir, db_name)
        cursor = conn.cursor()

        # INSERTS
        insert_blobs(cursor, blobs)
        insert_demos(cursor, demos)
        insert_templates(cursor, templates)
        insert_tags(cursor, tags)

        insert_demos_blobs(cursor, demos_blobs)
        insert_templates_blobs(cursor, templates_blobs)
        insert_demos_templates(cursor, demos)
        insert_blobs_tags(cursor, blobs_tags)

        conn.commit()

        # Remove backup
        # os.remove(os.path.join(db_dir, "old_blobs.db"))
    except Exception as ex:
        print "Failure in the migration. Error: {}".format(ex)
        conn.rollback()

        try:
            os.remove(os.path.join(db_dir, db_name))
            os.rename(os.path.join(db_dir, "old_blobs.db"), os.path.join(db_dir, db_name))
        except Exception as ex:
            print "Failure restoring original DB. Error:", ex
    finally:
        if conn is not None:
            conn.close()


def get_tags(cursor):
    # Get all tags
    tags = []
    try:
        cursor.execute("""
                SELECT id, name
                FROM tag
                """)
        for row in cursor.fetchall():
            tags.append({"id": row[0], "name": row[1]})
    except Exception as ex:
        print "get_tags", ex
        raise

    return tags


def get_demos_and_templates(cursor):
    # Get all demos and templates
    demos = []
    templates = []
    try:
        cursor.execute("""
                SELECT id, name, is_template, template_id
                FROM demo
                """)
        for row in cursor.fetchall():
            if row[2] == 0:  # if is_template = 0 it means is a demo, otherwise is a template
                demos.append({"id": row[0], "editor_demo_id": row[1], "template_id": row[3]})
            else:
                templates.append({"id": row[0], "name": row[1]})
    except Exception as ex:
        print "get_demos_and_templates. Error:", ex
        raise

    return demos, templates


def get_blobs(cursor):
    # Get all blobs
    blobs = []
    try:
        cursor.execute("""
            SELECT id, hash, format, extension, title, credit
            FROM blob
            """)
        for row in cursor.fetchall():
            blobs.append({"id": row[0], "hash": row[1], "format": row[2], "extension": row[3],
                          "title": row[4], "credit": row[5]})
    except Exception as ex:
        print "get_blobs", ex
        raise

    return blobs


def get_blob_tag_join_table(cursor):
    blob_tag = []
    try:
        cursor.execute("""
                SELECT blob_id, tag_id
                FROM blob_tag
                """)
        for row in cursor.fetchall():
            blob_tag.append({"blob_id": row[0], "tag_id": row[1]})
    except Exception as ex:
        print "get_blob_tag_join_table", ex
        raise

    return blob_tag


def get_demo_blob_join_table(cursor):
    demo_blob = []
    try:
        cursor.execute("""
                    SELECT blob_id, demo_id, blob_set, demo_blob.id, blob_pos_in_set
                    FROM demo_blob, demo
                    WHERE demo_id = demo.id
                    AND is_template = 0
                    """)
        for row in cursor.fetchall():
            demo_blob.append({"blob_id": row[0], "demo_id": row[1], "blob_set": row[2], "id": row[3],
                              "blob_pos_in_set": row[4]})
    except Exception as ex:
        print "get_demo_blob_join_table", ex
        raise

    return demo_blob


def get_template_blob_join_table(cursor):
    template_blob = []
    try:
        cursor.execute("""
                    SELECT blob_id, demo_id, blob_set, demo_blob.id, blob_pos_in_set
                    FROM demo_blob, demo
                    WHERE demo_id = demo.id
                    AND is_template = 1
                    """)
        for row in cursor.fetchall():
            template_blob.append({"blob_id": row[0], "demo_id": row[1], "blob_set": row[2], "id": row[3],
                                  "blob_pos_in_set": row[4]})
    except Exception as ex:
        print "get_template_blob_join_table", ex
        raise

    return template_blob


def create_new_db(db_dir, db_name):
    try:
        conn = connect_to_db(db_dir, db_name)
        cursor_db = conn.cursor()
        sql_buffer = ""
        with open(db_dir + '/drop_create_db_schema.sql', 'r') as sql_file:
            for line in sql_file:
                sql_buffer += line
                if lite.complete_statement(sql_buffer):
                    sql_buffer = sql_buffer.strip()
                    cursor_db.execute(sql_buffer)
                    sql_buffer = ""

        conn.commit()
        conn.close()

    except Exception as ex:
        print "Couldn't create the new DB. Error:", ex
        raise


def insert_blobs(cursor, blobs):
    try:
        for blob in blobs:
            cursor.execute("""
                INSERT INTO blobs (id, hash, format, extension, title, credit)
                VALUES (?,?,?,?,?,?)
                """, (blob['id'], blob['hash'], blob['format'],
                      blob['extension'], blob['title'], blob['credit']))

    except Exception as ex:
        print "insert_blobs_and_templates. Error:", ex
        raise


def insert_demos(cursor, demos):
    current_demo = None
    try:
        for demo in demos:
            current_demo = demo
            cursor.execute("""
                INSERT INTO demos (id, editor_demo_id)
                VALUES (?,?)
                """, (demo['id'], int(demo['editor_demo_id'])))

    except Exception as ex:
        print "insert_demos_and_templates. Error: {}, for demo #{}".format(ex, current_demo['id'])
        raise


def insert_templates(cursor, templates):
    try:
        for templates in templates:
            cursor.execute("""
                INSERT INTO templates (id, name)
                VALUES (?,?)
                """, (templates['id'], templates['name']))

    except Exception as ex:
        print "insert_templates. Error:", ex
        raise


def insert_tags(cursor, tags):
    try:
        for tag in tags:
            cursor.execute("""
                INSERT INTO tags (id, name)
                VALUES (?,?)
                """, (tag['id'], tag['name']))

    except Exception as ex:
        print "insert_tags. Error:", ex
        raise


def insert_demos_blobs(cursor, demos_blobs):
    current_row = None
    try:
        for row in demos_blobs:
            current_row = row

            if row['blob_set'] == "":
                row['blob_set'] = get_blob_set(cursor, row['blob_id'])

            cursor.execute("""
                INSERT INTO demos_blobs (demo_id, blob_id, blob_set, pos_in_set)
                VALUES (?,?,?,?)
                """, (row['demo_id'], row['blob_id'], row['blob_set'], row['blob_pos_in_set']))

    except Exception as ex:
        print "insert_demos_blobs. Error: {}, for row {}".format(ex, current_row)
        raise


def insert_demos_templates(cursor, demos):
    try:
        for demo in demos:
            if demo['template_id'] == 0:
                continue
            cursor.execute("""
                INSERT INTO demos_templates (demo_id, template_id)
                VALUES (?,?)
                """, (demo['id'], demo['template_id']))

    except Exception as ex:
        print "insert_demos_templates. Error:", ex
        raise


def insert_templates_blobs(cursor, templates_blobs):
    current_row = None
    try:
        for row in templates_blobs:
            current_row = row

            if row['blob_set'] == "":
                row['blob_set'] = get_blob_set(cursor, row['blob_id'])

            cursor.execute("""
                INSERT INTO templates_blobs (template_id, blob_id, blob_set, pos_in_set)
                VALUES (?,?,?,?)
                """, (row['demo_id'], row['blob_id'], row['blob_set'], row['blob_pos_in_set']))

    except Exception as ex:
        print "insert_templates_blobs. Error: {}, for row {}".format(ex, current_row)
        raise


def insert_blobs_tags(cursor, blobs_tags):
    try:
        for row in blobs_tags:
            cursor.execute("""
                INSERT INTO blobs_tags (blob_id, tag_id)
                VALUES (?,?)
                """, (row['blob_id'], row['tag_id']))

    except Exception as ex:
        print "insert_blobs_tags. Error:", ex
        raise


def remove_duplicated_demos(cursor):
    # Demo 125 is duplicated
    try:
        cursor.execute("""
           DELETE
           FROM demo
           WHERE id in (SELECT id
                        FROM (SELECT *, COUNT(*) c
                              FROM demo
                              GROUP BY name
                              HAVING c > 1))
           """)
    except Exception as ex:
        print "remove_duplicated_demos. Error:", ex
        raise


def remove_duplicated_demos_blobs(cursor):
    # 17 blobs with duplicated (demo_id, blob_set, pos_in_set)
    # in demo_blob from demos with id 2, 60 and 98
    try:
        cursor.execute("""
            DELETE
            FROM demo_blob
            WHERE blob_id in (SELECT blob_id
                            FROM (SELECT blob_id, COUNT(*) c
                                  FROM demo_blob
                                  GROUP BY demo_id, blob_set, blob_pos_in_set
                                  HAVING c > 1));
            """)
    except Exception as ex:
        print "remove_duplicated_demos_blobs. Error:", ex
        raise


def get_blob_set(cursor, blob_id):
    try:
        cursor.execute("""
            SELECT hash
            FROM blobs
            WHERE id = ?
            """, (blob_id,))
        return "__" + cursor.fetchone()[0]
    except Exception as ex:
        print "get_blob_set. Error:", ex
        raise


##################
# Calls the main #
##################
main()

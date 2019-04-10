#!/usr/bin/env python

'''
April 10, 2019.
The problem was that the pos_in_set of the blobsets were not referencing to an input.
We couldn't link an optional input with the position in the blobset. This happens when there are gaps between 
blob locations inside the blobset designed positions.
'''

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
    blobs_db_name = "blobs.db"
    blobs_conn = None
    try:
        blobs_conn = connect_to_db(blobs_db_dir, blobs_db_name)
        blobs_cursor = blobs_conn.cursor()

        demo_ids = get_all_demo_id(blobs_cursor)

        for demo_id in demo_ids:
            blobsets = get_demo_blobsets(blobs_cursor, demo_id)
            for blobset in blobsets:
                blobset_blobs = get_blobset_blobs(blobs_cursor, demo_id, blobset)
                for i, blob in enumerate(blobset_blobs):
                    pos_in_set = blob[4]
                    if i != pos_in_set: 
                        print("For demo #{} updating blobset {}: {} -> {}".format(demo_id, blobset[0],pos_in_set, i))
                        blobs_cursor.execute("""
                            UPDATE demos_blobs
                            SET pos_in_set = ?
                            WHERE demo_id = ?
                            AND blob_set = ?
                            AND pos_in_set = ?
                        """, (i, str(demo_id), str(blobset[0]), pos_in_set))

        blobs_conn.commit()
    except Exception as ex:
        print "Failure in the migration. Error: {}".format(ex)
        blobs_conn.rollback()

    finally:
        if blobs_conn:
            blobs_conn.close()

def get_all_demo_id(blobs_cursor):
    blobs_cursor.execute("""
        SELECT id
        FROM demos
        """)
    id_list = []
    for demo_id in blobs_cursor.fetchall():
        id_list.append(demo_id[0])
    return id_list

def get_demo_blobsets(blobs_cursor, demo_id):
    blobs_cursor.execute("""
        SELECT DISTINCT blob_set
        FROM demos_blobs
        WHERE demo_id = ?
        ORDER by id
        """, (str(demo_id),))
    blobsets = []
    for blobset in blobs_cursor.fetchall():
        blobsets.append(blobset)
    return blobsets

def get_blobset_blobs(blobs_cursor, demo_id, blobset):
    blobs_cursor.execute("""
        SELECT *
        FROM demos_blobs
        WHERE demo_id = ?
        AND blob_set = ?
        ORDER by pos_in_set
        """, (str(demo_id), str(blobset[0])))
    blobs = []
    for blob in blobs_cursor.fetchall():
        blobs.append(blob)
    return blobs

main()

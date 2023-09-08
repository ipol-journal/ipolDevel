#!/usr/bin/env python3

import datetime
import json
import os
import requests
import argparse
import sqlite3 as lite

# parse the arguments
ap = argparse.ArgumentParser()
ap.add_argument("--database_dir", "-db", required=True, help="databse directory containing 'demoinfo.db' file")
ap.add_argument("-r", '--remove', help="Remove Demo", action="store_true")
args = ap.parse_args()
database_dir = args.database_dir


def connect_to_db(db_file):
    try:
        return lite.connect(db_file)
    except Exception as ex:
        print("Couldn't connect to the DB {}. Error: {}".format(db_file, ex))
        raise

def main():
    di_conn = None
    DI_DB = os.path.join(database_dir, 'demoinfo.db')
    
    try:
        di_conn = connect_to_db(DI_DB)
        di_cursor = di_conn.cursor()
        
        demoinfo_demo_list = get_test_demos_from_demoinfo(di_cursor)

        test_demo_list, old_test_demo_list, broadcast_list = ([] for i in range(3))
        for test_demos in demoinfo_demo_list:
            demo_id = test_demos['id']
            test_demo_list.append(demo_id)
            updated_date_str = test_demos['modification']
            a_name = test_demos['a_name']
            a_mail = test_demos['a_mail']
            e_name = test_demos['e_name']
            e_mail = test_demos['e_mail']
            try:
                updated_date = datetime.datetime.strptime(updated_date_str, '%Y-%m-%d %H:%M:%S.%f')
            except:
                updated_date = datetime.datetime.strptime(updated_date_str, '%Y-%m-%d %H:%M:%S')
            if (datetime.datetime.now() - updated_date).total_seconds() > 60 * 60 * 24* 30 * 6:
                old_test_demo_list.append(demo_id)                
                entry = {"demo_id": demo_id, "Editor Name": e_name, "Editor Mail": e_mail, "Author Name": a_name, "Author Mail": a_mail}

                if a_mail or e_mail: broadcast_list.append(entry)

                # delete 6 months old demos
                '''                
                if args.remove:
                    params={
                        'demo_id': demo_id
                    }
                    response = requests.post('http://ipolcore.ipol.im/api/core/delete_demo', params=params).json()
                    if response ['status'] != 'OK':
                        print("Failed to delete demo ID: {}".format(demo_id))
                '''
            
        print("List of All Test Demos:", len(test_demo_list), "\n" ,test_demo_list, "\n")
        print("List of 6 months old Test Demos:", len(old_test_demo_list), "\n" ,old_test_demo_list, "\n")
        print("List of Emails:", "\n", broadcast_list)

    except Exception as ex:
        print("Failure in the migration. Error: {}".format(ex))

    finally:
        if di_conn is not None:
            di_conn.close()


def get_test_demos_from_demoinfo(demoinfo_cursor):
    """
    Get the list of all test demos, their authors and editors
    """
    test_demos = []
    
    demoinfo_cursor.execute("""
        SELECT d.editor_demo_id, d.modification
        FROM demo AS d, state AS s
        WHERE s.name = "test" AND d.stateID = s.ID
        """)
    test_demos = [{'id': i[0], 'modification': i[1], 'a_name': '', 'a_mail': '', 'e_name': '', 'e_mail': ''} for i in demoinfo_cursor.fetchall()]
    for test_demo in test_demos:
        demoinfo_cursor.execute("""
            SELECT a.name, a.mail
            FROM author as a, demo_author as da
            WHERE da.demoID = ? AND a.ID = da.authorId
            """, (test_demo['id'],))
        author_info = demoinfo_cursor.fetchone()
        if author_info:
            test_demo['a_name'] = author_info[0]
            test_demo['a_mail'] = author_info[1]
    for test_demo in test_demos:
        demoinfo_cursor.execute("""
            SELECT e.name, e.mail
            FROM editor as e, demo_editor as de
            WHERE de.demoID = ? AND e.ID = de.editorId
            """, (test_demo['id'],))
        editor_info = demoinfo_cursor.fetchone()
        if editor_info:
            test_demo['e_name'] = editor_info[0]
            test_demo['e_mail'] = editor_info[1]
    return test_demos


main()


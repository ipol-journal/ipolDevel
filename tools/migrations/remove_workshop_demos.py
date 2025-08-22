#!/usr/bin/env python3

import datetime
import json
import os
import sys
import requests
import argparse
import sqlite3 as lite


# parse the arguments
ap = argparse.ArgumentParser()
ap.add_argument("--demoinfo_db", "-demoinfodb", required=True, help="databse directory containing 'demoinfo.db' file")
ap.add_argument("--blob_db", "-blobsdb", required=True, help="databse directory containing 'blobs.db' file")
ap.add_argument("--blob_dir", "-blobsdir", required=True, help="staticData directory containing blobs")
ap.add_argument("-r", '--remove', help="Remove Demo", action="store_true")
args = ap.parse_args()
demoinfo_db = args.demoinfo_db
blob_db = args.blob_db
blob_dir = args.blob_dir

def connect_to_db(db_file):
    try:
        return lite.connect(db_file)
    except Exception as ex:
        print("Couldn't connect to the DB {}. Error: {}".format(db_file, ex))
        raise

def main():
    di_conn = None
    DI_DB = os.path.join(demoinfo_db, 'demoinfo.db')
    BL_DB = os.path.join(blob_db, 'blobs.db')
    try:
        di_conn = connect_to_db(DI_DB)
        di_cursor = di_conn.cursor()

        bl_conn = connect_to_db(BL_DB)
        bl_cursor = bl_conn.cursor()

        demoinfo_demo_list = get_workshop_demos_from_demoinfo(di_cursor)

        workshop_demo_list, old_workshop_demo_list, non_working_demos = ([] for i in range(3))
        for workshop_demos in demoinfo_demo_list:
            demo_id = workshop_demos['id']
            workshop_demo_list.append(demo_id)

            parameter = get_params(di_cursor, demo_id)

            #input blob required to run the demo
            blob = get_blob(bl_cursor, demo_id)
            if not blob:
                continue
            blob_path = os.path.join(blob_dir, blob[:1], blob[1:2], blob)
            
            #check if blob exists
            if not os.path.isfile(blob_path):
                raise FileNotFoundError(blob)

            for demo_id in workshop_demo_list:
                clientData = {"demo_id": demo_id, "params": parameter, "origin": "upload"}

                files = {'file_0': blob_path}

                params = {
                    'clientData': json.dumps(clientData),

                }

            #Execute the demos
            r = requests.post('https://ipolcore.ipol.im/api/core/run', files=files, params=params)

            response = r.json()
            if response ['status'] != 'OK':
                non_working_demos.append(demo_id)
                #print(f'Failed to run the demo: {demo_id}')
            
            '''
            #Remove workshop demos that's not working
            if args.remove:
                params={
                    'demo_id': demo_id
                }
                response = requests.post('http:/ipolcore.ipol.im/api/core/delete_demo', params=params).json()
                if response ['status'] != 'OK':
                    print("Failed to delete demo ID: {}".format(demo_id))
            '''

        print("List of All workshop Demos:", len(workshop_demo_list), "\n" ,workshop_demo_list, "\n")
        print("List of 6 months old workshop Demos:", len(old_workshop_demo_list), "\n" ,old_workshop_demo_list, "\n")
        print("List of All non working Demos:", len(non_working_demos), "\n" ,non_working_demos, "\n")


    except Exception as ex:
        print("Failure in the migration. Error: {}".format(ex))

    finally:
        if di_conn is not None:
            di_conn.close()


def get_workshop_demos_from_demoinfo(demoinfo_cursor):
    """
    Get the list of all workshop demos, their authors and editors
    """
    workshop_demos = []

    demoinfo_cursor.execute("""
        SELECT d.editor_demo_id, d.modification
        FROM demo AS d, state AS s
        WHERE s.name = "workshop" AND d.stateID = s.ID
        """)
    workshop_demos = [{'id': i[0], 'modification': i[1], 'a_name': '', 'a_mail': '', 'e_name': '', 'e_mail': ''} for i in demoinfo_cursor.fetchall()]
    for workshop_demo in workshop_demos:
        demoinfo_cursor.execute("""
            SELECT a.name, a.mail
            FROM author as a, demo_author as da
            WHERE da.demoID = ? AND a.ID = da.authorId
            """, (workshop_demo['id'],))
        author_info = demoinfo_cursor.fetchone()
        if author_info:
            workshop_demo['a_name'] = author_info[0]
            workshop_demo['a_mail'] = author_info[1]
    for workshop_demo in workshop_demos:
        demoinfo_cursor.execute("""
            SELECT e.name, e.mail
            FROM editor as e, demo_editor as de
            WHERE de.demoID = ? AND e.ID = de.editorId
            """, (workshop_demo['id'],))
        editor_info = demoinfo_cursor.fetchone()
        if editor_info:
            workshop_demo['e_name'] = editor_info[0]
            workshop_demo['e_mail'] = editor_info[1]
    return workshop_demos


def get_params(demoinfo_cursor, editor_demo_id):
    """
    Get the list of parameters for given demo ID
    """
    param_dict = {}
    
    demoinfo_cursor.execute("""
        SELECT demod.DDL
        FROM demo AS d, demo_demodescription AS dd, demodescription AS demod
        WHERE d.editor_demo_id = ? AND dd.demoID = d.ID AND dd.demodescriptionId = demod.ID
        ORDER BY demod.creation DESC LIMIT 1
        """, (editor_demo_id, ))

    param_infos = demoinfo_cursor.fetchone()
    
    if param_infos:
        param_info = json.loads(param_infos[0])
        if 'params' in param_info:
            for param in param_info['params']:
                if 'id' not in param.keys():
                    continue
                if 'default_value' in param.keys():
                    param_dict[param['id']] = param['default_value']
                elif 'values' in param.keys():
                    if 'default' in param['values'].keys():
                        param_dict[param['id']] = param['values']['default']
                    else:
                        param_dict[param['id']] = param['values'][list(param['values'].keys())[0]]
                else:
                    pass
    return param_dict


def get_blob(blobs_cursor, editor_demo_id):
    """
    Get the first blob for given demo ID
    """
    param_info = []

    blobs_cursor.execute("""
        SELECT b.hash, b.extension
        FROM demos AS d, demos_blobs AS db, blobs AS b
        WHERE d.editor_demo_id = ? AND d.id = db.demo_id AND db.blob_id = b.ID
        """, (editor_demo_id, ))
    blob_info = blobs_cursor.fetchone()

    if blob_info:
        return blob_info[0] + blob_info[1]

    return None


main()
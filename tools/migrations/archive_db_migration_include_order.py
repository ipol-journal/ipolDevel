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


from collections import OrderedDict
import os
import os.path
import shutil
import json
import socket
import sqlite3 as lite
import requests


def copy_database(original, destination):
    """
    It creates a new database with the original fields from the old archive database
    Include the new column (order) if it is not in the original database
    """
    if os.path.isfile(destination):
        os.remove(destination)
        print "Deleted {}. Creating a correct new database".format(destination)
    try:
        exec_string = 'sqlite3 {} ".dump blobs" | sqlite3 {}'.format(original, destination)
        os.system(exec_string)
        print "Copy blobs table..."
        exec_string = 'sqlite3 {} ".dump correspondence" | sqlite3 {}'.format(original, destination)
        os.system(exec_string)
        print "Copy correspondence table"
        exec_string = 'sqlite3 {} ".dump experiments" | sqlite3 {}'.format(original, destination)
        os.system(exec_string)
        print "Copy experiments table"

        conn = lite.connect(destination)
        cursor_db = conn.cursor()
        ## Check if the original database already has the order column in the correspondence table
        cursor_db.execute("""PRAGMA table_info(correspondence);""")
        number_of_columns = cursor_db.fetchall()
        if len(number_of_columns) < 5:
            cursor_db.execute("""ALTER TABLE correspondence ADD COLUMN order_exp INTEGER""")
        conn.commit()
        conn.close()
        print "Created new column in correspondece table: order_exp"

    except Exception as ex:
        message = "Error in init_database. Error = {}".format(ex)
        print message
        if os.path.isfile(destination):
            try:
                os.remove(destination)
            except Exception as ex:
                message = "Error in init_database. Error = {}".format(ex)
                return False
    return True


def post(module, service, machine, params=None, json_message=None):
    """
    Do the post to demoinfo
    """
    try:
        url = 'http://{}/api/{}/{}'.format(
            machine,
            module,
            service
        )
        return requests.post(url, params=params, data=json_message)
    except Exception as ex:
        print "ERROR: Failure in the post function - {}".format(str(ex))

def read_DDL(editors_demoid, machine):
    """
    Returs the DDL for the demo with the given editordemoid
    """
    try:
        resp = post('demoinfo', 'get_ddl', machine, params={"demo_id": editors_demoid})
        response = resp.json()
        if response['status'] != 'OK':
            print "ERROR: get_ddl returned KO for demo {}".format(editors_demoid)
            return
        if response['last_demodescription'] is None:
            return
        last_demodescription = response['last_demodescription']
        return json.loads(last_demodescription['ddl'], object_pairs_hook=OrderedDict)
    except Exception as ex:
        print "ERROR: Failed to read DDL from {} - {}".format(editors_demoid, ex)



def get_demo_list(machine):
    """
    Returns the list of demos
    """
    resp = post('demoinfo', 'demo_list', machine)
    response = resp.json()
    if response['status'] != 'OK':
        print "ERROR: demo_list returned KO"
        return
    return response['demo_list']

def get_data_experiment(cursor_db, id_exp):
    """
    Build a dictionnary containing all the datas needed on a given
    experiment for sorting them
    """
    try:
        dict_exp = {}
        cursor_db.execute("""
            SELECT name, id_blob FROM correspondence  
            WHERE id_experiment = ? """, (id_exp,))
        dict_exp["id"] = id_exp
        dict_exp["blobs"] = cursor_db.fetchall()
        return dict_exp
    except Exception as ex:
        message = "Failure in get_data_experiment. Error = {}".format(ex)
        print message
        raise

def order_blobs(blobs, ddl_files):
    """
    We sort the blobs according to the ddl (files, hidden_files and compressed_files)
    If there is not information in the DDL about a blob, we copy it at the tail.
    """
    try:
        experiment_ordered = []
        for counter_experiments, name in enumerate(ddl_files.values()):
            for counter in range(0, len(blobs)):
                element = blobs[counter]
                if element[0] == name:
                    triple = (element[0], element[1], counter_experiments)
                    experiment_ordered.append(triple)
                    blobs.pop(counter)
                    break

        if blobs:
            for counter in range(0, len(blobs)):
                index = counter + counter_experiments
                element = blobs[counter]
                experiment_ordered.append((element[0], element[1], index))

        return experiment_ordered
    except Exception as ex:
        message = "Failure in order_blobs. Error = {}".format(ex)
        print message
        raise

def order_params(params, ddl_params):
    """
    We sort the parameters according to the ddl (params and info)
    If there is not information in the DDL about a parameter, we copy it at the tail.
    """
    try:
        correct_params = OrderedDict()
        lonely_params = params.copy()
        for key, parameter in ddl_params.iteritems():
            if key == 'params':
                for value in parameter:
                    if value in params:
                        correct_params[value] = params[value]
                        if value in lonely_params:
                            del lonely_params[value]
            if key == 'info':
                for value in parameter.values():
                    if value in params:
                        correct_params[value] = params[value]
                        if value in lonely_params:
                            del lonely_params[value]
        if lonely_params:
            correct_params.update(lonely_params)
        return correct_params
    except Exception as ex:
        message = "Failure in order_params. Error = {}".format(ex)
        print message
        raise

def get_and_sort_experiments(database_file, id_demo, ddl_archive):
    """
    Get the experiments (blobs and params) from the original database and return them sorted
    """
    ddl_files = OrderedDict()
    ddl_params = OrderedDict()
    for key, value in ddl_archive.iteritems():
        if (key == 'info' or key == 'params'):
            ddl_params[key] = value
        elif (key == 'files' or key == 'hidden_files' or key == 'compressed_files'):
            ddl_files.update(value)

    conn = lite.connect(database_file)
    cursor_db = conn.cursor()

    cursor_db.execute("""
    SELECT id, params
    FROM experiments WHERE id_demo = ?""", (id_demo,))

    all_rows = cursor_db.fetchall()

    dictionary_ordered_experiments = OrderedDict()
    params_ordered_experiments = OrderedDict()
    for row in all_rows:
        id_exp = row[0]
        original_experiment = get_data_experiment(cursor_db, id_exp)
        if 'blobs' in original_experiment:
            blobs = original_experiment['blobs']
            dictionary_ordered_experiments[id_exp] = order_blobs(blobs, ddl_files)
            print "Exp '{}' sorted!".format(id_exp)

        params = json.loads(row[1], object_pairs_hook=OrderedDict)
        if params:
            params_ordered_experiments[id_exp] = order_params(params, ddl_params)

    conn.commit()
    conn.close()

    return dictionary_ordered_experiments, params_ordered_experiments

def insert_params_ordered_in_database(database_file, correct_params):
    """
    Insert the params according to the DDL in the database
    """
    try:
        conn = lite.connect(database_file)
        cursor_db = conn.cursor()
        for id_exp, parameter_dic in correct_params.items():
            cursor_db.execute("""
            UPDATE experiments
            SET params = ?
            WHERE id = ?
             """, (json.dumps(parameter_dic), id_exp))
        conn.commit()
        conn.close()
    except Exception as ex:
        message = "Failure in insert_params_ordered_in_database. Error = {}".format(ex)
        print message
        raise

def insert_experiments_ordered_in_database(database_file, exp):
    """
    Insert experiments according to the DDL in the dabase
    """
    try:
        conn = lite.connect(database_file)
        cursor_db = conn.cursor()
        for id_exp, blobs in exp.items():
            for name, id_blob, order_exp in blobs:
                cursor_db.execute("""
                UPDATE correspondence
                SET order_exp = ?
                WHERE id_blob = ? and id_experiment = ? and name = ?
                """, (order_exp, id_blob, id_exp, name))

        conn.commit()
        conn.close()
    except Exception as ex:
        message = "Failure in insert_experiments_ordered_in_database. Error = {}".format(ex)
        print message
        raise

#-----------------------------------------------------------------------
if __name__ == '__main__':

    server = socket.getfqdn()
    os.system("clear")
    try:
        archive_db_dir = '../../ipol_demo/modules/archive/db'
        archive_db_original = '{}/{}'.format(archive_db_dir, 'archive.db')
        archive_db_destiny = "archive.db"

        if os.path.isfile(archive_db_original):
            print 'Original Archive DB: {}'.format(archive_db_original)
            print 'Destiny Archive DB: {}'.format(archive_db_destiny)
            copy_database(archive_db_original, archive_db_destiny)
            demos = get_demo_list(server)
            for demo in demos:

                demo_id = demo['editorsdemoid']
                title = demo['title']
                state = demo['state']
                ddl = read_DDL(demo['editorsdemoid'], server)

                if 'archive' in ddl:
                    print "\nDemoid: {} | Title: {} | state : {} ".format(demo_id, title, state)
                    experiments_ordered, params_ordered = get_and_sort_experiments(archive_db_original, demo_id, ddl['archive'])
                    if experiments_ordered:
                        print "Experiments ordered..."
                        insert_experiments_ordered_in_database(archive_db_destiny, experiments_ordered)
                        print "Blobs included with the correct order in the database..."
                    else:
                        print "No experiments to sort..."
                    if params_ordered:
                        insert_params_ordered_in_database(archive_db_destiny, params_ordered)
                        print "Parameters included with the correct order in the database..."
                    else:
                        print "No parameters to sort..."

            final_db = os.path.join(archive_db_dir, archive_db_destiny)
            user_message = '\n\nDo you want to overwrite the original archive file {}'.format(final_db)
            print user_message
            user_message = "Write 'y' or 'yes'"
            copy_or_not = raw_input(user_message)
            if copy_or_not == 'y' or copy_or_not == 'yes':
                if os.path.isfile(final_db):
                    os.remove(final_db)
                shutil.copy(archive_db_destiny, final_db)
                print "{} copied".format(final_db)
                os.remove(archive_db_destiny)
        else:
            print '>> Error: Database file not found'
        print 'Finished!!'

    except Exception as ex:
        print '>> EXCEPTION: ' + str(ex)

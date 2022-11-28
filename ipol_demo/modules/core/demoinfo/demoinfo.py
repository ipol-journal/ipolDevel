"""
DemoInfo: an information container module
"""

import glob
import json
import logging
import os
import shutil
import socket
import sqlite3 as lite
import sys
from collections import OrderedDict
from math import ceil
from urllib.request import pathname2url

import magic
from .model import (Demo, DemoDAO,
                   DemoDemoDescriptionDAO, DemoDescriptionDAO, DemoEditorDAO,
                   Editor, EditorDAO, initDb)
from .tools import is_json, generate_ssh_keys


class DemoInfo:

    def __init__(self,
                 dl_extras_dir: str,
                 database_path: str,
                 ):
        self.logger = init_logging()

        if not dl_extras_dir.endswith('/'):
            dl_extras_dir += '/'
        self.dl_extras_dir = dl_extras_dir
        os.makedirs(self.dl_extras_dir, exist_ok=True)

        self.database_file = database_path
        if not self.create_database():
            sys.exit("Initialization of database failed. Check the logs.")

    def create_database(self):
        """
        Creates the database used by the module if it doesn't exist.
        If the file is empty, the system delete it and create a new one.
        """
        if os.path.isfile(self.database_file):

            file_info = os.stat(self.database_file)

            if file_info.st_size == 0:
                try:
                    os.remove(self.database_file)
                except Exception as ex:
                    self.logger.exception("init_database: {}".format(str(ex)))
                    return False

        if not os.path.isfile(self.database_file):
            try:
                conn = lite.connect(self.database_file)
                cursor_db = conn.cursor()

                sql_buffer = ""

                curdir = os.path.dirname(__file__)
                with open(os.path.join(curdir, 'db/drop_create_db_schema.sql'), 'r') as sql_file:
                    for line in sql_file:

                        sql_buffer += line
                        if lite.complete_statement(sql_buffer):
                            sql_buffer = sql_buffer.strip()
                            cursor_db.execute(sql_buffer)
                            sql_buffer = ""

                conn.commit()
                conn.close()
                # Initializes the DB
                initDb(self.database_file)
            except Exception as ex:
                self.logger.exception("init_database - {}".format(str(ex)))

                if os.path.isfile(self.database_file):
                    try:
                        os.remove(self.database_file)
                    except Exception as ex:
                        self.logger.exception("init_database - {}".format(str(ex)))
                        return False

        return True

    def get_compressed_file_url(self, demo_id):
        """
        Get the URL of the demo's demoExtras
        """
        demoextras_folder = os.path.join(self.dl_extras_dir, demo_id)
        demoextras_file = glob.glob(demoextras_folder+"/*")

        if not demoextras_file:
            return None
        demoextras_name = pathname2url(os.path.basename(demoextras_file[0]))
        protocol = 'https'  # TODO
        return "{}://{}/api/demoinfo/{}{}/{}".format(
            protocol,
            socket.getfqdn(),
            self.dl_extras_dir,
            demo_id,
            demoextras_name)

    def delete_demoextras(self, demo_id):
        """
        Delete the demoExtras from a demo
        """
        data = {}
        data['status'] = "OK"

        try:
            demoextras_folder = os.path.join(self.dl_extras_dir, demo_id)
            if os.path.exists(demoextras_folder):
                shutil.rmtree(demoextras_folder)
        except Exception as ex:
            data['status'] = "KO"
            self.logger.exception(str(ex))
        return json.dumps(data).encode()

    def add_demoextras(self, demo_id, demoextras, demoextras_name):
        """
        Add a new demoExtras file to a demo
        """
        data = {'status': 'KO'}
        try:
            conn = lite.connect(self.database_file)
            demo_dao = DemoDAO(conn)

            if not demo_dao.exist(demo_id):
                return json.dumps(data).encode()

            if demoextras is None:
                data['error_message'] = "File not found"
                return json.dumps(data).encode()

            mime_type = magic.from_buffer(demoextras.file.read(1024), mime=True)
            _, type_of_file = mime_type.split("/")
            type_of_file = type_of_file.lower()

            accepted_types = (
                "zip",
                "tar",
                "gzip",
                "x-tar",
                "x-bzip2"
            )

            if type_of_file not in accepted_types:
                data['error_message'] = "Unexpected type: {}.".format(mime_type)
                return json.dumps(data).encode()

            demoextras_folder = os.path.join(self.dl_extras_dir, demo_id)
            if os.path.exists(demoextras_folder):
                shutil.rmtree(demoextras_folder)

            os.makedirs(demoextras_folder)
            destination = os.path.join(demoextras_folder, demoextras_name)

            demoextras.file.seek(0)
            with open(destination, 'wb') as f:
                shutil.copyfileobj(demoextras.file, f)

            data['status'] = "OK"
            return json.dumps(data).encode()

        except Exception as ex:
            error_message = "Failure in 'add_demoextras' for demo '{}'. Error {}".format(demo_id, ex)
            self.logger.exception(error_message)
            data['error_message'] = error_message
            return json.dumps(data).encode()

    def get_demo_extras_info(self, demo_id):
        """
        Return the date of creation, the size of the file, and eventually the demoExtras file name
        """
        data = {'status': 'KO'}
        try:
            demoExtras_url = self.get_compressed_file_url(demo_id)

            if demoExtras_url is None:
                # DemoInfo does not have any demoExtras
                return json.dumps({'status': 'OK'}).encode()

            demoextras_folder = os.path.join(self.dl_extras_dir, demo_id)
            demoExtras_path = glob.glob(demoextras_folder+"/*")[0]

            file_stats = os.stat(demoExtras_path)
            data['date'] = file_stats.st_mtime
            data['size'] = file_stats.st_size
            data['url'] = demoExtras_url
            data['status'] = 'OK'
            return json.dumps(data).encode()

        except Exception as ex:
            self.logger.exception("Failure in get_demo_extras_info")
            print("get_demo_extras_info. Error: {}".format(ex))
            return json.dumps(data).encode()

    def demo_list(self):
        """
        Return the list of the demos
        """
        data = {}
        data["status"] = "KO"
        demo_list = list()
        try:
            conn = lite.connect(self.database_file)
            demo_dao = DemoDAO(conn)
            for d in demo_dao.list():
                # convert to Demo class to json
                demo_list.append(d.__dict__)
            data["demo_list"] = demo_list
            data["status"] = "OK"
            conn.close()
        except Exception as ex:
            error_string = "demoinfo demo_list error %s" % str(ex)
            print(error_string)
            self.logger.exception(error_string)
            try:
                conn.close()
            except Exception as ex:
                pass
            # raise Exception
            data["error"] = error_string

        return json.dumps(data).encode()

    def demo_list_by_editorid(self, editorid):
        """
        return the list of demos matching the editor `editorid`
        """
        data = {}
        data["status"] = "KO"
        demo_list = list()

        try:
            conn = lite.connect(self.database_file)
            demo_dao = DemoDAO(conn)
            for d in demo_dao.list_by_editorid(editorid):
                demo_list.append(d.__dict__)

            data["demo_list"] = demo_list
            data["status"] = "OK"
            conn.close()
        except Exception as ex:
            error_string = "demoinfo demo_list_by_editorid error %s" % str(ex)
            print(error_string)
            self.logger.exception(error_string)
            try:
                conn.close()
            except Exception as ex:
                pass
            # raise Exception
            data["error"] = error_string

        return json.dumps(data).encode()

    def demo_list_pagination_and_filter(self, num_elements_page, page, qfilter=None):
        """
        return a paginated and filtered list of demos
        """
        data = {}
        data["status"] = "KO"
        demo_list = list()
        next_page_number = None
        previous_page_number = None

        try:
            # validate params
            num_elements_page = int(num_elements_page)
            page = int(page)

            conn = lite.connect(self.database_file)
            demo_dao = DemoDAO(conn)

            complete_demo_list = demo_dao.list()

            # filter or return all
            if qfilter:
                for demo in complete_demo_list:
                    if qfilter.lower() in demo.title.lower() or qfilter == str(demo.editorsdemoid):
                        demo_list.append(demo.__dict__)
            else:
                # convert to Demo class to json
                for demo in complete_demo_list:
                    demo_list.append(demo.__dict__)

            # if demos found, return pagination
            if demo_list:
                # [ToDo] Check if the first float cast r=float(.) is
                # really needed. It seems not, because the divisor is
                # already a float and thus the result must be a float.
                r = float(len(demo_list)) / float(num_elements_page)

                totalpages = int(ceil(r))

                if page is None:
                    page = 1
                else:
                    if page < 1:
                        page = 1
                    elif page > totalpages:
                        page = totalpages

                next_page_number = page + 1
                if next_page_number > totalpages:
                    next_page_number = None

                previous_page_number = page - 1
                if previous_page_number <= 0:
                    previous_page_number = None

                start_element = (page - 1) * num_elements_page

                demo_list = demo_list[start_element: start_element + num_elements_page]

            else:
                totalpages = None

            data["demo_list"] = demo_list
            data["next_page_number"] = next_page_number
            data["number"] = totalpages
            data["previous_page_number"] = previous_page_number
            data["status"] = "OK"
            conn.close()
        except Exception as ex:
            error_string = "demoinfo demo_list_pagination_and_filter error %s" % str(ex)
            print(error_string)
            self.logger.exception(error_string)
            try:
                conn.close()  # [ToDo] It seems that this should do in a
                # finally clause, not in a nested try. Check all similar
                # cases in this file.
            except Exception as ex:
                pass
            # raise Exception
            data["error"] = error_string
        return json.dumps(data).encode()

    def demo_get_editors_list(self, demo_id):
        """
        return the editors of a given demo.
        """
        data = {}
        data["status"] = "KO"
        editor_list = list()
        try:
            conn = lite.connect(self.database_file)
            demo_dao = DemoDAO(conn)

            if not demo_dao.exist(demo_id):
                return json.dumps(data).encode()

            de_dao = DemoEditorDAO(conn)

            for e in de_dao.read_demo_editors(int(demo_id)):
                # convert to Demo class to json
                editor_list.append(e.__dict__)

            data["editor_list"] = editor_list
            conn.close()
            data["status"] = "OK"
        except Exception as ex:
            error_string = "demoinfo demo_get_editors_list error %s" % str(ex)
            print(error_string)
            self.logger.exception(error_string)
            try:
                conn.close()
            except Exception as ex:
                pass
            # raise Exception
            data["error"] = error_string
        return json.dumps(data).encode()

    def demo_get_available_editors_list(self, demo_id):
        """
        return all editors that are not currently assigned to a given demo
        """
        data = {}
        data["status"] = "KO"
        available_editor_list = list()

        try:
            conn = lite.connect(self.database_file)

            # get all available editors
            a_dao = EditorDAO(conn)
            list_of_all_editors = a_dao.list()

            # get the editors of this demo
            da_dao = DemoEditorDAO(conn)
            list_of_editors_assigned_to_this_demo = da_dao.read_demo_editors(int(demo_id))

            for a in list_of_all_editors:
                if a not in list_of_editors_assigned_to_this_demo:
                    # convert to Demo class to json
                    available_editor_list.append(a.__dict__)

            data["editor_list"] = available_editor_list
            data["status"] = "OK"
            conn.close()
        except Exception as ex:
            error_string = "demoinfo demo_get_available_editors_list error %s" % str(ex)
            print(error_string)
            self.logger.exception(error_string)
            try:
                conn.close()
            except Exception as ex:
                pass
            # raise Exception
            data["error"] = error_string
        return json.dumps(data).encode()

    def read_demo(self, demoid):
        """
        Return DAO for given demo.
        """
        demo = None
        try:
            the_id = int(demoid)
            conn = lite.connect(self.database_file)
            dao = DemoDAO(conn)
            demo = dao.read(the_id)
            conn.close()

        except Exception as ex:
            error_string = ("read_demo  e:%s" % (str(ex)))
            print(error_string)
            conn.close()

        return demo

    def read_demo_metainfo(self, demoid):
        """
        Return metadata of a demo.
        """
        data = dict()
        data["status"] = "KO"
        try:

            demo = self.read_demo(demoid)
            if demo is None:
                data['error'] = "No demo retrieved for this id"
                print("No demo retrieved for this id")
                return json.dumps(data).encode()
            data["editorsdemoid"] = demo.editorsdemoid
            data["title"] = demo.title
            data["state"] = demo.state
            data["creation"] = demo.creation
            data["modification"] = demo.modification
            data["status"] = "OK"

        except Exception as ex:
            error_string = "demoinfo read_demo_metainfo error %s" % str(ex)
            print(error_string)
            self.logger.exception(error_string)
            # raise Exception
            data["error"] = error_string

        return json.dumps(data).encode()

    def add_demo(self, demo_id, title, state, ddl_id=None, ddl=None):
        """
        Create a demo
        """
        data = {"status": "KO"}
        conn = None
        try:
            conn = lite.connect(self.database_file)
            demo_db = DemoDAO(conn)

            demo_id = int(demo_id)

            # Check if the demo already exists
            # In that case, get out with an error
            if demo_db.exist(demo_id):
                return json.dumps({"status": "KO", "error": "Demo ID={} already exists".format(demo_id)}).encode()

            demo = Demo(int(demo_id), title, state)
            if ddl_id: # old CP dependency [TODO] remove when CP1 is not used anymore
                # asigns to demo an existing demodescription
                demo_id = demo_db.add(demo)
                ddl_db = DemoDemoDescriptionDAO(conn)
                ddl_db.add(int(demo_id), int(ddl_id))
            else:
                # if ddl is none add empty json string
                if ddl is None:
                    ddl = '{}'
                ddl_id = DemoDescriptionDAO(conn).add(ddl)
                demo_id = demo_db.add(demo)
                ddl_db = DemoDemoDescriptionDAO(conn)
                ddl_db.add(int(demo_id), int(ddl_id))
                data["demo_id"] = demo_id

            conn.close()

            data["status"] = "OK"

        except lite.IntegrityError as ex:
            if conn is not None:
                conn.close()
            data['error'] = str(ex)

        except Exception as ex:
            error_string = " demoinfo add_demo error %s" % str(ex)
            print(error_string)
            self.logger.exception(error_string)
            try:
                conn.close()
            except Exception as ex:
                pass
            data["error"] = error_string

        return json.dumps(data).encode()

    def delete_demo(self, demo_id):
        """
        Delete the specified demo
        """
        data = {}
        data["status"] = "KO"

        try:

            conn = lite.connect(self.database_file)

            demo_dao = DemoDAO(conn)
            # read demo
            dd_dao = DemoDemoDescriptionDAO(conn)

            # delete demo decription history borra ddl id 3
            # d_dd con id 2 , y demoid=2, demodescpid 3 deberia no estar
            dd_dao.delete_all_demodescriptions_for_demo(int(demo_id))
            # delete demo, and delete on cascade demodemodescription
            demo_dao.delete(int(demo_id))
            data["status"] = "OK"
            conn.close()

        except Exception as ex:
            error_string = "demoinfo delete_demo error %s" % str(ex)
            print(error_string)
            self.logger.exception(error_string)
            try:
                conn.close()
            except Exception as ex:
                pass
            # raise Exception
            data["error"] = error_string

        return json.dumps(data).encode()

    def update_demo(self, demo, old_editor_demoid):
        """
        Update the demo.
        """
        data = {"status": "KO"}

        demo_json = json.loads(demo)

        if 'creation' in demo_json:
            # Change creation date
            d = Demo(demo_json.get('demo_id'), demo_json.get('title'), demo_json.get('state'),
                     demo_json.get('creation'))
        else:
            # update Demo
            d = Demo(demo_json.get('demo_id'), demo_json.get('title'), demo_json.get('state'))

        try:
            old_editor_demoid = int(old_editor_demoid)
            d_editorsdemoid = int(d.editorsdemoid)

            conn = lite.connect(self.database_file)
            dao = DemoDAO(conn)
            dao.update(d, old_editor_demoid)
            conn.close()

            if old_editor_demoid != d_editorsdemoid \
                    and os.path.isdir(os.path.join(self.dl_extras_dir, str(old_editor_demoid))):
                if os.path.isdir(os.path.join(self.dl_extras_dir, str(d_editorsdemoid))):
                    # If the destination path exists, it should be removed
                    shutil.rmtree(os.path.join(self.dl_extras_dir, str(d_editorsdemoid)))

                if os.path.isdir(os.path.join(self.dl_extras_dir, str(old_editor_demoid))):
                    os.rename(os.path.join(self.dl_extras_dir, str(old_editor_demoid)),
                              os.path.join(self.dl_extras_dir, str(d_editorsdemoid)))

            data["status"] = "OK"
        except OSError as ex:
            data["error"] = "demoinfo update_demo error {}".format(ex)
        except Exception as ex:
            error_string = (" demoinfo update_demo error %s" % (str(ex)))
            print(error_string)
            try:
                conn.close()
            except Exception as ex:
                pass
            data["error"] = error_string

        return json.dumps(data).encode()

    def editor_list(self):
        """
        Returns the editor list
        """
        data = {}
        data["status"] = "KO"
        editor_list = list()
        try:
            conn = lite.connect(self.database_file)
            editor_dao = EditorDAO(conn)
            for e in editor_dao.list():
                # convert to Demo class to json
                editor_list.append(e.__dict__)

            data["editor_list"] = editor_list
            data["status"] = "OK"
            conn.close()
        except Exception as ex:
            error_string = "demoinfo editor_list error %s" % str(ex)
            print(error_string)
            self.logger.exception(error_string)
            try:
                conn.close()
            except Exception as ex:
                pass
            # raise Exception
            data["error"] = error_string
        return json.dumps(data).encode()

    def get_editor(self, email):
        """
        Returns an editor information
        """
        data = {}
        data["status"] = "KO"
        try:
            conn = lite.connect(self.database_file)
            editor_dao = EditorDAO(conn)
            editor = editor_dao.read_from_email(email)
            if editor:
                data["editor"] = editor.__dict__
                data["status"] = "OK"
            else:
                data["editor"] = {}
                data["status"] = "OK"
            conn.close()

        except Exception as ex:
            error_string = "demoinfo editor_list error %s" % str(ex)
            print(error_string)
            self.logger.exception(error_string)
            try:
                conn.close()
            except Exception as ex:
                pass
            # raise Exception
            data["error"] = error_string
        return json.dumps(data).encode()

    def update_editor_email(self, new_email, old_email, name):
        """
        Update editor if old email exists and new one doesn't
        """

        data = {}
        conn = lite.connect(self.database_file)
        old_editor = EditorDAO(conn).read_from_email(old_email)
        new_email_exists = EditorDAO(conn).read_from_email(new_email)

        if new_email_exists:
            data["error"] = 'New email already exists in demoinfo'
            data["status"] = 'KO'
            return json.dumps(data).encode()
        if not old_editor:
            resp = self.add_editor(name, new_email)
            resp_json = json.loads(resp)
            if resp_json['status'] != 'OK':
                data["message"] = f'Editor could not be added with email {new_email}'
                data["status"] = "KO"
            else:
                data["message"] = f'New editor added {new_email}'
                data["status"] = "OK"
            return json.dumps(data).encode()

        e = Editor(name, new_email, old_editor.id, old_editor.creation)

        # update editor
        try:
            conn = lite.connect(self.database_file)
            editor_object = EditorDAO(conn)

            if not editor_object.exist(e.id):
                return json.dumps(data).encode()

            editor_object.update(e)
            conn.close()
            data["status"] = "OK"
        except Exception as ex:
            error_string = "demoinfo update_editor error %s" % str(ex)
            print(error_string)
            self.logger.exception(error_string)
            try:
                conn.close()
            except Exception as ex:
                pass
            # raise Exception
            data["error"] = error_string
        return json.dumps(data).encode()

    def read_editor(self, editorid):
        """
        Returns editor info.
        """
        data = dict()
        data["status"] = "KO"

        try:
            editor = None
            try:
                editorid = int(editorid)
                conn = lite.connect(self.database_file)
                dao = EditorDAO(conn)
                editor = dao.read(editorid)
                conn.close()
            except Exception as ex:
                error_string = ("read_editor  e:%s" % (str(ex)))
                print(error_string)

            if editor is None:
                print("No editor retrieved for this id")
                data['error'] = "No editor retrieved for this id"
                return json.dumps(data).encode()

            data["id"] = editor.id
            data["name"] = editor.name
            data["mail"] = editor.mail
            data["creation"] = editor.creation
            data["status"] = "OK"

        except Exception as ex:
            error_string = "demoinfo read_editor error %s" % str(ex)
            print(error_string)
            self.logger.exception(error_string)
            try:
                conn.close()
            except Exception as ex:
                pass
            # raise Exception
            data["error"] = error_string

        return json.dumps(data).encode()

    def add_editor(self, name, mail):
        """
        Add editor.
        """
        data = {"status": "KO"}
        conn = None
        try:
            e = Editor(name, mail)
            conn = lite.connect(self.database_file)
            dao = EditorDAO(conn)
            the_id = dao.add(e)
            conn.close()
            data["status"] = "OK"
            data["editorid"] = the_id

        except lite.IntegrityError as ex:
            print(ex)
            data['error'] = str(ex)
            if conn is not None:
                conn.close()
        except Exception as ex:
            error_string = "demoinfo add_editor error %s" % str(ex)
            print(error_string)
            self.logger.exception(error_string)
            if conn is not None:
                conn.close()

            data["error"] = error_string
        return json.dumps(data).encode()

    def add_editor_to_demo(self, demo_id, editor_id):
        """
        Add the given editor to the given demo.
        """
        data = {}
        data["status"] = "KO"
        try:
            conn = lite.connect(self.database_file)
            demo_dao = DemoDAO(conn)
            editor_dao = EditorDAO(conn)

            if not demo_dao.exist(demo_id) or not editor_dao.exist(editor_id):
                return json.dumps(data).encode()

            dao = DemoEditorDAO(conn)
            dao.add(int(demo_id), int(editor_id))
            conn.close()
            data["status"] = "OK"
        except Exception as ex:
            error_string = "demoinfo add_editor_to_demo error %s" % str(ex)
            print(error_string)
            self.logger.exception(error_string)
            try:
                conn.close()
            except Exception as ex:
                pass
            # raise Exception
            data["error"] = error_string
        return json.dumps(data).encode()

    def remove_editor_from_demo(self, demo_id, editor_id):
        """
        Remove the given editor from the given demo.
        """
        data = {}
        data["status"] = "KO"
        try:
            conn = lite.connect(self.database_file)
            demo_dao = DemoDAO(conn)
            editor_dao = EditorDAO(conn)

            if not demo_dao.exist(demo_id) or not editor_dao.exist(editor_id):
                return json.dumps(data).encode()

            dao = DemoEditorDAO(conn)
            dao.remove_editor_from_demo(int(demo_id), int(editor_id))
            conn.close()
            data["status"] = "OK"
        except Exception as ex:
            error_string = "demoinfo remove_editor_from_demo error %s" % str(ex)
            print(error_string)
            self.logger.exception(error_string)
            try:
                conn.close()
            except Exception as ex:
                pass
            # raise Exception
            data["error"] = error_string
        return json.dumps(data).encode()

    def remove_editor(self, editor_id):
        """
        Delete editor
        """
        data = {}
        data["status"] = "KO"
        try:

            editorid = int(editor_id)
            conn = lite.connect(self.database_file)
            dedao = DemoEditorDAO(conn)
            # deletes the editor relation with its demos
            demolist = dedao.read_editor_demos(editorid)
            if demolist:
                # remove editor from demos
                for demo in demolist:
                    dedao.remove_editor_from_demo(demo.editorsdemoid, editorid)
            # deletes the editor
            edao = EditorDAO(conn)
            edao.delete(editorid)
            conn.close()
            data["status"] = "OK"
        except Exception as ex:
            error_string = "demoinfo remove_editor error %s" % str(ex)
            print(error_string)
            self.logger.exception(error_string)
            try:
                conn.close()
            except Exception as ex:
                pass
            # raise Exception
            data["error"] = error_string
        return json.dumps(data).encode()

    def read_ddl(self, ddl_id):
        """
        Return the DDL.
        """
        data = {}
        data["status"] = "KO"
        data["demo_description"] = None
        try:
            ddl_id = int(ddl_id)
            conn = lite.connect(self.database_file)
            dao = DemoDescriptionDAO(conn)

            ddl = dao.read(ddl_id)
            ddl_str = str(ddl)

            data["demo_description"] = ddl_str
            conn.close()
            data["status"] = "OK"
        except Exception as ex:
            error_string = "demoinfo read_ddl error %s" % str(ex)
            print(error_string)
            self.logger.exception(error_string)
            try:
                conn.close()
            except Exception as ex:
                pass
            # raise Exception
            data["error"] = error_string

        return json.dumps(data).encode()

    def get_interface_ddl(self, demo_id, sections=None):
        """
        Read the DDL of the specified demo without unneeded or private fields. Used by the website interface.
        """
        try:
            # Validate demo_id
            try:
                demo_id = int(demo_id)
            except(TypeError, ValueError) as ex:
                return json.dumps({'status': 'KO', 'error': "Invalid demo_id: {}".format(demo_id)}).encode()

            ddl = self.get_stored_ddl(demo_id)
            if not ddl:
                return json.dumps({'status': 'KO', 'error': "There isn't any DDL for the demo {}".format(demo_id)}).encode()

            ddl = json.loads(ddl.get("ddl"), object_pairs_hook=OrderedDict)
            # removing sections that shouldn't be obtained by the web interface
            if 'build' in ddl:
                del ddl['build']
            if 'run' in ddl:
                del ddl['run']
            # obtaining the sections given as a parameter
            if sections:
                ddl_sections = self.get_ddl_sections(ddl, sections)
                return json.dumps({'status': 'OK', 'last_demodescription': {"ddl": ddl_sections}}).encode()
            return json.dumps({'status': 'OK', 'last_demodescription': {"ddl": ddl}}).encode()
        except Exception as ex:
            error_string = "Failure in function get_interface_ddl with demo {}, Error = {}".format(demo_id, ex)
            print(error_string)
            self.logger.exception(error_string)
            return json.dumps({'status': 'KO', 'error': error_string}).encode()


    @staticmethod
    def get_ddl_sections(ddl, ddl_sections):
        """
        Returns DDL sections
        """
        sections = OrderedDict()
        for section in ddl_sections.split(','):
            if ddl.get(section):
                sections[str(section)] = ddl.get(section)
        return sections

    def get_ddl_history(self, demo_id):
        """
        Return a list with all the DDLs
        """
        ddl_history = []
        data = {'status':'KO'}
        try:
            conn = lite.connect(self.database_file)
            dd_dao = DemoDemoDescriptionDAO(conn)
            ddl_history = dd_dao.read_history(demo_id)
            if not ddl_history:
                data['error'] = "There isn't any DDL for demo {}".format(demo_id)
                return json.dumps(data).encode()
            data['ddl_history'] = ddl_history
            data['status'] = 'OK'
            return json.dumps(data).encode()
        except Exception as ex:
            error_msg = "Failure in function get_ddl_history. Error: {}".format(ex)
            self.logger.exception(error_msg)
            print(error_msg)
            data['error'] = error_msg
            return json.dumps(data).encode()

    def get_ddl(self, demo_id, sections=None):
        """
        Reads the current DDL of the demo
        """
        # Error code description:
        # code -1: the DDL of the requested ID doesn't exist
        # code -2: Invalid demo_id
        try:
            # Validate demo_id
            try:
                demo_id = int(demo_id)
            except(TypeError, ValueError) as ex:
                return json.dumps({'status': 'KO', 'error': "Invalid demo_id: {}".format(demo_id), 'error_code': -2}).encode()

            ddl = self.get_stored_ddl(demo_id)
            if not ddl:
                error = "There isn't any DDL for demo {}".format(demo_id)
                return json.dumps({'status': 'KO', 'error': error, 'error_code': -1}).encode()
            if sections:
                ddl = json.loads(ddl.get("ddl"), object_pairs_hook=OrderedDict)
                ddl_sections = self.get_ddl_sections(ddl, sections)
                return json.dumps({'status': 'OK', 'last_demodescription': ddl_sections}).encode()
            return json.dumps({'status': 'OK', 'last_demodescription': ddl}).encode()
        except Exception as ex:
            error_string = "Failure in function get_ddl, Error = {}".format(ex)
            print(error_string)
            self.logger.exception(error_string)
            return json.dumps({'status': 'KO'}).encode()

    def get_stored_ddl(self, demo_id):
        """
        Method that gives the stored DDL given a demo_id
        """
        conn = lite.connect(self.database_file)
        dd_dao = DemoDemoDescriptionDAO(conn)
        last_demodescription = dd_dao.get_ddl(int(demo_id))
        conn.close()
        return last_demodescription

    def save_ddl(self, demoid, ddl):
        """
        Save the DDL.
        """
        data = {}
        data["status"] = "KO"
        if not is_json(ddl):
            print("\n save_ddl ddl is not a valid json ")
            print("ddl: ", ddl)
            print("ddl type: ", type(ddl))
            data['error'] = "save_ddl ddl is not a valid json"
            return json.dumps(data).encode()
        try:
            conn = lite.connect(self.database_file)
            demo_dao = DemoDAO(conn)
            demo = demo_dao.read(int(demoid))
            if demo is None:
                data['error'] = 'There is no demo with that demoid'
                return json.dumps(data).encode()
            state = demo_dao.read(int(demoid)).state
            if state != "published":  # If the demo is not published the DDL is overwritten
                ddddao = DemoDemoDescriptionDAO(conn)
                demodescription = ddddao.get_ddl(int(demoid))
                dao = DemoDescriptionDAO(conn)

                if demodescription is None:  # Check if is a new demo
                    demodescription_id = dao.add(ddl)

                    dao = DemoDemoDescriptionDAO(conn)
                    dao.add(int(demoid), int(demodescription_id))
                else:
                    dao.update(ddl, demoid)

            else:  # Otherwise it's create a new one
                dao = DemoDescriptionDAO(conn)
                demodescription_id = dao.add(ddl)
                dao = DemoDemoDescriptionDAO(conn)
                dao.add(int(demoid), int(demodescription_id))

            data["added_to_demo_id"] = demoid

            conn.close()
            # return id
            data["status"] = "OK"

        except Exception as ex:
            error_string = "demoinfo save_ddl error %s" % str(ex)
            print(error_string)
            self.logger.exception(error_string)
            try:
                conn.close()
            except Exception as ex:
                pass
            # raise Exception
            data["error"] = error_string

        return json.dumps(data).encode()

    def get_ssh_keys(self, demo_id):
        """
        Returns the ssh keys for a given demo_id.
        """
        try:
            demo_id = int(demo_id)
        except(TypeError, ValueError) as ex:
            return json.dumps({'status': 'KO', 'error': "Invalid demo_id: {}".format(demo_id), 'error_code': -2}).encode()

        data = {'status': 'KO'}
        try:
            conn = lite.connect(self.database_file)
            demo_dao = DemoDAO(conn)

            if not demo_dao.exist(demo_id):
                return json.dumps(data).encode()

            if not demo_dao.has_ssh_key(demo_id):
                pubkey, privkey = generate_ssh_keys()
                demo_dao.set_ssh_key(demo_id, pubkey, privkey)

            pubkey, privkey = demo_dao.get_ssh_key(demo_id)
            data = {
                'status': 'OK',
                'pubkey': pubkey.decode('utf-8'),
                'privkey': privkey.decode('utf-8'),
            }
            return json.dumps(data).encode()

        except Exception as ex:
            error_message = "Failure in 'get_ssh_keys' for demo '{}'. Error {}".format(demo_id, ex)
            self.logger.exception(error_message)
            data['error_message'] = error_message
            return json.dumps(data).encode()

    def reset_ssh_keys(self, demo_id):
        """
        Renews ssh keys for a given demo.
        """
        try:
            demo_id = int(demo_id)
        except(TypeError, ValueError) as ex:
            return json.dumps({'status': 'KO', 'error': "Invalid demo_id: {}".format(demo_id), 'error_code': -2}).encode()

        data = {'status': 'KO'}
        try:
            conn = lite.connect(self.database_file)
            demo_dao = DemoDAO(conn)

            if not demo_dao.exist(demo_id):
                return json.dumps(data).encode()

            demo_dao.reset_ssh_key(demo_id)

            data = {
                'status': 'OK',
            }
            return json.dumps(data).encode()

        except Exception as ex:
            error_message = "Failure in 'get_ssh_keys' for demo '{}'. Error {}".format(demo_id, ex)
            self.logger.exception(error_message)
            data['error_message'] = error_message
            return json.dumps(data).encode()


def init_logging():
    """
    Initialize the error logs of the module.
    """
    logger = logging.getLogger("demoinfo")

    logger.setLevel(logging.DEBUG)
    handler = logging.StreamHandler()
    formatter = logging.Formatter(
        '%(asctime)s; [%(filename)s:%(lineno)s - %(funcName)20s() ] %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S')
    handler.setFormatter(formatter)

    logger.addHandler(handler)
    return logger

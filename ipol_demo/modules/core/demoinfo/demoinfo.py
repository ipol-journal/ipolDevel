import glob
import json
import logging
import os
import shutil
import sqlite3
from collections import OrderedDict
from math import ceil
from typing import Optional
from urllib.request import pathname2url
from result import Ok, Err, Result

import magic
from .model import (Demo, DemoDAO,
                   DemoDemoDescriptionDAO, DemoDescriptionDAO, DemoEditorDAO,
                   Editor, EditorDAO, initDb)
from .tools import is_json, generate_ssh_keys


class DemoInfo:

    def __init__(self,
                 dl_extras_dir: str,
                 database_path: str,
                 base_url: str
                 ):
        self.logger = init_logging()

        if not dl_extras_dir.endswith('/'):
            dl_extras_dir += '/'
        self.dl_extras_dir = dl_extras_dir
        os.makedirs(self.dl_extras_dir, exist_ok=True)
        self.base_url = base_url

        self.database_file = database_path
        self.create_database()

    def create_database(self):
        """
        Creates the database used by the module if it doesn't exist.
        If the file is empty, the system delete it and create a new one.
        """
        if os.path.isfile(self.database_file):
            file_info = os.stat(self.database_file)
            if file_info.st_size == 0:
                os.remove(self.database_file)

        if not os.path.isfile(self.database_file):
            db = sqlite3.connect(self.database_file)

            curdir = os.path.dirname(__file__)
            with open(os.path.join(curdir, 'db/drop_create_db_schema.sql'), 'r') as sql_file:
                sql_script = sql_file.read()

            cursor = db.cursor()
            cursor.executescript(sql_script)
            db.commit()
            db.close()
            initDb(self.database_file)

    def get_compressed_file_url(self, demo_id):
        """
        Get the URL of the demo's demoExtras
        """
        demoextras_folder = os.path.join(self.dl_extras_dir, str(demo_id))
        demoextras_file = glob.glob(demoextras_folder+"/*")

        if not demoextras_file:
            return None
        demoextras_name = pathname2url(os.path.basename(demoextras_file[0]))
        return "{}/api/demoinfo/{}{}/{}".format(
            self.base_url,
            self.dl_extras_dir,
            demo_id,
            demoextras_name)

    def delete_demoextras(self, demo_id: int) -> Result[None, str]:
        """
        Delete the demoExtras from a demo
        """
        demoextras_folder = os.path.join(self.dl_extras_dir, str(demo_id))
        try:
            if os.path.exists(demoextras_folder):
                shutil.rmtree(demoextras_folder)
        except OSError as ex:
            self.logger.exception(str(ex))
            return Err(str(ex))
        return Ok()

    def add_demoextras(self, demo_id, demoextras: bytes, demoextras_name) -> Result[None, str]:
        """
        Add a new demoExtras file to a demo
        """
        try:
            conn = sqlite3.connect(self.database_file)
            demo_dao = DemoDAO(conn)

            if not demo_dao.exist(demo_id):
                return Err(f"demo {demo_id} does not exist")

            conn.close()
        except sqlite3.Error as ex:
            self.logger.exception(ex)
            return Err(str(ex))

        try:
            mime_type = magic.from_buffer(demoextras, mime=True)
        except magic.MagicException as ex:
            self.logger.exception(ex)
            return Err(str(ex))

        accepted_types = (
            "zip",
            "tar",
            "gzip",
            "x-tar",
            "x-bzip2"
        )
        _, type_of_file = mime_type.split("/")
        if type_of_file.lower() not in accepted_types:
            return Err(f"Unexpected type: {mime_type}")

        demoextras_folder = os.path.join(self.dl_extras_dir, str(demo_id))
        destination = os.path.join(demoextras_folder, demoextras_name)
        try:
            if os.path.exists(demoextras_folder):
                shutil.rmtree(demoextras_folder)

            os.makedirs(demoextras_folder)
            with open(destination, 'wb') as f:
                f.write(demoextras)
        except OSError as ex:
            self.logger.exception(ex)
            return Err(str(ex))

        return Ok()

    def get_demo_extras_info(self, demo_id: int) -> Result[Optional[dict], str]:
        """
        Return the date of creation, the size of the file, and eventually the demoExtras url.
        If the demo does not have a demoextras file, Ok(None) is returned.
        """
        demoExtras_url = self.get_compressed_file_url(demo_id)

        if demoExtras_url is None:
            # DemoInfo does not have any demoExtras
            return Ok(None)

        demoextras_folder = os.path.join(self.dl_extras_dir, str(demo_id))
        demoExtras_path = glob.glob(demoextras_folder+"/*")[0]

        try:
            file_stats = os.stat(demoExtras_path)
        except OSError as ex:
            self.logger.exception(ex)
            return Err(str(ex))

        info = {
            'date': file_stats.st_mtime,
            'size': file_stats.st_size,
            'url': demoExtras_url,
        }
        return Ok(info)

    def demo_list(self) -> Result[list[dict], str]:
        """
        Return the list of the demos
        """
        try:
            conn = sqlite3.connect(self.database_file)
            demo_dao = DemoDAO(conn)
            demo_list = []
            for d in demo_dao.list():
                demo_list.append(d.__dict__)
            conn.close()
        except sqlite3.Error as ex:
            self.logger.exception(ex)
            return Err(str(ex))

        return Ok(demo_list)

    def demo_list_by_editorid(self, editorid: int) -> Result[list[dict], str]:
        """
        return the list of demos matching the editor `editorid`
        """
        try:
            conn = sqlite3.connect(self.database_file)
            demo_dao = DemoDAO(conn)
            demo_list = []
            for d in demo_dao.list_by_editorid(editorid):
                demo_list.append(d.__dict__)
            conn.close()
        except sqlite3.Error as ex:
            self.logger.exception(ex)
            return Err(str(ex))

        return Ok(demo_list)

    def demo_list_pagination_and_filter(self, num_elements_page: int, page: int, qfilter: Optional[str]=None) -> Result[dict, str]:
        """
        return a paginated and filtered list of demos
        """
        try:
            conn = sqlite3.connect(self.database_file)

            demo_dao = DemoDAO(conn)
            complete_demo_list = demo_dao.list()

            conn.close()
        except sqlite3.Error as ex:
            self.logger.exception(ex)
            return Err(str(ex))

        demo_list = []
        next_page_number = None
        previous_page_number = None

        # filter or return all
        for demo in complete_demo_list:
            if qfilter is None or qfilter.lower() in demo.title.lower() or qfilter == str(demo.editorsdemoid):
                demo_list.append(demo.__dict__)

        # if demos found, return pagination
        if demo_list:
            r = len(demo_list) / num_elements_page
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

        data = {}
        data["demo_list"] = demo_list
        data["next_page_number"] = next_page_number
        data["number"] = totalpages
        data["previous_page_number"] = previous_page_number
        data["status"] = "OK"
        return Ok(data)

    def demo_get_editors_list(self, demo_id: int) -> Result[list[dict], str]:
        """
        return the editors of a given demo.
        """
        try:
            conn = sqlite3.connect(self.database_file)
            demo_dao = DemoDAO(conn)

            if not demo_dao.exist(demo_id):
                return Err(f"demo {demo_id} does not exist")

            de_dao = DemoEditorDAO(conn)
            editor_list = []
            for e in de_dao.read_demo_editors(int(demo_id)):
                editor_list.append(e.__dict__)
            conn.close()
        except sqlite3.Error as ex:
            self.logger.exception(ex)
            return Err(str(ex))

        return Ok(editor_list)

    def demo_get_available_editors_list(self, demo_id: int) -> Result[list[dict], str]:
        """
        return all editors that are not currently assigned to a given demo
        """
        try:
            conn = sqlite3.connect(self.database_file)

            # get all available editors
            a_dao = EditorDAO(conn)
            list_of_all_editors = a_dao.list()

            # get the editors of this demo
            da_dao = DemoEditorDAO(conn)
            list_of_editors_assigned_to_this_demo = da_dao.read_demo_editors(demo_id)
            conn.close()
        except sqlite3.Error as ex:
            self.logger.exception(ex)
            return Err(str(ex))


        available_editor_list = []
        for a in list_of_all_editors:
            if a not in list_of_editors_assigned_to_this_demo:
                available_editor_list.append(a.__dict__)
        return Ok(available_editor_list)

    def read_demo_metainfo(self, demoid: int) -> Result[dict, str]:
        """
        Return metadata of a demo.
        """
        try:
            conn = sqlite3.connect(self.database_file)
            dao = DemoDAO(conn)
            demo = dao.read(demoid)
            conn.close()
        except sqlite3.Error as ex:
            self.logger.exception(ex)
            return Err(str(ex))

        if demo is None:
            return Err(f"no demo retrieved for the demoid {demoid}")

        info = {
            'editorsdemoid': demo.editorsdemoid,
            'title': demo.title,
            'state': demo.state,
            'creation': demo.creation,
            'modification': demo.modification,
        }
        return Ok(info)

    def add_demo(self, demo_id: int, title: str, state: str, ddl: Optional[str]=None) -> Result[int, str]:
        """
        Create a demo
        """
        if ddl is None:
            ddl = '{}'

        try:
            conn = sqlite3.connect(self.database_file)
            demo_db = DemoDAO(conn)

            if demo_db.exist(demo_id):
                return Err(f"demo ID {demo_id} already exists")

            ddl_id = DemoDescriptionDAO(conn).add(ddl)

            demo = Demo(demo_id, title, state)
            demo_db.add(demo)

            ddl_db = DemoDemoDescriptionDAO(conn)
            ddl_db.add(demo_id, ddl_id)

            conn.close()
        except sqlite3.Error as ex:
            self.logger.exception(ex)
            return Err(str(ex))

        return Ok(demo_id)

    def delete_demo(self, demo_id: int) -> Result[None, str]:
        """
        Delete the specified demo
        """
        try:
            conn = sqlite3.connect(self.database_file)

            demo_dao = DemoDAO(conn)
            dd_dao = DemoDemoDescriptionDAO(conn)

            # delete demo decription history borra ddl id 3
            # d_dd con id 2 , y demoid=2, demodescpid 3 deberia no estar
            dd_dao.delete_all_demodescriptions_for_demo(demo_id)
            # delete demo, and delete on cascade demodemodescription
            demo_dao.delete(int(demo_id))

            conn.close()
        except sqlite3.Error as ex:
            self.logger.exception(ex)
            return Err(str(ex))

        return Ok()

    def update_demo(self, demo: dict, old_editor_demoid: int) -> Result[None, str]:
        """
        Update the demo.
        """
        d = Demo(demo['demo_id'], demo['title'], demo['state'])

        try:
            conn = sqlite3.connect(self.database_file)
            dao = DemoDAO(conn)
            if old_editor_demoid != d.editorsdemoid and dao.exist(d.editorsdemoid):
                return Err(f"cannot rename demo {old_editor_demoid}, target demo ID {d.editorsdemoid} is already taken")

            dao.update(d, old_editor_demoid)
            conn.close()
        except sqlite3.Error as ex:
            self.logger.exception(ex)
            return Err(str(ex))

        try:
            src = os.path.join(self.dl_extras_dir, str(old_editor_demoid))
            dst = os.path.join(self.dl_extras_dir, str(d.editorsdemoid))
            if old_editor_demoid != d.editorsdemoid:
                if os.path.isdir(dst):
                    shutil.rmtree(dst)
                if os.path.isdir(src):
                    os.rename(src, dst)
        except OSError as ex:
            self.logger.exception(ex)
            return Err(str(ex))

        return Ok()

    def editor_list(self) -> Result[list[dict], str]:
        """
        Returns the editor list
        """
        try:
            conn = sqlite3.connect(self.database_file)
            editor_dao = EditorDAO(conn)

            editor_list = []
            for e in editor_dao.list():
                editor_list.append(e.__dict__)

            conn.close()
        except Exception as ex:
            self.logger.exception(ex)
            return Err(str(ex))

        return Ok(editor_list)

    def get_editor(self, email: str) -> Result[Optional[dict], str]:
        """
        Returns an editor information
        """
        try:
            conn = sqlite3.connect(self.database_file)
            editor_dao = EditorDAO(conn)

            editor = editor_dao.read_from_email(email)

            conn.close()
        except sqlite3.Error as ex:
            self.logger.exception(ex)
            return Err(str(ex))

        if editor:
            editor = editor.__dict__
        return Ok(editor)

    def update_editor_email(self, new_email: str, old_email: str, name: str) -> Result[Optional[str], str]:
        """
        Update editor if old email exists and new one doesn't
        """
        try:
            conn = sqlite3.connect(self.database_file)
            dao = EditorDAO(conn)

            new_email_exists = dao.read_from_email(new_email)
            if new_email_exists:
                return Err("New email already exists in demoinfo")

            old_editor = dao.read_from_email(old_email)
            if not old_editor:
                resp = self.add_editor(name, new_email)
                resp_json = json.loads(resp)
                if resp_json['status'] != 'OK':
                    return Err(f"Editor could not be added with email {new_email}")
                else:
                    return Ok(f"New editor added {new_email}")

            e = Editor(name, new_email, old_editor.id, old_editor.creation)
            dao.update(e)
            conn.close()
        except sqlite3.Error as ex:
            self.logger.exception(ex)
            return Err(str(ex))

        return Ok(None)

    def add_editor(self, name: str, mail: str) -> Result[int, str]:
        """
        Add editor.
        """
        try:
            conn = sqlite3.connect(self.database_file)
            dao = EditorDAO(conn)

            e = Editor(name, mail)
            editor_id = dao.add(e)

            conn.close()
        except sqlite3.Error as ex:
            self.logger.exception(ex)
            return Err(str(ex))

        return Ok(editor_id)

    def add_editor_to_demo(self, demo_id: int, editor_id: int) -> Result[None, str]:
        """
        Add the given editor to the given demo.
        """
        try:
            conn = sqlite3.connect(self.database_file)
            demo_dao = DemoDAO(conn)
            editor_dao = EditorDAO(conn)

            if not demo_dao.exist(demo_id):
                return Err(f"demo {demo_id} does not exist")
            if not editor_dao.exist(editor_id):
                return Err(f"editor {editor_id} does not exist")

            dao = DemoEditorDAO(conn)
            dao.add(demo_id, editor_id)

            conn.close()
        except sqlite3.Error as ex:
            self.logger.exception(ex)
            return Err(str(ex))

        return Ok()

    def remove_editor_from_demo(self, demo_id: int, editor_id: int) -> Result[None, str]:
        """
        Remove the given editor from the given demo.
        """
        try:
            conn = sqlite3.connect(self.database_file)
            demo_dao = DemoDAO(conn)
            editor_dao = EditorDAO(conn)

            if not demo_dao.exist(demo_id):
                return Err(f"demo {demo_id} does not exist")
            if not editor_dao.exist(editor_id):
                return Err(f"editor {editor_id} does not exist")

            dao = DemoEditorDAO(conn)
            dao.remove_editor_from_demo(demo_id, editor_id)

            conn.close()
        except sqlite3.Error as ex:
            self.logger.exception(ex)
            return Err(str(ex))

        return Ok()

    def remove_editor(self, editor_id: int) -> Result[None, str]:
        """
        Delete editor
        """
        try:
            conn = sqlite3.connect(self.database_file)
            dedao = DemoEditorDAO(conn)

            demolist = dedao.read_editor_demos(editor_id)
            for demo in demolist:
                dedao.remove_editor_from_demo(demo.editorsdemoid, editor_id)

            edao = EditorDAO(conn)
            edao.delete(editor_id)

            conn.close()
        except sqlite3.Error as ex:
            self.logger.exception(ex)
            return Err(str(ex))

        return Ok()

    def read_ddl(self, ddl_id):
        """
        Return the DDL.
        """
        data = {}
        data["status"] = "KO"
        data["demo_description"] = None
        try:
            ddl_id = int(ddl_id)
            conn = sqlite3.connect(self.database_file)
            dao = DemoDescriptionDAO(conn)

            ddl = dao.read(ddl_id)
            ddl_str = str(ddl)

            data["demo_description"] = ddl_str
            conn.close()
            data["status"] = "OK"
        except sqlite3.Error as ex:
            self.logger.exception(ex)
            return Err(str(ex))

        return json.dumps(data).encode()

    def get_interface_ddl(self, demo_id: int, sections: Optional[str]=None) -> Result[dict, str]:
        """
        Read the DDL of the specified demo without unneeded or private fields. Used by the website interface.
        """
        try:
            conn = sqlite3.connect(self.database_file)

            dd_dao = DemoDemoDescriptionDAO(conn)
            ddl = dd_dao.get_ddl(demo_id)

            conn.close()
        except sqlite3.Error as ex:
            self.logger.exception(ex)
            return Err(str(ex))

        if not ddl:
            return Err(f"There isn't any DDL for the demo {demo_id}")

        ddl = json.loads(ddl, object_pairs_hook=OrderedDict)

        # remove sections that shouldn't be obtained by the web interface
        if 'build' in ddl:
            del ddl['build']
        if 'run' in ddl:
            del ddl['run']

        # keep only the sections given as a parameter
        if sections:
            ddl_sections = self.get_ddl_sections(ddl, sections)
            return Ok(ddl_sections)

        return Ok(ddl)

    @staticmethod
    def get_ddl_sections(ddl, ddl_sections):
        """
        Returns DDL sections
        """
        sections = OrderedDict()
        for section in ddl_sections.split(','):
            if ddl.get(section):
                sections[section] = ddl.get(section)
        return sections

    def get_ddl_history(self, demo_id: int) -> Result[list[dict], str]:
        """
        Return a list with all the DDLs
        """
        try:
            conn = sqlite3.connect(self.database_file)
            dd_dao = DemoDemoDescriptionDAO(conn)

            ddl_history = dd_dao.read_history(demo_id)

            conn.close()
        except sqlite3.Error as ex:
            self.logger.exception(ex)
            return Err(str(ex))

        if not ddl_history:
            return Err(f"There isn't any DDL for demo {demo_id}")

        return Ok(ddl_history)

    def get_ddl(self, demo_id: int) -> Result[str, str]:
        """
        Reads the current DDL of the demo
        """
        try:
            conn = sqlite3.connect(self.database_file)

            dd_dao = DemoDemoDescriptionDAO(conn)
            ddl = dd_dao.get_ddl(demo_id)

            conn.close()
        except sqlite3.Error as ex:
            self.logger.exception(ex)
            return Err(str(ex))

        if ddl is None:
            return Err(f"There isn't any DDL for demo {demo_id}")

        return Ok(ddl)

    def save_ddl(self, demoid: int, ddl: str) -> Result[str, str]:
        """
        Save the DDL.
        """
        if not is_json(ddl):
            return Err("input ddl is not a valid json")

        try:
            conn = sqlite3.connect(self.database_file)

            demo_dao = DemoDAO(conn)
            demo = demo_dao.read(int(demoid))
            if demo is None:
                return Err(f"There is no demo with the demo ID {demoid}")

            state = demo_dao.read(demoid).state
            if state != "published":  # If the demo is not published the DDL is overwritten
                ddddao = DemoDemoDescriptionDAO(conn)
                demodescription = ddddao.get_ddl(demoid)
                dao = DemoDescriptionDAO(conn)

                if demodescription is None:  # Check if is a new demo
                    demodescription_id = dao.add(ddl)

                    dao = DemoDemoDescriptionDAO(conn)
                    dao.add(demoid, demodescription_id)
                else:
                    dao.update(ddl, demoid)

            else:  # Otherwise create a new one
                dao = DemoDescriptionDAO(conn)
                demodescription_id = dao.add(ddl)
                dao = DemoDemoDescriptionDAO(conn)
                dao.add(demoid, demodescription_id)

            conn.close()
        except sqlite3.Error as ex:
            self.logger.exception(ex)
            return Err(str(ex))

        return Ok()

    def get_ssh_keys(self, demo_id: int) -> Result[tuple[str,str],str]:
        """
        Returns the ssh keys for a given demo_id.
        """
        try:
            conn = sqlite3.connect(self.database_file)
            demo_dao = DemoDAO(conn)

            if not demo_dao.exist(demo_id):
                return Err(f"demo {demo_id} does not exist")

            if not demo_dao.has_ssh_key(demo_id):
                pubkey, privkey = generate_ssh_keys()
                demo_dao.set_ssh_key(demo_id, pubkey, privkey)

            pubkey, privkey = demo_dao.get_ssh_key(demo_id)

            conn.close()
        except sqlite3.Error as ex:
            self.logger.exception(ex)
            return Err(str(ex))

        pubkey = pubkey.decode('utf-8')
        privkey = privkey.decode('utf-8')
        return Ok((pubkey, privkey))

    def reset_ssh_keys(self, demo_id: int) -> Result[None, str]:
        """
        Renews ssh keys for a given demo.
        """
        try:
            conn = sqlite3.connect(self.database_file)
            demo_dao = DemoDAO(conn)

            if not demo_dao.exist(demo_id):
                return Err(f"demo {demo_id} does not exist")

            demo_dao.reset_ssh_key(demo_id)

            conn.close()
        except sqlite3.Error as ex:
            self.logger.exception(ex)
            return Err(str(ex))

        return Ok()

    def stats(self) -> Result[dict, str]:
        """
        Returns usage statistics.
        """
        stats = {}
        try:
            conn = sqlite3.connect(self.database_file)
            cursor_db = conn.cursor()

            cursor_db.execute('SELECT COUNT(*) FROM demo')
            stats["nb_demos"] = cursor_db.fetchone()[0]
            cursor_db.execute('SELECT COUNT(*) FROM editor')
            stats["nb_editors"] = cursor_db.fetchone()[0]

            conn.close()
        except sqlite3.Error as ex:
            self.logger.exception(ex)
            return Err(str(ex))

        return Ok(stats)


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

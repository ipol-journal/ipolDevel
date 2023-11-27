#!/usr/bin/env python
import errno
import hashlib
import json
import logging
import os
import os.path
import shutil
import sqlite3 as lite
from collections import OrderedDict
from datetime import datetime

import magic
from config import settings
from result import Err, Ok, Result


class Archive:
    def __init__(self):
        self.logger = init_logging()
        self.init_database()

    def delete_exp_w_deps(self, conn, experiment_id: int) -> int:
        """
        This function remove, in the database, an experiment from
        the experiments table, and its dependencies in the correspondence
        table. If the blobs are used only by this experiment, they will be
        removed too.
        """
        ids_blobs = []
        cursor_db = conn.cursor()
        cursor_db.execute(
            """
        PRAGMA foreign_keys=ON"""
        )

        # save a list of blobs used by the experiment
        for row in cursor_db.execute(
            "SELECT * FROM correspondence where id_experiment = ?", (experiment_id,)
        ):
            ids_blobs.append(row[2])

        self.purge_unique_blobs(conn, ids_blobs, experiment_id)

        cursor_db.execute("DELETE FROM experiments WHERE id = ?", (experiment_id,))
        n_changes = cursor_db.rowcount
        cursor_db.execute(
            "DELETE FROM correspondence WHERE id_experiment = ?", (experiment_id,)
        )
        return n_changes

    def purge_unique_blobs(self, conn, ids_blobs: int, experiment_id: int) -> None:
        """
        This function checks if the blobs are used only in this experiment.
                If this is the case, they are deleted both in the database
                and physically.
        """
        cursor_db = conn.cursor()

        for blob in ids_blobs:
            cursor_db.execute(
                """SELECT COUNT(*) 
                FROM correspondence 
                WHERE id_blob = ? 
                AND id_experiment <> ?
                """,
                (
                    blob,
                    experiment_id,
                ),
            )
            if cursor_db.fetchone()[0] == 0:
                self.delete_blob(conn, blob)

    def delete_blob(self, conn, id_blob: int) -> None:
        """
        This function delete the given id_blob, in the database and physically.
        """
        cursor_db = conn.cursor()
        cursor_db.execute("SELECT * FROM blobs WHERE id = ?", (id_blob,))
        tmp = cursor_db.fetchone()

        # get the new path of the blob and thumbnail
        path_blob = None
        path_thumb = None
        if tmp is not None:
            path_blob, _ = self.get_new_path(settings.archive_blobs_dir, tmp[1], tmp[2])
            path_thumb, _ = self.get_new_path(
                settings.archive_thumbs_dir, tmp[1], "jpeg"
            )

        cursor_db.execute("DELETE FROM blobs WHERE id = ?", (id_blob,))

        # delete the files of this blob
        try:
            os.remove(path_blob)
            os.remove(path_thumb)
        except Exception:
            pass

    def mkdir_p(path: str) -> None:
        """
        Implement the UNIX shell command "mkdir -p"
        with given path as parameter.
        """
        try:
            os.makedirs(path)
        except OSError as exc:
            if exc.errno == errno.EEXIST and os.path.isdir(path):
                pass
            else:
                raise

    def get_hash_blob(self, path: str) -> str:
        """
        Return sha1 hash of given blob
        """
        with open(path, "rb") as the_file:
            return hashlib.sha1(the_file.read()).hexdigest()

    def file_format(self, the_file: str) -> str:
        """
        Return format of the file
        """
        mime = magic.Magic(mime=True)
        fileformat = mime.from_file(the_file)
        fileformat = fileformat.split("/")[0]
        return fileformat

    #####
    # adding an experiment to the archive database
    #####
    def create_experiment(
        self,
        demo_id: int,
        blobs: str = None,
        parameters: str = None,
        execution: str = None,
    ) -> Result[dict, str]:
        """
        Add an experiment to the archive.
        """
        # # initialize list of copied files, to delete them in case of exception
        copied_files_list = []
        try:
            conn = lite.connect(settings.database_file)
            id_experiment = self.update_exp_table(conn, demo_id, parameters, execution)
            dict_corresp = []
            dict_corresp = self.update_blob(conn, blobs, copied_files_list)
            self.update_correspondence_table(conn, id_experiment, dict_corresp)
            conn.commit()
            conn.close()
            return Ok({"experiment_id": id_experiment})

        except Exception as ex:
            message = "Failure in add_experiment. Error = {}".format(ex)
            self.logger.exception(message)
            try:
                # Execute database rollback
                conn.rollback()
                conn.close()

                # Execute deletion of copied files
                for copied_file in copied_files_list:
                    os.remove(copied_file)

            except Exception:
                return Err({"experiment_id": id_experiment})

    def get_new_path(
        self, main_directory: str, hash_name: str, file_extension: str, depth: int = 2
    ) -> tuple[str, str]:
        """
        This method creates a new fullpath to store the blobs in the archive,
        where new directories are created for each 'depth' first letters
        of the hash, for example:
        input  is /tmp/abvddff.png
        output is /tmp/a/b/abvddff.png
        where the full path /tmp/a/b/ has been created
        returns this new_path and the subdirectory (a/b/) if depth = 2
        """
        length = min(len(hash_name), depth)

        subdirs = "/".join(list(hash_name[:length]))
        new_directory_name = main_directory + subdirs + "/"

        if not os.path.isdir(new_directory_name):
            os.makedirs(new_directory_name)

        new_path = new_directory_name + hash_name + "." + file_extension

        return new_path, subdirs

    def copy_file_in_folder(self, original_path, main_dir, hash_file, extension) -> str:
        """
        Write a file in its respective folder
        """
        try:
            final_path, _ = self.get_new_path(main_dir, hash_file, extension)
            if not os.path.exists(final_path):
                shutil.copyfile(original_path, final_path)
            return final_path
        except Exception as ex:
            message = "Failure in copy_file_in_folder. Error={}".format(ex)
            self.logger.exception(message)
            print(message)
            raise

    def add_blob_in_the_database(
        self, conn, hash_file: str, type_file: str, format_file: str
    ) -> int:
        """
        check if a blob already exists in the database. If not, we include it
        return the id of the blob
        """
        try:
            cursor_db = conn.cursor()
            # First, we check if the blob is already in the database
            query = cursor_db.execute(
                """
                SELECT id FROM blobs WHERE hash = ?
                """,
                (hash_file,),
            )
            row = query.fetchone()
            if row is not None:
                return int(row[0])

            cursor_db.execute(
                """
                INSERT INTO blobs(hash, type, format) VALUES(?, ?, ?)
                """,
                (
                    hash_file,
                    type_file,
                    format_file,
                ),
            )
            # get id of the blob previously inserted
            return int(str(cursor_db.lastrowid))
        except Exception as ex:
            message = "Failure in add_blob_in_the_database. Error = {}".format(ex)
            self.logger.exception(message)
            raise

    def add_blob(self, conn, blob_dict: dict, copied_files_list: list) -> None:
        """
        This function checks if a blob exists in the table. If it exists,
        the id is returned. If not, the blob is added, then the id is returned.
        """
        # List of copied files. Useful to delete them if an exception is thrown
        # copied_files = []
        try:
            thumb_key = list(
                key for key, value in blob_dict.items() if "thumbnail" in key
            )
            if thumb_key:
                blob_thumbnail_name = thumb_key[0]
                blob_thumbnail_path = blob_dict[blob_thumbnail_name]
                del blob_dict[blob_thumbnail_name]

            blob_name = list(blob_dict.keys())[0]
            blob_path = list(blob_dict.values())[0]

            # If the file doesn't exist, just return None
            if not os.path.isfile(blob_path):
                return None, None

            hash_file = self.get_hash_blob(blob_path)
            format_file = self.file_format(blob_path)

            _, type_file = os.path.splitext(blob_path)
            type_file = type_file.split(".")[1]
            type_file.lower()

            id_blob = self.add_blob_in_the_database(
                conn, hash_file, type_file, format_file
            )
            # copy the files in their respective folders
            path_new_blob = self.copy_file_in_folder(
                blob_path, settings.archive_blobs_dir, hash_file, type_file
            )
            copied_files_list.append(path_new_blob)
            if thumb_key:
                path_new_thumbnail = self.copy_file_in_folder(
                    blob_thumbnail_path, settings.archive_thumbs_dir, hash_file, "jpeg"
                )
                copied_files_list.append(path_new_thumbnail)
            return id_blob, blob_name
        except Exception as ex:
            message = "Failure in add_blob. Error = {}".format(ex)
            self.logger.exception(message)
            raise

    def update_exp_table(
        self, conn, demo_id: int, parameters: str, execution: str
    ) -> int:
        """
        This function update the experiment table
        """
        cursor_db = conn.cursor()
        cursor_db.execute(
            """
        INSERT INTO
        experiments (id_demo, params, execution, timestamp)
        VALUES (?, ?, ?,datetime(CURRENT_TIMESTAMP, 'localtime'))""",
            (demo_id, parameters, execution),
        )
        return int(cursor_db.lastrowid)

    def update_blob(self, conn, blobs: dict, copied_files_list: list) -> dict:
        """
        This function updates the blobs table.
        It return a dictionary of data to be added to the correspondences table.
        """
        try:
            id_blob = int()
            dict_blobs = json.loads(blobs)
            dict_corresp = []

            for blob_element in dict_blobs:
                id_blob, blob_name = self.add_blob(
                    conn, blob_element, copied_files_list
                )
                dict_corresp.append({"blob_id": id_blob, "blob_name": blob_name})

        except Exception as ex:
            self.logger.exception("update_blob. Error {}".format(ex))
            raise

        return dict_corresp

    def update_correspondence_table(
        self, conn, id_experiment: int, dict_corresp: dict
    ) -> None:
        """
        This function update the correspondence table, associating
                blobs, experiments, and descriptions of blobs.
        """
        cursor_db = conn.cursor()
        for order_exp, item in enumerate(dict_corresp):
            cursor_db.execute(
                """
            INSERT INTO
            correspondence (id_experiment, id_blob, name, order_exp)
            VALUES (?, ?, ?, ?)""",
                (id_experiment, item["blob_id"], item["blob_name"], order_exp),
            )

    def get_dict_file(
        self, path_file, path_thumb: str, name: str, id_blob: int
    ) -> dict:
        """
        Build a dict containing the path to the file, the path to the thumb
                and the name of the file.
        """
        dict_file = {}
        dict_file["url"] = "/api/archive/" + path_file
        dict_file["name"] = name
        dict_file["id"] = id_blob

        if os.path.exists(path_thumb):
            dict_file["url_thumb"] = "/api/archive/" + path_thumb

        return dict_file

    def get_experiment_page(self, conn, demo_id: int, page: int) -> list:
        """
        This function return a list of dicts with all the informations needed
                for displaying the experiments on a given page.
        """
        data_exp = []
        cursor_db = conn.cursor()
        starting_index = (page - 1) * settings.number_of_experiments_by_pages

        cursor_db.execute(
            """
        SELECT id, params, execution, timestamp
        FROM experiments WHERE id_demo = ?
        ORDER BY timestamp
        LIMIT ? OFFSET ?""",
            (
                demo_id,
                settings.number_of_experiments_by_pages,
                starting_index,
            ),
        )

        all_rows = cursor_db.fetchall()

        for row in all_rows:
            data_exp.append(
                self.get_data_experiment(conn, row[0], row[1], row[2], row[3])
            )

        return data_exp

    def get_data_experiment(
        self, conn, id_exp: int, parameters: str, execution: str, date: datetime
    ) -> dict:
        """
        Build a dictionnary containing all the datas needed on a given
                experiment for building the archive page.
        """
        dict_exp = {}
        list_files = []
        path_file = str()
        path_thumb = str()

        try:
            cursor_db = conn.cursor()
            cursor_db.execute(
                """
                SELECT blb.hash, blb.type, cor.name, blb.id
                FROM blobs blb
                JOIN correspondence cor ON blb.id=cor.id_blob
                WHERE id_experiment = ?
                ORDER by cor.order_exp """,
                (id_exp,),
            )

            all_rows = cursor_db.fetchall()

            for row in all_rows:
                path_file, subdirs = self.get_new_path(
                    main_directory=settings.archive_blobs_dir,
                    hash_name=row[0],
                    file_extension=row[1],
                )
                thumb_dir = "{}{}".format(settings.archive_thumbs_dir, subdirs)
                thumb_name = "{}.jpeg".format(row[0])
                path_thumb = os.path.join(thumb_dir, thumb_name)
                list_files.append(
                    self.get_dict_file(path_file, path_thumb, row[2], row[3])
                )

            dict_exp["id"] = id_exp
            dict_exp["date"] = date
            dict_exp["parameters"] = json.loads(
                parameters, object_pairs_hook=OrderedDict
            )
            dict_exp["execution"] = execution
            dict_exp["files"] = list_files
            return dict_exp
        except Exception as ex:
            message = "Failure in get_data_experiment. Error = {}".format(ex)
            print(message)
            self.logger.exception(message)
            raise

    def get_meta_info(self, conn, id_demo: int) -> list:
        """
        This function return the number of archive pages to be displayed
        for a given demo, and the number of experiments done with
        this demo.
        """
        meta_info = {}

        meta_info[
            "number_of_experiments_in_a_page"
        ] = settings.number_of_experiments_by_pages

        cursor_db = conn.cursor()

        cursor_db.execute(
            """
        SELECT COUNT(*) FROM experiments WHERE id_demo = ?""",
            (id_demo,),
        )

        number_of_experiments = cursor_db.fetchone()[0]
        meta_info["number_of_experiments"] = number_of_experiments

        if number_of_experiments == 0:
            meta_info["first_date_of_an_experiment"] = "never"
            meta_info["number_of_pages"] = 0
            return meta_info
        cursor_db.execute(
            """
        SELECT timestamp
        FROM experiments WHERE id_demo = ?
        ORDER BY timestamp """,
            (id_demo,),
        )

        first_date_of_an_experiment = cursor_db.fetchone()[0]

        if number_of_experiments % settings.number_of_experiments_by_pages != 0:
            pages_to_add = 1
        else:
            pages_to_add = 0

        number_of_pages = (
            int(number_of_experiments / settings.number_of_experiments_by_pages)
            + pages_to_add
        )

        meta_info["first_date_of_an_experiment"] = first_date_of_an_experiment
        meta_info["number_of_pages"] = number_of_pages

        return meta_info

    def init_database(self) -> bool:
        """
        Initialize the database used by the module if it doesn't exist.
        If the file is empty, the system delete it and create a new one.
        """
        if os.path.isfile(settings.database_file):
            file_info = os.stat(settings.database_file)

            if file_info.st_size == 0:
                print(str(settings.database_file) + " is empty. Removing the file...")
                try:
                    self.logger.error("init_database: Database file was empty")
                    os.remove(settings.database_file)
                except Exception as ex:
                    message = "Error in init_database. Error = {}".format(ex)
                    self.logger.exception(message)
                    return False

                print("Creating a correct new database")

        if not os.path.isfile(settings.database_file):
            try:
                conn = lite.connect(settings.database_file)
                cursor_db = conn.cursor()

                sql_buffer = ""

                curdir = os.path.dirname(__file__)
                with open(
                    os.path.join(curdir, "drop_create_db_schema.sql"), "r"
                ) as sql_file:
                    for line in sql_file:
                        sql_buffer += line
                        if lite.complete_statement(sql_buffer):
                            sql_buffer = sql_buffer.strip()
                            cursor_db.execute(sql_buffer)
                            sql_buffer = ""

                conn.commit()
                conn.close()

            except Exception as ex:
                message = "Error in init_database. Error = {}".format(ex)
                self.logger.exception(message)
                if os.path.isfile(settings.database_file):
                    try:
                        os.remove(settings.database_file)
                    except Exception as ex:
                        message = "Error in init_database. Error = {}".format(ex)
                        self.logger.exception(message)
                        return False

        return True


def init_logging():
    """
    Initialize the error logs of the module.
    """
    logger = logging.getLogger("archive")
    logger.setLevel(logging.ERROR)
    handler = logging.FileHandler(os.path.join(settings.logs_dir, "error.log"))
    formatter = logging.Formatter(
        "%(asctime)s ERROR in %(message)s", datefmt="%Y-%m-%d %H:%M:%S"
    )
    handler.setFormatter(formatter)
    logger.addHandler(handler)
    return logger

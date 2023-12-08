#!/usr/bin/env python3
import glob
import hashlib
import logging
import mimetypes
import operator
import os
import shutil
import sqlite3 as lite
from contextlib import contextmanager
from sqlite3 import Error
from threading import Lock

import magic
from config import settings
from fastapi import UploadFile
from ipolutils.utils import thumbnail
from result import Err, Ok, Result

from . import database
from .errors import (
    IPOLBlobsDataBaseError,
    IPOLBlobsTemplateError,
    IPOLBlobsThumbnailError,
    IPOLRemoveDirError,
)

lock = Lock()


class Blobs:
    def __init__(self) -> None:
        self.log = init_logging()
        self.init_database()

    def error_log(self, function_name: str, error: str) -> None:
        """
        Write an error log in the logs_dir defined in demo.conf
        """
        error_string = function_name + ": " + error
        self.log.error(error_string)

    def init_database(self) -> bool:
        """
        Initialize the database used by the module if it doesn't exist.
        If the file is empty, the system delete it and create a new one.
        """

        if os.path.isfile(settings.blobs_database_file):
            file_info = os.stat(settings.blobs_database_file)

            if file_info.st_size == 0:
                try:
                    os.remove(settings.blobs_database_file)
                except Exception:
                    self.log.exception("init_database")
                    return False

        if not os.path.isfile(settings.blobs_database_file):
            try:
                conn = lite.connect(settings.blobs_database_file)
                cursor_db = conn.cursor()

                sql_buffer = ""

                with open(
                    settings.database_dir + "/drop_create_db_schema.sql", "r"
                ) as sql_file:
                    for line in sql_file:
                        sql_buffer += line
                        if lite.complete_statement(sql_buffer):
                            sql_buffer = sql_buffer.strip()
                            cursor_db.execute(sql_buffer)
                            sql_buffer = ""

                conn.commit()
                conn.close()

            except Exception:
                self.log.exception("init_database")

                if os.path.isfile(settings.blobs_database_file):
                    try:
                        os.remove(settings.blobs_database_file)
                    except Exception:
                        self.log.exception("init_database")
                        return False

        return True

    @contextmanager
    def get_db_connection(self):
        """
        Returns a SQLite database connection object using a context manager.
        """
        connection = None
        try:
            connection = lite.connect(settings.blobs_database_file)
            yield connection
        except IPOLBlobsDataBaseError:
            self.log.exception("DB error could not get a connection")
        except Error:
            self.log.exception("Error connectin to database")
        finally:
            if connection:
                connection.close()

    def get_blobs(self, demo_id: int) -> Result[dict, str]:
        conn = None
        try:
            conn = lite.connect(settings.blobs_database_file)

            demo_blobs = database.get_demo_owned_blobs(conn, demo_id)
            templates = database.get_demo_templates(conn, demo_id)
            sets = self.prepare_list(demo_blobs)
            for template in templates:
                sets += self.prepare_list(
                    database.get_template_blobs(conn, template["id"])
                )
            return Ok(sets)

        except IPOLBlobsDataBaseError:
            message = f"Fails obtaining all the blobs from demo #{demo_id}"
            logging.exception(message)
            return Err(message)
        except Exception:
            message = f"*** Unhandled exception while obtaining all the blobs from demo #{demo_id}"
            logging.exception(message)
            return Err(message)
        finally:
            if conn is not None:
                conn.close()

    def add_blob(
        self,
        blob: UploadFile,
        blob_set: str,
        pos_set: int,
        title: str,
        credit: str,
        dest: dict,
        blob_vr: UploadFile,
    ) -> bool:
        """
        Copies the blob and store it in the DB
        """
        res = False
        conn = None
        try:
            conn = lite.connect(settings.blobs_database_file)
            mime = self.get_blob_mime(blob.file)

            blob_format, ext = self.get_format_and_extension(mime)
            blob_hash = self.get_hash(blob.file)
            blob_id = self.store_blob(
                conn, blob.file, credit, blob_hash, ext, blob_format
            )
            try:
                if blob_vr:
                    # If the user specified to use a new VR, then we use it
                    _, vr_ext = self.get_format_and_extension(
                        self.get_blob_mime(blob_vr.file)
                    )
                    blob_file = self.copy_blob(
                        blob_vr.file, blob_hash, vr_ext, settings.vr_dir
                    )
                    self.create_thumbnail(blob_file, blob_hash)
                else:
                    # The user didn't give any new VR.
                    # We'll update the thumbnail only if it doesn't have already a VR
                    if not self.blob_has_VR(blob_hash):
                        blob_file = os.path.join(
                            settings.blob_dir, self.get_subdir(blob_hash)
                        )
                        blob_file = os.path.join(blob_file, blob_hash + ext)
                        self.create_thumbnail(blob_file, blob_hash)

            except IPOLBlobsThumbnailError:
                # An error in the creation of the thumbnail doesn't stop the execution of the method
                self.log.exception("Error creating the thumbnail.")

            # If the set is empty the module generates an unique set name
            if not blob_set:
                blob_set = self.generate_set_name(blob_id)
                pos_set = 0

            if dest["dest"] == "demo":
                demo_id = dest["demo_id"]
                # Check if the pos is empty
                if database.is_pos_occupied_in_demo_set(
                    conn, demo_id, blob_set, pos_set
                ):
                    editor_demo_id = database.get_demo_id(conn, demo_id)
                    pos_set = database.get_available_pos_in_demo_set(
                        conn, editor_demo_id, blob_set
                    )

                self.do_add_blob_to_demo(
                    conn, demo_id, blob_id, blob_set, pos_set, title
                )
                res = True
            elif dest["dest"] == "template":
                template_id = dest["template_id"]
                # Check if the pos is empty
                if database.is_pos_occupied_in_template_set(
                    conn, template_id, blob_set, pos_set
                ):
                    pos_set = database.get_available_pos_in_template_set(
                        conn, template_id, blob_set
                    )

                self.do_add_blob_to_template(
                    conn, template_id, blob_id, blob_set, pos_set, title
                )
                res = True
            else:
                self.log.error(
                    f'Failed to add the blob in add_blob. Unknown dest: {dest["dest"]}'
                )
        except IOError:
            self.log.exception("Error copying uploaded blob.")
        except IPOLBlobsDataBaseError:
            self.log.exception("Error adding blob info to DB.")
        except IPOLBlobsTemplateError:
            self.log.exception(
                "Couldn't add blob to template. blob. Template doesn't exists."
            )
        except Exception:
            self.log.exception("*** Unhandled exception while adding the blob.")
        finally:
            if conn is not None:
                conn.close()

        return res

    def store_blob(
        self, conn, blob, credit: str, blob_hash: str, ext: str, blob_format: str
    ) -> int:
        """
        Stores the blob info in the DB, copy it in the file system and returns the blob_id and blob_file
        """
        blob_id = database.get_blob_id(conn, blob_hash)
        if blob_id is not None:
            # If the DB already have the hash there is no need to store the blob
            return blob_id

        try:
            self.copy_blob(blob, blob_hash, ext, settings.blob_dir)
            blob_id = database.store_blob(conn, blob_hash, blob_format, ext, credit)
            conn.commit()
            return blob_id
        except IPOLBlobsDataBaseError:
            conn.rollback()
            raise

    def get_blob_mime(self, blob) -> str:
        """
        Return format from blob
        """
        mime = magic.Magic(mime=True)
        blob.seek(0)
        blob_format = mime.from_buffer(blob.read())
        return blob_format

    def get_format_and_extension(self, mime: str) -> tuple[str, str]:
        """
        get format and extension from mime
        """
        mime_format = mime.split("/")[0]
        ext = mimetypes.guess_extension(mime)
        # some mime type maybe unknown, especially for exotic file format
        if not ext:
            ext = ".dat"
        return mime_format, ext

    def get_hash(self, blob) -> str:
        """
        Return the sha1 hash from blob
        """
        blob.seek(0)
        return hashlib.sha1(blob.read()).hexdigest()

    def copy_blob(self, blob, blob_hash: str, ext: str, dst_dir: str) -> str:
        """
        Stores the blob in the file system, returns the dest path
        """
        dst_path = os.path.join(dst_dir, self.get_subdir(blob_hash))
        if not os.path.isdir(dst_path):
            os.makedirs(dst_path)
        dst_path = os.path.join(dst_path, blob_hash + ext)
        blob.seek(0)
        with open(dst_path, "wb") as f:
            shutil.copyfileobj(blob, f)
        return dst_path

    def get_subdir(self, blob_hash: str) -> str:
        """
        Returns the subdirectory from the blob hash
        """
        return os.path.join(blob_hash[0], blob_hash[1])

    def do_add_blob_to_demo(
        self,
        conn,
        demo_id: int,
        blob_id: int,
        pos_set: int,
        blob_set: str,
        blob_title: str,
    ) -> None:
        """
        Associates the blob to a demo in the DB
        """
        try:
            if not database.demo_exist(conn, demo_id):
                database.create_demo(conn, demo_id)
            database.add_blob_to_demo(
                conn, demo_id, blob_id, pos_set, blob_set, blob_title
            )
            conn.commit()
        except IPOLBlobsDataBaseError:
            conn.rollback()
            raise

    def do_add_blob_to_template(
        self,
        conn,
        template_id: int,
        blob_id: int,
        blob_set: str,
        pos_set: int,
        blob_title: str,
    ) -> None:
        """
        Associates the template to a demo in the DB
        """
        try:
            if not database.template_exist(conn, template_id):
                raise IPOLBlobsTemplateError("Template doesn't exist")

            database.add_blob_to_template(
                conn, template_id, blob_id, pos_set, blob_set, blob_title
            )
            conn.commit()
        except IPOLBlobsDataBaseError:
            conn.rollback()
            raise

    def create_thumbnail(self, src_file, blob_hash: str) -> None:
        """
        Creates a thumbnail for blob_file.
        """
        src_file = os.path.realpath(src_file)
        thumb_height = 256
        dst_path = os.path.join(settings.thumb_dir, self.get_subdir(blob_hash))
        if not os.path.isdir(dst_path):
            os.makedirs(dst_path)
        dst_file = os.path.join(dst_path, blob_hash + ".jpg")
        try:
            thumbnail(src_file, height=thumb_height, dst_file=dst_file)
        except Exception as ex:
            raise IPOLBlobsThumbnailError(f"File '{src_file}', thumbnail error. {ex}")

    def prepare_list(self, blobs) -> list:
        """
        Prepare the output list of blobs
        """
        sets = {}
        for blob in blobs:
            blob_set = blob["blob_set"]
            if blob_set in sets:
                sets[blob_set].append(self.get_blob_info(blob))
            else:
                sets[blob_set] = [self.get_blob_info(blob)]

        sorted_sets = sorted(list(sets.items()), key=operator.itemgetter(0))
        result = []
        for blob_set in sorted_sets:
            dic = {}
            for blob in blob_set[1]:
                position = blob["pos_set"]
                del blob["pos_set"]
                dic[position] = blob

            result.append({"name": blob_set[0], "blobs": dic})
        return result

    def blob_has_thumbnail(self, blob_hash: str) -> str:
        """
        Check if the blob has already thumbnail
        """
        subdir = self.get_subdir(blob_hash)
        thumb_physical_dir = os.path.join(settings.thumb_dir, subdir)
        return os.path.isfile(
            os.path.join(
                settings.blobs_data_root, thumb_physical_dir, blob_hash + ".jpg"
            )
        )

    def blob_has_VR(self, blob_hash: str) -> str:
        """
        Check if the blob is associated to a VR
        """
        subdir = self.get_subdir(blob_hash)
        vr_physical_dir = os.path.join(settings.vr_dir, subdir)
        vr_extension = self.get_vr_extension(
            os.path.join(settings.blobs_data_root, vr_physical_dir), blob_hash
        )
        return vr_extension is not None

    def get_blob_info(self, blob) -> list:
        """
        Return the required information from the blob
        """
        subdir = self.get_subdir(blob["hash"])
        vr_physical_dir = os.path.join(settings.vr_dir, subdir)
        thumb_physical_dir = os.path.join(settings.thumb_dir, subdir)
        blob_physical_dir = os.path.join(settings.blob_dir, subdir)

        vr_url = "/api/blobs/" + vr_physical_dir
        thumbnail_url = "/api/blobs/" + thumb_physical_dir
        blob_url = "/api/blobs/" + blob_physical_dir

        vr_path = os.path.join(vr_physical_dir, blob["hash"] + blob["extension"])

        vr_mtime = ""
        if os.path.exists(vr_path):
            vr_mtime = os.path.getmtime(vr_path)

        blob_info = {
            "id": blob["id"],
            "title": blob["title"],
            "blob": os.path.join(blob_url, blob["hash"] + blob["extension"]),
            "format": blob["format"],
            "credit": blob["credit"],
            "pos_set": blob["pos_set"],
            "vr_mtime": vr_mtime,
        }

        if self.blob_has_thumbnail(blob["hash"]):
            blob_info["thumbnail"] = os.path.join(
                settings.blobs_data_root, thumbnail_url, blob["hash"] + ".jpg"
            )

        vr_extension = self.get_vr_extension(
            os.path.join(settings.blobs_data_root, vr_physical_dir), blob["hash"]
        )

        if vr_extension is not None:
            blob_info["vr"] = os.path.join(vr_url, blob["hash"] + vr_extension)

        return blob_info

    def get_vr_extension(self, vr_dir: str, blob_hash: str) -> str:
        """
        If the visual representation exists, the function returns its extension
        if not, returns None
        """
        vr_extension = None
        if os.path.isdir(vr_dir):
            file_without_extension = os.path.join(vr_dir, blob_hash)
            vr = glob.glob(file_without_extension + ".*")
            if vr:
                _, vr_extension = os.path.splitext(vr[0])

        return vr_extension

    def remove_blob(self, blob_set: str, pos_set: int, dest: str) -> bool:
        """
        Remove the blob
        """
        with lock:
            res = False
            conn = None
            try:
                conn = lite.connect(settings.blobs_database_file)

                if dest["dest"] == "demo":
                    demo_id = dest["demo_id"]
                    blob_data = database.get_blob_data_from_demo(
                        conn, demo_id, blob_set, pos_set
                    )

                    if blob_data:
                        blob_id = blob_data.get("id")
                        num_refs = database.get_blob_refcount(conn, blob_id)

                        database.remove_blob_from_demo(conn, demo_id, blob_set, pos_set)
                elif dest["dest"] == "template":
                    template_id = dest["template_id"]
                    blob_data = database.get_blob_data_from_template(
                        conn, template_id, blob_set, pos_set
                    )

                    if blob_data:
                        blob_id = blob_data.get("id")
                        num_refs = database.get_blob_refcount(conn, blob_id)

                        database.remove_blob_from_template(
                            conn, template_id, blob_set, pos_set
                        )
                else:
                    self.log.error(
                        f'Failed to remove blob. Unknown dest: {dest["dest"]}'
                    )
                    return res

                if blob_data is None:
                    return res

                blob_hash = blob_data.get("hash")
                if num_refs == 1:
                    database.remove_blob(conn, blob_id)
                    self.remove_files_associated_to_a_blob(blob_hash)
                conn.commit()
                res = True
            except IPOLBlobsDataBaseError:
                conn.rollback()
                self.log.exception("DB error while removing blob.")
            except OSError:
                conn.rollback()
                self.log.exception("OS error while deleting blob file.")
            except IPOLRemoveDirError:
                # There is no need to do a rollback if the problem was deleting directories
                self.log.exception("Failed to remove directories.")
            except Exception:
                conn.rollback()
                self.log.exception("*** Unhandled exception while removing the blob.")
            finally:
                if conn is not None:
                    conn.close()
            return res

    def delete_blob_container(self, dest: str) -> bool:
        """
        Remove the demo or template and all the blobs only used by them
        """
        with lock:
            res = False
            conn = None
            ref_count = {}  # Number of uses for  a blob before removing
            try:
                conn = lite.connect(settings.blobs_database_file)
                if dest["dest"] == "demo":
                    demo_id = dest["demo_id"]
                    blobs = database.get_demo_owned_blobs(conn, demo_id)

                    for blob in blobs:
                        ref_count[blob["id"]] = database.get_blob_refcount(
                            conn, blob["id"]
                        )

                    database.remove_demo_blobs_association(conn, demo_id)
                    database.remove_demo(conn, demo_id)
                elif dest["dest"] == "template":
                    template_id = dest["id"]
                    blobs = database.get_template_blobs(conn, template_id)

                    for blob in blobs:
                        ref_count[blob["id"]] = database.get_blob_refcount(
                            conn, blob["id"]
                        )

                    database.remove_template_blobs_association(conn, template_id)
                    database.remove_template(conn, template_id)
                else:
                    self.log.error(
                        f'Failed to remove blob. Unknown dest: {dest["dest"]}'
                    )
                    return res

                for blob in blobs:
                    if ref_count[blob["id"]] == 1:
                        database.remove_blob(conn, blob["id"])
                        self.remove_files_associated_to_a_blob(blob["hash"])

                conn.commit()
                res = True
            except OSError:
                conn.rollback()
                self.log.exception("OS error while deleting blob file.")
            except IPOLRemoveDirError:
                # There is no need to do a rollback if the problem was deleting directories
                self.log.exception("Failed to remove directories.")
            except IPOLBlobsDataBaseError:
                conn.rollback()
                self.log.exception("DB error while removing the demo/template.")
            except Exception:
                conn.rollback()
                self.log.exception(
                    "*** Unhandled exception while removing the demo/template."
                )
            finally:
                if conn is not None:
                    conn.close()
            return res

    def remove_files_associated_to_a_blob(self, blob_hash: str) -> None:
        """
        This function removes the blob, the thumbnail and
        the visual representation from the hash given
        """
        subdir = self.get_subdir(blob_hash)

        blob_folder = os.path.join(settings.blobs_data_root, settings.blob_dir, subdir)
        thumb_folder = os.path.join(
            settings.blobs_data_root, settings.thumb_dir, subdir
        )
        vr_folder = os.path.join(settings.blobs_data_root, settings.vr_dir, subdir)

        blob_file = glob.glob(os.path.join(blob_folder, blob_hash + ".*"))
        thumb_file = glob.glob(os.path.join(thumb_folder, blob_hash + ".*"))
        vr_file = glob.glob(os.path.join(vr_folder, blob_hash + ".*"))

        # remove blob and its folder if necessary
        if blob_file:
            os.remove(blob_file[0])
            self.remove_dirs(blob_folder)

        # remove thumbnail and its folder if necessary
        if thumb_file:
            os.remove(thumb_file[0])
            self.remove_dirs(thumb_folder)

        # remove visual representation and its folder if necessary
        if vr_file:
            os.remove(vr_file[0])
            self.remove_dirs(vr_folder)

    def remove_dirs(self, blob_folder) -> None:
        """
        Remove all the empty directories
        """
        try:
            if not os.listdir(blob_folder):
                os.rmdir(blob_folder)
                self.remove_dirs(os.path.dirname(blob_folder))
        except Exception as ex:
            raise IPOLRemoveDirError(ex)

    def generate_set_name(self, blob_id: int) -> str:
        """
        Generate a unique set name for the given blob id
        """
        return "__" + str(blob_id)

    def edit_blob(
        self,
        blob_set: str,
        new_blob_set: str,
        pos_set: int,
        new_pos_set: int,
        title: str,
        credit: str,
        blob_vr: str,
        dest: str,
    ) -> bool:
        """
        Edit blob information
        """
        res = False
        conn = None

        try:
            conn = lite.connect(settings.blobs_database_file)
            if dest["dest"] == "demo":
                demo_id = dest["demo_id"]

                if new_blob_set != blob_set or new_pos_set != pos_set:
                    if database.is_pos_occupied_in_demo_set(
                        conn, demo_id, new_blob_set, new_pos_set
                    ):
                        editor_demo_id = database.get_demo_id(conn, demo_id)
                        new_pos_set = database.get_available_pos_in_demo_set(
                            conn, editor_demo_id, new_blob_set
                        )

                database.edit_blob_from_demo(
                    conn,
                    demo_id,
                    blob_set,
                    new_blob_set,
                    pos_set,
                    new_pos_set,
                    title,
                    credit,
                )
                blob_data = database.get_blob_data_from_demo(
                    conn, demo_id, new_blob_set, new_pos_set
                )
            elif dest["dest"] == "template":
                template_id = dest["id"]

                if new_blob_set != blob_set or new_pos_set != pos_set:
                    if database.is_pos_occupied_in_template_set(
                        conn, template_id, new_blob_set, new_pos_set
                    ):
                        new_pos_set = database.get_available_pos_in_template_set(
                            conn, template_id, new_blob_set
                        )

                database.edit_blob_from_template(
                    conn,
                    template_id,
                    blob_set,
                    new_blob_set,
                    pos_set,
                    new_pos_set,
                    title,
                    credit,
                )
                blob_data = database.get_blob_data_from_template(
                    conn, template_id, new_blob_set, new_pos_set
                )
            else:
                self.log.error(f'Failed to edit blob. Unknown dest: {dest["dest"]}')
                return res

            if blob_data is None:
                return res

            blob_hash = blob_data.get("hash")
            blob_id = blob_data.get("id")

            if blob_vr:
                self.delete_vr_from_blob(blob_id)

                _, vr_ext = self.get_format_and_extension(
                    self.get_blob_mime(blob_vr.file)
                )

                blob_file = self.copy_blob(
                    blob_vr.file, blob_hash, vr_ext, settings.vr_dir
                )
                try:
                    self.create_thumbnail(blob_file, blob_hash)
                except IPOLBlobsThumbnailError:
                    self.log.exception("Error creating the thumbnail.")
            conn.commit()
            res = True

        except IPOLBlobsDataBaseError:
            conn.rollback()
            self.log.exception("DB error while editing the blob.")
        except Exception:
            conn.rollback()
            self.log.exception("*** Unhandled exception while editing the blob.")
        finally:
            if conn is not None:
                conn.close()
        return res


def init_logging():
    """
    Initialize the error logs of the module.
    """
    logger = logging.getLogger("blobs_log")
    # handle all messages for the moment
    logger.setLevel(logging.DEBUG)
    handler = logging.FileHandler(os.path.join(settings.logs_dir, "error.log"))
    formatter = logging.Formatter(
        "%(asctime)s; [%(filename)s:%(lineno)s - %(funcName)20s() ] %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )
    handler.setFormatter(formatter)

    logger.addHandler(handler)
    return logger

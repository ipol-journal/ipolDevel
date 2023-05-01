#!/usr/bin/env python3
# -*- coding:utf-8 -*-

"""
This file implements the system core of the server
It implements Blob object and web service
"""
import configparser
import glob
import hashlib
import json
import logging
import mimetypes
import operator
import os
import re
import shutil
import sqlite3 as lite
from threading import Lock

import database
import magic
from errors import (
    IPOLBlobsDataBaseError,
    IPOLBlobsTemplateError,
    IPOLBlobsThumbnailError,
    IPOLRemoveDirError,
)
from fastapi import APIRouter, Depends, FastAPI, HTTPException, Request
from ipolutils.utils import thumbnail
from pydantic import BaseSettings


class Settings(BaseSettings):
    # Blobs
    blobs_dir: str = "staticData/blobs/"
    blobs_thumbs_dir: str = "staticData/blobs_thumbs/"
    # Database
    database_dir = "db"
    database_file: str = os.path.join("db", "blobs.db")
    module_dir: str = os.path.expanduser("~") + "/ipolDevel/ipol_demo/modules/blobs"
    logs_dir: str = "logs/"
    config_common_dir: str = (
        os.path.expanduser("~") + "/ipolDevel/ipol_demo/modules/config_common"
    )
    number_of_experiments_by_pages: int = 5
    authorized_patterns: str = "authorized_patterns.conf"

    # Paths
    blob_dir: str = "staticData/blob_directory"
    thumb_dir: str = "staticData/thumbnail"
    vr_dir: str = "staticData/visrep"


settings = Settings()
app = FastAPI()


def validate_ip(request: Request) -> bool:
    # Check if the request is coming from an allowed IP address
    patterns = []
    ip = request.headers["x-real-ip"]
    # try:
    for pattern in read_authorized_patterns():
        patterns.append(
            re.compile(pattern.replace(".", "\\.").replace("*", "[0-9a-zA-Z]+"))
        )
    for pattern in patterns:
        if pattern.match(ip) is not None:
            return True
    raise HTTPException(status_code=403, detail="IP not allowed")


private_route = APIRouter(dependencies=[Depends(validate_ip)])


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


def error_log(function_name: str, error: str) -> None:
    """
    Write an error log in the logs_dir defined in demo.conf
    """
    error_string = function_name + ": " + error
    log.error(error_string)


def init_database() -> bool:
    """
    Initialize the database used by the module if it doesn't exist.
    If the file is empty, the system delete it and create a new one.
    """

    if os.path.isfile(settings.database_file):
        file_info = os.stat(settings.database_file)

        if file_info.st_size == 0:
            try:
                os.remove(settings.database_file)
            except Exception as ex:
                log.exception("init_database: {}".format(ex))
                return False

    if not os.path.isfile(settings.database_file):
        try:
            conn = lite.connect(settings.database_file)
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

        except Exception as ex:
            log.exception("init_database: {}".format(ex))

            if os.path.isfile(settings.database_file):
                try:
                    os.remove(settings.database_file)
                except Exception as ex:
                    log.exception("init_database: {}".format(ex))
                    return False

    return True


@app.get("/ping", status_code=200)
def ping() -> dict[str, str]:
    """
    Ping service: answer with a pong.
    """
    return {"status": "OK", "ping": "pong"}


@app.on_event("shutdown")
def shutdown_event():
    log.info("Application shutdown")


def add_blob(
    blob, blob_set: str, pos_set: int, title: str, credit: str, dest: str, blob_vr
):
    """
    Copies the blob and store it in the DB
    """
    res = False
    conn = None
    try:
        conn = lite.connect(settings.database_file)
        mime = get_blob_mime(blob.file)

        blob_format, ext = get_format_and_extension(mime)
        # ext = "." + ext

        blob_hash = get_hash(blob.file)
        blob_id = store_blob(conn, blob.file, credit, blob_hash, ext, blob_format)

        try:
            if blob_vr:
                # If the user specified to use a new VR, then we use it
                _, vr_ext = get_format_and_extension(get_blob_mime(blob_vr.file))
                blob_file = copy_blob(blob_vr.file, blob_hash, vr_ext, settings.vr_dir)
                create_thumbnail(blob_file, blob_hash)
            else:
                # The user didn't give any new VR.
                # We'll update the thumbnail only if it doesn't have already a VR
                if not blob_has_VR(blob_hash):
                    blob_file = os.path.join(settings.blob_dir, get_subdir(blob_hash))
                    blob_file = os.path.join(blob_file, blob_hash + ext)
                    create_thumbnail(blob_file, blob_hash)

        except IPOLBlobsThumbnailError as ex:
            # An error in the creation of the thumbnail doesn't stop the execution of the method
            log.exception("Error creating the thumbnail")
            print("Couldn't create the thumbnail. Error: {}".format(ex))

        # If the set is empty the module generates an unique set name
        if not blob_set:
            blob_set = generate_set_name(blob_id)
            pos_set = 0

        if dest["dest"] == "demo":
            demo_id = dest["demo_id"]
            # Check if the pos is empty
            if database.is_pos_occupied_in_demo_set(conn, demo_id, blob_set, pos_set):
                editor_demo_id = database.get_demo_id(conn, demo_id)
                pos_set = database.get_available_pos_in_demo_set(
                    conn, editor_demo_id, blob_set
                )

            do_add_blob_to_demo(conn, demo_id, blob_id, blob_set, pos_set, title)
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

            do_add_blob_to_template(
                conn, template_id, blob_id, blob_set, pos_set, title
            )
            res = True
        else:
            log.error(
                "Failed to add the blob in add_blob. Unknown dest: {}".format(
                    dest["dest"]
                )
            )

    except IOError as ex:
        log.exception("Error copying uploaded blob")
        print("Couldn't copy uploaded blob. Error: {}".format(ex))
    except IPOLBlobsDataBaseError as ex:
        log.exception("Error adding blob info to DB")
        print("Couldn't add blob info to DB. Error: {}".format(ex))
    except IPOLBlobsTemplateError as ex:
        print(
            "Couldn't add blob to template. blob. Template doesn't exists. Error: {}".format(
                ex
            )
        )
    except Exception as ex:
        log.exception("*** Unhandled exception while adding the blob")
        print("*** Unhandled exception while adding the blob. Error: {}".format(ex))
    finally:
        if conn is not None:
            conn.close()

    return res


@private_route.post("/add_blob_to_demo", status_code=201)
def add_blob_to_demo(
    blob=None,
    demo_id: int = None,
    blob_set: str = None,
    pos_set: int = None,
    title: str = None,
    credit: str = None,
    blob_vr=None,
):
    """
    Adds a new blob to a demo
    """
    dest = {"dest": "demo", "demo_id": demo_id}
    if add_blob(blob, blob_set, pos_set, title, credit, dest, blob_vr):
        return json.dumps({"status": "OK"}).encode()

    return json.dumps({"status": "KO"}).encode()


@private_route.post("/add_blob_to_template", status_code=201)
def add_blob_to_template(
    blob=None,
    template_id: int = None,
    blob_set: str = None,
    pos_set: int = None,
    title: str = None,
    credit: str = None,
    blob_vr=None,
):
    """
    Adds a new blob to a template
    """
    dest = {"dest": "template", "template_id": template_id}

    if add_blob(blob, blob_set, pos_set, title, credit, dest, blob_vr):
        return json.dumps({"status": "OK"}).encode()
    return json.dumps({"status": "KO"}).encode()


def store_blob(
    conn, blob, credit: str, blob_hash: str, ext: str, blob_format: str
) -> int:
    """
    Stores the blob info in the DB, copy it in the file system and returns the blob_id and blob_file
    """
    blob_id = database.get_blob_id(conn, blob_hash)
    if blob_id is not None:
        # If the DB already have the hash there is no need to store the blob
        return blob_id

    try:
        copy_blob(blob, blob_hash, ext, settings.blob_dir)
        blob_id = database.store_blob(conn, blob_hash, blob_format, ext, credit)
        conn.commit()
        return blob_id
    except IPOLBlobsDataBaseError:
        conn.rollback()
        raise


@staticmethod
def get_blob_mime(blob) -> str:
    """
    Return format from blob
    """
    mime = magic.Magic(mime=True)
    blob.seek(0)
    blob_format = mime.from_buffer(blob.read())
    return blob_format


@staticmethod
def get_format_and_extension(mime: str) -> tuple[str, str]:
    """
    get format and extension from mime
    """
    mime_format = mime.split("/")[0]
    ext = mimetypes.guess_extension(mime)
    # some mime type maybe unknown, especially for exotic file format
    if not ext:
        ext = ".dat"
    return mime_format, ext


@staticmethod
def get_hash(blob) -> str:
    """
    Return the sha1 hash from blob
    """
    blob.seek(0)
    return hashlib.sha1(blob.read()).hexdigest()


def copy_blob(blob, blob_hash: str, ext: str, dst_dir: str) -> str:
    """
    Stores the blob in the file system, returns the dest path
    """
    dst_path = os.path.join(dst_dir, get_subdir(blob_hash))
    if not os.path.isdir(dst_path):
        os.makedirs(dst_path)
    dst_path = os.path.join(dst_path, blob_hash + ext)
    blob.seek(0)
    with open(dst_path, "wb") as f:
        shutil.copyfileobj(blob, f)
    return dst_path


@staticmethod
def get_subdir(blob_hash: str) -> str:
    """
    Returns the subdirectory from the blob hash
    """
    return os.path.join(blob_hash[0], blob_hash[1])


@staticmethod
def do_add_blob_to_demo(
    conn, demo_id: int, blob_id: int, pos_set: int, blob_set: str, blob_title: str
) -> None:
    """
    Associates the blob to a demo in the DB
    """
    try:
        if not database.demo_exist(conn, demo_id):
            database.create_demo(conn, demo_id)
        database.add_blob_to_demo(conn, demo_id, blob_id, pos_set, blob_set, blob_title)
        conn.commit()
    except IPOLBlobsDataBaseError:
        conn.rollback()
        raise


@staticmethod
def do_add_blob_to_template(
    conn, template_id: int, blob_id: int, blob_set: str, pos_set: int, blob_title: str
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


def create_thumbnail(src_file, blob_hash: str) -> None:
    """
    Creates a thumbnail for blob_file.
    """
    src_file = os.path.realpath(src_file)
    thumb_height = 256
    dst_path = os.path.join(settings.thumb_dir, get_subdir(blob_hash))
    if not os.path.isdir(dst_path):
        os.makedirs(dst_path)
    dst_file = os.path.join(dst_path, blob_hash + ".jpg")
    try:
        thumbnail(src_file, height=thumb_height, dst_file=dst_file)
    except Exception as ex:
        raise IPOLBlobsThumbnailError(
            "File '{}', thumbnail error. {}".format(src_file, ex)
        )


@private_route.post("/create_template", status_code=201)
def create_template(template_name: str) -> list:
    """
    Creates a new empty template
    """

    status = {"status": "KO"}
    conn = None
    try:
        conn = lite.connect(settings.database_file)
        result = database.template(conn, template_name)
        if result is not None and result["template_id"]:
            status = {"status": "OK", "template_id": result["template_id"]}
        else:
            template_id = database.create_template(conn, template_name)
            conn.commit()
            status = {"status": "OK", "template_id": template_id}

    except IPOLBlobsDataBaseError as ex:
        if conn is not None:
            conn.rollback()
        log.exception("Fail creating template {}".format(template_name))
        print("Couldn't create the template {}. Error: {}".format(template_name, ex))
    except Exception as ex:
        if conn is not None:
            conn.rollback()
        log.exception(
            "*** Unhandled exception while creating the template {}".format(
                template_name
            )
        )
        print(
            "*** Unhandled exception while creating the template {}. Error: {}".format(
                template_name, ex
            )
        )

    finally:
        if conn is not None:
            conn.close()
    return json.dumps(status).encode()


@private_route.post("/add_template_to_demo", status_code=201)
def add_template_to_demo(demo_id: int, template_id: int) -> list:
    """
    Associates the demo to the list of templates
    """
    status = {"status": "KO"}
    conn = None
    try:
        conn = lite.connect(settings.database_file)

        if not database.template_exist(conn, template_id):
            raise IPOLBlobsTemplateError("Not all the templates exist")

        if not database.demo_exist(conn, demo_id):
            database.create_demo(conn, demo_id)

        database.add_template_to_demo(conn, template_id, demo_id)
        conn.commit()
        status = {"status": "OK"}

    except IPOLBlobsDataBaseError as ex:
        if conn is not None:
            conn.rollback()
        log.exception(
            "Fails linking templates {} to the demo #{}".format(template_id, demo_id)
        )
        print(
            "Couldn't link templates {} to the demo #{}. Error: {}".format(
                template_id, demo_id, ex
            )
        )
    except IPOLBlobsTemplateError as ex:
        if conn is not None:
            conn.rollback()
        print(
            "Some of the templates {} does not exist. Error: {}".format(template_id, ex)
        )
    except Exception as ex:
        if conn is not None:
            conn.rollback()
        log.exception(
            "*** Unhandled exception while linking the templates {} to the demo #{}".format(
                template_id, demo_id
            )
        )
        print(
            "*** Unhandled exception while linking the templates {} to the demo #{}. Error:{}".format(
                template_id, demo_id, ex
            )
        )
    finally:
        if conn is not None:
            conn.close()
    return json.dumps(status).encode()


@app.get("/blobs/{demo_id}", status_code=200)
def get_blobs(demo_id: int) -> list:
    """
    Get all the blobs used by the demo: owned blobs and from templates
    """
    data = {"status": "KO"}
    conn = None
    try:
        # Validate demo_id
        try:
            demo_id = int(demo_id)
        except (TypeError, ValueError):
            return json.dumps(
                {"status": "KO", "error": "Invalid demo_id: {}".format(demo_id)}
            ).encode()

        conn = lite.connect(settings.database_file)

        demo_blobs = database.get_demo_owned_blobs(conn, demo_id)
        templates = database.get_demo_templates(conn, demo_id)
        sets = prepare_list(demo_blobs)
        for template in templates:
            sets += prepare_list(database.get_template_blobs(conn, template["id"]))

        data["sets"] = sets
        data["status"] = "OK"

    except IPOLBlobsDataBaseError as ex:
        log.exception("Fails obtaining all the blobs from demo #{}".format(demo_id))
        print(
            "Couldn't obtain all the blobs from demo #{}. Error: {}".format(demo_id, ex)
        )
    except Exception as ex:
        log.exception(
            "*** Unhandled exception while obtaining all the blobs from demo #{}".format(
                demo_id
            )
        )
        print(
            "*** Unhandled exception while obtaining all the blobs from demo #{}. Error: {}".format(
                demo_id, ex
            )
        )
    finally:
        if conn is not None:
            conn.close()
    return data


def prepare_list(blobs) -> dict:
    """
    Prepare the output list of blobs
    """
    sets = {}
    for blob in blobs:
        blob_set = blob["blob_set"]
        if blob_set in sets:
            sets[blob_set].append(get_blob_info(blob))
        else:
            sets[blob_set] = [get_blob_info(blob)]

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


@app.get("/templates/{template_id}", status_code=200)
def get_template_blobs(template_id: int) -> list:
    """
    Get the list of blobs in the given template
    """
    data = {"status": "KO"}
    conn = None
    try:
        conn = lite.connect(settings.database_file)

        if not database.template_exist(conn, template_id):
            # If the requested template doesn't exist the method will return a KO
            return data
        sets = prepare_list(database.get_template_blobs(conn, template_id))

        data["sets"] = sets
        data["status"] = "OK"

    except IPOLBlobsDataBaseError as ex:
        log.exception(
            "Fails obtaining the owned blobs from template '{}'".format(template_id)
        )
        print(
            "Couldn't obtain owned blobs from template '{}'. Error: {}".format(
                template_id, ex
            )
        )
    except Exception as ex:
        log.exception(
            "*** Unhandled exception while obtaining the owned blobs from template '{}'".format(
                template_id
            )
        )
        print(
            "*** Unhandled exception while obtaining the owned blobs from template '{}'. Error: {}".format(
                template_id, ex
            )
        )
    finally:
        if conn is not None:
            conn.close()
    return data


@app.get("/get_demo_owned_blobs", status_code=200)
def get_demo_owned_blobs(demo_id: int) -> list:
    """
    Get the list of owned blobs for the demo
    """
    data = {"status": "KO"}
    conn = None
    try:
        conn = lite.connect(settings.database_file)

        blobs = database.get_demo_owned_blobs(conn, demo_id)
        sets = prepare_list(blobs)
        data["sets"] = sets
        data["status"] = "OK"

    except IPOLBlobsDataBaseError as ex:
        log.exception("Fails obtaining the owned blobs from demo #{}".format(demo_id))
        print(
            "Couldn't obtain owned blobs from demo #{}. Error: {}".format(demo_id, ex)
        )
    except Exception as ex:
        log.exception(
            "*** Unhandled exception while obtaining the owned blobs from demo #{}".format(
                demo_id
            )
        )
        print(
            "*** Unhandled exception while obtaining the owned blobs from demo #{}. Error: {}".format(
                demo_id, ex
            )
        )
    finally:
        if conn is not None:
            conn.close()
    return data


def blob_has_thumbnail(blob_hash: str) -> str:
    """
    Check if the blob has already thumbnail
    """
    subdir = get_subdir(blob_hash)
    thumb_physical_dir = os.path.join(settings.thumb_dir, subdir)
    return os.path.isfile(
        os.path.join(settings.module_dir, thumb_physical_dir, blob_hash + ".jpg")
    )


def blob_has_VR(blob_hash: str) -> str:
    """
    Check if the blob is associated to a VR
    """
    subdir = get_subdir(blob_hash)
    vr_physical_dir = os.path.join(settings.vr_dir, subdir)
    vr_extension = get_vr_extension(
        os.path.join(settings.module_dir, vr_physical_dir), blob_hash
    )
    return vr_extension is not None


def get_blob_info(blob) -> list:
    """
    Return the required information from the blob
    """
    subdir = get_subdir(blob["hash"])
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

    if blob_has_thumbnail(blob["hash"]):
        blob_info["thumbnail"] = os.path.join(
            settings.module_dir, thumbnail_url, blob["hash"] + ".jpg"
        )

    vr_extension = get_vr_extension(
        os.path.join(settings.module_dir, vr_physical_dir), blob["hash"]
    )
    if vr_extension is not None:
        blob_info["vr"] = os.path.join(vr_url, blob["hash"] + vr_extension)

    return blob_info


@staticmethod
def get_vr_extension(vr_dir: str, blob_hash: str) -> str:
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


@app.get("/demo/{demo_id}", status_code=200)
def get_demo_templates(demo_id: int) -> list:
    """
    Get the list of templates used by the demo
    """
    data = {"status": "KO"}
    conn = None
    try:
        conn = lite.connect(settings.database_file)

        db_response = database.get_demo_templates(conn, demo_id)
        data["templates"] = db_response
        data["status"] = "OK"

    except IPOLBlobsDataBaseError as ex:
        log.exception(
            "Fails obtaining the owned templates from demo #{}".format(demo_id)
        )
        print(
            "Couldn't obtain owned templates from demo #{}. Error: {}".format(
                demo_id, ex
            )
        )
    except Exception as ex:
        log.exception(
            "*** Unhandled exception while obtaining the owned templates from demo #{}".format(
                demo_id
            )
        )
        print(
            "*** Unhandled exception while obtaining the owned templates from demo #{}. Error: {}".format(
                demo_id, ex
            )
        )
    finally:
        if conn is not None:
            conn.close()
    return data


def remove_blob(blob_set: str, pos_set: int, dest: str) -> bool:
    """
    Remove the blob
    """
    with Lock():
        res = False
        conn = None
        try:
            conn = lite.connect(settings.database_file)

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
                log.error(
                    "Failed to remove blob. Unknown dest: {}".format(dest["dest"])
                )
                return res

            if blob_data is None:
                return res

            blob_hash = blob_data.get("hash")
            if num_refs == 1:
                database.remove_blob(conn, blob_id)
                remove_files_associated_to_a_blob(blob_hash)
            conn.commit()
            res = True
        except IPOLBlobsDataBaseError as ex:
            conn.rollback()
            log.exception("DB error while removing blob")
            print("Failed to remove blob from DB. Error: {}".format(ex))
        except OSError as ex:
            conn.rollback()
            log.exception("OS error while deleting blob file")
            print("Failed to remove blob from file system. Error: {}".format(ex))
        except IPOLRemoveDirError as ex:
            # There is no need to do a rollback if the problem was deleting directories
            log.exception("Failed to remove directories")
            print("Failed to remove directories. Error: {}".format(ex))
        except Exception as ex:
            conn.rollback()
            log.exception("*** Unhandled exception while removing the blob")
            print(
                "*** Unhandled exception while removing the blob. Error: {}".format(ex)
            )
        finally:
            if conn is not None:
                conn.close()
        return res


@private_route.post("/remove_blob_from_demo", status_code=201)
def remove_blob_from_demo(demo_id: int, blob_set: str, pos_set: int) -> list:
    """
    Remove a blob from the demo
    """
    dest = {"dest": "demo", "demo_id": demo_id}
    if remove_blob(blob_set, pos_set, dest):
        return json.dumps({"status": "OK"}).encode()
    return json.dumps({"status": "KO"}).encode()


@private_route.post("/remove_blob_from_template", status_code=201)
def remove_blob_from_template(template_id: int, blob_set: str, pos_set: int) -> list:
    """
    Remove a blob from the template
    """
    dest = {"dest": "template", "template_id": template_id}
    if remove_blob(blob_set, pos_set, dest):
        return json.dumps({"status": "OK"}).encode()
    return json.dumps({"status": "KO"}).encode()


def delete_blob_container(dest: str) -> bool:
    """
    Remove the demo or template and all the blobs only used by them
    """
    with Lock():
        res = False
        conn = None
        ref_count = {}  # Number of uses for  a blob before removing
        try:
            conn = lite.connect(settings.database_file)
            if dest["dest"] == "demo":
                demo_id = dest["demo_id"]
                blobs = database.get_demo_owned_blobs(conn, demo_id)

                for blob in blobs:
                    ref_count[blob["id"]] = database.get_blob_refcount(conn, blob["id"])

                database.remove_demo_blobs_association(conn, demo_id)
                database.remove_demo(conn, demo_id)
            elif dest["dest"] == "template":
                template_id = dest["id"]
                blobs = database.get_template_blobs(conn, template_id)

                for blob in blobs:
                    ref_count[blob["id"]] = database.get_blob_refcount(conn, blob["id"])

                database.remove_template_blobs_association(conn, template_id)
                database.remove_template(conn, template_id)
            else:
                log.error(
                    "Failed to remove blob. Unknown dest: {}".format(dest["dest"])
                )
                return res

            for blob in blobs:
                if ref_count[blob["id"]] == 1:
                    database.remove_blob(conn, blob["id"])
                    remove_files_associated_to_a_blob(blob["hash"])

            conn.commit()
            res = True
        except OSError as ex:
            conn.rollback()
            log.exception("OS error while deleting blob file")
            print("Failed to remove blob from file system. Error: {}".format(ex))
        except IPOLRemoveDirError as ex:
            # There is no need to do a rollback if the problem was deleting directories
            log.exception("Failed to remove directories")
            print("Failed to remove directories. Error: {}".format(ex))
        except IPOLBlobsDataBaseError as ex:
            conn.rollback()
            log.exception("DB error while removing the demo/template")
            print("Failed to remove the demo/template. Error: {}".format(ex))
        except Exception as ex:
            conn.rollback()
            log.exception("*** Unhandled exception while removing the demo/template")
            print(
                "*** Unhandled exception while removing the demo/template. Error: {}".format(
                    ex
                )
            )
        finally:
            if conn is not None:
                conn.close()
        return res


@private_route.post("/delete_demo", status_code=201)
def delete_demo(demo_id: int) -> list:
    """
    Remove the demo
    """
    dest = {"dest": "demo", "demo_id": demo_id}
    if delete_blob_container(dest):
        return json.dumps({"status": "OK"}).encode()
    return json.dumps({"status": "KO"}).encode()


@private_route.post("/delete_template", status_code=201)
def delete_template(template_id: int) -> list:
    """
    Remove the template
    """
    dest = {"dest": "template", "id": template_id}
    if delete_blob_container(dest):
        return json.dumps({"status": "OK"}).encode()
    return json.dumps({"status": "KO"}).encode()


@private_route.post("/remove_template_from_demo", status_code=201)
def remove_template_from_demo(demo_id: int, template_id: int) -> list:
    """
    Remove the template from the demo
    """
    data = {"status": "KO"}
    conn = None
    try:
        conn = lite.connect(settings.database_file)
        if database.remove_template_from_demo(conn, demo_id, template_id):
            conn.commit()
            data["status"] = "OK"
    except IPOLBlobsDataBaseError as ex:
        conn.rollback()
        log.exception("DB error while removing the template from the demo")
        print("Failed to remove the template from the demo. Error: {}".format(ex))
    except Exception as ex:
        conn.rollback()
        log.exception(
            "*** Unhandled exception while removing the template from the demo"
        )
        print(
            "*** Unhandled exception while removing the template from the demo. Error: {}".format(
                ex
            )
        )
    finally:
        if conn is not None:
            conn.close()
    return data


def remove_files_associated_to_a_blob(blob_hash: str) -> None:
    """
    This function removes the blob, the thumbnail and
    the visual representation from the hash given
    """
    subdir = get_subdir(blob_hash)

    blob_folder = os.path.join(settings.module_dir, settings.blob_dir, subdir)
    thumb_folder = os.path.join(settings.module_dir, settings.thumb_dir, subdir)
    vr_folder = os.path.join(settings.module_dir, settings.vr_dir, subdir)

    blob_file = glob.glob(os.path.join(blob_folder, blob_hash + ".*"))
    thumb_file = glob.glob(os.path.join(thumb_folder, blob_hash + ".*"))
    vr_file = glob.glob(os.path.join(vr_folder, blob_hash + ".*"))

    # remove blob and its folder if necessary
    if blob_file:
        os.remove(blob_file[0])
        remove_dirs(blob_folder)

    # remove thumbnail and its folder if necessary
    if thumb_file:
        os.remove(thumb_file[0])
        remove_dirs(thumb_folder)

    # remove visual representation and its folder if necessary
    if vr_file:
        os.remove(vr_file[0])
        remove_dirs(vr_folder)


def remove_dirs(blob_folder) -> None:
    """
    Remove all the empty directories
    """
    try:
        if not os.listdir(blob_folder):
            os.rmdir(blob_folder)
            remove_dirs(os.path.dirname(blob_folder))
    except Exception as ex:
        raise IPOLRemoveDirError(ex)


@staticmethod
def generate_set_name(blob_id: int) -> str:
    """
    Generate a unique set name for the given blob id
    """
    return "__" + str(blob_id)


@private_route.post("/edit_blob_from_demo", status_code=201)
def edit_blob_from_demo(
    demo_id: int = None,
    blob_set: str = None,
    new_blob_set: str = None,
    pos_set: int = None,
    new_pos_set: int = None,
    title: str = None,
    credit: str = None,
    vr: str = None,
) -> list:
    """
    Edit blob information in a demo
    """
    dest = {"dest": "demo", "demo_id": demo_id}
    if edit_blob(blob_set, new_blob_set, pos_set, new_pos_set, title, credit, vr, dest):
        return json.dumps({"status": "OK"}).encode()
    return json.dumps({"status": "KO"}).encode()


@private_route.post("/edit_blob_from_template", status_code=201)
def edit_blob_from_template(
    template_id: int = None,
    blob_set: str = None,
    new_blob_set: str = None,
    pos_set: int = None,
    new_pos_set: int = None,
    title: str = None,
    credit: str = None,
    vr: str = None,
) -> list:
    """
    Edit blob information in a template
    """
    dest = {"dest": "template", "id": template_id}
    if edit_blob(blob_set, new_blob_set, pos_set, new_pos_set, title, credit, vr, dest):
        return json.dumps({"status": "OK"}).encode()
    return json.dumps({"status": "KO"}).encode()


def edit_blob(
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
        new_pos_set = int(new_pos_set)
    except Exception:
        log.error("new_pos_set needs to be an integer")
        return res

    try:
        conn = lite.connect(settings.database_file)
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
            log.error("Failed to edit blob. Unknown dest: {}".format(dest["dest"]))
            return res

        if blob_data is None:
            return res

        blob_hash = blob_data.get("hash")
        blob_id = blob_data.get("id")

        if blob_vr:
            delete_vr_from_blob(blob_id)

            _, vr_ext = get_format_and_extension(get_blob_mime(blob_vr.file))

            blob_file = copy_blob(blob_vr.file, blob_hash, vr_ext, settings.vr_dir)
            try:
                create_thumbnail(blob_file, blob_hash)
            except IPOLBlobsThumbnailError as ex:
                log.exception("Error creating the thumbnail")
                print("Couldn't create the thumbnail. Error: {}".format(ex))
        conn.commit()
        res = True

    except IPOLBlobsDataBaseError as ex:
        conn.rollback()
        log.exception("DB error while editing the blob")
        print("Failed editing the blob. Error: {}".format(ex))
    except Exception as ex:
        conn.rollback()
        log.exception("*** Unhandled exception while editing the blob")
        print("*** Unhandled exception while editing the blob. Error: {}".format(ex))
    finally:
        if conn is not None:
            conn.close()
    return res


@app.get("/templates", status_code=200)
def get_all_templates() -> list:
    """
    Return all the templates in the system
    """
    conn = None
    data = {"status": "KO"}
    try:
        conn = lite.connect(settings.database_file)
        data["templates"] = database.get_all_templates(conn)
        data["status"] = "OK"
    except IPOLBlobsDataBaseError as ex:
        log.exception("DB error while reading all the templates")
        print("Failed reading all the templates. Error: {}".format(ex))
    except Exception as ex:
        log.exception("*** Unhandled exception while reading all the templates")
        print(
            "*** Unhandled exception while reading all the templates. Error: {}".format(
                ex
            )
        )
    finally:
        if conn is not None:
            conn.close()
    return data


@private_route.post("/delete_vr_from_blob", status_code=201)
def delete_vr_from_blob(blob_id: int) -> list:
    """
    Remove the visual representation of the blob (in all the demos and templates)
    """
    data = {"status": "KO"}
    conn = None
    try:
        conn = lite.connect(settings.database_file)
        blob_data = database.get_blob_data(conn, blob_id)
        if blob_data is None:
            return data

        blob_hash = blob_data.get("hash")
        subdir = get_subdir(blob_hash)

        # Delete VR
        vr_folder = os.path.join(settings.vr_dir, subdir)
        if os.path.isdir(vr_folder):
            files_in_dir = glob.glob(os.path.join(vr_folder, blob_hash + ".*"))
            for f in files_in_dir:
                os.remove(f)
            remove_dirs(vr_folder)

        # Delete old thumbnail
        thumb_folder = os.path.join(settings.module_dir, settings.thumb_dir, subdir)
        if os.path.isdir(thumb_folder):
            thumb_files_in_dir = glob.glob(os.path.join(thumb_folder, blob_hash + ".*"))
            if thumb_files_in_dir:
                os.remove(thumb_files_in_dir[0])
                remove_dirs(thumb_folder)

        # Creates the new thumbnail with the blob (if it is possible)
        try:
            blob_folder = os.path.join(settings.blob_dir, subdir)
            if os.path.isdir(blob_folder):
                blobs_in_dir = glob.glob(os.path.join(blob_folder, blob_hash + ".*"))
                if blobs_in_dir:
                    create_thumbnail(blobs_in_dir[0], blob_hash)
        except IPOLBlobsThumbnailError as ex:
            log.exception("Error creating the thumbnail")
            print("Couldn't create the thumbnail. Error: {}".format(ex))

    except IPOLBlobsDataBaseError as ex:
        log.exception("DB error while removing the visual representation")
        print("Failed removing the visual representation. Error: {}".format(ex))
    except Exception as ex:
        mess = "*** Unhandled exception while removing the visual representation."
        log.exception(mess)
        print("{} Error: {}".format(mess, ex))
    finally:
        if conn is not None:
            conn.close()

    data["status"] = "OK"
    return data


@private_route.post("/update_demo_id/{old_demo_id}", status_code=201)
def update_demo_id(old_demo_id: int, new_demo_id: int) -> list:
    """
    Update an old demo ID by the given new ID
    """
    conn = None
    data = {"status": "KO"}
    try:
        conn = lite.connect(settings.database_file)
        database.update_demo_id(conn, old_demo_id, new_demo_id)
        data["status"] = "OK"
        conn.commit()
    except IPOLBlobsDataBaseError as ex:
        conn.rollback()
        log.exception("DB error while updating demo id")
        print("Failed while updating demo id. Error: {}".format(ex))
    except Exception as ex:
        conn.rollback()
        log.exception("*** Unhandled exception while updating demo id")
        print("*** Unhandled exception while updating demo id. Error: {}".format(ex))
    finally:
        if conn is not None:
            conn.close()
    return data


@app.get("/demos_using_template/{template_id}", status_code=200)
def get_demos_using_the_template(template_id: int) -> list:
    """
    Return the list of demos that use the given template
    """
    conn = None
    data = {"status": "KO"}
    try:
        conn = lite.connect(settings.database_file)
        data["demos"] = database.get_demos_using_the_template(conn, template_id)
        data["status"] = "OK"
    except IPOLBlobsDataBaseError as ex:
        log.exception(
            "DB operation failed while getting the list of demos that uses the template"
        )
        print(
            "DB operation failed while getting the list of demos that uses the template. Error: {}".format(
                ex
            )
        )
    except Exception as ex:
        conn.rollback()
        log.exception(
            "*** Unhandled exception while getting the list of demos that uses the template"
        )
        print(
            "*** Unhandled exception while getting the list of demos that uses the template. Error: {}".format(
                ex
            )
        )
    finally:
        if conn is not None:
            conn.close()
    return data


@app.get("/stats", status_code=200)
def stats() -> list:
    """
    Return module stats
    """
    conn = None
    data = {"status": "KO"}
    try:
        conn = lite.connect(settings.database_file)
        data["nb_templates"] = len(database.get_all_templates(conn))
        data["nb_blobs"] = database.get_nb_of_blobs(conn)
        data["status"] = "OK"
    except Exception as ex:
        log.exception("*** Unhandled exception while getting the blobs stats")
        print(
            "*** Unhandled exception while getting the blobs stats. Error: {}".format(
                ex
            )
        )
    finally:
        if conn is not None:
            conn.close()
    return data


def read_authorized_patterns() -> list:
    """
    Read from the IPs conf file
    """
    # Check if the config file exists
    authorized_patterns_path = os.path.join(
        settings.config_common_dir, settings.authorized_patterns
    )
    if not os.path.isfile(authorized_patterns_path):
        log.exception(
            f"read_authorized_patterns: \
                      File {authorized_patterns_path} doesn't exist"
        )
        return []

    # Read config file
    try:
        cfg = configparser.ConfigParser()
        cfg.read([authorized_patterns_path])
        patterns = []
        for item in cfg.items("Patterns"):
            patterns.append(item[1])
        return patterns
    except configparser.Error:
        log.exception(f"Bad format in {authorized_patterns_path}")
        return []


app.include_router(private_route)

log = init_logging()
init_database()
init_database()

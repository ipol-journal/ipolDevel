#!/usr/bin/env python
import configparser
import errno
import hashlib
import json
import logging
import os
import os.path
import re
import shutil
import sqlite3 as lite
import traceback
from collections import OrderedDict
from datetime import datetime
from typing import Union

import magic
from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import JSONResponse
from pydantic import BaseModel, BaseSettings


class Settings(BaseSettings):
    blobs_dir: str = "staticData/blobs/"
    blobs_thumbs_dir: str = "staticData/blobs_thumbs/"
    database_file: str = os.path.join("db", "archive.db")
    logs_dir: str = "logs/"
    config_common_dir: str = (
        os.path.expanduser("~") + "/ipolDevel/ipol_demo/modules/config_common"
    )
    number_of_experiments_by_pages: str = 5
    authorized_patterns: str = "authorized_patterns.conf"


settings = Settings()
app = FastAPI()


class Experiment(BaseModel):
    demo_id: int
    blobs: Union[str, None] = None
    parameters: Union[str, None] = None
    execution: Union[str, None] = None


# TODO since we now use systemd this method makes no sense anymore
@app.on_event("shutdown")
def shutdown_event():
    log.info("Application shutdown")


@app.get("/ping", status_code=200)
def ping() -> dict:
    """
    Ping service: answer with a pong.
    """
    return {"status": "OK", "ping": "pong"}


@app.get("/stats", status_code=200)
def stats() -> dict:
    """
    return the stats of the module.
    """
    data = {}
    conn = None
    try:
        conn = lite.connect(settings.database_file)
        cursor_db = conn.cursor()

        cursor_db.execute(
            """
            SELECT
            (SELECT COUNT(*) FROM experiments),
            (SELECT COUNT(*) FROM blobs)
            """
        )
        results = cursor_db.fetchall()
        data["nb_experiments"] = results[0][0]
        data["nb_blobs"] = results[0][1]

    except Exception as ex:
        message = "Failure in stats function. Error: {}".format(ex)
        print(message)
        log.exception(message)
    finally:
        if conn is not None:
            conn.close()

    return data


# TODO change this name
# TODO No usage?
@app.get("/executions_per_demo", status_code=200)
def executions_per_demo() -> dict:
    """
    return the number of executions per demo
    """
    conn = None
    try:
        conn = lite.connect(settings.database_file)
        cursor_db = conn.cursor()

        cursor_db.execute(
            """
            SELECT id_demo, COUNT(*)
            FROM experiments
            GROUP BY id_demo
        """
        )
        data = {id: nb for id, nb in cursor_db.fetchall()}

    except Exception as ex:
        message = "Failure in stats function. Error: {}".format(ex)
        print(message)
        log.exception(message)
    finally:
        if conn is not None:
            conn.close()

    return data


# TODO only used in archive tests
@app.get("/demo_list", status_code=200)
def demo_list() -> dict:
    """
    Return the list of demos with at least one experiment
    """
    demo_list = []
    try:
        conn = lite.connect(settings.database_file)
        cursor_db = conn.cursor()
        cursor_db.execute(
            """
        SELECT DISTINCT id_demo FROM experiments"""
        )

        for row in cursor_db.fetchall():
            demoid = row[0]
            demo_list.append(demoid)

        conn.close()
    except Exception as ex:
        message = "Failure in demo_list. Error = {}".format(ex)
        log.exception(message)
        raise HTTPException(status_code=404, detail=message)
    return {"demo_list": demo_list}


@app.post("/experiment", status_code=201)
def create_experiment(experiment: Experiment) -> dict:
    """
    Add an experiment to the archive.
    """
    demo_id = int(experiment.demo_id)
    # # initialize list of copied files, to delete them in case of exception
    copied_files_list = []
    try:
        conn = lite.connect(settings.database_file)
        id_experiment = update_exp_table(
            conn, demo_id, experiment.parameters, experiment.execution
        )
        dict_corresp = []
        dict_corresp = update_blob(conn, experiment.blobs, copied_files_list)
        update_correspondence_table(conn, id_experiment, dict_corresp)
        conn.commit()
        conn.close()
    except Exception as ex:
        message = "Failure in add_experiment. Error = {}".format(ex)
        log.exception(message)
        try:
            # Execute database rollback
            conn.rollback()
            conn.close()

            # Execute deletion of copied files
            for copied_file in copied_files_list:
                os.remove(copied_file)

        except Exception:
            pass

    return {"experiment_id": id_experiment}


@app.get("/experiment/{experiment_id}", status_code=200)
def get_experiment(experiment_id: int) -> dict:
    """
    Get a single experiment
    """
    conn = None
    try:
        conn = lite.connect(settings.database_file)
        cursor_db = conn.cursor()
        cursor_db.execute(
            """SELECT params, execution, timestamp
            FROM experiments WHERE id = ?""",
            (experiment_id,),
        )
        row = cursor_db.fetchone()
        if row:
            experiment = get_data_experiment(
                conn, experiment_id, row[0], row[1], row[2]
            )
        else:
            message = "Experiment not found"
            raise HTTPException(status_code=404, detail=message)
        conn.close()
    except Exception:
        log.exception("Error getting experiment #{}".format(experiment_id))

        if conn is not None:
            conn.close()
        raise HTTPException(status_code=404, detail=message)

    return experiment


# TODO Unused?
@app.put("/experiment/{experiment_id}", status_code=200)
def update_experiment_date(experiment_id: int, date: datetime, date_format: str) -> dict:
    """
    MIGRATION
    Update the date of an experiment.
    This is used when migrating demos from the old system to this.
    """
    try:
        conn = lite.connect(settings.database_file)
        cursor_db = conn.cursor()

        cursor_db.execute(
            """
        UPDATE experiments
        SET timestamp = ?
        WHERE id = ?
        """,
            (datetime.strptime(date, date_format), experiment_id),
        )

        conn.commit()
        conn.close()

    except Exception as ex:
        message = "Failed to update the date of experiment #{}: {}".format(ex, date)
        log.exception(message)
        if conn:
            conn.rollback()
            conn.close()
        raise HTTPException(status_code=404, detail=message)

    return {"experiment_id": experiment_id}


@app.get("/page/{page}", status_code=200)
def get_page(demo_id: int, page: int = 0) -> dict:
    """
    This function return all the information needed
    to build the given page for the given demo.
    if the page number is not in the range [1,number_of_pages],
    the last page is used
    """
    try:
        conn = lite.connect(settings.database_file)
        meta_info = get_meta_info(conn, demo_id)
        meta_info["id_demo"] = demo_id

        if meta_info["number_of_experiments"] == 0:
            return {"meta_info": meta_info, "experiments": {}}
        if page > meta_info["number_of_pages"] or page <= 0:
            page = meta_info["number_of_pages"]
        experiments = get_experiment_page(conn, demo_id, page)

        conn.close()
    except Exception:
        log.exception("Error getting page #{} from demo #{}".format(demo_id, page))
        try:
            conn.close()
        except Exception:
            pass

    return {"meta_info": meta_info, "experiments": experiments}


# @authenticate
@app.delete("/experiment/{experiment_id}", status_code=204)
def delete_experiment(experiment_id: int) -> None:
    """
    Remove an experiment
    """
    try:
        conn = lite.connect(settings.database_file)
        if delete_exp_w_deps(conn, experiment_id) > 0:
            conn.commit()
            conn.close()

    except Exception:
        log.exception("Error deleting experiment #{}".format(experiment_id))
        print(traceback.format_exc())
        try:
            conn.rollback()
            conn.close()
        except Exception:
            pass


# TODO Used only by archive tests
# @authenticate
@app.delete("/blob/{blob_id}", status_code=204)
def delete_blob_w_deps(blob_id: int) -> None:
    """
    Remove a blob
    """
    try:
        conn = lite.connect(settings.database_file)
        cursor_db = conn.cursor()
        list_tmp = []

        for row in cursor_db.execute(
            """
            SELECT id_experiment FROM correspondence WHERE id_blob = ?""",
            (blob_id,),
        ):
            tmp = row[0]
            list_tmp.append(tmp)

        for value in list_tmp:
            delete_exp_w_deps(conn, value)

        conn.commit()
        conn.close()
    except Exception:
        log.exception("Error deleting experiment with dependencies #{}".format(blob_id))
        try:
            conn.rollback()
            conn.close()
        except Exception:
            pass


# authenticate
@app.delete("/demo/{demo_id}", status_code=204)
def delete_demo(demo_id: int) -> None:
    """
    Delete the demo from the archive.
    """
    try:
        # Get all experiments for this demo
        conn = lite.connect(settings.database_file)
        cursor_db = conn.cursor()
        cursor_db.execute(
            "SELECT DISTINCT id FROM experiments WHERE id_demo = ?", (demo_id,)
        )

        experiment_id_list = cursor_db.fetchall()

        if not experiment_id_list:
            return None

        # Delete experiments and files
        for experiment_id in experiment_id_list:
            delete_exp_w_deps(conn, experiment_id[0])
        conn.commit()
        conn.close()

    except Exception:
        log.exception(f"Error deleting demo #{demo_id}")
        raise HTTPException(status_code=404, detail=f"Error deleting demo {demo_id}")

    return None


@app.put("/demo/{demo_id}", status_code=204)
def update_demo_id(demo_id: int, new_demo_id: int) -> None:
    """
    Change the given old demo ID by the new demo ID
    """
    conn = None
    try:
        if demo_id != new_demo_id:
            conn = lite.connect(settings.database_file)
            cursor_db = conn.cursor()
            cursor_db.execute(
                """
            UPDATE experiments
            SET id_demo = ?
            WHERE id_demo = ?
            """,
                (new_demo_id, demo_id),
            )

            conn.commit()
            conn.close()
        return None

    except Exception as ex:
        log.exception(
            "Error changing demo ID (#{} --> #{})".format(demo_id, new_demo_id)
        )
        if conn is not None:
            conn.rollback()
            conn.close()
        raise HTTPException(status_code=500, detail=f"blobs update_demo_id error: {ex}")


def delete_exp_w_deps(conn, experiment_id: int) -> int:
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

    purge_unique_blobs(conn, ids_blobs, experiment_id)

    cursor_db.execute("DELETE FROM experiments WHERE id = ?", (experiment_id,))
    n_changes = cursor_db.rowcount
    cursor_db.execute(
        "DELETE FROM correspondence WHERE id_experiment = ?", (experiment_id,)
    )
    return n_changes


def purge_unique_blobs(conn, ids_blobs: int, experiment_id: int) -> None:
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
            delete_blob(conn, blob)


def delete_blob(conn, id_blob: int) -> None:
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
        path_blob, _ = get_new_path(settings.blobs_dir, tmp[1], tmp[2])
        path_thumb, _ = get_new_path(settings.blobs_thumbs_dir, tmp[1], "jpeg")

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


def get_hash_blob(path: str) -> str:
    """
    Return sha1 hash of given blob
    """
    with open(path, "rb") as the_file:
        return hashlib.sha1(the_file.read()).hexdigest()


def file_format(the_file: str) -> str:
    """
    Return format of the file
    """
    mime = magic.Magic(mime=True)
    fileformat = mime.from_file(the_file)
    fileformat = fileformat.split("/")[0]
    return fileformat


def init_logging():
    """
    Initialize the error logs of the module.
    """
    logger = logging.getLogger("archive_log")
    logger.setLevel(logging.ERROR)
    handler = logging.FileHandler(os.path.join(settings.logs_dir, "error.log"))
    formatter = logging.Formatter(
        "%(asctime)s ERROR in %(message)s", datefmt="%Y-%m-%d %H:%M:%S"
    )
    handler.setFormatter(formatter)
    logger.addHandler(handler)
    return logger


def init_database() -> bool:
    """
    Initialize the database used by the module if it doesn't exist.
    If the file is empty, the system delete it and create a new one.
    """
    if os.path.isfile(settings.database_file):
        file_info = os.stat(settings.database_file)

        if file_info.st_size == 0:
            print(str(settings.database_file) + " is empty. Removing the file...")
            try:
                log.error("init_database: Database file was empty")
                os.remove(settings.database_file)
            except Exception as ex:
                message = "Error in init_database. Error = {}".format(ex)
                log.exception(message)
                return False

            print("Creating a correct new database")

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
            message = "Error in init_database. Error = {}".format(ex)
            log.exception(message)
            if os.path.isfile(settings.database_file):
                try:
                    os.remove(settings.database_file)
                except Exception as ex:
                    message = "Error in init_database. Error = {}".format(ex)
                    log.exception(message)
                    return False

    return True


#####
# adding an experiment to the archive database
#####


def get_new_path(
    main_directory: str, hash_name: str, file_extension: str, depth: int = 2
) -> :
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


def copy_file_in_folder(original_path, main_dir, hash_file, extension) -> str:
    """
    Write a file in its respective folder
    """
    try:
        final_path, _ = get_new_path(main_dir, hash_file, extension)
        if not os.path.exists(final_path):
            shutil.copyfile(original_path, final_path)
        return final_path
    except Exception as ex:
        message = "Failure in copy_file_in_folder. Error={}".format(ex)
        log.exception(message)
        print(message)
        raise


def add_blob_in_the_database(
    conn, hash_file: str, type_file: str, format_file: str
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
        log.exception(message)
        raise


def add_blob(conn, blob_dict, copied_files_list: list) -> None:
    """
    This function checks if a blob exists in the table. If it exists,
    the id is returned. If not, the blob is added, then the id is returned.
    """
    # List of copied files. Useful to delete them if an exception is thrown
    # copied_files = []
    try:
        thumb_key = list(key for key, value in blob_dict.items() if "thumbnail" in key)
        if thumb_key:
            blob_thumbnail_name = thumb_key[0]
            blob_thumbnail_path = blob_dict[blob_thumbnail_name]
            del blob_dict[blob_thumbnail_name]

        blob_name = list(blob_dict.keys())[0]
        blob_path = list(blob_dict.values())[0]

        # If the file doesn't exist, just return None
        if not os.path.isfile(blob_path):
            return None, None

        hash_file = get_hash_blob(blob_path)
        format_file = file_format(blob_path)

        _, type_file = os.path.splitext(blob_path)
        type_file = type_file.split(".")[1]
        type_file.lower()

        id_blob = add_blob_in_the_database(conn, hash_file, type_file, format_file)
        # copy the files in their respective folders
        path_new_blob = copy_file_in_folder(
            blob_path, settings.blobs_dir, hash_file, type_file
        )
        copied_files_list.append(path_new_blob)
        if thumb_key:
            path_new_thumbnail = copy_file_in_folder(
                blob_thumbnail_path, settings.blobs_thumbs_dir, hash_file, "jpeg"
            )
            copied_files_list.append(path_new_thumbnail)

        return id_blob, blob_name
    except Exception as ex:
        message = "Failure in add_blob. Error = {}".format(ex)
        log.exception(message)
        print(message)
        raise


def update_exp_table(conn, demo_id: int, parameters: str, execution: str) -> int:
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


def update_blob(conn, blobs: dict, copied_files_list: list) -> dict:
    """
    This function updates the blobs table.
    It return a dictionary of data to be added to the correspondences table.
    """
    try:
        id_blob = int()
        dict_blobs = json.loads(blobs)
        dict_corresp = []

        for blob_element in dict_blobs:
            id_blob, blob_name = add_blob(conn, blob_element, copied_files_list)
            dict_corresp.append({"blob_id": id_blob, "blob_name": blob_name})

    except Exception as ex:
        log.exception("update_blob. Error {}".format(ex))
        raise

    return dict_corresp


def update_correspondence_table(conn, id_experiment: int, dict_corresp: dict) -> None:
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


def get_dict_file(path_file, path_thumb: str, name: str, id_blob: int) -> dict:
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


def get_experiment_page(conn, demo_id: int, page: int) -> list:
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
        data_exp.append(get_data_experiment(conn, row[0], row[1], row[2], row[3]))

    return data_exp


def get_data_experiment(
    conn, id_exp: int, parameters: str, execution: str, date: datetime
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
            path_file, subdirs = get_new_path(settings.blobs_dir, row[0], row[1])
            thumb_dir = "{}{}".format(settings.blobs_thumbs_dir, subdirs)
            thumb_name = "{}.jpeg".format(row[0])
            path_thumb = os.path.join(thumb_dir, thumb_name)
            list_files.append(get_dict_file(path_file, path_thumb, row[2], row[3]))

        dict_exp["id"] = id_exp
        dict_exp["date"] = date
        dict_exp["parameters"] = json.loads(parameters, object_pairs_hook=OrderedDict)
        dict_exp["execution"] = execution
        dict_exp["files"] = list_files
        return dict_exp
    except Exception as ex:
        message = "Failure in get_data_experiment. Error = {}".format(ex)
        print(message)
        log.exception(message)
        raise


def get_meta_info(conn, id_demo: int) -> list:
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


@app.middleware("http")
async def validate_ip(request: Request, call_next):
    # Check if the request is coming from an allowed IP address
    patterns = []
    ip = request.client.host
    try:
        for pattern in read_authorized_patterns():
            patterns.append(
                re.compile(pattern.replace(".", "\\.").replace("*", "[0-9a-zA-Z]+"))
            )
        for pattern in patterns:
            if pattern.match(ip) is not None:
                response = await call_next(request)
                return response
        raise HTTPException(status_code=403, detail="IP not allowed")
    except HTTPException as e:
        return JSONResponse(content={"error": str(e.detail)}, status_code=403)


log = init_logging()
init_database()

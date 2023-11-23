import logging
import sqlite3 as lite
import traceback
from datetime import datetime
from typing import Union

from archive import archive
from config import settings
from fastapi import APIRouter, Depends, HTTPException
from guards import validate_ip
from pydantic import BaseModel
from result import Err

archiveRouter = APIRouter(prefix="/archive")
archive = archive.Archive()


class Experiment(BaseModel):
    demo_id: int
    blobs: Union[str, None] = None
    parameters: Union[str, None] = None
    execution: Union[str, None] = None


class Stored_Experiment(BaseModel):
    id: int
    date: datetime
    parameters: dict = None
    execution: str
    files: list


@archiveRouter.on_event("shutdown")
def shutdown_event():
    logging.info("Application shutdown")


@archiveRouter.get("/ping", status_code=200)
def ping() -> dict[str, str]:
    """
    Ping service: answer with a pong.
    """
    return {"status": "OK", "ping": "pong"}


@archiveRouter.get("/stats", status_code=200)
def stats() -> dict[str, int]:
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
        logging.exception(message)
    finally:
        if conn is not None:
            conn.close()

    return data


@archiveRouter.get("/executions_per_demo", status_code=200)
def executions_per_demo() -> dict[str, int]:
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
        logging.exception(message)
    finally:
        if conn is not None:
            conn.close()

    return data


# Only used in archive tests
@archiveRouter.get("/demo_list", status_code=200)
def demo_list() -> dict[str, list]:
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
        logging.exception(message)
        raise HTTPException(status_code=404, detail=message)
    return {"demo_list": demo_list}


@archiveRouter.post("/experiment", dependencies=[Depends(validate_ip)], status_code=201)
def create_experiment(experiment: Experiment) -> dict[str, int]:
    """
    Add an experiment to the archive.
    """
    result = archive.create_experiment(
        experiment.demo_id,
        experiment.blobs,
        experiment.parameters,
        experiment.execution,
    )
    if isinstance(result, Err):
        raise HTTPException(status_code=500, detail=result.value)
    return result.value


@archiveRouter.get("/experiment/{experiment_id}", status_code=200)
def get_experiment(experiment_id: int) -> Stored_Experiment:
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
            experiment = archive.get_data_experiment(
                conn, experiment_id, row[0], row[1], row[2]
            )
        else:
            message = "Experiment not found"
            raise HTTPException(status_code=404, detail=message)
        conn.close()
    except Exception:
        logging.exception("Error getting experiment #{}".format(experiment_id))

        if conn is not None:
            conn.close()
        raise HTTPException(status_code=404, detail=message)

    return experiment


@archiveRouter.put(
    "/experiment/{experiment_id}", dependencies=[Depends(validate_ip)], status_code=200
)
def update_experiment_date(
    experiment_id: int, date: datetime, date_format: str
) -> dict[str, int]:
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
        logging.exception(message)
        if conn:
            conn.rollback()
            conn.close()
        raise HTTPException(status_code=404, detail=message)

    return {"experiment_id": experiment_id}


@archiveRouter.get("/page/{page}", status_code=200)
def get_page(demo_id: int, page: int = 0) -> dict:
    """
    This function return all the information needed
    to build the given page for the given demo.
    if the page number is not in the range [1,number_of_pages],
    the last page is used
    """
    try:
        conn = lite.connect(settings.database_file)
        meta_info = archive.get_meta_info(conn, demo_id)
        meta_info["id_demo"] = demo_id

        if meta_info["number_of_experiments"] == 0:
            return {"meta_info": meta_info, "experiments": {}}
        if page > meta_info["number_of_pages"] or page <= 0:
            page = meta_info["number_of_pages"]
        experiments = archive.get_experiment_page(conn, demo_id, page)

        conn.close()
    except Exception:
        logging.exception("Error getting page #{} from demo #{}".format(demo_id, page))
        try:
            conn.close()
        except Exception:
            pass

    return {"meta_info": meta_info, "experiments": experiments}


@archiveRouter.delete(
    "/experiment/{experiment_id}", dependencies=[Depends(validate_ip)], status_code=204
)
def delete_experiment(experiment_id: int) -> None:
    """
    Remove an experiment
    """
    try:
        conn = lite.connect(settings.database_file)
        if archive.delete_exp_w_deps(conn, experiment_id) > 0:
            conn.commit()
            conn.close()

    except Exception:
        logging.exception("Error deleting experiment #{}".format(experiment_id))
        print(traceback.format_exc())
        try:
            conn.rollback()
            conn.close()
        except Exception:
            pass


# Used only by archive tests
@archiveRouter.delete(
    "/blob/{blob_id}", dependencies=[Depends(validate_ip)], status_code=204
)
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
            archive.delete_exp_w_deps(conn, value)

        conn.commit()
        conn.close()
    except Exception:
        logging.exception(
            "Error deleting experiment with dependencies #{}".format(blob_id)
        )
        try:
            conn.rollback()
            conn.close()
        except Exception:
            pass


@archiveRouter.delete(
    "/demo/{demo_id}", dependencies=[Depends(validate_ip)], status_code=204
)
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
            archive.delete_exp_w_deps(conn, experiment_id[0])
        conn.commit()
        conn.close()

    except Exception:
        logging.exception(f"Error deleting demo #{demo_id}")
        raise HTTPException(status_code=404, detail=f"Error deleting demo {demo_id}")

    return None


@archiveRouter.put("/demo/{demo_id}", status_code=204)
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
        logging.exception(
            "Error changing demo ID (#{} --> #{})".format(demo_id, new_demo_id)
        )
        if conn is not None:
            conn.rollback()
            conn.close()
        raise HTTPException(status_code=500, detail=f"blobs update_demo_id error: {ex}")

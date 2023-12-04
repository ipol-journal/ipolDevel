import glob
import logging
import os
import sqlite3 as lite

from blobs import blobs
from config import settings
from fastapi import APIRouter, Depends, HTTPException, UploadFile
from guards import validate_ip
from result import Err

from . import database
from .errors import IPOLBlobsDataBaseError, IPOLBlobsThumbnailError

blobsRouter = APIRouter(prefix="/blobs")
blobs = blobs.Blobs()


@blobsRouter.get("/ping", status_code=200)
def ping() -> dict[str, str]:
    """
    Ping service: answer with a pong.
    """
    return {"status": "OK", "ping": "pong"}


@blobsRouter.on_event("shutdown")
def shutdown_event():
    logging.info("blobsRouterlication shutdown")


@blobsRouter.post(
    "/demo_blobs/{demo_id}", dependencies=[Depends(validate_ip)], status_code=201
)
def add_blob_to_demo(
    blob: UploadFile,
    demo_id: int,
    title: str,
    blob_set: str = None,
    pos_set: int = None,
    credit: str = None,
    blob_vr: UploadFile = None,
):
    """
    Adds a new blob to a demo
    """
    dest = {"dest": "demo", "demo_id": demo_id}
    if blobs.add_blob(blob, blob_set, pos_set, title, credit, dest, blob_vr):
        return None
    message = f"error adding blob to demo {demo_id}"
    raise HTTPException(status_code=404, detail=message)


@blobsRouter.post(
    "/template_blobs/{template_id}",
    dependencies=[Depends(validate_ip)],
    status_code=201,
)
def add_blob_to_template(
    template_id: int,
    title: str,
    blob: UploadFile,
    blob_set: str = None,
    pos_set: int = None,
    credit: str = None,
    blob_vr: UploadFile = None,
):
    """
    Adds a new blob to a template
    """
    dest = {"dest": "template", "template_id": template_id}

    if blobs.add_blob(blob, blob_set, pos_set, title, credit, dest, blob_vr):
        return None
    message = f"error adding blob to template {template_id}"
    raise HTTPException(status_code=404, detail=message)


@blobsRouter.post("/templates", dependencies=[Depends(validate_ip)], status_code=201)
def create_template(template_name: str) -> dict:
    """
    Creates a new empty template
    """

    conn = None
    try:
        conn = lite.connect(settings.blobs_database_file)
        result = database.template(conn, template_name)
        if result is not None and result["template_id"]:
            return {"template_id": result["template_id"]}

        template_id = database.create_template(conn, template_name)
        conn.commit()
        return {"template_id": template_id}

    except IPOLBlobsDataBaseError:
        if conn is not None:
            conn.rollback()
        logging.exception(f"Fail creating template {template_name}.")
    except Exception:
        if conn is not None:
            conn.rollback()
        logging.exception(
            f"*** Unhandled exception while creating the template {template_name}."
        )

    finally:
        if conn is not None:
            conn.close()


@blobsRouter.post(
    "/add_template_to_demo/{demo_id}",
    dependencies=[Depends(validate_ip)],
    status_code=201,
)
def add_template_to_demo(demo_id: int, template_id: int) -> None:
    """
    Associates the demo to the list of templates
    """
    with blobs.get_db_connection() as conn:
        if not database.template_exist(conn, template_id):
            message = f"Template {template_id} not found"
            raise HTTPException(status_code=404, detail=message)

        if not database.demo_exist(conn, demo_id):
            database.create_demo(conn, demo_id)

        database.add_template_to_demo(conn, template_id, demo_id)
        conn.commit()
        return None


# TODO Create endpoint to get a single blob given the demo_id, blob_pos and set_name


@blobsRouter.get("/demo_blobs/{demo_id}", status_code=200)
def get_blobs(demo_id: int) -> list:
    """
    Get all the blobs used by the demo: owned blobs and from templates
    """
    result = blobs.get_blobs(demo_id)
    if isinstance(result, Err):
        raise HTTPException(status_code=500, detail=result.value)
    return result.value


@blobsRouter.get("/templates", status_code=200)
def get_all_templates() -> list:
    """
    Return all the templates in the system
    """
    conn = None
    try:
        conn = lite.connect(settings.blobs_database_file)
        return database.get_all_templates(conn)
    except IPOLBlobsDataBaseError:
        logging.exception("DB error while reading all the templates.")
    except Exception:
        logging.exception("*** Unhandled exception while reading all the templates.")
    finally:
        if conn is not None:
            conn.close()


@blobsRouter.get("/templates/{template_id}", status_code=200)
def get_template_blobs(template_id: int) -> list:
    """
    Get the list of blobs in the given template
    """
    with blobs.get_db_connection() as conn:
        if not database.template_exist(conn, template_id):
            message = f"Template {template_id} not found"
            raise HTTPException(status_code=404, detail=message)

        return blobs.prepare_list(database.get_template_blobs(conn, template_id))


@blobsRouter.get("/demo_owned_blobs/{demo_id}", status_code=200)
def get_demo_owned_blobs(demo_id: int) -> list:
    """
    Get the list of owned blobs for the demo
    """
    conn = None
    try:
        conn = lite.connect(settings.blobs_database_file)

        demo_blobs = database.get_demo_owned_blobs(conn, demo_id)
        return blobs.prepare_list(demo_blobs)

    except IPOLBlobsDataBaseError:
        logging.exception(f"Fails obtaining the owned blobs from demo #{demo_id}.")
    except Exception:
        logging.exception(
            f"*** Unhandled exception while obtaining the owned blobs from demo #{demo_id}."
        )
    finally:
        if conn is not None:
            conn.close()


@blobsRouter.get("/demo_templates/{demo_id}", status_code=200)
def get_demo_templates(demo_id: int) -> list:
    """
    Get the list of templates used by the demo
    """
    with blobs.get_db_connection() as conn:
        return database.get_demo_templates(conn, demo_id)


@blobsRouter.delete(
    "/demo_blobs/{demo_id}", dependencies=[Depends(validate_ip)], status_code=204
)
def remove_blob_from_demo(demo_id: int, blob_set: str, pos_set: int) -> None:
    """
    Remove a blob from the demo
    """
    dest = {"dest": "demo", "demo_id": demo_id}
    blobs.remove_blob(blob_set, pos_set, dest)


@blobsRouter.delete(
    "/template_blobs/{template_id}",
    dependencies=[Depends(validate_ip)],
    status_code=204,
)
def remove_blob_from_template(template_id: int, blob_set: str, pos_set: int) -> None:
    """
    Remove a blob from the template
    """
    dest = {"dest": "template", "template_id": template_id}
    blobs.remove_blob(blob_set, pos_set, dest)


@blobsRouter.delete(
    "/demos/{demo_id}", dependencies=[Depends(validate_ip)], status_code=204
)
def delete_demo(demo_id: int) -> None:
    """
    Remove the demo
    """
    dest = {"dest": "demo", "demo_id": demo_id}
    blobs.delete_blob_container(dest)


@blobsRouter.delete(
    "/templates/{template_id}", dependencies=[Depends(validate_ip)], status_code=204
)
def delete_template(template_id: int) -> None:
    """
    Remove the template
    """
    dest = {"dest": "template", "id": template_id}
    blobs.delete_blob_container(dest)


@blobsRouter.delete(
    "/demo_templates/{demo_id}", dependencies=[Depends(validate_ip)], status_code=204
)
def remove_template_from_demo(demo_id: int, template_id: int) -> None:
    """
    Remove the template from the demo
    """
    with blobs.get_db_connection() as conn:
        if database.remove_template_from_demo(conn, demo_id, template_id):
            conn.commit()
    return None


@blobsRouter.put(
    "/demo_blobs/{demo_id}", dependencies=[Depends(validate_ip)], status_code=204
)
def edit_blob_from_demo(
    demo_id: int = None,
    blob_set: str = None,
    new_blob_set: str = None,
    pos_set: int = None,
    new_pos_set: int = None,
    title: str = None,
    credit: str = None,
    vr: UploadFile = None,
) -> None:
    """
    Edit blob information in a demo
    """
    dest = {"dest": "demo", "demo_id": demo_id}
    if blobs.edit_blob(
        blob_set, new_blob_set, pos_set, new_pos_set, title, credit, vr, dest
    ):
        return None
    message = f"Error updating blob on demo {demo_id}"
    raise HTTPException(status_code=404, detail=message)


@blobsRouter.put(
    "/template_blobs/{template_id}",
    dependencies=[Depends(validate_ip)],
    status_code=204,
)
def edit_blob_from_template(
    template_id: int = None,
    blob_set: str = None,
    new_blob_set: str = None,
    pos_set: int = None,
    new_pos_set: int = None,
    title: str = None,
    credit: str = None,
    vr: UploadFile = None,
) -> None:
    """
    Edit blob information in a template
    """
    dest = {"dest": "template", "id": template_id}
    if blobs.edit_blob(
        blob_set, new_blob_set, pos_set, new_pos_set, title, credit, vr, dest
    ):
        return None
    message = f"error updating blob on template {template_id}"
    raise HTTPException(status_code=404, detail=message)


@blobsRouter.delete(
    "/visual_representations/{blob_id}",
    dependencies=[Depends(validate_ip)],
    status_code=204,
)
def delete_vr_from_blob(blob_id: int) -> None:
    """
    Remove the visual representation of the blob (in all the demos and templates)
    """
    conn = None
    try:
        conn = lite.connect(settings.blobs_database_file)
        blob_data = database.get_blob_data(conn, blob_id)
        if blob_data is None:
            return None

        blob_hash = blob_data.get("hash")
        subdir = blobs.get_subdir(blob_hash)

        # Delete VR
        vr_folder = os.path.join(settings.vr_dir, subdir)
        if os.path.isdir(vr_folder):
            files_in_dir = glob.glob(os.path.join(vr_folder, blob_hash + ".*"))
            for f in files_in_dir:
                os.remove(f)
            blobs.remove_dirs(vr_folder)

        # Delete old thumbnail
        thumb_folder = os.path.join(
            settings.blobs_data_root, settings.thumb_dir, subdir
        )
        if os.path.isdir(thumb_folder):
            thumb_files_in_dir = glob.glob(os.path.join(thumb_folder, blob_hash + ".*"))
            if thumb_files_in_dir:
                os.remove(thumb_files_in_dir[0])
                blobs.remove_dirs(thumb_folder)

        # Creates the new thumbnail with the blob (if it is possible)
        try:
            blob_folder = os.path.join(settings.blob_dir, subdir)
            if os.path.isdir(blob_folder):
                blobs_in_dir = glob.glob(os.path.join(blob_folder, blob_hash + ".*"))
                if blobs_in_dir:
                    blobs.create_thumbnail(blobs_in_dir[0], blob_hash)
        except IPOLBlobsThumbnailError:
            logging.exception("Error creating the thumbnail.")

    except IPOLBlobsDataBaseError:
        logging.exception("DB error while removing the visual representation.")
    except Exception:
        mess = "*** Unhandled exception while removing the visual representation."
        logging.exception(mess)
    finally:
        if conn is not None:
            conn.close()

    return None


@blobsRouter.put(
    "/demos/{old_demo_id}", dependencies=[Depends(validate_ip)], status_code=201
)
def update_demo_id(old_demo_id: int, new_demo_id: int) -> None:
    """
    Update an old demo ID by the given new ID
    """
    conn = None
    try:
        conn = lite.connect(settings.blobs_database_file)
        database.update_demo_id(conn, old_demo_id, new_demo_id)
        conn.commit()
    except IPOLBlobsDataBaseError:
        conn.rollback()
        logging.exception("DB error while updating demo id.")
    except Exception:
        conn.rollback()
        logging.exception("*** Unhandled exception while updating demo id.")
    finally:
        if conn is not None:
            conn.close()


@blobsRouter.get("/demos_using_template/{template_id}", status_code=200)
def get_demos_using_the_template(template_id: int) -> list:
    """
    Return the list of demos that use the given template
    """
    conn = None
    try:
        conn = lite.connect(settings.blobs_database_file)
        return database.get_demos_using_the_template(conn, template_id)
    except IPOLBlobsDataBaseError:
        logging.exception(
            "DB operation failed while getting the list of demos that uses the template."
        )
    except Exception:
        conn.rollback()
        logging.exception(
            "*** Unhandled exception while getting the list of demos that uses the template."
        )
    finally:
        if conn is not None:
            conn.close()


@blobsRouter.get("/stats", status_code=200)
def stats() -> dict:
    """
    Return module stats
    """
    conn = None
    data = {}
    try:
        conn = lite.connect(settings.blobs_database_file)
        data["nb_templates"] = len(database.get_all_templates(conn))
        data["nb_blobs"] = database.get_nb_of_blobs(conn)
    except Exception:
        logging.exception("*** Unhandled exception while getting the blobs stats.")
    finally:
        if conn is not None:
            conn.close()
    return data

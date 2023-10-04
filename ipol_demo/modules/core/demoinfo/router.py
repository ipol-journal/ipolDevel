import configparser
import json
import logging
import os
import re
from typing import Any, Dict

from config import settings
from fastapi import (
    APIRouter,
    Body,
    Depends,
    File,
    Form,
    HTTPException,
    Request,
    Response,
    UploadFile,
    status,
)
from result import Err, Ok

demoinfoRouter = APIRouter(prefix="/demoinfo")


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


def read_authorized_patterns() -> list:
    """
    Read from the IPs conf file
    """
    # Check if the config file exists
    authorized_patterns_path = os.path.join(
        settings.config_common_dir, settings.authorized_patterns
    )
    if not os.path.isfile(authorized_patterns_path):
        logger.exception(
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
        logger.exception(f"Bad format in {authorized_patterns_path}")
        return []


def init_logging():
    """
    Initialize the error logs of the module.
    """
    logger = logging.getLogger("demoinfo")

    logger.setLevel(logging.DEBUG)
    handler = logging.StreamHandler()
    formatter = logging.Formatter(
        "%(asctime)s; [%(filename)s:%(lineno)s - %(funcName)20s() ] %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )
    handler.setFormatter(formatter)

    logger.addHandler(handler)
    return logger


@demoinfoRouter.delete(
    "/demoextras/{demo_id}", dependencies=[Depends(validate_ip)], status_code=204
)
def delete_demoextras(demo_id: int):
    result = settings.demoinfo.delete_demoextras(demo_id)

    if not result.is_ok():
        logger.exception(result.value)
        raise HTTPException(status_code=500, detail=result.value)


@demoinfoRouter.post(
    "/demoextras/{demo_id}", dependencies=[Depends(validate_ip)], status_code=201
)
def add_demoextras(
    demo_id: int, demoextras_name: str = Form(...), demoextras: UploadFile = File(...)
):
    demoextras = demoextras.file.read()
    result = settings.demoinfo.add_demoextras(demo_id, demoextras, demoextras_name)
    if isinstance(result, Err):
        raise HTTPException(status_code=500, detail=result.value)


@demoinfoRouter.get("/demoextras/{demo_id}", status_code=200)
def get_demo_extras_info(demo_id: int):
    result = settings.demoinfo.get_demo_extras_info(demo_id)
    if isinstance(result, Ok):
        data = {}
        if result.value is not None:
            data.update(**result.value)
    else:
        data = {"error": result.value}
    return data


@demoinfoRouter.get("/demos", status_code=200)
def demo_list() -> list:
    result = settings.demoinfo.demo_list()
    if isinstance(result, Ok):
        data = result.value
    else:
        data = {"error": result.value}
    return data


@demoinfoRouter.get("/demo_list_by_editorid/{editorid}", status_code=200)
def demo_list_by_editorid(editorid: int):
    result = settings.demoinfo.demo_list_by_editorid(editorid)
    if isinstance(result, Ok):
        data = result.value
    else:
        data = {"error": result.value}
    return data


@demoinfoRouter.get("/demo_list_pagination_and_filter", status_code=201)
def demo_list_pagination_and_filter(
    num_elements_page: int, page: int = 1, qfilter: str = None
):
    result = settings.demoinfo.demo_list_pagination_and_filter(
        num_elements_page, page, qfilter
    )
    if isinstance(result, Ok):
        data = {}
        data.update(**result.value)
    else:
        data = {"error": result.value}
    return data


@demoinfoRouter.get(
    "/demos/{demo_id}/editors", dependencies=[Depends(validate_ip)], status_code=200
)
def demo_get_editors_list(demo_id: int):
    result = settings.demoinfo.demo_get_editors_list(demo_id)
    if isinstance(result, Ok):
        data = result.value
    else:
        data = {"error": result.value}
    return data


@demoinfoRouter.get(
    "/available_editors/{demo_id}",
    dependencies=[Depends(validate_ip)],
    status_code=200,
)
def demo_get_available_editors_list(demo_id: int):
    result = settings.demoinfo.demo_get_available_editors_list(demo_id)
    if isinstance(result, Ok):
        data = result.value
    else:
        data = {"error": result.value}
    return data


@demoinfoRouter.get("/demo_metainfo/{demo_id}", status_code=200)
def read_demo_metainfo(demo_id: int):
    result = settings.demoinfo.read_demo_metainfo(demo_id)
    if isinstance(result, Ok):
        data = {}
        data.update(**result.value)
    else:
        data = {"error": result.value}
    return data


@demoinfoRouter.post("/demo", dependencies=[Depends(validate_ip)], status_code=201)
def add_demo(demo_id: int, title: str, state: str, ddl: str = None) -> dict:
    result = settings.demoinfo.add_demo(demo_id, title, state, ddl)
    if isinstance(result, Ok):
        data = {"demo_id": result.value}
    else:
        data = {"error": result.value}
    return data


@demoinfoRouter.patch(
    "/demo/{old_demo_id}", dependencies=[Depends(validate_ip)], status_code=201
)
def update_demo(
    old_demo_id: int,
    demo_id: int = Form(),
    state: str = Form(),
    title: str = Form(None),
):
    demo_dict = {"demo_id": demo_id, "state": state, "title": title}
    result = settings.demoinfo.update_demo(demo_dict, old_demo_id)
    if isinstance(result, Ok):
        data = {"demo_id": demo_id}
    else:
        data = {"error": result.value}
    return data


@demoinfoRouter.get("/editors", dependencies=[Depends(validate_ip)], status_code=200)
def editor_list():
    result = settings.demoinfo.editor_list()
    if isinstance(result, Ok):
        data = result.value
    else:
        data = {"error": result.value}
    return data


@demoinfoRouter.get("/editor", dependencies=[Depends(validate_ip)], status_code=200)
def get_editor(email: str, response: Response):
    result = settings.demoinfo.get_editor(email)
    if isinstance(result, Ok):
        data: dict[str, Any] = {}
        if editor := result.value:
            data["editor"] = editor
        if editor is None:
            response.status_code = status.HTTP_204_NO_CONTENT
    else:
        data = {"error": result.value}
    return data


@demoinfoRouter.patch("/editor", dependencies=[Depends(validate_ip)], status_code=201)
def update_editor_email(new_email: str, old_email: str, name: str):
    result = settings.demoinfo.update_editor_email(new_email, old_email, name)
    if isinstance(result, Ok):
        data = {}
        if message := result.value:
            data["message"] = message
    else:
        data = {"error": result.value}
    return data


@demoinfoRouter.post("/editor", dependencies=[Depends(validate_ip)], status_code=201)
def add_editor(name: str, mail: str):
    result = settings.demoinfo.add_editor(name, mail)
    if isinstance(result, Ok):
        data = {}
    else:
        data = {"error": result.value}
    return data


@demoinfoRouter.delete(
    "/editor/{editor_id}", dependencies=[Depends(validate_ip)], status_code=204
)
def remove_editor(editor_id: int):
    result = settings.demoinfo.remove_editor(editor_id)
    if isinstance(result, Ok):
        return
    else:
        data = {"error": result.value}
        return data


@demoinfoRouter.post(
    "/demos/{demo_id}/editor/{editor_id}",
    dependencies=[Depends(validate_ip)],
    status_code=201,
)
def add_editor_to_demo(demo_id: int, editor_id: int):
    result = settings.demoinfo.add_editor_to_demo(demo_id, editor_id)
    if isinstance(result, Ok):
        data = {}
    else:
        data = {"error": result.value}
    return data


@demoinfoRouter.delete(
    "/demos/{demo_id}/editor/{editor_id}",
    dependencies=[Depends(validate_ip)],
    status_code=204,
)
def remove_editor_from_demo(demo_id: int, editor_id: int):
    result = settings.demoinfo.remove_editor_from_demo(demo_id, editor_id)
    if isinstance(result, Ok):
        data = {}
    else:
        data = {"error": result.value}
    return data


@demoinfoRouter.get(
    "/ddl_history/{demo_id}", dependencies=[Depends(validate_ip)], status_code=200
)
def get_ddl_history(demo_id: int):
    result = settings.demoinfo.get_ddl_history(demo_id)
    if isinstance(result, Ok):
        data = result.value
    else:
        data = {"error": result.value}
    return data


@demoinfoRouter.get(
    "/ddl/{demo_id}", dependencies=[Depends(validate_ip)], status_code=200
)
def get_ddl(demo_id: int):
    result = settings.demoinfo.get_ddl(demo_id)
    if isinstance(result, Ok):
        data = json.loads(result.value)
    else:
        data = {"error": result.value}
    return data


@demoinfoRouter.post(
    "/ddl/{demo_id}", dependencies=[Depends(validate_ip)], status_code=201
)
def save_ddl(demo_id: int, ddl: Dict[str, Any] = Body()):
    ddl_text = json.dumps(ddl, ensure_ascii=False, indent=3).encode("utf-8")
    result = settings.demoinfo.save_ddl(demo_id, ddl_text)
    if isinstance(result, Ok):
        data = {}
    else:
        data = {"error": result.value}
    return data


@demoinfoRouter.get("/get_interface_ddl", status_code=200)
def get_interface_ddl(demo_id: int, sections=None):
    result = settings.demoinfo.get_interface_ddl(demo_id, sections)
    if isinstance(result, Ok):
        data = {
            "last_demodescription": {
                "ddl": result.value,
            },
        }
    else:
        data = {"error": result.value}
    return data


@demoinfoRouter.get(
    "/ssh_keys/{demo_id}", dependencies=[Depends(validate_ip)], status_code=200
)
def get_ssh_keys(demo_id: int):
    result = settings.demoinfo.get_ssh_keys(demo_id)
    if isinstance(result, Ok):
        pubkey, privkey = result.value
        data = {
            "pubkey": pubkey,
            "privkey": privkey,
        }
    else:
        data = {"error": result.value}
    return data


@demoinfoRouter.get(
    "/reset_ssh_keys/{demo_id}", dependencies=[Depends(validate_ip)], status_code=200
)
def reset_ssh_keys(demo_id: int):
    result = settings.demoinfo.reset_ssh_keys(demo_id)
    if isinstance(result, Ok):
        data = {}
    else:
        data = {"error": result.value}
    return data


@demoinfoRouter.get("/stats", dependencies=[Depends(validate_ip)], status_code=200)
def stats():
    result = settings.demoinfo.stats()
    if isinstance(result, Ok):
        data = {}
        data.update(**result.value)
    else:
        data = {"error": result.value}
    return data


logger = init_logging()
logger = init_logging()

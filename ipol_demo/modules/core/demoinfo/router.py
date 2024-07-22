import json
from typing import Any, Dict

from config import settings
from demoinfo import demoinfo
from fastapi import (
    APIRouter,
    Body,
    Depends,
    File,
    Form,
    HTTPException,
    Response,
    UploadFile,
    status,
)
from guards import validate_ip
from logger import logger
from result import Err, Ok

demoinfoRouter = APIRouter(prefix="/demoinfo")
demoinfo = demoinfo.DemoInfo(
    dl_extras_dir=settings.demoinfo_dl_extras_dir,
    database_path=settings.demoinfo_db,
    base_url=settings.base_url,
)


@demoinfoRouter.delete(
    "/demoextras/{demo_id}", dependencies=[Depends(validate_ip)], status_code=204
)
def delete_demoextras(demo_id: int):
    result = demoinfo.delete_demoextras(demo_id)

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
    result = demoinfo.add_demoextras(demo_id, demoextras, demoextras_name)
    if isinstance(result, Err):
        raise HTTPException(status_code=500, detail=result.value)


@demoinfoRouter.get("/demoextras/{demo_id}", status_code=200)
def get_demo_extras_info(demo_id: int):
    result = demoinfo.get_demo_extras_info(demo_id)
    if isinstance(result, Ok):
        data = {}
        if result.value is not None:
            data.update(**result.value)
    else:
        data = {"error": result.value}
    return data


@demoinfoRouter.get("/demos", status_code=200)
def demo_list() -> list:
    result = demoinfo.demo_list()
    if isinstance(result, Ok):
        data = result.value
    else:
        data = {"error": result.value}
    return data


@demoinfoRouter.get("/demo_list_by_editorid/{editorid}", status_code=200)
def demo_list_by_editorid(editorid: int):
    result = demoinfo.demo_list_by_editorid(editorid)
    if isinstance(result, Ok):
        data = result.value
    else:
        data = {"error": result.value}
    return data


@demoinfoRouter.get("/demo_list_pagination_and_filter", status_code=201)
def demo_list_pagination_and_filter(
    num_elements_page: int, page: int = 1, qfilter: str = None
):
    result = demoinfo.demo_list_pagination_and_filter(num_elements_page, page, qfilter)
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
    result = demoinfo.demo_get_editors_list(demo_id)
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
    result = demoinfo.demo_get_available_editors_list(demo_id)
    if isinstance(result, Ok):
        data = result.value
    else:
        data = {"error": result.value}
    return data


@demoinfoRouter.get("/demo_metainfo/{demo_id}", status_code=200)
def read_demo_metainfo(demo_id: int):
    result = demoinfo.read_demo_metainfo(demo_id)
    if isinstance(result, Ok):
        data = {}
        data.update(**result.value)
    else:
        data = {"error": result.value}
    return data


@demoinfoRouter.post("/demo", dependencies=[Depends(validate_ip)], status_code=201)
def add_demo(demo_id: int, title: str, state: str, ddl: str = None) -> dict:
    result = demoinfo.add_demo(demo_id, title, state, ddl)
    print(result)
    if isinstance(result, Ok):
        data = {"demo_id": result.value}
    else:
        data = {"error": result.value}
        raise HTTPException(status_code=409, detail=data)
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
    result = demoinfo.update_demo(demo_dict, old_demo_id)
    if isinstance(result, Ok):
        data = {"demo_id": demo_id}
    else:
        data = {"error": result.value}
    return data


@demoinfoRouter.get("/editors", dependencies=[Depends(validate_ip)], status_code=200)
def editor_list():
    result = demoinfo.editor_list()
    if isinstance(result, Ok):
        data = result.value
    else:
        data = {"error": result.value}
    return data


@demoinfoRouter.get("/editor", dependencies=[Depends(validate_ip)], status_code=200)
def get_editor(email: str, response: Response):
    result = demoinfo.get_editor(email)
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
    result = demoinfo.update_editor_email(new_email, old_email, name)
    if isinstance(result, Ok):
        data = {}
        if message := result.value:
            data["message"] = message
    else:
        data = {"error": result.value}
    return data


@demoinfoRouter.post("/editor", dependencies=[Depends(validate_ip)], status_code=201)
def add_editor(name: str, mail: str):
    result = demoinfo.add_editor(name, mail)
    if isinstance(result, Ok):
        data = {}
    else:
        data = {"error": result.value}
    return data


@demoinfoRouter.delete(
    "/editor/{editor_id}", dependencies=[Depends(validate_ip)], status_code=204
)
def remove_editor(editor_id: int):
    result = demoinfo.remove_editor(editor_id)
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
    result = demoinfo.add_editor_to_demo(demo_id, editor_id)
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
    result = demoinfo.remove_editor_from_demo(demo_id, editor_id)
    if isinstance(result, Ok):
        data = {}
    else:
        data = {"error": result.value}
    return data


@demoinfoRouter.get(
    "/ddl_history/{demo_id}", dependencies=[Depends(validate_ip)], status_code=200
)
def get_ddl_history(demo_id: int):
    result = demoinfo.get_ddl_history(demo_id)
    if isinstance(result, Ok):
        data = result.value
    else:
        data = {"error": result.value}
    return data


@demoinfoRouter.get(
    "/ddl/{demo_id}", dependencies=[Depends(validate_ip)], status_code=200
)
def get_ddl(demo_id: int):
    result = demoinfo.get_ddl(demo_id)
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
    result = demoinfo.save_ddl(demo_id, ddl_text)
    if isinstance(result, Ok):
        data = {}
    else:
        data = {"error": result.value}
    return data


@demoinfoRouter.get("/get_interface_ddl", status_code=200)
def get_interface_ddl(demo_id: int, sections=None):
    result = demoinfo.get_interface_ddl(demo_id, sections)
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
    result = demoinfo.get_ssh_keys(demo_id)
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
    result = demoinfo.reset_ssh_keys(demo_id)
    if isinstance(result, Ok):
        data = {}
    else:
        data = {"error": result.value}
    return data


@demoinfoRouter.get("/stats", status_code=200)
def stats():
    result = demoinfo.stats()
    if isinstance(result, Ok):
        data = {}
        data.update(**result.value)
    else:
        data = {"error": result.value}
    return data

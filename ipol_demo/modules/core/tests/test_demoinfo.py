import json
import os

import pytest
from demoinfo.demoinfo import DemoInfo

demo_id = 0
demo_title = "Demo test"
state = "test"

editor_name = "Editor Test"
editor_email = "editortestmail@email.com"

ROOT = os.path.dirname(os.path.abspath(__file__)) + "/../../../.."
demo_extras_file = os.path.join(ROOT, "ci_tests/resources/test_demo_extras.tar.gz")


@pytest.fixture
def ddl() -> str:
    ddl_file = os.path.join(ROOT, "ci_tests/resources/test_ddl.txt")
    with open(ddl_file, "r") as f:
        ddl = f.read()
    return ddl


@pytest.fixture
def demoinfo(tmpdir) -> DemoInfo:
    db_path = str(tmpdir / "db.db")
    return DemoInfo(
        dl_extras_dir=str(tmpdir),
        database_path=db_path,
        base_url="http://localhost",
    )


def test_add_and_delete_demo(demoinfo: DemoInfo):
    demoinfo.add_demo(demo_id, demo_title, state).unwrap()

    result = demoinfo.read_demo_metainfo(demo_id)
    info = result.unwrap()
    assert info["title"] == demo_title

    demoinfo.delete_demo(demo_id).unwrap()


def test_add_same_demo_again(demoinfo: DemoInfo):
    demoinfo.add_demo(demo_id, demo_title, state).unwrap()

    result = demoinfo.add_demo(demo_id, demo_title, state)
    assert result.is_err()


def test_delete_non_existent_demo(demoinfo: DemoInfo):
    demoinfo.delete_demo(demo_id).unwrap()


def test_add_ddl_to_new_demo(demoinfo: DemoInfo, ddl: str):
    demoinfo.add_demo(demo_id, demo_title, state).unwrap()
    demoinfo.save_ddl(demo_id, ddl).unwrap()

    ddl_read = demoinfo.get_ddl(demo_id).unwrap()
    assert json.loads(ddl_read) == json.loads(ddl)


def test_get_interface_ddl(demoinfo: DemoInfo, ddl: str):
    demoinfo.add_demo(demo_id, demo_title, state).unwrap()
    demoinfo.save_ddl(demo_id, ddl).unwrap()

    ddl_read = demoinfo.get_interface_ddl(demo_id, sections="inputs,archive").unwrap()
    assert set(ddl_read.keys()) == {"inputs", "archive"}

    ddl_read = demoinfo.get_interface_ddl(
        demo_id, sections="inputs,archive,build,unknown"
    ).unwrap()
    assert set(ddl_read.keys()) == {"inputs", "archive"}

    ddl_read = demoinfo.get_interface_ddl(demo_id).unwrap()
    assert set(ddl_read.keys()) == {"general", "archive", "results", "inputs", "params"}

    result = demoinfo.get_interface_ddl(demo_id + 2)
    assert result.is_err()


def test_add_ddl_to_non_existent_demo(demoinfo, ddl):
    result = demoinfo.save_ddl(demo_id, ddl)
    assert result.is_err()


def test_add_demoextras_to_new_demo(demoinfo: DemoInfo):
    demoinfo.add_demo(demo_id, demo_title, state).unwrap()

    with open(demo_extras_file, "rb") as demo_extras:
        demo_extras_name = os.path.basename(demo_extras.name)
        demoinfo.add_demoextras(demo_id, demo_extras.read(), demo_extras_name).unwrap()
        extras_name = demo_extras.name

    result = demoinfo.get_demo_extras_info(demo_id)
    info = result.unwrap()
    assert info is not None
    assert info["size"] == os.stat(extras_name).st_size


def test_add_demoextras_to_non_existent_demo(demoinfo: DemoInfo):
    with open(demo_extras_file, "rb") as demo_extras:
        demo_extras_name = os.path.basename(demo_extras.name)
        result = demoinfo.add_demoextras(demo_id, demo_extras.read(), demo_extras_name)
        assert result.is_err()


def test_demo_list(demoinfo: DemoInfo):
    result = demoinfo.demo_list()
    result.unwrap()


def test_update_demo(demoinfo: DemoInfo):
    new_title = demo_title + "2"
    new_state = "published"
    demoinfo.add_demo(demo_id, demo_title, state).unwrap()
    new_demo = {
        "title": new_title,
        "demo_id": demo_id,
        "state": new_state,
    }
    demoinfo.update_demo(new_demo, demo_id).unwrap()

    result = demoinfo.read_demo_metainfo(demo_id)
    info = result.unwrap()

    assert new_state == info["state"]
    assert new_title == info["title"]


def test_add_and_delete_editor(demoinfo: DemoInfo):
    editor_id = demoinfo.add_editor(editor_name, editor_email).unwrap()

    demoinfo.remove_editor(editor_id).unwrap()


def test_add_already_existing_editor(demoinfo: DemoInfo):
    demoinfo.add_editor(editor_name, editor_email).unwrap()

    result = demoinfo.add_editor(editor_name, editor_email)
    assert result.is_err()


def test_editor_list(demoinfo: DemoInfo):
    result = demoinfo.editor_list()
    editor_list = result.unwrap()
    assert len(editor_list) == 0

    demoinfo.add_editor(editor_name, editor_email).unwrap()

    result = demoinfo.editor_list()
    editor_list = result.unwrap()
    assert len(editor_list) == 1


def test_add_editor_to_demo(demoinfo: DemoInfo):
    editor_id = demoinfo.add_editor(editor_name, editor_email).unwrap()
    demoinfo.add_demo(demo_id, demo_title, state).unwrap()

    demoinfo.add_editor_to_demo(demo_id, editor_id).unwrap()


def test_add_editor_to_non_existent_demo(demoinfo: DemoInfo):
    editor_id = demoinfo.add_editor(editor_name, editor_email).unwrap()

    result = demoinfo.add_editor_to_demo(demo_id, editor_id)
    assert result.is_err()


def test_add_non_existent_editor_to_demo(demoinfo: DemoInfo):
    demoinfo.add_demo(demo_id, demo_title, state).unwrap()

    result = demoinfo.add_editor_to_demo(demo_id, 0)
    assert result.is_err()


def test_demo_get_editor_list(demoinfo: DemoInfo):
    editor_id = demoinfo.add_editor(editor_name, editor_email).unwrap()

    demoinfo.add_demo(demo_id, demo_title, state).unwrap()

    demoinfo.add_editor_to_demo(demo_id, editor_id).unwrap()

    result = demoinfo.demo_get_editors_list(demo_id)
    editor_list = result.unwrap()

    assert len(editor_list) == 1
    assert editor_name == editor_list[0].get("name")
    assert editor_email == editor_list[0].get("mail")


def test_demo_get_editor_list_in_non_existent_demo(demoinfo: DemoInfo):
    result = demoinfo.demo_get_editors_list(demo_id)
    assert result.is_err()


def test_remove_editor_from_demo(demoinfo: DemoInfo):
    editor_id = demoinfo.add_editor(editor_name, editor_email).unwrap()

    demoinfo.add_demo(demo_id, demo_title, state).unwrap()

    demoinfo.add_editor_to_demo(demo_id, editor_id).unwrap()

    demoinfo.remove_editor_from_demo(demo_id, editor_id).unwrap()

    result = demoinfo.demo_get_editors_list(demo_id)
    editor_list = result.unwrap()
    assert editor_list == []


def test_remove_editor_from_non_existent_demo(demoinfo: DemoInfo):
    editor_id = demoinfo.add_editor(editor_name, editor_email).unwrap()

    result = demoinfo.remove_editor_from_demo(demo_id, editor_id)
    assert result.is_err()


def test_remove_non_existent_editor_from_demo(demoinfo: DemoInfo):
    demoinfo.add_demo(demo_id, demo_title, state).unwrap()

    result = demoinfo.remove_editor_from_demo(demo_id, 0)
    assert result.is_err()


def test_ssh_keys(demoinfo: DemoInfo):
    demoinfo.add_demo(demo_id, demo_title, state).unwrap()

    pub, priv = demoinfo.get_ssh_keys(demo_id).unwrap()
    pub2, priv2 = demoinfo.get_ssh_keys(demo_id).unwrap()
    assert pub == pub2
    assert priv == priv2

    demoinfo.reset_ssh_keys(demo_id).unwrap()

    pub3, priv3 = demoinfo.get_ssh_keys(demo_id).unwrap()
    assert pub != pub3
    assert priv != priv3

import logging
import os

import requests

# function in order to know wich machine/server it's used for POST and GET methods (/api/....)


logger = logging.getLogger(__name__)


def api_post(resource, method, **kwargs):
    host = os.environ["IPOL_URL"]
    if method == "get":
        response = requests.get(f"{host}{resource}", **kwargs)
        return response.json(), response.status_code
    elif method == "put":
        response = requests.put(f"{host}{resource}", **kwargs)
        return response, response.status_code
    elif method == "patch":
        response = requests.patch(f"{host}{resource}", **kwargs)
        return response.json(), response.status_code
    elif method == "post":
        response = requests.post(f"{host}{resource}", **kwargs)
        return response.json(), response.status_code
    elif method == "delete":
        response = requests.delete(f"{host}{resource}", **kwargs)
        return response, response.status_code
    else:
        assert False, f"Invalid HTTP(S) method: '{method}'."


def user_can_edit_demo(user, demo_id):
    if user.is_staff or user.is_superuser:
        return True
    editors_list, status = api_post(
        f"/api/demoinfo/demos/{demo_id}/editors", method="get"
    )
    if status != 200:
        logger.error(
            "Something wrong in user_can_edit_demo, %s %s", editors_list, status
        )
        return False
    for editor in editors_list:
        if editor.get("mail") == user.email:
            return True
    return False

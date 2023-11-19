import logging
import os

import requests

# function in order to know wich machine/server it's used for POST and GET methods (/api/....)


logger = logging.getLogger(__name__)


def api_post(resource, method, **kwargs):
    try:
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
    except requests.exceptions.Timeout:
        logger.warning(f"Request timeout: {resource}")
        # Maybe set up for a retry, or continue in a retry loop
        return {"status": "KO"}
    except requests.exceptions.TooManyRedirects:
        logger.warning(f"Too many redirects for request: {resource}")
        # Tell the user their URL was bad and try a different one
        return {"status": "KO"}
    except requests.exceptions.RequestException:
        logger.warning(f"Unknown error when requesting: {resource}")
        # catastrophic error. bail.
        return {"status": "KO"}


def user_can_edit_demo(user, demo_id):
    if user.is_staff or user.is_superuser:
        return True
    editors_list, _ = api_post(f"/api/demoinfo/editors/{demo_id}", method="get")
    for editor in editors_list:
        if editor.get("mail") == user.email:
            return True
    return False

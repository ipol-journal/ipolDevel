import logging
import os
import socket

import requests

#function in order to know wich machine/server it's used for POST and GET methods (/api/....)


logger = logging.getLogger(__name__)

def api_post(resource, params=None, files=None, json=None):
    host = os.environ.get('IPOL_URL', f'http://{socket.gethostbyname(socket.getfqdn())}')
    response = requests.post(f"{host}{resource}", params=params, data=json, files=files)
    try:
        return response.json()
    except requests.exceptions.Timeout:
        logger.warning(f'Request timeout: {resource}')
        # Maybe set up for a retry, or continue in a retry loop
        return {'status': 'KO'}
    except requests.exceptions.TooManyRedirects:
        logger.warning(f'Too many redirects for request: {resource}')
        # Tell the user their URL was bad and try a different one
        return {'status': 'KO'}
    except requests.exceptions.RequestException as e:
        logger.warning(f'Unknown error when requesting: {resource}')
        # catastrophic error. bail.
        raise SystemExit(e)


def user_can_edit_demo(user, demo_id):
    if user.is_staff or user.is_superuser:
        return True
    settings = {'demo_id' : demo_id}
    editors_list = api_post("/api/demoinfo/demo_get_editors_list", settings)
    for editor in editors_list.get('editor_list'):
        if editor.get('mail') == user.email:
            return True
    return False


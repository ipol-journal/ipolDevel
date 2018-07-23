import requests
import socket
import json
from django.http import HttpRequest
from django.http import HttpResponse, HttpResponseRedirect
from django.db import connection
from django.contrib.auth.models import User
#function in order to know wich machine/server it's used for POST and GET methods (/api/....) 

def api_post(resource, params=None, files=None):
    server = socket.gethostbyname(socket.getfqdn())
    url = "http://{}{}".format(server, resource)
    print(url)
    return requests.post(url, params=params, files=files)


def user_can_edit_demo(user_email, demo_id):
    settings = {'demo_id' : demo_id}
    response_api = api_post("/api/demoinfo/demo_get_editors_list", settings)
    editors_list = response_api.json()
    for editor in editors_list.get('editor_list'):
        if editor.get('mail') == user_email:
            return True
    return False


    
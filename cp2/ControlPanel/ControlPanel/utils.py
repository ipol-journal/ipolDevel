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


def email_check(request, demo_id):
    user_email = request.user.email
    #print(user_email)
    settings = {'demo_id' : demo_id}
    response_api = api_post("/api/demoinfo/demo_get_editors_list", settings)
    editors_list = response_api.json()
    mail = editors_list['editor_list']
    #print(mail)
    email = mail.get('mail')
    print(email)
    for editor in editors_list.get('editor_list'):
         if editor.get('mail') == user_email:
             print("gagné")
             return True
    return False



    #return user.email.endswith('@utt.fr')
    #return user.


# def has_permission(demo_id, user):
#     try:
#         if user.is_staff or user.is_superuser:
#             return True

#     #     editors = json.loads(ipolservices.demoinfo_editor_list_for_demo(demo_id))
#     #     for editor in editors.get('editor_list'):
#     #         if editor.get('mail') == user.email:
#     #             return True
#     #     return False

#     # except Exception:
#     #     print "has_permission failed"
#     #     return False

    
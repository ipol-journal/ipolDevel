import requests
import socket
#function in order to know wich machine/server it's used for POST and GET methods (/api/....) 

def api_post(resource, params=None, files=None):
    server = socket.gethostbyname(socket.getfqdn())
    url = "http://{}{}".format(server, resource)
    print(url)
    return requests.post(url, params=params, files=files)

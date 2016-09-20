import json

__author__ = 'josearrecio'


####################
#       TOOLS      #
####################
#get payload from json object
class Payload(object):
        def __init__(self, jsonstr):
                self.__dict__ = json.loads(jsonstr)

def is_json(myjson):
        #verify if string is in json format
        try:
                json_object = json.loads(myjson)
        except Exception, e:
                print("is_json e:%s"%e)
                return False
        return True

def convert_str_to_bool(b):
        r = None
        if b == 'False':
                r = False
        elif b == 'True':
                r = True
        elif b == 'false':
                r = False
        elif b == 'true':
                r = True
        elif int(b) == 0:
                r = False
        elif int(b) == 1:
                r = True
        return r

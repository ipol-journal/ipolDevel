
"""
Little tools.
"""

import json

__author__ = 'josearrecio'

def is_json(myjson):
    """
    verify if string is in json format
    """
    try:
        json_object = json.loads(myjson)
        del json_object
    except Exception, e:
        print "is_json e:%s" % e
        return False
    return True

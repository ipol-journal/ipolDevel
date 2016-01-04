__author__ = 'josearrecio'

import json

def get_status_and_error_from_json(result):
	#get ws result data and sends it to view
	#All demoinfo ws must return status, and error if any
	#if thet return anything else I must process the data retunned, serializers...etc
	
	status = None
	error = None
	try:
		resultdict = json.loads(result)
		status = resultdict['status']
		if 'error' in resultdict:
			error = resultdict['error']
	except Exception as e:
		print "get_status_and_error_from_json error"
		raise ValueError
	return status,error


def convert_str_to_bool(b):
	r = None
	if b == 'False':
		r = False
	elif b == 'True':
		r = True
	if b == 'false':
		r = False
	elif b == 'true':
		r = True
	elif b == 0:
		r = False
	elif b == 1:
		r = True
	return r

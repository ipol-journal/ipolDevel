from apps.controlpanel.views.ipolwebservices.ipolservices import demoinfo_get_states, demoinfo_demo_list, \
	demoinfo_available_author_list_for_demo, demoinfo_author_list, demoinfo_available_editor_list_for_demo, \
	demoinfo_editor_list

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
		#if using proxy, get proxy error codes
		if 'code' in resultdict:
			error = resultdict['code']
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


def get_demoinfo_module_states():
	# returns demoinfo states for the demos form, pubhished,etc
	state_list=None

	try:
		statesjson = demoinfo_get_states()
		statesdict= json.loads(statesjson)
		#print "statesdict", statesdict

		state_list= statesdict['state_list']
	except Exception as e:
		msg=" get_demoinfo_module_states Error %s "%e
		print(msg)

	return state_list


def get_demoinfo_demo_list():
	#returns the list of demos in demoinfo module

	demo_list_option=list()

	try:
		demo_list_json = demoinfo_demo_list()
		demo_list_dict= json.loads(demo_list_json)
		# print "demo_list_dict", demo_list_dict

		demo_list= demo_list_dict['demo_list']

		demo_list_option.append( (0,"None selected") )
		for d in demo_list:
			d = (d["id"],str(d["editorsdemoid"])+", "+str(d["title"]))
			demo_list_option.append(d)

		print "demo_list_option", demo_list_option

	except Exception as e:
		msg=" get_demoinfo_demo_list Error %s "%e
		print(msg)

	return demo_list_option


def get_demoinfo_available_author_list(demoid=None):
	#returns the list of authors not currently asigned to a demo, if demoid is provided.
	#if not, returns all authors

	author_list_option=list()

	try:

		#get authors from demoinfo module
		if demoid:
			author_list_json = demoinfo_available_author_list_for_demo(demoid)
		else:
			author_list_json = demoinfo_author_list()


		author_list_dict= json.loads(author_list_json)
		author_list= author_list_dict['author_list']
		#author_list_option.append( (0,"None selected") )
		for a in author_list:
			a = (a["id"],str(a["name"])+", "+str(a["mail"]))
			author_list_option.append(a)


	except Exception as e:
		msg=" get_demoinfo_available_author_list Error %s "%e
		print(msg)

	return author_list_option


def get_demoinfo_available_editor_list(demoid=None):
	#returns the list of editors not currently asigned to a demo, if demoid is provided.
	#if not, returns all editors

	editor_list_option=list()

	try:

		#get editors from demoinfo module
		if demoid:
			editor_list_json = demoinfo_available_editor_list_for_demo(demoid)
		else:
			editor_list_json = demoinfo_editor_list()


		editor_list_dict= json.loads(editor_list_json)
		editor_list= editor_list_dict['editor_list']
		#editor_list_option.append( (0,"None selected") )
		for a in editor_list:
			a = (a["id"],str(a["name"])+", "+str(a["mail"]))
			editor_list_option.append(a)


	except Exception as e:
		msg=" get_demoinfo_available_editor_list Error %s "%e
		print(msg)

	return editor_list_option

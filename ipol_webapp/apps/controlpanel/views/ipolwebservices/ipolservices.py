# coding=utf-8
__author__ = 'josearrecio'
import json
import requests
import logging
from apps.controlpanel.views.ipolwebservices.ipolwsurls import blobs_demo_list, archive_ws_url_stats, archive_ws_url_page, \
	archive_ws_url_shutdown, archive_ws_url_delete_experiment, archive_ws_url_delete_blob_w_deps, archive_ws_url_add_experiment_test, \
	archive_ws_url_demo_list, archive_ws_url_delete_demo, demoinfo_ws_url_stats, demoinfo_ws_url_demo_list, \
	demoinfo_ws_url_author_list, demoinfo_ws_url_delete_demo, demoinfo_ws_url_read_demo_description, \
	demoinfo_ws_url_last_demodescription_from_demo,demoinfo_ws_url_update_demo_description, \
	demoinfo_ws_url_add_demo_description, demoinfo_ws_url_read_demo, demoinfo_ws_url_read_states, \
	demoinfo_ws_url_update_demo, demoinfo_ws_url_add_demo

logger = logging.getLogger(__name__)

####################
#     UTILITIES    #
####################

def is_json(myjson):
	try:
		json_object = json.loads(myjson)
	except Exception, e:
		print("e:%s"%e)
		return False
	return True

#todo add param for html verb, get post etc
def get_JSON_from_webservice(ws_url,METHOD=None, params=None,json=None):
	"""

	:param ws_url:
	:param params:
	:return:  JSON (from WS) or None

	RUNS THE WEBSERVICES, expects a JSON

	"""
	#todo if needeed insert schema validation here
	result = None
	# print
	# print "SEND WS, get_JSON_from_webservice"
	# print "params ",params
	# print "json ",json
	# print "json type",type(json)
	try:

		if not METHOD or METHOD=='GET':
			response = requests.get(ws_url,params=params)

		elif METHOD=='POST':
			print ("POST")
			if json is not None:
				response = requests.post(ws_url,params=params, json=json)
			else:
				response = requests.post(ws_url,params=params)
		else:
			msg="get_JSON_from_webservice: Not valid METHOD: %s" % result
			logger.error(msg)
			print(msg)
			raise ValueError(msg)

		result =  response.content
		print "JSON:",result

		if not is_json(result):
			msg="get_JSON_from_webservice: Not valid JSON: %s" % result
			logger.error(msg)
			print(msg)
			raise ValueError(msg)
	except Exception as e:
		msg=" get_JSON_from_webservice: error=%s"%(e)
		print(msg)
		logger.error(msg)
	return result

#####################
#  DEMOINFO MODULE  #
#####################

def demoinfo_get_stats():

	wsurl = demoinfo_ws_url_stats
	return get_JSON_from_webservice(wsurl)

def demoinfo_get_states():

	wsurl = demoinfo_ws_url_read_states
	return get_JSON_from_webservice(wsurl)


def demoinfo_demo_list():
	"""
	list demos present in database
	{ return:OK or KO, list demos:
	"""

	wsurl = demoinfo_ws_url_demo_list
	return get_JSON_from_webservice(wsurl)


# DDL


def demoinfo_read_last_demodescription_from_demo(demo_id,returnjsons=None):
	wsurl = demoinfo_ws_url_last_demodescription_from_demo

	if returnjsons == True or returnjsons == 'True':
		params = {'demo_id': demo_id,'returnjsons':True}
	else:
		params = {'demo_id': demo_id}

	#ojo, el metodo debe estar en consonancia con la llamada ajax
	return get_JSON_from_webservice(wsurl,'POST',params)


def demoinfo_read_demo_description(demo_descp_id):
	wsurl = demoinfo_ws_url_read_demo_description
	params = {'demodescriptionID': demo_descp_id}
	return get_JSON_from_webservice(wsurl,'POST',params)


def demoinfo_update_demo_description(demodescriptionID,pjson=None):

	#pjson is unicode str, directly returned from form cleaned data, its is sent as the body of the post request
	# to demoinfo update_demo_description (no need to json dump, this would result in doubly-encoding JSON strings)

	wsurl = demoinfo_ws_url_update_demo_description
	params = {'demodescriptionID': demodescriptionID}

	# print
	# print "SEND demoinfo_update_demo_description"
	# print "params ",params
	# print "json ",pjson[-50:]
	# print "json type",type(pjson)
	# print
	#
	# # #convert unicode str to dict for WS
	# # pjson=json.loads(pjson)
	# # #convert dict to  str
	# # pjson=json.dumps(pjson)
	#
	# print "json ",pjson
	# print "json type",type(pjson)

	return get_JSON_from_webservice(wsurl,'POST',params=params,json=pjson)


def demoinfo_add_demo_description(pjson,demoid=None,inproduction=None):

	wsurl = demoinfo_ws_url_add_demo_description
	if demoid is not None and inproduction is not None:
		params = {'demoid': demoid,'inproduction':inproduction}
	elif demoid is not None:
		params = {'demoid': demoid}
	elif inproduction is not None:
		params = {'inproduction':inproduction}

	return get_JSON_from_webservice(wsurl,'POST',params=params,json=pjson)


# DEMO

##########################################
#  helper clases  (copyed from demoinfo) #
##########################################

class Demo(object):

	editorsdemoid = None
	title = None
	abstract = None
	zipURL = None
	active = None
	stateID = None
	id = None

	# @validates(editorsdemoid=typ(int),
	#            title=inst(basestring),
	#            abstract=inst(basestring),
	#            #zipurl=type(url),
	#            zipurl=inst(basestring),
	#            active=typ(int),
	#            stateid=typ(int),
	#            id= Or(typ(int) , inst(basestring) ),
	#            creation= Or(typ(datetime.datetime) , inst(basestring) ),
	#            modification= Or(typ(datetime.datetime) , inst(basestring) )
	#            )
	def __init__(self, editorsdemoid, title, abstract, zipurl, active, stateid, id=None):

		self.editorsdemoid = editorsdemoid
		self.title = title
		self.abstract = abstract
		self.zipURL = zipurl
		self.active = active
		self.stateID = stateid


def demoinfo_delete_demo(demo_id,hard_delete = False):

	wsurl = demoinfo_ws_url_delete_demo
	params = {'demo_id': demo_id,'hard_delete':hard_delete}

	return get_JSON_from_webservice(wsurl,'POST',params)


def demoinfo_read_demo(demo_id):
	print "demoinfo_update_demo"
	wsurl = demoinfo_ws_url_read_demo
	params = {'demoid': demo_id}
	return get_JSON_from_webservice(wsurl,'POST',params)


def demoinfo_update_demo(demo):
	# print
	# print "demoinfo_update_demo"
	# print
	wsurl = demoinfo_ws_url_update_demo
	params = {'demo': json.dumps(demo)}
	return get_JSON_from_webservice(wsurl,'POST',params)

def demoinfo_add_demo(editorsdemoid ,title ,abstract,zipURL ,active ,stateID):
	# print
	# print "demoinfo_add_demo"
	# print
	wsurl = demoinfo_ws_url_add_demo
	params = {'editorsdemoid': editorsdemoid,'title': title,'abstract': abstract,'zipURL': zipURL,'active': active,'stateID': stateID}
	return get_JSON_from_webservice(wsurl,'POST',params)

# AUTHOR


def demoinfo_author_list():


	wsurl = demoinfo_ws_url_author_list
	return get_JSON_from_webservice(wsurl)


#EDITOR


def demoinfo_editor_list():


	wsurl = demoinfo_ws_url_demo_list
	return get_JSON_from_webservice(wsurl)



####################
#  ARCHIVE MODULE  #
####################

def archive_get_page(experimentid , page='1'):
	"""
	:param experimentid:
	:param page:
	:return:
	The method “page” returns a JSON response with, for a given page of a given demo, all the data of the experiments
	that should be displayed on this page. Twelve experiments are displayed by page. For rendering the archive page in
	the browser
	"""
	wsurl = archive_ws_url_page
	params = {'demo_id': experimentid, 'page': page}

	return get_JSON_from_webservice(wsurl,params)


def archive_get_stats():
	"""
	:param experimentid:
	:param page:
	:return:
	The method “page” returns a JSON response with, for a given page of a given demo, all the data of the experiments
	that should be displayed on this page. Twelve experiments are displayed by page. For rendering the archive page in
	the browser
	"""

	wsurl = archive_ws_url_stats
	return get_JSON_from_webservice(wsurl)


def archive_shutdown():
	"""
	Shutdown archive
	"""

	wsurl = archive_ws_url_shutdown
	return get_JSON_from_webservice(wsurl)


def archive_demo_list():
	"""
	list demos present in database
	{ return:OK or KO, list demos: {id,name, id template, template } }
	"""

	wsurl = archive_ws_url_demo_list
	return get_JSON_from_webservice(wsurl)


def archive_add_experiment_to_test_demo():

	wsurl = archive_ws_url_add_experiment_test

	return get_JSON_from_webservice(wsurl)


def archive_delete_demo(demo_id):

	wsurl = archive_ws_url_delete_demo
	params = {'demo_id': demo_id}

	return get_JSON_from_webservice(wsurl,params)


def archive_delete_experiment(experiment_id):

	wsurl = archive_ws_url_delete_experiment
	params = {'experiment_id': experiment_id}

	return get_JSON_from_webservice(wsurl,params)


def archive_delete_file(file_id):

	wsurl = archive_ws_url_delete_blob_w_deps
	params = {'id_blob': file_id}

	return get_JSON_from_webservice(wsurl,params)


####################
#   BLOBS MODULE   #
####################

def get_blobs_demo_list():
	"""
	list demos present in database
	{ return:OK or KO, list demos: {id,name, id template, template } }
	"""

	wsurl = blobs_demo_list
	return get_JSON_from_webservice(wsurl)


#
# def get_demo_list():
# 	"""
# 	list demos present in database
# 	{ return:OK or KO, list demos: {id:name, id template, template } }
# 	"""
# 	#todo deberia devolver demo_id, debe ser un numero
# 	result = None
# 	try:
#
# 		r = requests.get(blobs_demo_list)
# 		result = r.json()
#
#
# 		if not is_json(result):
# 			msg="No es un Json valido:  is_json:%s" % is_json(result)
# 			logger.error(msg)
# 			print(msg)
# 			raise ValueError(msg)
#
#
# 	except Exception as e:
# 		msg=" get_demo_list: error=%s"%(e)
# 		print(msg)
# 		logger.error(msg)
# 	return result

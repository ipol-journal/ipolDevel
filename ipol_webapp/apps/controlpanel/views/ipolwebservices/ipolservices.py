# coding=utf-8
__author__ = 'josearrecio'
import json
import requests
import logging
from apps.controlpanel.views.ipolwebservices.ipolwsurls import blobs_demo_list, archive_ws_url_stats, archive_ws_url_page, \
	archive_ws_url_shutdown, archive_ws_url_delete_experiment, archive_ws_url_delete_blob_w_deps, archive_ws_url_add_experiment_test, \
	archive_ws_url_demo_list, archive_ws_url_delete_demo

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

def get_JSON_from_webservice(ws_url, params=None):
	"""

	:param ws_url:
	:param params:
	:return:  JSON (from WS) or None
	"""
	result = None
	try:
		response = requests.get(ws_url,params)
		result =  response.content
		print "JSON:"
		print result

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

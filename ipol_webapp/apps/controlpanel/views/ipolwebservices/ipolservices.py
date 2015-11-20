# coding=utf-8
__author__ = 'josearrecio'
import json
from apps.controlpanel.views.ipolwebservices.ipolwsurls import blobs_demo_list, archive_ws_url_stats, archive_ws_url_page, \
	archive_ws_url_shutdown, archive_ws_url_delete_experiment_web
import requests
import logging
logger = logging.getLogger(__name__)


def is_json(myjson):
	try:
		json_object = json.loads(myjson)
	except Exception, e:
		print("e:%s"%e)
		return False
	return True

import json

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
		print result

		if not is_json(result):
			msg="get_JSON_from_webservice: Not valid JSON:  is_json:%s" % is_json(result)
			logger.error(msg)
			print(msg)
			raise ValueError(msg)
	except Exception as e:
		msg=" get_JSON_from_webservice: error=%s"%(e)
		print(msg)
		logger.error(msg)
	return result

def get_page(experimentid , page='1'):
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

def get_stats():
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

def get_demo_list():
	"""
	list demos present in database
	{ return:OK or KO, list demos: {id,name, id template, template } }
	"""

	wsurl = blobs_demo_list
	return get_JSON_from_webservice(wsurl)

def archive_shutdown():
	"""
	Shutdown archive
	"""

	wsurl = archive_ws_url_shutdown
	return get_JSON_from_webservice(wsurl)

def archive_delete_experiment_web(experiment_id,demo_id):

	wsurl = archive_ws_url_delete_experiment_web
	params = {'experiment_id': experiment_id, 'demo_id': demo_id}

	return get_JSON_from_webservice(wsurl,params)

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
# 		msg=" get_page: error=%s"%(e)
# 		print(msg)
# 		logger.error(msg)
# 	return result

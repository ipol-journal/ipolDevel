# coding=utf-8
__author__ = 'josearrecio'
import json
from apps.controlpanel.views.ipolwebservices.ipolwsurls import blobs_demo_list, archive_ws_url_stats, archive_ws_url_page
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


def get_page(experimentid , page='1'):
	"""
	:param experimentid:
	:param page:
	:return:
	The method “page” returns a JSON response with, for a given page of a given demo, all the data of the experiments
	that should be displayed on this page. Twelve experiments are displayed by page. For rendering the archive page in
	the browser
	"""
	import json
	result = None
	wsurl = archive_ws_url_page
	try:

		params = {'demo_id': experimentid, 'page': page}
		response = requests.get(wsurl,params)
		result =  response.content
		if not is_json(result):
			msg="No es un Json valido:  is_json:%s" % is_json(result)
			logger.error(msg)
			print(msg)
			raise ValueError(msg)



	except Exception as e:
		msg=" get_page: error=%s"%(e)
		print(msg)
		logger.error(msg)
	return result



def get_stats():
	"""
	:param experimentid:
	:param page:
	:return:
	The method “page” returns a JSON response with, for a given page of a given demo, all the data of the experiments
	that should be displayed on this page. Twelve experiments are displayed by page. For rendering the archive page in
	the browser
	"""

	result = None
	wsurl = archive_ws_url_stats
	try:

		response = requests.get(wsurl)
		result =  response.content
		#result =  response.json()

		print result

		if not is_json(result):
			msg="No es un Json valido:  is_json:%s" % is_json(result)
			logger.error(msg)
			print(msg)
			raise ValueError(msg)



	except Exception as e:
		msg=" get_page: error=%s"%(e)
		print(msg)
		logger.error(msg)
	return result


def get_demo_list():
	"""
	list demos present in database
	{ return:OK or KO, list demos: {id:name, id template, template } }
	"""
	#todo deberia devolver demo_id, debe ser un numero
	result = None
	wsurl = blobs_demo_list
	try:

		response = requests.get(wsurl)
		result =  response.content


		if not is_json(result):
			msg="No es un Json valido:  is_json:%s" % is_json(result)
			logger.error(msg)
			print(msg)
			raise ValueError(msg)


	except Exception as e:
		msg=" get_page: error=%s"%(e)
		print(msg)
		logger.error(msg)
	return result


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

# coding=utf-8
from ipol_webapp.settings import IPOL_SERVICES_MODULE_PROXY, IPOL_SERVICES_MODULE_DEMOINFO, \
	IPOL_SERVICES_MODULE_ACHIVE, IPOL_SERVICES_MODULE_BLOBS

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
	demoinfo_ws_url_update_demo, demoinfo_ws_url_add_demo, demoinfo_ws_url_demo_list_pagination_and_filter, \
	demoinfo_ws_url_author_list_pagination_and_filter, demoinfo_ws_url_delete_author, demoinfo_ws_url_read_author, \
	demoinfo_ws_url_update_author, demoinfo_ws_url_add_author, demoinfo_ws_url_add_author_to_demo, \
	demoinfo_ws_url_author_list_for_demo, demoinfo_ws_url_available_author_list_for_demo, \
	demoinfo_ws_url_delete_author_from_demo, demoinfo_ws_url_editor_list, demoinfo_ws_url_editor_list_for_demo, \
	demoinfo_ws_url_available_editor_list_for_demo, demoinfo_ws_url_editor_list_pagination_and_filter, \
	demoinfo_ws_url_delete_editor, demoinfo_ws_url_add_editor, demoinfo_ws_url_read_editor, \
	demoinfo_ws_url_update_editor, demoinfo_ws_url_add_editor_to_demo, demoinfo_ws_url_delete_editor_from_demo, \
	demoinfo_ws_url_demo_list_by_demoeditorid, proxy_ws_url_stats, proxy_ws_url_service_call

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

	MAKES THE WEBSERVICE CALL using reuqests library, expects ws to return a valid JSON

	http://docs.python-requests.org/en/latest/user/quickstart/
	Instead of encoding the dict yourself, you can also pass it directly using the json parameter
	(added in version 2.4.2) and it will be encoded automatically:

	"""
	#todo if needeed insert schema validation here
	result = None
	# print
	# print "SEND WS, get_JSON_from_webservice"
	# print
	# print "params ",params
	# print "json ",json
	# print "json type",type(json)
	# print "METHOD",METHOD
	# print "METHOD",type(METHOD)
	# print
	try:

		if not METHOD or METHOD=='GET':
			response = requests.get(ws_url,params=params)
		elif METHOD=='POST':
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
		# print "JSON:",result

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
#  PROXY MODULE  #
#####################


# MISC

#todo proxy has no stats, only ping, create stats ws on proxy
def proxy_get_stats():

	wsurl =  IPOL_SERVICES_MODULE_PROXY % proxy_ws_url_stats
	return get_JSON_from_webservice(wsurl)



#####################
#  DEMOINFO MODULE  #
#####################


# MISC


def demoinfo_get_stats():

	service_name = demoinfo_ws_url_stats

	proxywsurl = IPOL_SERVICES_MODULE_PROXY % proxy_ws_url_service_call
	serviceparams = None
	servicejson = None
	proxyparams = {'module': "demoinfo",'service': service_name,'servicehtmlmethod': "GET",'params': serviceparams,'jsonparam': servicejson}
	return get_JSON_from_webservice(proxywsurl,params=proxyparams)



def demoinfo_get_states():

	service_name = demoinfo_ws_url_read_states

	proxywsurl = IPOL_SERVICES_MODULE_PROXY % proxy_ws_url_service_call
	serviceparams = None
	servicejson = None
	proxyparams = {'module': "demoinfo",'service': service_name,'servicehtmlmethod': "GET",'params': serviceparams,'jsonparam': servicejson}
	return get_JSON_from_webservice(proxywsurl,params=proxyparams)



# DDL


def demoinfo_read_last_demodescription_from_demo(demo_id,returnjsons=None):


	service_name = demoinfo_ws_url_last_demodescription_from_demo

	proxywsurl = IPOL_SERVICES_MODULE_PROXY % proxy_ws_url_service_call
	#proxy can be called by GET or POST, prefer POST if submiting data to server
	module = "demoinfo"
	if returnjsons == True or returnjsons == 'True':
		serviceparams = {'demo_id': demo_id,'returnjsons':True}
	else:
		serviceparams = {'demo_id': demo_id}
	#send as string to proxy, proxy will load this into a dict for the request lib call
	serviceparams = json.dumps(serviceparams)
	servicehtmlmethod = "POST"
	servicejson = None
	proxyparams = {'module': module,'service': service_name ,'servicehtmlmethod':servicehtmlmethod ,'params': serviceparams,'jsonparam': servicejson}
	return get_JSON_from_webservice(proxywsurl,'POST',params=proxyparams)




def demoinfo_read_demo_description(demo_descp_id):

	service_name = demoinfo_ws_url_read_demo_description

	proxywsurl = IPOL_SERVICES_MODULE_PROXY % proxy_ws_url_service_call
	#proxy can be called by GET or POST, prefer POST if submiting data to server
	module = "demoinfo"
	serviceparams = {'demodescriptionID': demo_descp_id}
	#send as string to proxy, proxy will load this into a dict for the request lib call
	serviceparams = json.dumps(serviceparams)
	servicehtmlmethod = "POST"
	servicejson = None
	proxyparams = {'module': module,'service': service_name ,'servicehtmlmethod':servicehtmlmethod ,'params': serviceparams,'jsonparam': servicejson}
	return get_JSON_from_webservice(proxywsurl,'POST',params=proxyparams)




def demoinfo_update_demo_description(demodescriptionID,pjson=None):

	#pjson is unicode str, directly returned from form cleaned data, its is sent as the body of the post request
	# to demoinfo update_demo_description (no need to json dump, this would result in doubly-encoding JSON strings)

	# print
	# print "demoinfo_update_demo_description"
	# print

	service_name = demoinfo_ws_url_update_demo_description

	proxywsurl = IPOL_SERVICES_MODULE_PROXY % proxy_ws_url_service_call
	#proxy can be called by GET or POST, prefer POST if submiting data to server
	module = "demoinfo"
	serviceparams = {'demodescriptionID': demodescriptionID}
	#send as string to proxy, proxy will load this into a dict for the request lib call
	serviceparams = json.dumps(serviceparams)
	servicehtmlmethod = "POST"
	servicejson = pjson
	proxyparams = {'module': module,'service': service_name ,'servicehtmlmethod':servicehtmlmethod ,'params': serviceparams,'jsonparam': servicejson}
	return get_JSON_from_webservice(proxywsurl,'POST',params=proxyparams)



def demoinfo_add_demo_description(pjson,demoid=None,inproduction=None):

	service_name = demoinfo_ws_url_add_demo_description

	proxywsurl = IPOL_SERVICES_MODULE_PROXY % proxy_ws_url_service_call
	#proxy can be called by GET or POST, prefer POST if submiting data to server
	module = "demoinfo"
	if demoid is not None and inproduction is not None:
		serviceparams = {'demoid': demoid,'inproduction':inproduction}
	elif demoid is not None:
		serviceparams = {'demoid': demoid}
	elif inproduction is not None:
		serviceparams = {'inproduction':inproduction}
	#send as string to proxy, proxy will load this into a dict for the request lib call
	serviceparams = json.dumps(serviceparams)
	servicehtmlmethod = "POST"
	servicejson = pjson
	proxyparams = {'module': module,'service': service_name ,'servicehtmlmethod':servicehtmlmethod ,'params': serviceparams,'jsonparam': servicejson}
	return get_JSON_from_webservice(proxywsurl,'POST',params=proxyparams)




# DEMO

#todo se usa esto?
def demoinfo_demo_list():
	"""
	list demos present in database
	{ return:OK or KO, list demos:
	"""

	service_name = demoinfo_ws_url_demo_list

	proxywsurl = IPOL_SERVICES_MODULE_PROXY % proxy_ws_url_service_call
	serviceparams = None
	servicejson = None
	proxyparams = {'module': "demoinfo",'service': service_name,'servicehtmlmethod': "GET",'params': serviceparams,'jsonparam': servicejson}
	return get_JSON_from_webservice(proxywsurl,params=proxyparams)




def demoinfo_demo_list_by_demoeditorid(demoeditorid_list):
	"""
	list demos present in database with demo_editor_id in  demoeditorid_list
	demoeditorid_list must be sent to WS as a JSON string
	if no demoeditorid_list is provided return None

	{ return:OK or KO, list demos:...
	"""

	service_name = demoinfo_ws_url_demo_list_by_demoeditorid
	result = None

	if demoeditorid_list :

		proxywsurl = IPOL_SERVICES_MODULE_PROXY % proxy_ws_url_service_call
		serviceparams = {'demoeditorid_list': json.dumps(demoeditorid_list)}
		serviceparams = json.dumps(serviceparams)
		servicejson = None
		proxyparams = {'module': "demoinfo",'service': service_name,'servicehtmlmethod': "GET",'params': serviceparams,'jsonparam': servicejson}
		result = get_JSON_from_webservice(proxywsurl,params=proxyparams)

	return result


def demoinfo_demo_list_pagination_and_filtering( num_elements_page, page, qfilter):
	"""
	list demos present in database
	demo_list_pagination_and_filter(self,num_elements_page,page,qfilter):
	 demo list filtered and pagination {"status": "OK", "demo_list": [{"creation": "2015-12-29 15:03:07", "stateID": 1,
	 "abstract": "DemoTEST3 Abstract", "title": "DemoTEST3 Title", "editorsdemoid": 25, "active": 1, "id": 3, "zipURL":
	 "https://DemoTEST3.html", "modification": "2015-12-29 15:03:07"}], "next_page_number": null,
	 "previous_page_number": 1, "number": 2.0}
	"""

	service_name = demoinfo_ws_url_demo_list_pagination_and_filter

	proxywsurl = IPOL_SERVICES_MODULE_PROXY % proxy_ws_url_service_call
	#proxy can be called by GET or POST, prefer POST if submiting data to server
	module = "demoinfo"
	serviceparams = {'num_elements_page': num_elements_page,'page':page,'qfilter':qfilter}
	#send as string to proxy, proxy will load this into a dict for the request lib call
	serviceparams = json.dumps(serviceparams)
	servicehtmlmethod = "GET"
	servicejson = None
	proxyparams = {'module': module,'service': service_name ,'servicehtmlmethod':servicehtmlmethod ,'params': serviceparams,'jsonparam': servicejson}
	return get_JSON_from_webservice(proxywsurl,'POST',params=proxyparams)


def demoinfo_delete_demo(demo_id,hard_delete = False):

	service_name = demoinfo_ws_url_delete_demo

	proxywsurl = IPOL_SERVICES_MODULE_PROXY % proxy_ws_url_service_call
	serviceparams = {'demo_id': demo_id,'hard_delete':hard_delete}
	serviceparams = json.dumps(serviceparams)
	servicejson = None
	proxyparams = {'module': "demoinfo",'service': service_name,'servicehtmlmethod': "POST",'params': serviceparams,'jsonparam': servicejson}
	return get_JSON_from_webservice(proxywsurl,'POST',params=proxyparams)


def demoinfo_read_demo(demo_id):

	service_name = demoinfo_ws_url_read_demo

	proxywsurl = IPOL_SERVICES_MODULE_PROXY % proxy_ws_url_service_call
	serviceparams = {"demoid": demo_id}
	#send as string to proxy, proxy will load this into a dict for the request lib call
	serviceparams = json.dumps(serviceparams)
	servicehtmlmethod = "POST"
	servicejson = None
	proxyparams = {'module': "demoinfo",'service': service_name ,'servicehtmlmethod':servicehtmlmethod ,'params': serviceparams,'jsonparam': servicejson}
	return get_JSON_from_webservice(proxywsurl,'POST',params=proxyparams)




def demoinfo_update_demo(demo):

	service_name = demoinfo_ws_url_update_demo

	proxywsurl = IPOL_SERVICES_MODULE_PROXY % proxy_ws_url_service_call
	#proxy can be called by GET or POST, prefer POST if submiting data to server
	module = "demoinfo"
	serviceparams = {'demo': json.dumps(demo)}
	#send as string to proxy, proxy will load this into a dict for the request lib call
	serviceparams = json.dumps(serviceparams)
	servicehtmlmethod = "POST"
	servicejson = None
	proxyparams = {'module': module,'service': service_name ,'servicehtmlmethod':servicehtmlmethod ,'params': serviceparams,'jsonparam': servicejson}
	return get_JSON_from_webservice(proxywsurl,'POST',params=proxyparams)



def demoinfo_add_demo(editorsdemoid ,title ,abstract,zipURL ,active ,stateID):

	service_name = demoinfo_ws_url_add_demo

	proxywsurl = IPOL_SERVICES_MODULE_PROXY % proxy_ws_url_service_call
	#proxy can be called by GET or POST, prefer POST if submiting data to server
	module = "demoinfo"
	serviceparams = {'editorsdemoid': editorsdemoid,'title': title,'abstract': abstract,'zipURL': zipURL,'active': active,'stateID': stateID}
	#send as string to proxy, proxy will load this into a dict for the request lib call
	serviceparams = json.dumps(serviceparams)
	servicehtmlmethod = "POST"
	servicejson = None
	proxyparams = {'module': module,'service': service_name ,'servicehtmlmethod':servicehtmlmethod ,'params': serviceparams,'jsonparam': servicejson}
	return get_JSON_from_webservice(proxywsurl,'POST',params=proxyparams)



# AUTHOR


def demoinfo_author_list():

	service_name = demoinfo_ws_url_author_list

	proxywsurl = IPOL_SERVICES_MODULE_PROXY % proxy_ws_url_service_call
	serviceparams = None
	servicejson = None
	proxyparams = {'module': "demoinfo",'service': service_name,'servicehtmlmethod': "GET",'params': serviceparams,'jsonparam': servicejson}
	return get_JSON_from_webservice(proxywsurl,params=proxyparams)


def demoinfo_author_list_for_demo(demo_id):

	service_name = demoinfo_ws_url_author_list_for_demo

	proxywsurl = IPOL_SERVICES_MODULE_PROXY % proxy_ws_url_service_call
	serviceparams = {'demo_id': demo_id}
	serviceparams = json.dumps(serviceparams)
	servicejson = None
	proxyparams = {'module': "demoinfo",'service': service_name,'servicehtmlmethod': "GET",'params': serviceparams,'jsonparam': servicejson}
	return get_JSON_from_webservice(proxywsurl,params=proxyparams)




def demoinfo_available_author_list_for_demo(demo_id = None):

	service_name = demoinfo_ws_url_available_author_list_for_demo

	proxywsurl = IPOL_SERVICES_MODULE_PROXY % proxy_ws_url_service_call
	serviceparams = {'demo_id': demo_id}
	serviceparams = json.dumps(serviceparams)
	servicejson = None
	proxyparams = {'module': "demoinfo",'service': service_name,'servicehtmlmethod': "GET",'params': serviceparams,'jsonparam': servicejson}
	return get_JSON_from_webservice(proxywsurl,params=proxyparams)




def demoinfo_author_list_pagination_and_filtering( num_elements_page, page, qfilter):

	service_name = demoinfo_ws_url_author_list_pagination_and_filter

	proxywsurl = IPOL_SERVICES_MODULE_PROXY % proxy_ws_url_service_call
	serviceparams = {'num_elements_page': num_elements_page,'page':page,'qfilter':qfilter}
	serviceparams = json.dumps(serviceparams)
	servicejson = None
	proxyparams = {'module': "demoinfo",'service': service_name,'servicehtmlmethod': "GET",'params': serviceparams,'jsonparam': servicejson}
	return get_JSON_from_webservice(proxywsurl,params=proxyparams)



def demoinfo_delete_author(author_id):

	service_name = demoinfo_ws_url_delete_author

	proxywsurl = IPOL_SERVICES_MODULE_PROXY % proxy_ws_url_service_call
	serviceparams = {'author_id': author_id}
	serviceparams = json.dumps(serviceparams)
	servicejson = None
	proxyparams = {'module': "demoinfo",'service': service_name,'servicehtmlmethod': "POST",'params': serviceparams,'jsonparam': servicejson}
	return get_JSON_from_webservice(proxywsurl,'POST',params=proxyparams)



def demoinfo_add_author( name ,mail):

	service_name = demoinfo_ws_url_add_author

	proxywsurl = IPOL_SERVICES_MODULE_PROXY % proxy_ws_url_service_call
	serviceparams = {'name': name,'mail': mail}
	serviceparams = json.dumps(serviceparams)
	servicejson = None
	proxyparams = {'module': "demoinfo",'service': service_name,'servicehtmlmethod': "POST",'params': serviceparams,'jsonparam': servicejson}
	return get_JSON_from_webservice(proxywsurl,'POST',params=proxyparams)



def demoinfo_read_author(author_id):

	service_name = demoinfo_ws_url_read_author

	proxywsurl = IPOL_SERVICES_MODULE_PROXY % proxy_ws_url_service_call
	serviceparams = {'authorid': author_id}
	serviceparams = json.dumps(serviceparams)
	servicejson = None
	proxyparams = {'module': "demoinfo",'service': service_name,'servicehtmlmethod': "POST",'params': serviceparams,'jsonparam': servicejson}
	return get_JSON_from_webservice(proxywsurl,'POST',params=proxyparams)



def demoinfo_update_author(author):

	service_name = demoinfo_ws_url_update_author

	proxywsurl = IPOL_SERVICES_MODULE_PROXY % proxy_ws_url_service_call
	serviceparams = {'author': json.dumps(author)}
	serviceparams = json.dumps(serviceparams)
	servicejson = None
	proxyparams = {'module': "demoinfo",'service': service_name,'servicehtmlmethod': "POST",'params': serviceparams,'jsonparam': servicejson}
	return get_JSON_from_webservice(proxywsurl,'POST',params=proxyparams)



def demoinfo_add_author_to_demo( demo_id ,author_id):

	service_name = demoinfo_ws_url_add_author_to_demo

	proxywsurl = IPOL_SERVICES_MODULE_PROXY % proxy_ws_url_service_call
	serviceparams = {'demo_id': demo_id,'author_id': author_id}
	serviceparams = json.dumps(serviceparams)
	servicejson = None
	proxyparams = {'module': "demoinfo",'service': service_name,'servicehtmlmethod': "POST",'params': serviceparams,'jsonparam': servicejson}
	return get_JSON_from_webservice(proxywsurl,'POST',params=proxyparams)


def demoinfo_delete_author_from_demo(demo_id,author_id):

	service_name = demoinfo_ws_url_delete_author_from_demo

	proxywsurl = IPOL_SERVICES_MODULE_PROXY % proxy_ws_url_service_call
	serviceparams = {'demo_id': demo_id,'author_id': author_id}
	serviceparams = json.dumps(serviceparams)
	servicejson = None
	proxyparams = {'module': "demoinfo",'service': service_name,'servicehtmlmethod': "POST",'params': serviceparams,'jsonparam': servicejson}
	return get_JSON_from_webservice(proxywsurl,'POST',params=proxyparams)


#EDITOR


def demoinfo_editor_list():

	service_name = demoinfo_ws_url_editor_list

	proxywsurl = IPOL_SERVICES_MODULE_PROXY % proxy_ws_url_service_call
	serviceparams = None
	servicejson = None
	proxyparams = {'module': "demoinfo",'service': service_name,'servicehtmlmethod': "GET",'params': serviceparams,'jsonparam': servicejson}
	return get_JSON_from_webservice(proxywsurl,params=proxyparams)


def demoinfo_editor_list_for_demo(demo_id):

	service_name = demoinfo_ws_url_editor_list_for_demo

	proxywsurl = IPOL_SERVICES_MODULE_PROXY % proxy_ws_url_service_call
	serviceparams = {'demo_id': demo_id}
	serviceparams = json.dumps(serviceparams)
	servicejson = None
	proxyparams = {'module': "demoinfo",'service': service_name,'servicehtmlmethod': "GET",'params': serviceparams,'jsonparam': servicejson}
	return get_JSON_from_webservice(proxywsurl,params=proxyparams)



def demoinfo_available_editor_list_for_demo(demo_id=None):

	service_name = demoinfo_ws_url_available_editor_list_for_demo

	proxywsurl = IPOL_SERVICES_MODULE_PROXY % proxy_ws_url_service_call
	serviceparams = {'demo_id': demo_id}
	serviceparams = json.dumps(serviceparams)
	servicejson = None
	proxyparams = {'module': "demoinfo",'service': service_name,'servicehtmlmethod': "GET",'params': serviceparams,'jsonparam': servicejson}
	return get_JSON_from_webservice(proxywsurl,params=proxyparams)



def demoinfo_editor_list_pagination_and_filtering( num_elements_page, page, qfilter):

	service_name = demoinfo_ws_url_editor_list_pagination_and_filter


	proxywsurl = IPOL_SERVICES_MODULE_PROXY % proxy_ws_url_service_call
	serviceparams = {'num_elements_page': num_elements_page,'page':page,'qfilter':qfilter}
	serviceparams = json.dumps(serviceparams)
	servicejson = None
	proxyparams = {'module': "demoinfo",'service': service_name,'servicehtmlmethod': "GET",'params': serviceparams,'jsonparam': servicejson}
	return get_JSON_from_webservice(proxywsurl,params=proxyparams)



def demoinfo_delete_editor(editor_id):

	service_name = demoinfo_ws_url_delete_editor

	proxywsurl = IPOL_SERVICES_MODULE_PROXY % proxy_ws_url_service_call
	serviceparams = {'editor_id': editor_id}
	serviceparams = json.dumps(serviceparams)
	servicejson = None
	proxyparams = {'module': "demoinfo",'service': service_name,'servicehtmlmethod': "POST",'params': serviceparams,'jsonparam': servicejson}
	return get_JSON_from_webservice(proxywsurl,'POST',params=proxyparams)


def demoinfo_add_editor( name ,mail):

	service_name = demoinfo_ws_url_add_editor

	proxywsurl = IPOL_SERVICES_MODULE_PROXY % proxy_ws_url_service_call
	serviceparams = {'name': name,'mail': mail}
	serviceparams = json.dumps(serviceparams)
	servicejson = None
	proxyparams = {'module': "demoinfo",'service': service_name,'servicehtmlmethod': "POST",'params': serviceparams,'jsonparam': servicejson}
	return get_JSON_from_webservice(proxywsurl,'POST',params=proxyparams)



def demoinfo_read_editor(editor_id):

	service_name = demoinfo_ws_url_read_editor

	proxywsurl = IPOL_SERVICES_MODULE_PROXY % proxy_ws_url_service_call
	serviceparams = {'editorid': editor_id}
	serviceparams = json.dumps(serviceparams)
	servicejson = None
	proxyparams = {'module': "demoinfo",'service': service_name,'servicehtmlmethod': "POST",'params': serviceparams,'jsonparam': servicejson}
	return get_JSON_from_webservice(proxywsurl,'POST',params=proxyparams)



def demoinfo_update_editor(editor):

	service_name = demoinfo_ws_url_update_editor

	proxywsurl = IPOL_SERVICES_MODULE_PROXY % proxy_ws_url_service_call
	serviceparams = {'editor': json.dumps(editor)}
	serviceparams = json.dumps(serviceparams)
	servicejson = None
	proxyparams = {'module': "demoinfo",'service': service_name,'servicehtmlmethod': "POST",'params': serviceparams,'jsonparam': servicejson}
	return get_JSON_from_webservice(proxywsurl,'POST',params=proxyparams)


def demoinfo_add_editor_to_demo( demo_id ,editor_id):

	service_name = demoinfo_ws_url_add_editor_to_demo

	proxywsurl = IPOL_SERVICES_MODULE_PROXY % proxy_ws_url_service_call
	serviceparams = {'demo_id': demo_id,'editor_id': editor_id}
	serviceparams = json.dumps(serviceparams)
	servicejson = None
	proxyparams = {'module': "demoinfo",'service': service_name,'servicehtmlmethod': "POST",'params': serviceparams,'jsonparam': servicejson}
	return get_JSON_from_webservice(proxywsurl,'POST',params=proxyparams)

def demoinfo_delete_editor_from_demo(demo_id,editor_id):

	service_name = demoinfo_ws_url_delete_editor_from_demo

	proxywsurl = IPOL_SERVICES_MODULE_PROXY % proxy_ws_url_service_call
	serviceparams = {'demo_id': demo_id,'editor_id': editor_id}
	serviceparams = json.dumps(serviceparams)
	servicejson = None
	proxyparams = {'module': "demoinfo",'service': service_name,'servicehtmlmethod': "POST",'params': serviceparams,'jsonparam': servicejson}
	return get_JSON_from_webservice(proxywsurl,params=proxyparams)



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

	service_name = archive_ws_url_page

	proxywsurl = IPOL_SERVICES_MODULE_PROXY % proxy_ws_url_service_call
	serviceparams = {'demo_id': experimentid, 'page': page}
	serviceparams = json.dumps(serviceparams)
	servicejson = None
	proxyparams = {'module': "archive",'service': service_name,'servicehtmlmethod': "GET",'params': serviceparams,'jsonparam': servicejson}
	return get_JSON_from_webservice(proxywsurl,params=proxyparams)

def archive_get_stats():
	"""
	:param experimentid:
	:param page:
	:return:
	The method “page” returns a JSON response with, for a given page of a given demo, all the data of the experiments
	that should be displayed on this page. Twelve experiments are displayed by page. For rendering the archive page in
	the browser
	"""

	service_name = archive_ws_url_stats


	proxywsurl = IPOL_SERVICES_MODULE_PROXY % proxy_ws_url_service_call
	serviceparams = None
	servicejson = None
	proxyparams = {'module': "archive",'service': service_name,'servicehtmlmethod': "GET",'params': serviceparams,'jsonparam': servicejson}
	return get_JSON_from_webservice(proxywsurl,params=proxyparams)



#todo remove this method not used any more
def archive_shutdown():
	"""
	Shutdown archive
	"""

	service_name = archive_ws_url_shutdown

	proxywsurl = IPOL_SERVICES_MODULE_PROXY % proxy_ws_url_service_call
	serviceparams = None
	servicejson = None
	proxyparams = {'module': "archive",'service': service_name,'servicehtmlmethod': "GET",'params': serviceparams,'jsonparam': servicejson}
	return get_JSON_from_webservice(proxywsurl,params=proxyparams)



def archive_demo_list():
	"""
	list demos present in database
	{ return:OK or KO, list demos: {id,name, id template, template } }
	"""

	service_name = archive_ws_url_demo_list

	proxywsurl = IPOL_SERVICES_MODULE_PROXY % proxy_ws_url_service_call
	serviceparams = None
	servicejson = None
	proxyparams = {'module': "archive",'service': service_name,'servicehtmlmethod': "GET",'params': serviceparams,'jsonparam': servicejson}
	return get_JSON_from_webservice(proxywsurl,params=proxyparams)



def archive_add_experiment_to_test_demo():
#todo delete should use POST
	service_name = archive_ws_url_add_experiment_test

	proxywsurl = IPOL_SERVICES_MODULE_PROXY % proxy_ws_url_service_call
	serviceparams = None
	servicejson = None
	proxyparams = {'module': "archive",'service': service_name,'servicehtmlmethod': "GET",'params': serviceparams,'jsonparam': servicejson}
	return get_JSON_from_webservice(proxywsurl,params=proxyparams)



def archive_delete_demo(demo_id):
#todo delete should use POST
	service_name = archive_ws_url_delete_demo

	proxywsurl = IPOL_SERVICES_MODULE_PROXY % proxy_ws_url_service_call
	serviceparams = {'demo_id': demo_id}
	serviceparams = json.dumps(serviceparams)
	servicejson = None
	proxyparams = {'module': "archive",'service': service_name,'servicehtmlmethod': "GET",'params': serviceparams,'jsonparam': servicejson}
	return get_JSON_from_webservice(proxywsurl,params=proxyparams)


def archive_delete_experiment(experiment_id):
#todo delete should use POST
	service_name = archive_ws_url_delete_experiment

	proxywsurl = IPOL_SERVICES_MODULE_PROXY % proxy_ws_url_service_call
	serviceparams = {'experiment_id': experiment_id}
	serviceparams = json.dumps(serviceparams)
	servicejson = None
	proxyparams = {'module': "archive",'service': service_name,'servicehtmlmethod': "GET",'params': serviceparams,'jsonparam': servicejson}
	return get_JSON_from_webservice(proxywsurl,params=proxyparams)



def archive_delete_file(file_id):
#todo delete should use POST
	service_name = archive_ws_url_delete_blob_w_deps

	proxywsurl = IPOL_SERVICES_MODULE_PROXY % proxy_ws_url_service_call
	serviceparams = {'id_blob': file_id}
	serviceparams = json.dumps(serviceparams)
	servicejson = None
	proxyparams = {'module': "archive",'service': service_name,'servicehtmlmethod': "GET",'params': serviceparams,'jsonparam': servicejson}
	return get_JSON_from_webservice(proxywsurl,params=proxyparams)



####################
#   BLOBS MODULE   #
####################


def get_blobs_demo_list():
	"""
	list demos present in database
	{ return:OK or KO, list demos: {id,name, id template, template } }
	"""
	service_name = blobs_demo_list

	proxywsurl = IPOL_SERVICES_MODULE_PROXY % proxy_ws_url_service_call
	serviceparams = None
	servicejson = None
	proxyparams = {'module': "blobs",'service': service_name,'servicehtmlmethod': "GET",'params': serviceparams,'jsonparam': servicejson}
	return get_JSON_from_webservice(proxywsurl,params=proxyparams)


# coding=utf-8
from ipol_webapp.settings import IPOL_SERVICES_MODULE_ACHIVE, IPOL_SERVICES_MODULE_BLOBS, IPOL_SERVICES_MODULE_DEMOINFO, \
    IPOL_SERVICES_MODULE_PROXY

__author__ = 'josearrecio'

#todo This could  go in the DB, and we could let a certain user profile (sysops or admin) manage this.


#GLOBAL WS LIST


#####################
#  PROXY MODULE  #
#####################


# proxy executes index, gets params and asks ws, but...i need to be able to call proxy in POST, and get it to call the Sv depending
# of and htlm verb arg (get,post...)
# this is Why i modify proxy, and create a function, proxy_call(proxyhtmlverb, module, service, servicehtmlverb)


proxy_ws_url_service_call = 'proxy_service_call'
proxy_ws_url_service_call2 = 'proxy_post'
proxy_ws_url_stats =  'ping'


# param None


#####################
#  DEMOINFO MODULE  #
#####################


# MISC

#IPOL_SERVICES_MODULE_DEMOINFO ='http://ns3018037.ip-151-80-24.eu:9003/?module=demoinfo&service=%s'
#IPOL_SERVICES_MODULE_DEMOINFO ='http://ns3018037.ip-151-80-24.eu:9003/proxy_service_call'
#proxy_service_call(self,  module, service, servicehttpmethod=None, params=None, json=None):


# demoinfo_ws_url_stats =  'stats'
demoinfo_ws_url_stats = 'stats'



# param None


# DEMO

demoinfo_ws_url_demo_list =  'demo_list'
# param None , "demo_list": [{"creation": "2015-12-28 16:47:54", "stateID": 1, "abstract": "DemoTEST1 Abstract", "title": "DemoTEST1 Title", "editorsdemoid": 23, "active": 1, "id": 1, "zipURL": "https://DemoTEST1.html", "modification": "2015-12-28 16:47:54"},
demoinfo_ws_url_demo_list_by_demoeditorid =  'demo_list_by_demoeditorid'
# param demoeditorid_list  , "demo_list": {"status": "OK", "demo_list": [{"creation": "2016-01-12 20:46:38", "stateID": 1, "abstract": "DemoTEST4 Abstract", "title": "DemoTEST4 Title", "editorsdemoid": 26, "active": 1, "id": 4, "zipURL": "https://DemoTEST4.html", "modification": "2016-01-12 20:46:38"}]}[{"c
demoinfo_ws_url_demo_list_pagination_and_filter =  'demo_list_pagination_and_filter'
# param num_elements_page, page, qfilter ,
# result	 demo list filtered and pagination {"status": "OK", "demo_list": [{"creation": "2015-12-29 15:03:07", "stateID": 1,
# 	 "abstract": "DemoTEST3 Abstract", "title": "DemoTEST3 Title", "editorsdemoid": 25, "active": 1, "id": 3, "zipURL":
# 	 "https://DemoTEST3.html", "modification": "2015-12-29 15:03:07"}], "next_page_number": null,
# 	 "previous_page_number": 1, "number": 2.0}

demoinfo_ws_url_read_demo_description =  'read_demo_description'
# params  demodescriptionID

demoinfo_ws_url_last_demodescription_from_demo =  'read_last_demodescription_from_demo'
# params  demoid,returnjsons=False, result = {'id': row[0], 'inproduction': row[1], 'creation': row[2], 'json': row[3]}

demoinfo_ws_url_save_demo_description =  'save_demo_description'
# params demoid=None result: ["demo_description_id"] = demodescription_id ["added_to_demo_id"] = demoid ["status"] = "OK"

demoinfo_ws_url_read_states =  'read_states'
# method POST,  params none,{"status": "OK", "state_list": [[1, "published", "published"], [2, "preprint", "preprint"], [3, "inactive", "inactive"]]}

demoinfo_ws_url_delete_demo =  'delete_demo'
# method POST,  params demo_id,hard_delete = False

demoinfo_ws_url_read_demo =  'read_demo_metainfo'
# method POST, params demoid result:  {"status": "OK", "creation": "2015-12-21 12:39:11", "title": "demo2", "abstract":
# "demoabstract", "stateID": 1, "editorsdemoid": 777, "active": 1, "id": 2, "zipURL": "http://prueba.com", "modification": "2015-12-21 12:39:11"}

demoinfo_ws_url_add_demo =  'add_demo'
# method POST, params editorsdemoid, title, abstract, zipURL, active, stateID, demodescriptionID=None, demodescriptionJson=None):

demoinfo_ws_url_update_demo =  'update_demo'
 # method POST,  params demo json ='{"modification": "2015-12-02 13:24:43", "title": "newdemo1", "abstract": "newdemo1abstract","creation": "2015-12-02 13:24:43", "editorsdemoid": 1, "active": 1, "stateID": 1, "id": 1, "zipURL": "http://demo1updated.com"}'


#AUTHOR


demoinfo_ws_url_author_list =  'author_list'
# param None, returns {"status": "OK", "author_list": [{"mail": "pepe@jak.com", "creation": "2015-12-31 12:18:39.015639", "id": 2, "name": "author2"}, ...

demoinfo_ws_url_author_list_pagination_and_filter =  'author_list_pagination_and_filter'
# param num_elements_page, page, qfilter

#authors of this demo
demoinfo_ws_url_author_list_for_demo =  'demo_get_authors_list'
# param demo_id, returns {"status": "OK", "author_list": [{"mail": "pepe@jak.com", "creation": "2015-12-31 12:18:39.015639", "id": 2, "name": "author2"}, ...

#authors I can assign to this demo
demoinfo_ws_url_available_author_list_for_demo =  'demo_get_available_authors_list'
# param demo_id, returns {"status": "OK", "author_list": [{"mail": "pepe@jak.com", "creation": "2015-12-31 12:18:39.015639", "id": 2, "name": "author2"}, ...

demoinfo_ws_url_delete_author =  'remove_author'
# param author_id

demoinfo_ws_url_read_author =  'read_author'
# param author_id

demoinfo_ws_url_add_author =  'add_author'
# param name,mail  returns jsonresult {"status": "OK", "authorid": 8}

demoinfo_ws_url_update_author =  'update_author'
# param author data

demoinfo_ws_url_add_author_to_demo =  'add_author_to_demo'
# param demo_id ,author_id

demoinfo_ws_url_delete_author_from_demo =  'remove_author_from_demo'
# param demo_id,author_id


#EDITOR

demoinfo_ws_url_editor_list =  'editor_list'
# param None, returns {"status": "OK", "editor_list": [{"mail": "pepe@jak.com", "creation": "2015-12-31 12:18:39.015639", "id": 2, "name": "editor2"...

demoinfo_ws_url_editor_list_pagination_and_filter =  'editor_list_pagination_and_filter'
# param num_elements_page, page, qfilter

#editors of this demo
demoinfo_ws_url_editor_list_for_demo =  'demo_get_editors_list'
# param demo_id, returns {"status": "OK", "editor_list": [{"mail": "pepe@jak.com", "creation": "2015-12-31 12:18:39.015639", "id": 2, "name": "editor2" ...

#editors I can assign to this demo
demoinfo_ws_url_available_editor_list_for_demo =  'demo_get_available_editors_list'
# param demo_id, returns {"status": "OK", "editor_list": [{"mail": "pepe@jak.com", "creation": "2015-12-31 12:18:39.015639", "id": 2, "name": "editor2" ...

demoinfo_ws_url_delete_editor =  'remove_editor'
# param editor_id

demoinfo_ws_url_read_editor =  'read_editor'
# param editor_id

demoinfo_ws_url_add_editor =  'add_editor'
# param name,mail  returns jsonresult {"status": "OK", "editorid": 8}

demoinfo_ws_url_update_editor =  'update_editor'
# param editor data

demoinfo_ws_url_add_editor_to_demo =  'add_editor_to_demo'
# param demo_id ,editor_id

demoinfo_ws_url_delete_editor_from_demo =  'remove_editor_from_demo'
# param demo_id,editor_id

#DEMO EXTRAS
demoinfo_ws_url_demo_extras_list_for_demo = 'get_compressed_file_url_ws'
#param demo_id returns JSON {"status" : "OK", "code" : "2", "url_compressed_file" : "ruta/DemoExtras.tar.gz"}
demoinfo_ws_url_delete_demo_extras_from_demo = 'delete_compressed_file_ws'
#method: POST param demo_id
demoinfo_ws_url_add_demo_extra_to_demo = 'add_compressed_file_ws'
#method: POST param demo_id

####################
#  ARCHIVE MODULE  #
####################
archive_ws_url_page = 'page' #param demo_id, page='1'
archive_ws_url_ping =  'ping'# param None
archive_ws_url_stats =  'stats'# param None
archive_ws_url_admin =  'archive_admin'# param demo_id, page
archive_ws_url_delete_experiment =  'delete_experiment'# param experiment_id
archive_ws_url_delete_blob_w_deps =  'delete_blob_w_deps'# param  id_blob
archive_ws_url_shutdown =  'shutdown'# param None
archive_ws_url_demo_list =  'demo_list'# param None

#for testing, ads an experiment to test demo (id=-1)
archive_ws_url_add_experiment_test =  'add_exp_test'# param None
archive_ws_url_delete_demo =  'delete_demo_w_deps'# param demo_id

#todo , remove if not necessary
archive_ws_url_add_experiment =  'add_experiment'# param None



####################
#   BLOBS MODULE   #
####################
#view list of available demos
blobs_demo_list =  'demos_ws'


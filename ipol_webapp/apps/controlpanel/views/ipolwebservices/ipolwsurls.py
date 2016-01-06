# coding=utf-8
from ipol_webapp.settings import IPOL_SERVICES_MODULE_ACHIVE, IPOL_SERVICES_MODULE_BLOBS, IPOL_SERVICES_MODULE_DEMOINFO

__author__ = 'josearrecio'

#todo This should go in the DB


#GLOBAL WS LIST (todo in DB)


#####################
#  DEMOINFO MODULE  #
#####################


demoinfo_ws_url_stats = IPOL_SERVICES_MODULE_DEMOINFO+'/stats'
# param Nones

# DEMO
demoinfo_ws_url_demo_list = IPOL_SERVICES_MODULE_DEMOINFO+'/demo_list'
# param None , "demo_list": [{"creation": "2015-12-28 16:47:54", "stateID": 1, "abstract": "DemoTEST1 Abstract", "title": "DemoTEST1 Title", "editorsdemoid": 23, "active": 1, "id": 1, "zipURL": "https://DemoTEST1.html", "modification": "2015-12-28 16:47:54"},
demoinfo_ws_url_demo_list_pagination_and_filter = IPOL_SERVICES_MODULE_DEMOINFO+'/demo_list_pagination_and_filter'
# param num_elements_page, page, qfilter ,
# result	 demo list filtered and pagination {"status": "OK", "demo_list": [{"creation": "2015-12-29 15:03:07", "stateID": 1,
# 	 "abstract": "DemoTEST3 Abstract", "title": "DemoTEST3 Title", "editorsdemoid": 25, "active": 1, "id": 3, "zipURL":
# 	 "https://DemoTEST3.html", "modification": "2015-12-29 15:03:07"}], "next_page_number": null,
# 	 "previous_page_number": 1, "number": 2.0}
demoinfo_ws_url_read_demo_description = IPOL_SERVICES_MODULE_DEMOINFO+'/read_demo_description'
# params  demodescriptionID
demoinfo_ws_url_last_demodescription_from_demo = IPOL_SERVICES_MODULE_DEMOINFO+'/read_last_demodescription_from_demo'
# params  demoid,returnjsons=False, result = {'id': row[0], 'inproduction': row[1], 'creation': row[2], 'json': row[3]}
demoinfo_ws_url_update_demo_description = IPOL_SERVICES_MODULE_DEMOINFO+'/update_demo_description'
# params demodescriptionID  returns data["status"] = "OK"
demoinfo_ws_url_add_demo_description = IPOL_SERVICES_MODULE_DEMOINFO+'/add_demo_description'
# params demoid=None result: ["demo_description_id"] = demodescription_id ["added_to_demo_id"] = demoid ["status"] = "OK"
demoinfo_ws_url_read_states = IPOL_SERVICES_MODULE_DEMOINFO+'/read_states'
# method POST,  params none,{"status": "OK", "state_list": [[1, "published", "published"], [2, "preprint", "preprint"], [3, "inactive", "inactive"]]}
demoinfo_ws_url_delete_demo = IPOL_SERVICES_MODULE_DEMOINFO+'/delete_demo'
# method POST,  params demo_id,hard_delete = False
demoinfo_ws_url_read_demo = IPOL_SERVICES_MODULE_DEMOINFO+'/read_demo_metainfo'
# method POST, params demoid result:  {"status": "OK", "creation": "2015-12-21 12:39:11", "title": "demo2", "abstract":
# "demoabstract", "stateID": 1, "editorsdemoid": 777, "active": 1, "id": 2, "zipURL": "http://prueba.com", "modification": "2015-12-21 12:39:11"}
demoinfo_ws_url_add_demo = IPOL_SERVICES_MODULE_DEMOINFO+'/add_demo'
# method POST, params editorsdemoid, title, abstract, zipURL, active, stateID, demodescriptionID=None, demodescriptionJson=None):
demoinfo_ws_url_update_demo = IPOL_SERVICES_MODULE_DEMOINFO+'/update_demo'
 # method POST,  params demo json ='{"modification": "2015-12-02 13:24:43", "title": "newdemo1", "abstract": "newdemo1abstract","creation": "2015-12-02 13:24:43", "editorsdemoid": 1, "active": 1, "stateID": 1, "id": 1, "zipURL": "http://demo1updated.com"}'

#AUTHOR

demoinfo_ws_url_author_list = IPOL_SERVICES_MODULE_DEMOINFO+'/author_list'
# param None, returns {"status": "OK", "author_list": [{"mail": "pepe@jak.com", "creation": "2015-12-31 12:18:39.015639", "id": 2, "name": "author2"}, ...
demoinfo_ws_url_author_list_pagination_and_filter = IPOL_SERVICES_MODULE_DEMOINFO+'/author_list_pagination_and_filter'
# param num_elements_page, page, qfilter

demoinfo_ws_url_delete_author = IPOL_SERVICES_MODULE_DEMOINFO+'/remove_author'
# param author_id
demoinfo_ws_url_read_author = IPOL_SERVICES_MODULE_DEMOINFO+'/read_author'
# param author_id
demoinfo_ws_url_add_author = IPOL_SERVICES_MODULE_DEMOINFO+'/add_author'
# param name,mail  returns jsonresult {"status": "OK", "authorid": 8}

demoinfo_ws_url_update_author = IPOL_SERVICES_MODULE_DEMOINFO+'/update_author'
# param author data


demoinfo_ws_url_add_author_to_demo = IPOL_SERVICES_MODULE_DEMOINFO+'/add_author_to_demo'
# param demo_id ,author_id


#EDITOR
demoinfo_ws_url_editor_list = IPOL_SERVICES_MODULE_DEMOINFO+'/editor_list'
 # param None


####################
#  ARCHIVE MODULE  #
####################
archive_ws_url_page =IPOL_SERVICES_MODULE_ACHIVE+'/page' #param demo_id, page='1'
archive_ws_url_ping = IPOL_SERVICES_MODULE_ACHIVE+'/ping'# param None
archive_ws_url_stats = IPOL_SERVICES_MODULE_ACHIVE+'/stats'# param None
archive_ws_url_admin = IPOL_SERVICES_MODULE_ACHIVE+'/archive_admin'# param demo_id, page
archive_ws_url_delete_experiment = IPOL_SERVICES_MODULE_ACHIVE+'/delete_experiment'# param experiment_id
archive_ws_url_delete_blob_w_deps = IPOL_SERVICES_MODULE_ACHIVE+'/delete_blob_w_deps'# param  id_blob
archive_ws_url_shutdown = IPOL_SERVICES_MODULE_ACHIVE+'/shutdown'# param None
archive_ws_url_demo_list = IPOL_SERVICES_MODULE_ACHIVE+'/demo_list'# param None

#for testing, ads an experiment to test demo (id=-1)
archive_ws_url_add_experiment_test = IPOL_SERVICES_MODULE_ACHIVE+'/add_exp_test'# param None
archive_ws_url_delete_demo = IPOL_SERVICES_MODULE_ACHIVE+'/delete_demo_w_deps'# param demo_id

#todo
archive_ws_url_add_experiment = IPOL_SERVICES_MODULE_ACHIVE+'/add_experiment'# param None



####################
#   BLOBS MODULE   #
####################
#view list of available demos
blobs_demo_list=IPOL_SERVICES_MODULE_BLOBS+'/demos_ws'

"""
delete_experiment_web

	http://boucantrin.ovh.hw.ipol.im:9000/delete_experiment_web?experiment_id=21&demo_id=-1



"""
"""

delete_experiment

/delete_experiment'# experiment_id): todo:document

        Encapsulation of the delete_exp_w_deps function for removing an
            experiment.

        :rtype: JSON formatted string
        self.delete_exp_w_deps(conn, experiment_id)


    def delete_exp_w_deps(self, conn, experiment_id):

        This function remove, in the database, an experiment from
            the experiment table, and its dependencies in the correspondence
            table. If the blobs are used only in this experiment, they will be
            removed too.

"""
#
# http://<localhost>:<port>/add_exp_test?demo_id=42&blobs=<json_blobs>&parameters=<json_parameters>
# The method “add experiment” takes in the entry of the id of the demo used ; a JSON string of the format :
# {
#     url_blob : name,
# ... }
# containing a description of each blob used by and produced by the experiment, with their temporary URLs and names ;
#  and a JSON string describing the parameters of the demo used for the experiment. It will add an experiment to the
#  database by creating a new entry in the experiment table. If the blobs used by and produced by the experiment aren’t
# already in the database, it will copy them in the directory given in the configuration file, and create a thumbnail
#  for the images. It will return a json string containing the status of the operation, OK if it succeeded, KO if there
#  was an error and the operation wasn’t performed, as such :
# {
#     status : OK/KO
# }
# ￼￼If status is KO, a log describing the error will be written.
# 14
# Deleting an experiment from the archive
# When removing an experiment from the database via the method “delete experiment”, every blob linked to this experiment
#  and only to this experiment is removed.
# After that, all the entries in the correspondence table referencing this experiment are removed automatically due to
#  a foreign key constraint. It return
# a json response containing the status of the operation of the same format as the return of the method “add experiment”
# . The method shouldn’t be called anywhere else than through the user interface described later.
# Deleting a blob from the archive
# Due to a many-to-many link between blobs and experiments in the database, a blob has a lot of dependencies : it has
# of course the experiments using this blobs, but also the blobs linked to these experiments. For deletion of a blob
# from the archive, the precedent service is called on each experiment the blob is part of, assuring that no orphan
# data stay in the database (e.g. experiments linked to removed blobs or blobs linked to removed experiments).
#  The method implementing this service is “delete blob w deps”. It return a json response containing the status of
# the operation in the same format as the return of the method “add experiment”. The method shouldn’t be called anywhere
# else than through the user interface described later.

# Getting data
# Example :
# http://<localhost>:<port>/page?demo_id=42&page=3
# The method “page” returns a JSON response with, for a given page of a given demo, all the data of the experiments
# that should be displayed on this page. Twelve experiments are displayed by page. For rendering the archive page in
# the browser, the JSON response should be parsed and interpreted in a dedicated template furnished by the front-end
# of another module. The JSON response is formatted this way :
# {
#     status :  OK/KO,
#     experiments : [
#         {
#             date : timestamp_example,
#             files : [
#                 {
#                     url : url_example,
# 15
# ￼￼￼￼￼￼
# } ... ],
# id : id_example,
# name : name_example,
# url_thumb : url_thumbnail_example
#             id : id_example,
#             parameters = {parameters_example...}
#     ... ],
#     id_demo : id_demo_example,
#     nb_pages : nb_pages_example
# }

# Administrator interface for removing blobs/experiments

# Example :
# http://<localhost>:<port>/archive_admin?demo_id=42&page=3
# The only user interface furnished by the archive module is for removing blobs or experiment in a convenient manner.
# It uses the json response of the precedent service and renders the “archive admin tmp.html” template displaying a
#  page of archives for given demo, allowing the deletion of both blobs and experiments by simply linking to two other
#  services calling deletion methods and updating the template. In case of error, for example when invalid data is given
#  through URL, “error.html” is rendered.


# Example :
# http://<localhost>:<port>/shutdown
# The method “Shutdown” shuts down the archive application when called. It returns a json response containing the
# status of the operation.
# Other services
# Other services features the method “ping”, simply for checking if the module is up, and the method “stats”, formatted
# this way :
# ￼￼{
#     status : OK/KO,
#     nb_experiments : x,
# nb_blobs : y }

# Example :
# http://<localhost>:<port>/ping

# Example :
# http://<localhost>:<port>/stats

#BLOBS


# add_blob_ws
# ￼￼
# add blob to database
# demo id path tag ext the set title credit { return:OK or KO, the hash: ... }
# ￼￼
# ￼
# add_demo_ws
# ￼￼
# add demo to database name is template template
# { return:OK or KO }
# ￼
# add_tag_to_blob_ws
# ￼￼￼￼
# add tag to database blob id tag
# { return:OK or KO }
# ￼
# delete_blob_ws
# ￼￼
# delete blob from id demo and id blob demo id blob id
# { return:OK or KO, delete: (hash, extension) }
# ￼￼
# ￼￼
# get_blob_ws
# ￼￼
# return blob information from id
# blob id
# { return:OK or KO, {id, hash, extension, credit } }
# ￼
# 10
# get_blobs_from_template_ws
# ￼￼￼￼
# list blobs from name template template
# { return:OK or KO, blobs: {id, hash, extension, format } }
# get blobs of demo- by name ws
# ￼￼￼￼￼￼
# list_blobs_from_demo_name
# demo name
# { return:OK or KO, blobs: {id, hash,
# extension, format }, use template: {id: name, is template, id template}}
# ￼
# ￼￼￼
# get_blobs_of_demo_ws
# ￼￼￼￼
# list blobs from demo id demo
# { return:OK or KO, blobs: {id, hash, extension, format }, use template: {id: name, is template, id template}}
# ￼￼￼
# get_tags_ws
# ￼￼
# return list tags from blob id blob id
# { {id: name} }
# ￼
# get_template_demo_ws
# ￼￼￼
# return list demos templated
# { return:OK or KO, list template: {id: name} }
# ￼
# op_remove_demo_ws
# ￼￼￼
# remove demo from id demo demo id
# { return:OK or KO }
# ￼
# remove_tag_from_blob_ws
# ￼￼￼￼
# remove tag for a blob from id tag and id blob
# id tag id blob id
# { return:OK or KO }
# ￼￼
# set_template_ws
# ￼￼
# change the current template used by a demo
# demo id id name
# { return:OK or KO }
# coding=utf-8
from ipol_webapp.settings import IPOL_SERVICES_MODULE_PROXY, IPOL_SERVICES_MODULE_DEMOINFO, \
        IPOL_SERVICES_MODULE_ACHIVE, IPOL_SERVICES_MODULE_BLOBS, HOST_NAME

__author__ = 'josearrecio'
import json
import requests
# from poster.encode import MultipartParam
from django.core.files.base import ContentFile
import logging
from apps.controlpanel.views.ipolwebservices.ipolwsurls import archive_ws_url_stats, archive_ws_url_page, archive_ws_url_get_experiment, \
        archive_ws_url_shutdown, archive_ws_url_delete_experiment, archive_ws_url_delete_blob_w_deps, archive_ws_url_add_experiment_test, \
        archive_ws_url_demo_list, archive_ws_url_delete_demo, demoinfo_ws_url_stats, demoinfo_ws_url_demo_list, \
        demoinfo_ws_url_author_list, demoinfo_ws_url_delete_demo, demoinfo_ws_url_read_demo_description, \
        demoinfo_ws_url_last_demodescription_from_demo, \
        demoinfo_ws_url_save_demo_description, demoinfo_ws_url_read_demo, demoinfo_ws_url_read_states, \
        demoinfo_ws_url_update_demo, demoinfo_ws_url_add_demo, demoinfo_ws_url_demo_list_pagination_and_filter, \
        demoinfo_ws_url_author_list_pagination_and_filter, demoinfo_ws_url_delete_author, demoinfo_ws_url_read_author, \
        demoinfo_ws_url_update_author, demoinfo_ws_url_add_author, demoinfo_ws_url_add_author_to_demo, \
        demoinfo_ws_url_author_list_for_demo, demoinfo_ws_url_available_author_list_for_demo, \
        demoinfo_ws_url_delete_author_from_demo, demoinfo_ws_url_editor_list, demoinfo_ws_url_editor_list_for_demo, \
        demoinfo_ws_url_available_editor_list_for_demo, demoinfo_ws_url_editor_list_pagination_and_filter, \
        demoinfo_ws_url_delete_editor, demoinfo_ws_url_add_editor, demoinfo_ws_url_read_editor, \
        demoinfo_ws_url_update_editor, demoinfo_ws_url_add_editor_to_demo, demoinfo_ws_url_delete_editor_from_demo,demoinfo_ws_url_demo_extras_for_demo, \
        demoinfo_ws_url_delete_demo_extras_from_demo,demoinfo_ws_url_demo_list_by_demoeditorid, \
        proxy_ws_url_stats,demoinfo_ws_url_add_demo_extra_to_demo,archive_ws_url_update_demo_id,blobs_update_demo_id, \
        get_demo_owned_blobs, edit_blob_from_demo, remove_blob_from_demo,get_demo_templates,add_blob_to_demo, remove_vr_from_demo,\
        get_all_templates

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
def get_JSON_from_webservice(module,service, METHOD=None, params=None, json=None, files=None):
    """
    MAKES THE WEBSERVICE CALL using reuqests library, expects ws to return a valid JSON

    http://docs.python-requests.org/en/latest/user/quickstart/
    Instead of encoding the dict yourself, you can also pass it directly using the json parameter
    (added in version 2.4.2) and it will be encoded automatically:

    """
    #todo if needeed insert schema validation here
    url = 'http://{}/api/{}/{}'.format(
            HOST_NAME,
            module,
            service
    )
    try:
        if not METHOD or METHOD=='GET':
            response = requests.get(url,params=params)
        elif METHOD=='POST':
            if json is not None:
                if files is not None:
                    response = requests.post(url, params=params, data=json, files=files)
                else:
                    response = requests.post(url, params=params, data=json)
            else:
                if files is not None:
                    response = requests.post(url, params=params, files=files)
                else:
                    response = requests.post(url, params=params)
        else:
            msg="get_JSON_from_webservice: Not valid METHOD: %s" % result
            logger.error(msg)
            print(msg)
            raise ValueError(msg)

        result =  response.content

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


# MISC


def demoinfo_get_stats():

    service_name = demoinfo_ws_url_stats

    serviceparams = None
    servicejson = None
    return get_JSON_from_webservice("demoinfo", service_name, METHOD='GET', params=serviceparams, json=servicejson)



def demoinfo_get_states():

    service_name = demoinfo_ws_url_read_states

    serviceparams = None
    servicejson = None
    return get_JSON_from_webservice("demoinfo", service_name, METHOD='GET', params=serviceparams, json=servicejson)



# DDL


def demoinfo_get_ddl(demo_id):


    service_name = demoinfo_ws_url_last_demodescription_from_demo

    #proxy can be called by GET or POST, prefer POST if submiting data to server
    module = "demoinfo"
    serviceparams = {'demo_id': demo_id}
    #send as string to proxy, proxy will load this into a dict for the request lib call

    servicejson = None
    return get_JSON_from_webservice(module, service_name, METHOD='POST', params=serviceparams, json=servicejson)




def demoinfo_read_demo_description(demo_descp_id):

    service_name = demoinfo_ws_url_read_demo_description

    #proxy can be called by GET or POST, prefer POST if submiting data to server
    module = "demoinfo"
    serviceparams = {'demodescriptionID': demo_descp_id}
    #send as string to proxy, proxy will load this into a dict for the request lib call

    servicejson = None
    return get_JSON_from_webservice(module, service_name, METHOD='POST', params=serviceparams, json=servicejson)



def demoinfo_save_demo_description(pjson,demoid):

    service_name = demoinfo_ws_url_save_demo_description

    #proxy can be called by GET or POST, prefer POST if submiting data to server
    module = "demoinfo"
    serviceparams = {'demoid': demoid}
    #send as string to proxy, proxy will load this into a dict for the request lib call

    servicejson = pjson
    return get_JSON_from_webservice(module, service_name, METHOD='POST', params=serviceparams, json=servicejson)




# DEMO

#todo se usa esto?
def demoinfo_demo_list():
    """
    list demos present in database
    { return:OK or KO, list demos:
    """

    service_name = demoinfo_ws_url_demo_list
    module = "demoinfo"

    serviceparams = None
    servicejson = None
    return get_JSON_from_webservice(module, service_name, METHOD='GET', params=serviceparams, json=servicejson)




def demoinfo_demo_list_by_demoeditorid(demoeditorid_list):
    """
    list demos present in database with demo_editor_id in  demoeditorid_list
    demoeditorid_list must be sent to WS as a JSON string
    if no demoeditorid_list is provided return None

    { return:OK or KO, list demos:...
    """

    service_name = demoinfo_ws_url_demo_list_by_demoeditorid
    module = "demoinfo"
    result = None

    if demoeditorid_list :

        serviceparams = {'demoeditorid_list': json.dumps(demoeditorid_list)}

        servicejson = None
        result = get_JSON_from_webservice(module, service_name, METHOD='GET', params=serviceparams, json=servicejson)

    return result


def demoinfo_demo_list_pagination_and_filtering( num_elements_page, page, qfilter):
    """
    list demos present in database
    demo_list_pagination_and_filter(self,num_elements_page,page,qfilter):
     demo list filtered and pagination {"status": "OK", "demo_list": [{"creation": "2015-12-29 15:03:07", "state": published,
     "abstract": "DemoTEST3 Abstract", "title": "DemoTEST3 Title", "editorsdemoid": 25, "id": 3, "zipURL":
     "https://DemoTEST3.html", "modification": "2015-12-29 15:03:07"}], "next_page_number": null,
     "previous_page_number": 1, "number": 2.0}
    """

    service_name = demoinfo_ws_url_demo_list_pagination_and_filter

    #proxy can be called by GET or POST, prefer POST if submiting data to server
    module = "demoinfo"
    serviceparams = {'num_elements_page': num_elements_page,'page':page,'qfilter':qfilter}
    #send as string to proxy, proxy will load this into a dict for the request lib call
    servicejson = None
    return get_JSON_from_webservice(module, service_name, METHOD='POST', params=serviceparams, json=servicejson)

def demoinfo_delete_demo(demo_id):

    service_name = demoinfo_ws_url_delete_demo
    module = "demoinfo"

    serviceparams = {'demo_id': demo_id}

    servicejson = None
    return get_JSON_from_webservice(module, service_name, METHOD='POST', params=serviceparams, json=servicejson)


def demoinfo_read_demo(demo_id):

    service_name = demoinfo_ws_url_read_demo
    module = "demoinfo"

    serviceparams = {"demoid": demo_id}
    #send as string to proxy, proxy will load this into a dict for the request lib call

    servicejson = None
    return get_JSON_from_webservice(module, service_name, METHOD='POST', params=serviceparams, json=servicejson)




def demoinfo_update_demo(demo,old_editor_demoid):

    demoinfo_params = {'demo': json.dumps(demo),'old_editor_demoid':old_editor_demoid}
    blobs_params = {'new_demo_id': demo['editorsdemoid'],'old_demo_id':old_editor_demoid}
    archive_params = {'new_demo_id': demo['editorsdemoid'],'old_demo_id':old_editor_demoid}

    demoinfo_resp = get_JSON_from_webservice('demoinfo', demoinfo_ws_url_update_demo, METHOD='POST', params=demoinfo_params, json=None)
    if json.loads(demoinfo_resp)['status'] == 'KO':
        return demoinfo_resp

    blob_resp = get_JSON_from_webservice('blobs',blobs_update_demo_id,METHOD='POST',params=blobs_params,json=None)
    if json.loads(blob_resp)['status'] == 'KO':
        return blob_resp

    archive_resp = get_JSON_from_webservice('archive',archive_ws_url_update_demo_id,METHOD='POST',params=archive_params,json=None)
    if json.loads(archive_resp)['status'] == 'KO':
        return archive_resp

    return demoinfo_resp



def demoinfo_add_demo(editorsdemoid ,title ,abstract,zipURL ,state):

    service_name = demoinfo_ws_url_add_demo

    #proxy can be called by GET or POST, prefer POST if submiting data to server
    module = "demoinfo"
    serviceparams = {'editorsdemoid': editorsdemoid,'title': title,'abstract': abstract,'zipURL': zipURL,'state': state}
    #send as string to proxy, proxy will load this into a dict for the request lib call

    servicejson = None
    return get_JSON_from_webservice(module, service_name, METHOD='POST', params=serviceparams, json=servicejson)



# AUTHOR


def demoinfo_author_list():

    service_name = demoinfo_ws_url_author_list
    module = "demoinfo"

    serviceparams = None
    servicejson = None
    return get_JSON_from_webservice(module, service_name, METHOD='POST', params=serviceparams, json=servicejson)


def demoinfo_author_list_for_demo(demo_id):

    service_name = demoinfo_ws_url_author_list_for_demo
    module = "demoinfo"

    serviceparams = {'demo_id': demo_id}

    servicejson = None
    return get_JSON_from_webservice(module, service_name, METHOD='GET', params=serviceparams, json=servicejson)




def demoinfo_available_author_list_for_demo(demo_id = None):

    service_name = demoinfo_ws_url_available_author_list_for_demo
    module = "demoinfo"

    serviceparams = {'demo_id': demo_id}

    servicejson = None
    return get_JSON_from_webservice(module, service_name, METHOD='GET', params=serviceparams, json=servicejson)




def demoinfo_author_list_pagination_and_filtering( num_elements_page, page, qfilter):

    service_name = demoinfo_ws_url_author_list_pagination_and_filter
    module = "demoinfo"

    serviceparams = {'num_elements_page': num_elements_page,'page':page,'qfilter':qfilter}

    servicejson = None
    return get_JSON_from_webservice(module, service_name, METHOD='GET', params=serviceparams, json=servicejson)



def demoinfo_delete_author(author_id):

    service_name = demoinfo_ws_url_delete_author
    module = "demoinfo"

    serviceparams = {'author_id': author_id}

    servicejson = None
    return get_JSON_from_webservice(module, service_name, METHOD='POST', params=serviceparams, json=servicejson)



def demoinfo_add_author( name ,mail):

    service_name = demoinfo_ws_url_add_author
    module = "demoinfo"

    serviceparams = {'name': name,'mail': mail}

    servicejson = None
    return get_JSON_from_webservice(module, service_name, METHOD='POST', params=serviceparams, json=servicejson)



def demoinfo_read_author(author_id):

    service_name = demoinfo_ws_url_read_author
    module = "demoinfo"

    serviceparams = {'authorid': author_id}

    servicejson = None
    return get_JSON_from_webservice(module, service_name, METHOD='POST', params=serviceparams, json=servicejson)



def demoinfo_update_author(author):

    service_name = demoinfo_ws_url_update_author
    module = "demoinfo"

    serviceparams = {'author': json.dumps(author)}

    servicejson = None
    return get_JSON_from_webservice(module, service_name, METHOD='POST', params=serviceparams, json=servicejson)



def demoinfo_add_author_to_demo( demo_id ,author_id):

    service_name = demoinfo_ws_url_add_author_to_demo
    module = "demoinfo"

    serviceparams = {'demo_id': demo_id,'author_id': author_id}

    servicejson = None
    return get_JSON_from_webservice(module, service_name, METHOD='POST', params=serviceparams, json=servicejson)


def demoinfo_delete_author_from_demo(demo_id,author_id):

    service_name = demoinfo_ws_url_delete_author_from_demo
    module = "demoinfo"

    serviceparams = {'demo_id': demo_id,'author_id': author_id}

    servicejson = None
    return get_JSON_from_webservice(module, service_name, METHOD='POST', params=serviceparams, json=servicejson)


#EDITOR


def demoinfo_editor_list():

    service_name = demoinfo_ws_url_editor_list
    module = "demoinfo"

    serviceparams = None
    servicejson = None
    return get_JSON_from_webservice(module, service_name, METHOD='GET', params=serviceparams, json=servicejson)


def demoinfo_editor_list_for_demo(demo_id):

    service_name = demoinfo_ws_url_editor_list_for_demo
    module = "demoinfo"

    serviceparams = {'demo_id': demo_id}

    servicejson = None
    return get_JSON_from_webservice(module, service_name, METHOD='GET', params=serviceparams, json=servicejson)



def demoinfo_available_editor_list_for_demo(demo_id=None):

    service_name = demoinfo_ws_url_available_editor_list_for_demo
    module = "demoinfo"

    serviceparams = {'demo_id': demo_id}

    servicejson = None
    return get_JSON_from_webservice(module, service_name, METHOD='GET', params=serviceparams, json=servicejson)



def demoinfo_editor_list_pagination_and_filtering( num_elements_page, page, qfilter):

    service_name = demoinfo_ws_url_editor_list_pagination_and_filter
    module = "demoinfo"


    serviceparams = {'num_elements_page': num_elements_page,'page':page,'qfilter':qfilter}

    servicejson = None
    return get_JSON_from_webservice(module, service_name, METHOD='GET', params=serviceparams, json=servicejson)



def demoinfo_delete_editor(editor_id):

    service_name = demoinfo_ws_url_delete_editor
    module = "demoinfo"

    serviceparams = {'editor_id': editor_id}

    servicejson = None
    return get_JSON_from_webservice(module, service_name, METHOD='POST', params=serviceparams, json=servicejson)


def demoinfo_add_editor( name ,mail):

    service_name = demoinfo_ws_url_add_editor
    module = "demoinfo"

    serviceparams = {'name': name,'mail': mail}

    servicejson = None
    return get_JSON_from_webservice(module, service_name, METHOD='POST', params=serviceparams, json=servicejson)



def demoinfo_read_editor(editor_id):

    service_name = demoinfo_ws_url_read_editor
    module = "demoinfo"

    serviceparams = {'editorid': editor_id}

    servicejson = None
    return get_JSON_from_webservice(module, service_name, METHOD='POST', params=serviceparams, json=servicejson)



def demoinfo_update_editor(editor):

    service_name = demoinfo_ws_url_update_editor
    module = "demoinfo"

    serviceparams = {'editor': json.dumps(editor)}

    servicejson = None
    return get_JSON_from_webservice(module, service_name, METHOD='POST', params=serviceparams, json=servicejson)


def demoinfo_add_editor_to_demo( demo_id ,editor_id):

    service_name = demoinfo_ws_url_add_editor_to_demo
    module = "demoinfo"

    serviceparams = {'demo_id': demo_id,'editor_id': editor_id}

    servicejson = None
    return get_JSON_from_webservice(module, service_name, METHOD='POST', params=serviceparams, json=servicejson)

def demoinfo_delete_editor_from_demo(demo_id,editor_id):

    service_name = demoinfo_ws_url_delete_editor_from_demo
    module = "demoinfo"

    serviceparams = {'demo_id': demo_id,'editor_id': editor_id}

    servicejson = None
    return get_JSON_from_webservice(module, service_name, METHOD='POST', params=serviceparams, json=servicejson)

#DEMO EXTRAS

def demoinfo_demo_extras_for_demo(demo_id):

    service_name = demoinfo_ws_url_demo_extras_for_demo
    module = "demoinfo"

    serviceparams = {'demo_id': demo_id}

    servicejson = None
    return get_JSON_from_webservice(module, service_name, METHOD='GET', params=serviceparams, json=servicejson)

def demoinfo_delete_demo_extras_from_demo(demo_id):

    service_name = demoinfo_ws_url_delete_demo_extras_from_demo
    module = "demoinfo"

    serviceparams = {'demo_id': demo_id}

    servicejson = None
    return get_JSON_from_webservice(module, service_name, METHOD='POST', params=serviceparams, json=servicejson)

def demoinfo_add_demo_extra_to_demo(demo_id, request):

    service_name = demoinfo_ws_url_add_demo_extra_to_demo
    module = "demoinfo"
    files=None
    serviceparams = {'demo_id': demo_id}

    try:
        myfile = request.FILES['myfile']
        files = {'file_0': myfile.file}
    except Exception as ex:
        print ex
    servicejson = None
    return get_JSON_from_webservice(module, service_name, METHOD='POST', params=serviceparams, json=servicejson, files=files)


####################
#  ARCHIVE MODULE  #
####################

def archive_get_page(experimentid , page='1'):
    """
    The method “page” returns a JSON response with, for a given page of a given demo, all the data of the experiments
    that should be displayed on this page. Twelve experiments are displayed by page. For rendering the archive page in
    the browser
    """

    service_name = archive_ws_url_page
    module = "archive"

    serviceparams = {'demo_id': experimentid, 'page': page}

    servicejson = None
    return get_JSON_from_webservice(module, service_name, METHOD='GET', params=serviceparams, json=servicejson)

def archive_get_experiment(experiment_id):
    """
    The method returns a JSON response with all the data of the experiment with id=experiment_id
    """

    service_name = archive_ws_url_get_experiment
    module = "archive"

    serviceparams = {'experiment_id': experiment_id}

    servicejson = None
    return get_JSON_from_webservice(module, service_name, METHOD='GET', params=serviceparams, json=servicejson)


def archive_get_stats():
    """
    The method “page” returns a JSON response with, for a given page of a given demo, all the data of the experiments
    that should be displayed on this page. Twelve experiments are displayed by page. For rendering the archive page in
    the browser
    """

    service_name = archive_ws_url_stats
    module = "archive"


    serviceparams = None
    servicejson = None
    return get_JSON_from_webservice(module, service_name, METHOD='GET', params=serviceparams, json=servicejson)



#todo remove this method not used any more
def archive_shutdown():
    """
    Shutdown archive
    """

    service_name = archive_ws_url_shutdown
    module = "archive"

    serviceparams = None
    servicejson = None
    return get_JSON_from_webservice(module, service_name, METHOD='GET', params=serviceparams, json=servicejson)



def archive_demo_list():
    """
    list demos present in database
    { return:OK or KO, list demos: {id,name, id template, template } }
    """

    service_name = archive_ws_url_demo_list
    module = "archive"

    serviceparams = None
    servicejson = None
    return get_JSON_from_webservice(module, service_name, METHOD='GET', params=serviceparams, json=servicejson)



def archive_add_experiment_to_test_demo():
#todo delete should use POST
    service_name = archive_ws_url_add_experiment_test
    module = "archive"

    serviceparams = None
    servicejson = None

    return get_JSON_from_webservice(module, service_name, METHOD='GET', params=serviceparams, json=servicejson)



def archive_delete_demo(demo_id):
#todo delete should use POST
    service_name = archive_ws_url_delete_demo
    module = "archive"

    serviceparams = {'demo_id': demo_id}

    servicejson = None
    return get_JSON_from_webservice(module, service_name, METHOD='GET', params=serviceparams, json=servicejson)


def archive_delete_experiment(experiment_id):
#todo delete should use POST
    service_name = archive_ws_url_delete_experiment
    module = "archive"

    serviceparams = {'experiment_id': experiment_id}

    servicejson = None
    return get_JSON_from_webservice(module, service_name, METHOD='GET', params=serviceparams, json=servicejson)



def archive_delete_file(file_id):
#todo delete should use POST
    service_name = archive_ws_url_delete_blob_w_deps
    module = "archive"
    serviceparams = {'id_blob': file_id}

    servicejson = None
    return get_JSON_from_webservice(module, service_name, METHOD='GET', params=serviceparams, json=servicejson)



####################
#   BLOBS MODULE   #
####################


def get_demo_owned_blobs(demo_id):
    """
    Get the demo owned blobs
    """
    service_name = "get_demo_owned_blobs"
    #[todo] Change blobs2 to blobs
    module = "blobs"
    serviceparams = {'demo_id': demo_id}

    servicejson = None
    return get_JSON_from_webservice(module, service_name, METHOD='GET',params=serviceparams, json=servicejson)

def get_demo_templates(demo_id):
    """
    Get the demo owned blobs
    """
    service_name = "get_demo_templates"
    #[todo] Change blobs2 to blobs
    module = "blobs"
    serviceparams = {'demo_id': demo_id}

    servicejson = None
    return get_JSON_from_webservice(module, service_name, METHOD='GET',params=serviceparams, json=servicejson)

def edit_blob_from_demo(request,demo_id,tags,blob_set,new_blob_set,pos_set,new_pos_set,title,credit):
    """
    Get the demo owned blobs
    """
    service_name = "edit_blob_from_demo"
    module = "blobs"

    files = None
    try:
        if 'vr' in request.FILES:
            files = {'vr': request.FILES['vr'].file}
    except Exception as ex:
        print ex

    serviceparams = {'demo_id': demo_id, 'tags':tags, 'blob_set':blob_set,'new_blob_set':new_blob_set,
                     'pos_set':pos_set, 'new_pos_set':new_pos_set, 'title':title, 'credit':credit}

    return get_JSON_from_webservice(module, service_name, METHOD='POST',params=serviceparams, files=files)

def remove_blob_from_demo(demo_id, blob_set, pos_set):
    """
    Remove blob from demo
    """
    service_name = "remove_blob_from_demo"
    module = "blobs"
    serviceparams = {'demo_id': demo_id, 'blob_set': blob_set, 'pos_set': pos_set}

    return get_JSON_from_webservice(module, service_name, METHOD='GET', params=serviceparams)

def remove_template_from_demo(demo_id, template):
    """
    Remove blob from demo
    """
    service_name = "remove_template_from_demo"
    module = "blobs"
    serviceparams = {'demo_id': demo_id, 'template_name':template}

    return get_JSON_from_webservice(module, service_name, METHOD='GET', params=serviceparams)

def add_template_to_demo(demo_id, template):
    """
    Remove blob from demo
    """
    service_name = "add_templates_to_demo"
    module = "blobs"
    serviceparams = {'demo_id': demo_id, 'template_names':template}

    return get_JSON_from_webservice(module, service_name, METHOD='GET', params=serviceparams)

def add_blob_to_demo(request,demo_id,tags,blob_set,pos_set,title,credit):
    """
    Add a new blob to the demo
    """
    service_name = "add_blob_to_demo"
    module = "blobs"
    params = {'demo_id': demo_id, 'tags': tags, 'title': title, 'credit': credit}

    if blob_set !="":
        params['blob_set'] = blob_set
        params['pos_set'] = pos_set

    try:
        files = {'blob': request.FILES['blob'].file}
        if 'vr' in request.FILES:
            files['blob_vr']= request.FILES['vr'].file
    except Exception as ex:
        print ex

    return get_JSON_from_webservice(module, service_name, METHOD='POST', params=params, files=files)

def remove_vr_from_demo(demo_id, set, pos):
    """
    Remove the visual representation of the blob in the demo (in all the demos and templates)
    """
    service_name = "remove_visual_representation_from_demo"
    module = "blobs"
    serviceparams = {'demo_id': demo_id, 'blob_set': set, 'pos_set': pos}
    return get_JSON_from_webservice(module, service_name, METHOD='GET', params=serviceparams)

def get_all_templates():
    """
    Remove the visual representation of the blob in the demo (in all the demos and templates)
    """
    service_name = "get_all_templates"
    module = "blobs"
    return get_JSON_from_webservice(module, service_name, METHOD='GET')

def get_template_blobs(name):
    """
    Get template blobs
    """
    service_name = "get_template_blobs"
    module = "blobs"
    serviceparams = {'template_name': name}
    return get_JSON_from_webservice(module, service_name, METHOD='GET', params=serviceparams)

def add_blob_to_template(request,name,tags,blob_set,pos_set,title,credit):
    """
    Add a new blob to the template
    """
    service_name = "add_blob_to_template"
    module = "blobs"
    params = {'template_name': name, 'tags': tags, 'title': title, 'credit': credit}

    if blob_set !="":
        params['blob_set'] = blob_set
        params['pos_set'] = pos_set

    try:
        files = {'blob': request.FILES['blob'].file}
        if 'vr' in request.FILES:
            files['blob_vr']= request.FILES['vr'].file
    except Exception as ex:
        print ex

    return get_JSON_from_webservice(module, service_name, METHOD='POST', params=params, files=files)

def remove_blob_from_template(name, blob_set, pos_set):
    """
    Remove blob from template
    """
    service_name = "remove_blob_from_template"
    module = "blobs"
    serviceparams = {'template_name': name, 'blob_set': blob_set, 'pos_set': pos_set}
    return get_JSON_from_webservice(module, service_name, METHOD='GET', params=serviceparams)


def remove_vr_from_template(name, set, pos):
    """
    Remove the visual representation of the blob in the template (in all the demos and templates)
    """
    service_name = "remove_visual_representation_from_template"
    module = "blobs"
    serviceparams = {'template_name': name, 'blob_set': set, 'pos_set': pos}
    return get_JSON_from_webservice(module, service_name, METHOD='GET', params=serviceparams)

def edit_blob_from_template(request, name, tags, blob_set, new_blob_set, pos_set, new_pos_set, title, credit):
    """
    Edit blob info from template
    """
    service_name = "edit_blob_from_template"
    module = "blobs"

    files = None
    try:
        if 'vr' in request.FILES:
            files = {'vr': request.FILES['vr'].file}
    except Exception as ex:
        print ex

    serviceparams = {'template_name': name, 'tags':tags, 'blob_set':blob_set, 'new_blob_set':new_blob_set,
                     'pos_set':pos_set, 'new_pos_set':new_pos_set, 'title':title, 'credit':credit}

    return get_JSON_from_webservice(module, service_name, METHOD='POST', params=serviceparams, files=files)

def get_all_templates():
    """
    Get all the templates
    """
    service_name = "get_all_templates"
    module = "blobs"
    return get_JSON_from_webservice(module, service_name, METHOD='GET')

def delete_template(name):
    """
    Get all the templates
    """
    service_name = "remove_template"
    module = "blobs"
    serviceparams = {'template_name': name}
    return get_JSON_from_webservice(module, service_name, METHOD='GET', params=serviceparams)

def create_template(name):
    """
    Get all the templates
    """
    service_name = "create_template"
    module = "blobs"
    serviceparams = {'template_name': name}
    return get_JSON_from_webservice(module, service_name, METHOD='GET', params=serviceparams)
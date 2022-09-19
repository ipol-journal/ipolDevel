# [Miguel] [ToDo] Get rid of all these wrapper functions and call directly the API.
# We want the opposite: give visibility to the API, instead of using useless indirections.

# coding=utf-8
from ipol_webapp.settings import IPOL_SERVICES_MODULE_PROXY, IPOL_SERVICES_MODULE_DEMOINFO, \
    IPOL_SERVICES_MODULE_ACHIVE, IPOL_SERVICES_MODULE_BLOBS, HOST_NAME

import json
import requests
# from poster.encode import MultipartParam
from django.core.files.base import ContentFile
import logging

logger = logging.getLogger(__name__)


####################
#     UTILITIES    #
####################

def is_json(myjson):
    try:
        json_object = json.loads(myjson)
    except Exception, e:
        print("e:%s" % e)
        return False
    return True


# todo add param for html verb, get post etc
def http_request(path, METHOD=None, params=None, json=None, files=None):
    """
    MAKES THE WEBSERVICE CALL using reuqests library, expects ws to return a valid JSON

    http://docs.python-requests.org/en/latest/user/quickstart/
    Instead of encoding the dict yourself, you can also pass it directly using the json parameter
    (added in version 2.4.2) and it will be encoded automatically:

    """
    url = 'http://{}/{}'.format(HOST_NAME, path)
    try:
        if not METHOD or METHOD == 'GET':
            response = requests.get(url, params=params)
        elif METHOD == 'POST':
            response = requests.post(url, params=params, data=json, files=files)
        elif METHOD == 'DELETE':
            response = requests.delete(url, params=params)  
        else:
            msg = "http_request: Not valid METHOD: %s" % result
            logger.error(msg)
            print(msg)
            raise ValueError(msg)

        result = response.content

        if not is_json(result):
            msg = "http_request: Not valid JSON: %s" % result
            logger.error(msg)
            print(msg)
            raise ValueError(msg)
    except Exception as e:
        msg = " http_request: error=%s" % (e)
        print(msg)
        logger.error(msg)
        return msg

    return result

#####################
#    CORE MODULE    #
#####################
def core_ping():
    path = '/api/core/ping'
    return http_request(path, METHOD='GET')

#####################
# DISPATCHER MODULE #
#####################
def dispatcher_ping():
    path = '/api/dispatcher/ping'
    return http_request(path, METHOD='GET')

#####################
# CONVERSION MODULE #
#####################
def conversion_ping():
    path = '/api/conversion/ping'
    return http_request(path, METHOD='GET')


#####################
#  DEMOINFO MODULE  #
#####################


# MISC


def demoinfo_get_stats():
    path = '/api/demoinfo/stats'

    serviceparams = None
    servicejson = None
    return http_request(path, METHOD='GET', params=serviceparams, json=servicejson)


def demoinfo_get_states():
    path = '/api/demoinfo/read_states'

    serviceparams = None
    servicejson = None
    return http_request(path, METHOD='GET', params=serviceparams, json=servicejson)


# DDL


def demoinfo_get_ddl(demo_id):
    path = '/api/demoinfo/get_ddl'

    # proxy can be called by GET or POST, prefer POST if submiting data to server

    serviceparams = {'demo_id': demo_id}
    # send as string to proxy, proxy will load this into a dict for the request lib call

    servicejson = None
    return http_request(path, METHOD='POST', params=serviceparams, json=servicejson)


def demoinfo_read_demo_description(demo_descp_id):
    path = '/api/demoinfo/read_ddl'

    serviceparams = {'demodescriptionID': demo_descp_id}
    # send as string to proxy, proxy will load this into a dict for the request lib call

    servicejson = None
    return http_request(path, METHOD='POST', params=serviceparams, json=servicejson)


def get_ddl_history(demo_id):
    path = '/api/demoinfo/get_ddl_history'
    serviceparams = {'demo_id': demo_id}
    return http_request(path, METHOD='POST', params=serviceparams)


def demoinfo_save_demo_description(pjson, demoid):
    path = '/api/demoinfo/save_ddl'

    serviceparams = {'demoid': demoid}
    # send as string to proxy, proxy will load this into a dict for the request lib call

    servicejson = pjson
    return http_request(path, METHOD='POST', params=serviceparams, json=servicejson)


# DEMO

# todo se usa esto?
def demoinfo_demo_list():
    """
    list demos present in database
    { return:OK or KO, list demos:
    """

    path = '/api/demoinfo/demo_list'

    serviceparams = None
    servicejson = None
    return http_request(path, METHOD='GET', params=serviceparams, json=servicejson)


def demoinfo_demo_list_by_demoeditorid(demoeditorid_list):
    """
    list demos present in database with demo_editor_id in  demoeditorid_list
    demoeditorid_list must be sent to WS as a JSON string
    if no demoeditorid_list is provided return None

    { return:OK or KO, list demos:...
    """

    path = '/api/demoinfo/demo_list_by_demoeditorid'
    result = None

    if demoeditorid_list:
        serviceparams = {'demoeditorid_list': json.dumps(demoeditorid_list)}

        servicejson = None
        result = http_request(path, METHOD='GET', params=serviceparams, json=servicejson)

    return result


def demoinfo_demo_list_pagination_and_filtering(num_elements_page, page, qfilter):
    """
    list demos present in database
    demo_list_pagination_and_filter(self,num_elements_page,page,qfilter):
     demo list filtered and pagination {"status": "OK", "demo_list": [{"creation": "2015-12-29 15:03:07", "state": published,
     "title": "DemoTEST3 Title", "editorsdemoid": 25, "id": 3,
     "modification": "2015-12-29 15:03:07"}], "next_page_number": null,
     "previous_page_number": 1, "number": 2.0}
    """

    path = '/api/demoinfo/demo_list_pagination_and_filter'

    # proxy can be called by GET or POST, prefer POST if submiting data to server
    serviceparams = {'num_elements_page': num_elements_page, 'page': page, 'qfilter': qfilter}
    # send as string to proxy, proxy will load this into a dict for the request lib call
    servicejson = None
    return http_request(path, METHOD='POST', params=serviceparams, json=servicejson)


def demoinfo_delete_demo(demo_id):
    demoinfo_path = '/api/demoinfo/delete_demo'
    demoinfo_resp = http_request(demoinfo_path, METHOD='POST', params={'demo_id': demo_id})
    if json.loads(demoinfo_resp)['status'] == 'KO':
        return demoinfo_resp
    http_request("/api/blobs/delete_demo", METHOD='POST', params={'demo_id': demo_id})
    http_request("/api/demoinfo/delete_demoextras", METHOD='POST', params={'demo_id': demo_id})
    http_request("/api/archive/delete_demo", METHOD='POST', params={'demo_id': demo_id})
    return demoinfo_resp


def demoinfo_read_demo(demo_id):
    path = '/api/demoinfo/read_demo_metainfo'

    serviceparams = {"demoid": demo_id}
    # send as string to proxy, proxy will load this into a dict for the request lib call

    servicejson = None
    return http_request(path, METHOD='POST', params=serviceparams, json=servicejson)


def demoinfo_update_demo(demo, old_editor_demoid):
    demoinfo_params = {'demo': json.dumps(demo), 'old_editor_demoid': old_editor_demoid}
    blobs_params = {'new_demo_id': demo['demo_id'], 'old_demo_id': old_editor_demoid}
    archive_params = {'new_demo_id': demo['demo_id'], 'old_demo_id': old_editor_demoid}

    demoinfo_resp = http_request('/api/demoinfo/update_demo', METHOD='POST', params=demoinfo_params, json=None)
    if json.loads(demoinfo_resp)['status'] == 'KO':
        return demoinfo_resp

    blob_resp = http_request('/api/blobs/update_demo_id', METHOD='POST', params=blobs_params, json=None)
    if json.loads(blob_resp)['status'] == 'KO':
        return blob_resp

    archive_resp = http_request('/api/archive/update_demo_id', METHOD='POST', params=archive_params, json=None)
    if json.loads(archive_resp)['status'] == 'KO':
        return archive_resp

    return demoinfo_resp


def demoinfo_add_demo(editorsdemoid, title, state, editor):

    params = {'demo_id': editorsdemoid, 'title': title, 'state': state}

    add_demo_resp = http_request('/api/demoinfo/add_demo', METHOD='POST', params=params)
    if json.loads(add_demo_resp).get('status') == 'KO':
        return add_demo_resp

    params = {'demo_id': editorsdemoid, 'editor_id': editor}
    editor_to_demo_resp = http_request('/api/demoinfo/add_editor_to_demo', METHOD='POST', params=params)

    if json.loads(editor_to_demo_resp).get('status') == 'KO':
        return editor_to_demo_resp

    return add_demo_resp


# AUTHOR


def demoinfo_author_list():
    path = '/api/demoinfo/author_list'

    serviceparams = None
    servicejson = None
    return http_request(path, METHOD='POST', params=serviceparams, json=servicejson)


def demoinfo_author_list_for_demo(demo_id):
    path = '/api/demoinfo/demo_get_authors_list'

    serviceparams = {'demo_id': demo_id}

    servicejson = None
    return http_request(path, METHOD='GET', params=serviceparams, json=servicejson)


def demoinfo_available_author_list_for_demo(demo_id=None):
    path = '/api/demoinfo/demo_get_available_authors_list'

    serviceparams = {'demo_id': demo_id}

    servicejson = None
    return http_request(path, METHOD='GET', params=serviceparams, json=servicejson)


def demoinfo_author_list_pagination_and_filtering(num_elements_page, page, qfilter):
    path = '/api/demoinfo/author_list_pagination_and_filter'

    serviceparams = {'num_elements_page': num_elements_page, 'page': page, 'qfilter': qfilter}

    servicejson = None
    return http_request(path, METHOD='GET', params=serviceparams, json=servicejson)


def demoinfo_delete_author(author_id):
    path = '/api/demoinfo/remove_author'

    serviceparams = {'author_id': author_id}

    servicejson = None
    return http_request(path, METHOD='POST', params=serviceparams, json=servicejson)


def demoinfo_add_author(name, mail):
    path = '/api/demoinfo/add_author'
    serviceparams = {'name': name, 'mail': mail}

    servicejson = None
    return http_request(path, METHOD='POST', params=serviceparams, json=servicejson)


def demoinfo_read_author(author_id):
    path = '/api/demoinfo/read_author'

    serviceparams = {'authorid': author_id}

    servicejson = None
    return http_request(path, METHOD='POST', params=serviceparams, json=servicejson)


def demoinfo_update_author(author):
    path = '/api/demoinfo/update_author'

    serviceparams = {'author': json.dumps(author)}

    servicejson = None
    return http_request(path, METHOD='POST', params=serviceparams, json=servicejson)


def demoinfo_add_author_to_demo(demo_id, author_id):
    path = '/api/demoinfo/add_author_to_demo'

    serviceparams = {'demo_id': demo_id, 'author_id': author_id}

    servicejson = None
    return http_request(path, METHOD='POST', params=serviceparams, json=servicejson)


def demoinfo_delete_author_from_demo(demo_id, author_id):
    path = '/api/demoinfo/remove_author_from_demo'

    serviceparams = {'demo_id': demo_id, 'author_id': author_id}

    servicejson = None
    return http_request(path, METHOD='POST', params=serviceparams, json=servicejson)


# EDITOR


def demoinfo_editor_list():
    path = '/api/demoinfo/editor_list'

    serviceparams = None
    servicejson = None
    return http_request(path, METHOD='GET', params=serviceparams, json=servicejson)


def demoinfo_editor_list_for_demo(demo_id):
    path = '/api/demoinfo/demo_get_editors_list'

    serviceparams = {'demo_id': demo_id}

    servicejson = None
    return http_request(path, METHOD='GET', params=serviceparams, json=servicejson)


def demoinfo_available_editor_list_for_demo(demo_id=None):
    path = '/api/demoinfo/demo_get_available_editors_list'

    serviceparams = {'demo_id': demo_id}

    servicejson = None
    return http_request(path, METHOD='GET', params=serviceparams, json=servicejson)


def demoinfo_editor_list_pagination_and_filtering(num_elements_page, page, qfilter):
    path = '/api/demoinfo/editor_list_pagination_and_filter'

    serviceparams = {'num_elements_page': num_elements_page, 'page': page, 'qfilter': qfilter}

    servicejson = None
    return http_request(path, METHOD='GET', params=serviceparams, json=servicejson)


def demoinfo_delete_editor(editor_id):
    path = '/api/demoinfo/remove_editor'

    serviceparams = {'editor_id': editor_id}

    servicejson = None
    return http_request(path, METHOD='POST', params=serviceparams, json=servicejson)


def demoinfo_add_editor(name, mail):
    path = '/api/demoinfo/add_editor'

    serviceparams = {'name': name, 'mail': mail}

    servicejson = None
    return http_request(path, METHOD='POST', params=serviceparams, json=servicejson)


def demoinfo_read_editor(editor_id):
    path = '/api/demoinfo/read_editor'

    serviceparams = {'editorid': editor_id}

    servicejson = None
    return http_request(path, METHOD='POST', params=serviceparams, json=servicejson)


def demoinfo_update_editor(editor):
    path = '/api/demoinfo/update_editor'

    serviceparams = {'editor': json.dumps(editor)}

    servicejson = None
    return http_request(path, METHOD='POST', params=serviceparams, json=servicejson)


def demoinfo_add_editor_to_demo(demo_id, editor_id):
    path = '/api/demoinfo/add_editor_to_demo'

    serviceparams = {'demo_id': demo_id, 'editor_id': editor_id}

    servicejson = None
    return http_request(path, METHOD='POST', params=serviceparams, json=servicejson)


def demoinfo_delete_editor_from_demo(demo_id, editor_id):
    path = '/api/demoinfo/remove_editor_from_demo'

    serviceparams = {'demo_id': demo_id, 'editor_id': editor_id}

    servicejson = None
    return http_request(path, METHOD='POST', params=serviceparams, json=servicejson)


# DEMO EXTRAS

def demoinfo_demo_extras_for_demo(demo_id):
    path = '/api/demoinfo/get_demo_extras_info'

    serviceparams = {'demo_id': demo_id}

    servicejson = None
    return http_request(path, METHOD='GET', params=serviceparams, json=servicejson)


def demoinfo_delete_demo_extras_from_demo(demo_id):
    path = '/api/demoinfo/delete_demoextras'

    serviceparams = {'demo_id': demo_id}

    servicejson = None
    return http_request(path, METHOD='POST', params=serviceparams, json=servicejson)


def demoinfo_add_demo_extra_to_demo(demo_id, request):
    path = '/api/demoinfo/add_demoextras'

    files = None
    serviceparams = {'demo_id': demo_id}
    try:
        myfile   = request.FILES['myfile']
        filename = request.FILES['myfile'].name
        
        files = {'demoextras': myfile.file}
        serviceparams['demoextras_name'] = filename

    except Exception as ex:
        print ex
    
    servicejson = None
    return http_request(path, METHOD='POST', params=serviceparams, json=servicejson, files=files)


####################
#  ARCHIVE MODULE  #
####################

def archive_get_page(experimentid, page='1'):
    """
    The method "page" returns a JSON response with, for a given page of a given demo, all the data of the experiments
    that should be displayed on this page. Twelve experiments are displayed by page. For rendering the archive page in
    the browser
    """

    path = '/api/archive/get_page'

    serviceparams = {'demo_id': experimentid, 'page': page}

    servicejson = None
    return http_request(path, METHOD='GET', params=serviceparams, json=servicejson)


def archive_get_experiment(experiment_id):
    """
    The method returns a JSON response with all the data of the experiment with id=experiment_id
    """

    path = '/api/archive/get_experiment'

    serviceparams = {'experiment_id': experiment_id}

    servicejson = None
    return http_request(path, METHOD='GET', params=serviceparams, json=servicejson)


def archive_get_stats():
    """
    The method "page" returns a JSON response with, for a given page of a given demo, all the data of the experiments
    that should be displayed on this page. Twelve experiments are displayed by page. For rendering the archive page in
    the browser
    """

    path = '/api/archive/stats'

    serviceparams = None
    servicejson = None
    return http_request(path, METHOD='GET', params=serviceparams, json=servicejson)


def archive_demo_list():
    """
    list demos present in database
    { return:OK or KO, list demos: {id,name, id template, template } }
    """

    path = '/api/archive/demo_list'

    serviceparams = None
    servicejson = None
    return http_request(path, METHOD='GET', params=serviceparams, json=servicejson)


def archive_delete_demo(demo_id):
    path = '/api/archive/delete_demo'

    serviceparams = {'demo_id': demo_id}

    servicejson = None
    return http_request(path, METHOD='POST', params=serviceparams, json=servicejson)


def archive_delete_experiment(experiment_id):
    path = '/api/archive/delete_experiment'

    serviceparams = {'experiment_id': experiment_id}

    servicejson = None
    return http_request(path, METHOD='POST', params=serviceparams, json=servicejson)


def archive_delete_file(file_id):
    path = '/api/archive/delete_blob_w_deps'

    serviceparams = {'id_blob': file_id}

    servicejson = None
    return http_request(path, METHOD='POST', params=serviceparams, json=servicejson)


####################
#   BLOBS MODULE   #
####################


def get_demo_owned_blobs(demo_id):
    """
    Get the demo owned blobs
    """
    path = "/api/blobs/get_demo_owned_blobs"

    serviceparams = {'demo_id': demo_id}

    servicejson = None
    return http_request(path, METHOD='GET', params=serviceparams, json=servicejson)


def get_demo_templates(demo_id):
    """
    Get the demo owned blobs
    """
    path = "/api/blobs/get_demo_templates"

    serviceparams = {'demo_id': demo_id}

    servicejson = None
    return http_request(path, METHOD='GET', params=serviceparams, json=servicejson)


def edit_blob_from_demo(request, demo_id, blob_set, new_blob_set, pos_set, new_pos_set, title, credit):
    """
    Get the demo owned blobs
    """
    path = "/api/blobs/edit_blob_from_demo"

    files = None
    try:
        if 'vr' in request.FILES:
            files = {'vr': request.FILES['vr'].file}
    except Exception as ex:
        print ex

    serviceparams = {'demo_id': demo_id, 'blob_set': blob_set, 'new_blob_set': new_blob_set,
                     'pos_set': pos_set, 'new_pos_set': new_pos_set, 'title': title, 'credit': credit}

    return http_request(path, METHOD='POST', params=serviceparams, files=files)


def remove_blob_from_demo(demo_id, blob_set, pos_set):
    """
    Remove blob from demo
    """
    path = "/api/blobs/remove_blob_from_demo"

    serviceparams = {'demo_id': demo_id, 'blob_set': blob_set, 'pos_set': pos_set}

    return http_request(path, METHOD='GET', params=serviceparams)


def remove_template_from_demo(demo_id, template_id):
    """
    Remove blob from demo
    """
    path = "/api/blobs/remove_template_from_demo"

    serviceparams = {'demo_id': demo_id, 'template_id': template_id}

    return http_request(path, METHOD='DELETE', params=serviceparams)


def add_template_to_demo(demo_id, template_id):
    """
    Remove blob from demo
    """
    path = "/api/blobs/add_template_to_demo"

    serviceparams = {'demo_id': demo_id, 'template_id': template_id}

    return http_request(path, METHOD='GET', params=serviceparams)


def add_blob_to_demo(request, demo_id, blob_set, pos_set, title, credit):
    """
    Add a new blob to the demo
    """
    path = "/api/blobs/add_blob_to_demo"

    params = {'demo_id': demo_id, 'title': title, 'credit': credit}

    if blob_set != "":
        params['blob_set'] = blob_set
        params['pos_set'] = pos_set

    try:
        files = {'blob': request.FILES['blob'].file}
        if 'vr' in request.FILES:
            files['blob_vr'] = request.FILES['vr'].file
    except Exception as ex:
        print ex

    return http_request(path, METHOD='POST', params=params, files=files)


def delete_vr_from_blob(blob_id):
    """
    Remove the visual representation of the blob in the demo (in all the demos and templates)
    """
    path = "/api/blobs/delete_vr_from_blob"

    serviceparams = {'blob_id': blob_id}
    return http_request(path, METHOD='GET', params=serviceparams)


def get_all_templates():
    """
    Remove the visual representation of the blob in the demo (in all the demos and templates)
    """
    path = "/api/blobs/get_all_templates"

    return http_request(path, METHOD='GET')


def get_template_blobs(id):
    """
    Get template blobs
    """
    path = "/api/blobs/get_template_blobs"

    serviceparams = {'template_id': id}
    return http_request(path, METHOD='GET', params=serviceparams)


def add_blob_to_template(request, template_id, blob_set, pos_set, title, credit):
    """
    Add a new blob to the template
    """
    path = "/api/blobs/add_blob_to_template"

    params = {'template_id': template_id, 'title': title, 'credit': credit}

    if blob_set != "":
        params['blob_set'] = blob_set
        params['pos_set'] = pos_set

    try:
        files = {'blob': request.FILES['blob'].file}
        if 'vr' in request.FILES:
            files['blob_vr'] = request.FILES['vr'].file
    except Exception as ex:
        print ex

    return http_request(path, METHOD='POST', params=params, files=files)


def remove_blob_from_template(template_id, blob_set, pos_set):
    """
    Remove blob from template
    """
    path = "/api/blobs/remove_blob_from_template"

    serviceparams = {'template_id': template_id, 'blob_set': blob_set, 'pos_set': pos_set}
    return http_request(path, METHOD='GET', params=serviceparams)


def edit_blob_from_template(request, id, blob_set, new_blob_set, pos_set, new_pos_set, title, credit):
    """
    Edit blob info from template
    """
    path = "/api/blobs/edit_blob_from_template"

    files = None
    try:
        if 'vr' in request.FILES:
            files = {'vr': request.FILES['vr'].file}
    except Exception as ex:
        print ex

    serviceparams = {'template_id': id, 'blob_set': blob_set, 'new_blob_set': new_blob_set,
                     'pos_set': pos_set, 'new_pos_set': new_pos_set, 'title': title, 'credit': credit}

    return http_request(path, METHOD='POST', params=serviceparams, files=files)


def get_all_templates():
    """
    Get all the templates
    """
    path = "/api/blobs/get_all_templates"

    return http_request(path, METHOD='GET')


def delete_template(template_id):
    """
    Get all the templates
    """
    path = "/api/blobs/delete_template/"

    serviceparams = {'template_id': template_id}
    return http_request(path, METHOD='DELETE', params=serviceparams)


def create_template(name):
    """
    Get all the templates
    """
    path = "/api/blobs/create_template"

    serviceparams = {'template_name': name}
    return http_request(path, METHOD='POST', params=serviceparams)


def get_demos_using_the_template(template_id):
    """
    Get the list of demos that uses the given template
    """
    path = "/api/blobs/get_demos_using_the_template"

    serviceparams = {'template_id': template_id}
    return http_request(path, METHOD='GET', params=serviceparams)

def get_blobs_stats():
    """
    Return stats of the blobs module
    """
    path = "/api/blobs/stats"
    return http_request(path, METHOD='GET')

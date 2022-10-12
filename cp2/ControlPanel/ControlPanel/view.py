from django.shortcuts import render
from django.http import HttpResponse, HttpResponseRedirect, JsonResponse
from django.contrib.auth.decorators import login_required
from django.views.decorators.csrf import csrf_protect
from django.views.decorators.cache import never_cache
import json
from .utils import api_post, user_can_edit_demo
from ControlPanel.settings import HOST_NAME
import logging

logger = logging.getLogger(__name__)


@login_required(login_url='login')
def homepage(request):
    try:
        qfilter = request.GET.get('qfilter')
    except:
        qfilter = ""
    try:
        qfilter = request.GET.get('qfilter')
        page = request.GET.get('page')
        page = int(page)
    except:
        page = 1

    settings = {
        'num_elements_page': '100',
        'page': page,
        'qfilter': qfilter
    }
    demos = api_post('/api/demoinfo/demo_list_pagination_and_filter', settings)
    
    host_url = request.build_absolute_uri()
    host_url = host_url[:host_url.rfind('/cp2')]

    context = {
        "demos": demos['demo_list'],
        "page": page,
        "next_page_number": demos['next_page_number'],
        "previous_page_number": demos['previous_page_number'],
        "host_url": host_url
    }
    return render(request, 'homepage.html', context)

@login_required(login_url='login')
@csrf_protect
def status(request):
    return render(request, 'status.html')

@login_required(login_url='login')
def demo_editors(request):
    demo_id = request.GET['demo_id']
    title = request.GET['title']

    demo_editors = api_post('/api/demoinfo/demo_get_editors_list', { 'demo_id': demo_id })
    editor_list = demo_editors['editor_list']
    available_editors = api_post('/api/demoinfo/demo_get_available_editors_list', { 'demo_id': demo_id })
    available_editors = available_editors['editor_list']

    can_edit = user_can_edit_demo(request.user, demo_id)

    context = {
        'demo_id': demo_id,
        'title': title,
        'can_edit': can_edit,
        'editors_list': editor_list,
        'available_editors': available_editors
    }
    
    return render(request, 'demoEditors.html', context)

@login_required(login_url='login')
def add_demo_editor(request):
    demo_id = request.POST['demo_id']
    editor_id = request.POST['editor_id']
    settings = {
        'demo_id': demo_id,
        'editor_id': editor_id
    }
    if user_can_edit_demo(request.user, demo_id):
        demoinfo_response = api_post('/api/demoinfo/add_editor_to_demo', settings)

    response = {}
    if demoinfo_response.get('status') != 'OK':
        response['status'] = 'KO'
        response['message'] = demoinfo_response.get('error')
        return HttpResponse(json.dumps(response), 'application/json')
    else:
        return HttpResponseRedirect(request.META['HTTP_REFERER'])

@login_required(login_url='login')
def reset_ssh_key(request):
    demo_id = request.POST['demo_id']
    payload = {
        'demo_id': demo_id,
    }
    if user_can_edit_demo(request.user, demo_id):
        demoinfo_response = api_post('/api/demoinfo/reset_ssh_keys', payload)

    response = {}
    if demoinfo_response.get('status') != 'OK':
        response['status'] = 'KO'
        response['message'] = demoinfo_response.get('error')
        return HttpResponse(json.dumps(response), 'application/json')
    else:
        return HttpResponseRedirect(request.META['HTTP_REFERER'])

@login_required(login_url='login')
def remove_demo_editor(request):
    demo_id = request.POST['demo_id']
    editor_id = request.POST['editor_id']
    settings = {
        'demo_id': demo_id,
        'editor_id': editor_id
    }
    if user_can_edit_demo(request.user, demo_id):
        print(settings)
        demoinfo_response = api_post('/api/demoinfo/remove_editor_from_demo', settings)

    response = {}
    if demoinfo_response.get('status') != 'OK':
        response['status'] = 'KO'
        response['message'] = demoinfo_response.get('error')
        return HttpResponse(json.dumps(response), 'application/json')
    else:
        response['status'] = 'OK'
        return HttpResponse(json.dumps(response), 'application/json')


@login_required(login_url='login')
@csrf_protect
def ajax_add_demo(request):
    state = request.POST['state'].lower()
    title = request.POST['title']
    demo_id = request.POST['demo_id']

    settings = {'state': state, 'title': title, 'demo_id': demo_id, 'ddl': '{}'}
    result = api_post("/api/demoinfo/add_demo", settings, json='{}')

    editor_info = api_post('/api/demoinfo/get_editor', { 'email': request.user.email })
    editor_id = editor_info['editor']['id']
    settings = {'demo_id': demo_id, 'editor_id': editor_id }
    editor_add = api_post('/api/demoinfo/add_editor_to_demo', settings)

    response = {}
    if result.get('status') != 'OK' or editor_add.get('status') != 'OK':
        response['status'] = 'KO'
        response['message'] = result.get('error')
        return JsonResponse({
            'status': 'KO',
            'message': result.get('error')
        }, status=400)
    else:
        response['status'] = 'OK'
        return HttpResponseRedirect(f'/cp2/showDemo?demo_id={demo_id}&title={title}')

@login_required(login_url='login')
@csrf_protect
def ajax_delete_demo(request):
    demo_id = request.POST['demo_id']

    if user_can_edit_demo(request.user, demo_id):
        settings = {'demo_id': demo_id}
        response_api = api_post("/api/demoinfo/delete_demo", settings, json='{}')
        result = response_api

    response = {}
    if result.get('status') != 'OK':
        response['status'] = 'KO'
        response['message'] = result.get('error')
    else:
        response['status'] = 'OK'
    return HttpResponse(json.dumps(response), 'application/json')

@login_required(login_url='login')
def templates(request):
    demoinfo_response = api_post('/api/blobs/get_all_templates')
    templates = demoinfo_response['templates']
    context = {
        'templates': templates
    }
    return render(request, 'Templates.html', context)

@login_required(login_url='login')
@csrf_protect
def ajax_add_template(request):
    template_name = request.POST['templateName']
    settings = {'template_name' : template_name }
    result = api_post("/api/blobs/create_template", settings)

    if result['status'] == 'OK':
        return JsonResponse({
            'status': 'OK',
            'template_id': result['template_id']
        }, status=200)
    else:
        return JsonResponse({'status': 'KO', 'message': 'Unauthorized'}, status=401)

@login_required(login_url='login')
@never_cache
def showTemplate(request):
    template_id = request.GET['template_id']
    template_name = request.GET['template_name']

    template = api_post('/api/blobs/get_template_blobs', { 'template_id': template_id})
    template_sets = template['sets']

    demos = api_post('/api/blobs/get_demos_using_the_template', { 'template_id': template_id })
    demos_using_template = demos['demos']
    context = {
        'template_id': template_id,
        'template_name': template_name,
        'template_sets': template_sets,
        'demos_using_template': demos_using_template
    }
    return render(request, 'showTemplate.html', context)

@login_required(login_url='login')
@csrf_protect
def ajax_delete_blob_template(request):
    template_id = request.POST['template_id']
    pos_set = request.POST['pos_set']
    blob_set = request.POST['blob_set']
    response = {}
    settings = {'template_id' : template_id, 'blob_set' : blob_set, 'pos_set' : pos_set }
    response_api = api_post("/api/blobs/remove_blob_from_template", settings)
    result = response_api
    if result.get('status') != 'OK':
        response['status'] = 'KO'
        return HttpResponse(json.dumps(response), 'application/json')
    else:
        response['status'] = 'OK'
        return HttpResponse(json.dumps(response), 'application/json')

@login_required(login_url='login')
def ajax_delete_blob_demo(request):
    demo_id = request.POST['demo_id']
    pos_set = request.POST['pos_set']
    blob_set = request.POST['blob_set']
    response = {}
    if user_can_edit_demo(request.user, demo_id):
        settings = {'demo_id' : demo_id, 'blob_set' : blob_set, 'pos_set' : pos_set }
        response_api = api_post("/api/blobs/remove_blob_from_demo", settings)
        result = response_api
        if result.get('status') != 'OK':
            response['status'] = 'KO'
            return HttpResponse(json.dumps(response), 'application/json')
        else:
            response['status'] = 'OK'
            return HttpResponse(json.dumps(response), 'application/json')
    else:
        return render(request, 'homepage.html')


@login_required(login_url='login')
def ajax_delete_template(request):
    template_id = request.POST['template_id']
    response = {}
    settings = {'template_id' : template_id }
    response_api = api_post("/api/blobs/delete_template", settings)
    result = response_api
    if result.get('status') != 'OK':
        response['status'] = 'KO'
        return HttpResponse(json.dumps(response), 'application/json')
    else:
        response['status'] = 'OK'
        return HttpResponse(json.dumps(response), 'application/json')

@login_required(login_url='login')
def ajax_remove_blob_from_template(request):
    template_id = request.POST['template_id']
    blob_set = request.POST['blob_set']
    pos_set = request.POST['pos_set']

    settings = {
        'template_id': template_id,
        'blob_set': blob_set,
        'pos_set': pos_set
    }
    response = api_post("/api/blobs/remove_blob_from_template", settings)
    if response['status'] != 'OK':
        response['status'] = 'KO'
        return HttpResponse(json.dumps(response), 'application/json')
    else:
        response['status'] = 'OK'
        return HttpResponse(json.dumps(response), 'application/json')

@login_required(login_url='login')
def ajax_remove_blob_from_demo(request):
    demo_id = request.POST['demo_id']
    blob_set = request.POST['blob_set']
    pos_set = request.POST['pos_set']
    
    if not user_can_edit_demo(request.user, demo_id):
        response['status'] = 'KO'
        response['message'] = 'User not allowed'
        return HttpResponse(json.dumps(response), 'application/json')

    settings = {
        'demo_id': demo_id,
        'blob_set': blob_set,
        'pos_set': pos_set
    }
    response = api_post("/api/blobs/remove_blob_from_demo", settings)
    if response['status'] != 'OK':
        response['status'] = 'KO'
        return HttpResponse(json.dumps(response), 'application/json')
    else:
        response['status'] = 'OK'
        return HttpResponse(json.dumps(response), 'application/json')


@login_required(login_url='login')
def CreateBlob(request):
    context = {}
    if 'demo_id' in request.GET: # demo blob edit
        can_edit = user_can_edit_demo(request.user, request.GET['demo_id'])
        context = {
            'create_blob': True,
            'demo_id': request.GET['demo_id'],
            'can_edit': can_edit
        }
    else: #Template blob edit
        template_id = request.GET['template_id']
        template_name = request.GET['template_name']
        context = {
            'create_blob': True,
            'template_id': template_id,
            'template_name': template_name
        }
    return render(request, 'createBlob.html', context)

@login_required(login_url='login')
def ajax_add_blob_demo(request):
    print(request.POST)
    blob_set = request.POST['SET']
    pos_set = request.POST['PositionSet']
    title = request.POST['Title']
    credit = request.POST['Credit']
    demo_id = request.POST['demo_id']
    files = {'blob': request.FILES['Blobs'].file}
    if 'VR' in request.FILES:
        files['blob_vr'] = request.FILES['VR'].file

    response = {}
    if user_can_edit_demo(request.user, demo_id):
        settings = {'demo_id' : demo_id, 'blob_set' : blob_set, 'pos_set' : pos_set, 'title' : title, 'credit' : credit}
        response_api = api_post("/api/blobs/add_blob_to_demo",settings , files)
        result = response_api
        if result.get('status') != 'OK':
            response['status'] = 'KO'
            return HttpResponse(json.dumps(response), 'application/json')
        else:
            response['status'] = 'OK'
            return HttpResponse(json.dumps(response), 'application/json')
    else: 
        return render(request, 'homepage.html')


@login_required(login_url='login')
def ajax_add_blob_template(request):
    blob_set = request.POST['SET']
    pos_set = request.POST['PositionSet']
    title = request.POST['Title']
    credit = request.POST['Credit']
    template_id = request.POST['TemplateSelection']
    files = {'blob': request.FILES['Blobs'].file}
    if 'VR' in request.FILES:
        files['blob_vr'] = request.FILES['VR'].file

    response = {}
    settings = {'template_id' : template_id, 'blob_set' : blob_set, 'pos_set' : pos_set, 'title' : title, 'credit' : credit}
    print(settings)
    response_api = api_post("/api/blobs/add_blob_to_template",settings , files)
    result = response_api
    if result.get('status') != 'OK':
        response['status'] = 'KO'
        return HttpResponse(json.dumps(response), 'application/json')
    else:
        response['status'] = 'OK'
        return HttpResponse(json.dumps(response), 'application/json')
    
@login_required(login_url='login')
@never_cache
def detailsBlob(request):
    context = {}
    if 'demo_id' in request.GET: # demo blob edit
        demo_id = request.GET['demo_id']
        can_edit = user_can_edit_demo(request.user, demo_id)
        set_name = request.GET['set']
        blob_pos = request.GET['pos']
        blobs_response = api_post('/api/blobs/get_demo_owned_blobs', {'demo_id': demo_id})
        sets = blobs_response['sets']
        for blobset in sets:
            if blobset['name'] == set_name and blob_pos in blobset['blobs']:
                blob = blobset['blobs'][blob_pos]
                thumbnail = blob['thumbnail'] if 'thumbnail' in blob else ''
                vr = blob['vr'] if 'vr' in blob else ''
                context = {
                    'demo_id': request.GET['demo_id'],
                    'pos': blob_pos,
                    'set_name': blobset['name'],
                    'blob_id': blob['id'],
                    'title': blob['title'],
                    'blob': blob['blob'],
                    'format': blob['format'],
                    'credit': blob['credit'],
                    'thumbnail': thumbnail,
                    'vr': vr,
                    'can_edit': can_edit
                }
                return render(request, 'detailsBlob.html', context)

    else: #Template blob edit
        template_id = request.GET['template_id']
        template_name = request.GET['template_name']
        set_name = request.GET['set']
        blob_pos = request.GET['pos']
        blobs_response = api_post('/api/blobs/get_template_blobs', {'template_id': template_id})
        sets = blobs_response['sets']
        for blobset in sets:
            if blobset['name'] == set_name and blob_pos in blobset['blobs']:
                blob = blobset['blobs'][blob_pos]
                thumbnail = blob['thumbnail'] if 'thumbnail' in blob else ''
                vr = blob['vr'] if 'vr' in blob else ''
                context = {
                    'template_id': template_id,
                    'template_name': template_name,
                    'pos': blob_pos,
                    'set_name': blobset['name'],
                    'blob_id': blob['id'],
                    'title': blob['title'],
                    'blob': blob['blob'],
                    'format': blob['format'],
                    'credit': blob['credit'],
                    'thumbnail': thumbnail,
                    'vr': vr,
                }
                return render(request, 'detailsBlob.html', context)
        return JsonResponse({'status': 'OK', 'message': 'Blob not found'}, status=404)



@login_required(login_url='login')
def ajax_edit_blob_template(request):
    new_blob_set = request.POST['SET']
    blob_set = request.POST['old_set']
    new_pos_set = request.POST['PositionSet']
    pos_set = request.POST['old_pos']
    title = request.POST['Title']
    credit = request.POST['Credit']
    template_id = request.POST['template_id']
    files = {}
    if 'VR' in request.FILES:
        files['vr'] = request.FILES['VR'].file
    
    response = {}
    settings = {'template_id' : template_id, 'blob_set' : blob_set, 'new_blob_set' : new_blob_set, 'pos_set' : pos_set, 'new_pos_set' : new_pos_set, 'title' : title, 'credit' : credit}
    response_api = api_post("/api/blobs/edit_blob_from_template",settings ,files )
    result = response_api
    if result.get('status') != 'OK':
        response['status'] =  'KO'
        return HttpResponse(json.dumps(response), 'application/json')
    else:
        response['status'] = 'OK'
        return HttpResponse(json.dumps(response), 'application/json')

@login_required(login_url='login')
def showDemo(request):
    demo_id = request.GET['demo_id']
    title = request.GET['title']
    demoinfo_response = api_post('/api/demoinfo/get_ddl', { 'demo_id': demo_id })
    ssh_response = api_post('/api/demoinfo/get_ssh_keys', { 'demo_id': demo_id })
    ddl = None
    demo_editors = api_post('/api/demoinfo/demo_get_editors_list', { 'demo_id': demo_id })
    editor_list = demo_editors['editor_list']
    available_editors = api_post('/api/demoinfo/demo_get_available_editors_list', { 'demo_id': demo_id })
    available_editors = available_editors['editor_list']

    host_url = request.build_absolute_uri()
    host_url = host_url[:host_url.rfind('/cp2')]

    if demoinfo_response['status'] == 'OK':
        ddl = demoinfo_response['last_demodescription']
    else:
        ddl = '{}'

    if ssh_response['status'] != 'OK':
        pubkey = '(error fetching the ssh public key)'
    else:
        pubkey = ssh_response['pubkey']

    can_edit = user_can_edit_demo(request.user, demo_id)

    context = {
        'demo_id': demo_id,
        'title': title,
        'ddl': ddl,
        'can_edit': can_edit,
        'editors_list': editor_list,
        'available_editors': available_editors,
        'ssh_pubkey': pubkey,
        'host_url': host_url,
    }

    return render(request, 'showDemo.html', context)

@login_required(login_url='login')
def edit_demo(request):
    demo_id = request.POST['demo_id']
    new_demo_id = request.POST['new_demo_id']
    title = request.POST['demoTitle']
    state = request.POST['state']
    demo = {
        'demo_id': new_demo_id,
        'title': title,
        'state': state
    }

    settings ={
        'old_editor_demoid': demo_id,
        'demo': json.dumps(demo)
    }

    demoinfo_response = api_post('/api/demoinfo/update_demo', settings)
    settings ={
        'old_demo_id': demo_id,
        'new_demo_id': new_demo_id
    }
    blobs_response = api_post('/api/blobs/update_demo_id', settings)
    archive_response = api_post('/api/archive/update_demo_id', settings)

    response = {}
    if demoinfo_response.get('status') != 'OK' or blobs_response.get('status') != 'OK' or archive_response.get('status') != 'OK':
        response['status'] = 'KO'
        response['message'] = demoinfo_response.get('error')
        return HttpResponse(json.dumps(response), 'application/json')
    else:
        return HttpResponseRedirect(f'/cp2/showDemo?demo_id={new_demo_id}&title={title}')

@login_required(login_url='login')
def ddl_history(request):
    demo_id = request.GET['demo_id']
    title = request.GET['title']

    dll_history_response = api_post('/api/demoinfo/get_ddl_history', { 'demo_id': demo_id })
    ddl_history = dll_history_response['ddl_history']

    context = {
        'demo_id': demo_id,
        'title': title,
        'ddl_history': ddl_history,
    }
    return render(request, 'ddl_history.html', context)

@login_required(login_url='login')
def ajax_user_can_edit_demo(request):
    demo_id = request.POST['demoID']
    response = {}
    user_email = request.user
    print(user_email)
    if user_can_edit_demo(request.user, demo_id) :
        response['can_edit'] = True
        return HttpResponse(json.dumps(response), 'application/json')
    else:
        response['can_edit'] = False
        return HttpResponse(json.dumps(response), 'application/json')


@login_required(login_url='login')
def ajax_remove_vr(request):
    blob_id = request.POST['blob_id']
    settings = {'blob_id' : blob_id}
    response = {}
    response_api = api_post("/api/blobs/delete_vr_from_blob", settings)
    result = response_api
    if result.get('status') == 'OK':
        response['status'] ='OK'
        return JsonResponse({'status': 'OK'}, status=200)
    else: 
        return JsonResponse({'message': 'Could not remove VR'}, status=404)

@login_required(login_url='login')
def ajax_show_DDL(request):
    demo_id = request.POST['demoID']
    settings = {'demo_id': demo_id}
    response = {}
    response = api_post("/api/demoinfo/get_ddl", settings)
    return HttpResponse(json.dumps(response), 'application/json')

@login_required(login_url='login')
def ajax_save_DDL(request):
    demo_id = request.POST['demo_id']
    ddl = request.POST['ddl']

    if user_can_edit_demo(request.user, demo_id):
        demoinfo_response = api_post('/api/demoinfo/save_ddl', {'demoid': demo_id}, json=ddl)
        return JsonResponse({'status': 'OK'}, status=200)
    else:
        return JsonResponse({'status': 'OK', 'message': 'Unauthorized'}, status=401)

@login_required(login_url='login')
def showBlobsDemo(request):
    demo_id = request.GET['demo_id']
    title = request.GET['title']
    can_edit = user_can_edit_demo(request.user, demo_id)
    blobs = api_post('/api/blobs/get_demo_owned_blobs', { 'demo_id': demo_id})
    blob_sets = blobs['sets']

    demo_used_templates = api_post('/api/blobs/get_demo_templates', { 'demo_id': demo_id})
    demo_used_templates = demo_used_templates['templates']

    templates = api_post('/api/blobs/get_all_templates')
    template_list = templates['templates']

    context = {
        'can_edit': can_edit,
        'demo_id': demo_id,
        'title': title,
        'blob_sets': blob_sets,
        'demo_used_templates': demo_used_templates,
        'template_list': template_list
    }

    return render(request, 'showBlobsDemo.html', context)

@login_required(login_url='login')
def demoExtras(request):
    demo_id = request.GET['demo_id']
    response = api_post('/api/demoinfo/get_demo_extras_info', {'demo_id': demo_id })
    extras_name = None
    extras_url = None
    if 'url' in response:
        extras_name = response['url'].split('/')[-1]
        extras_url = response['url']

    context = {
        'demo_id': demo_id,
        'extras_url': extras_url,
        'extras_name': extras_name,
        'hostname': HOST_NAME,
        'can_edit': user_can_edit_demo(request.user, demo_id)
    }
    return render(request, 'demoExtras.html', context)

@login_required(login_url='login')
@csrf_protect
def ajax_add_demo_extras(request):
    demo_id = request.POST['demo_id']
    file = request.FILES['demoextras']
    filename = request.FILES['demoextras'].name
    if user_can_edit_demo(request.user, demo_id):
        params = { 
            'demo_id': demo_id,
            'demoextras_name': filename
            }
        files = { 'demoextras': file}
        api_post('/api/demoinfo/add_demoextras', params= params, files= files)
    return HttpResponseRedirect(f'/cp2/demoExtras?demo_id={demo_id}')

@login_required(login_url='login')
def ajax_delete_demo_extras(request):
    demo_id = request.GET['demo_id']
    if user_can_edit_demo(request.user, demo_id):
        response = api_post('/api/demoinfo/delete_demoextras', { 'demo_id': demo_id })
        # TODO
    return HttpResponseRedirect(f'/cp2/demoExtras?demo_id={demo_id}')

@login_required(login_url='login')
def ajax_add_template_to_demo(request):
    demo_id = request.POST['demo_id']
    template_id = request.POST['template_id']
    settings = {'demo_id': demo_id, 'template_id': template_id}
    response = {}
    if user_can_edit_demo(request.user, demo_id):
        response_api = api_post("/api/blobs/add_template_to_demo",settings)
        result = response_api
        if result.get('status') != 'OK':
            response['status'] = 'KO'
            return HttpResponse(json.dumps(response), 'application/json')
        else:
            response['status'] = 'OK'
            return HttpResponse(json.dumps(response), 'application/json')
    else: 
        return render(request, 'homepage.html')

@login_required(login_url='login')
def ajax_remove_template_to_demo(request):
    demo_id = request.POST['demo_id']
    template_id = request.POST['template_id']
    settings = {'demo_id': demo_id, 'template_id': template_id}
    response = {}
    if user_can_edit_demo(request.user, demo_id):
        response_api = api_post("/api/blobs/remove_template_from_demo", settings)
        result = response_api
        if result.get('status') != 'OK':
            response['status'] = 'KO'
            return HttpResponse(json.dumps(response), 'application/json')
        else:
            response['status'] = 'OK'
            return HttpResponse(json.dumps(response), 'application/json')
    else: 
        return render(request, 'homepage.html')

@login_required(login_url='login')
def ajax_edit_blob_demo(request):
    demo_id = request.POST['demo_id']
    files = {}
    if 'VR' in request.FILES:
        files['vr'] = request.FILES['VR'].file
    if user_can_edit_demo(request.user, demo_id):
        response = {}
        settings = {
            'demo_id' : demo_id,
            'blob_set' : request.POST['old_set'],
            'new_blob_set' : request.POST['SET'],
            'pos_set' : request.POST['old_pos'],
            'new_pos_set' : request.POST['PositionSet'],
            'title' : request.POST['Title'],
            'credit' : request.POST['Credit']
        }
        response = api_post("/api/blobs/edit_blob_from_demo",settings ,files)

        if response.get('status') != 'OK':
            response['status'] =  'KO'
            return HttpResponse(json.dumps(response), 'application/json')
        else:
            response['status'] = 'OK'
            return HttpResponse(json.dumps(response), 'application/json')
    else:
        return render(request, 'homepage.html')

@login_required(login_url='login')
def show_archive(request):
    demo_id = request.GET['demo_id']
    title = request.GET['title']

    if 'page' in request.GET:
        page = request.GET['page']
    else:
        page = 1

    if 'qfilter' in request.GET:
        experiment_id = request.GET['qfilter']
        archive_response = api_post('/api/archive/get_experiment', { 'experiment_id': experiment_id })
        experiment = archive_response['experiment']

    archive_response = api_post('/api/archive/get_page', { 'demo_id': demo_id, 'page': page })
    experiments = archive_response['experiments']
    meta = archive_response['meta']

    context = {
        'title': title,
        'demo_id': demo_id,
        'experiments': experiments,
        'meta': meta,
        'page': int(page),
        'can_edit': user_can_edit_demo(request.user, demo_id)
    }
    return render(request, 'archive.html', context)


@login_required(login_url='login')
def show_experiment(request):
    demo_id = request.GET['demo_id']
    title = request.GET['title']

    if 'experiment_id' in request.GET:
        experiment_id = request.GET['experiment_id']
        archive_response = api_post('/api/archive/get_experiment', { 'experiment_id': experiment_id })
        experiment = archive_response['experiment']

    archive_response = api_post('/api/archive/get_page', { 'demo_id': demo_id })
    meta = archive_response['meta']

    context = {
        'title': title,
        'demo_id': demo_id,
        'experiment': experiment,
        'meta': meta,
        'can_edit': user_can_edit_demo(request.user, demo_id)
    }
    return render(request, 'showExperiment.html', context)

@login_required(login_url='login')
def ajax_delete_experiment(request):
    demo_id = request.POST['demo_id']
    experiment_id = request.POST['experiment_id']
    if user_can_edit_demo(request.user, demo_id):
        response = api_post('/api/archive/delete_experiment', { 'experiment_id': experiment_id })

        if response.get('status') != 'OK':
            response['status'] =  'KO'
            return HttpResponse(json.dumps(response), 'application/json')
        else:
            response['status'] = 'OK'
            return HttpResponse(json.dumps(response), 'application/json')

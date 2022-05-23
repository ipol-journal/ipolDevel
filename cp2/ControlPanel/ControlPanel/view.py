from django.shortcuts import render, redirect
from django.http import HttpResponse, HttpResponseRedirect, JsonResponse
from django.contrib.auth.decorators import login_required
from django.views.decorators.csrf import csrf_protect
from django.views.decorators.cache import never_cache
from django.contrib.auth import logout, authenticate, login
from .forms import loginForm
import json, requests
from .utils import api_post, user_can_edit_demo
from django.contrib.auth.decorators import user_passes_test
from django.contrib.auth.models import User
from django.core.files.uploadedfile import SimpleUploadedFile
from ControlPanel.settings import HOST_NAME



@login_required(login_url='/cp2/loginPage')
def Homepage(request):
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
        'num_elements_page': '8',
        'page': page,
        'qfilter': qfilter
    }
    demos = api_post('/api/demoinfo/demo_list_pagination_and_filter', settings).json()
    
    host_url = request.build_absolute_uri()
    host_url = host_url[:host_url.rfind('/cp2')]

    context = {
        "demos": demos['demo_list'],
        "page": page,
        "next_page_number": demos['next_page_number'],
        "previous_page_number": demos['previous_page_number'],
        "host_url": host_url
    }
    return render(request, 'Homepage.html', context)

@csrf_protect
def loginPage(request):
    form = loginForm(request.POST or None)
    username = request.POST.get('username')
    password = request.POST.get('password')
    user = authenticate(request, username=username, password=password)
    if user is not None:
        login(request, user)
        return HttpResponseRedirect('/cp2/')
    else:
        return render(request, "loginPage.html", {'form': form})

@login_required(login_url='/cp2/loginPage')
def signout(request):
    return render(request, 'signout.html')

@login_required(login_url='/cp2/loginPage')
def logoff(request):
    logout(request)
    return redirect ('/cp2/loginPage')

@login_required(login_url='/cp2/loginPage')
def status(request):
    # dr_response = api_post('/api/dispatcher/get_demorunners_stats').json()
    # archive_stats = api_post('/api/archive/stats').json()
    # blobs_stats = api_post('/api/blobs/stats').json()
    # core = api_post('/api/core/ping').json()
    # conversion = api_post('/api/conversion/ping').json()
    # context = {
    #     'dr': dr_response['demorunners'],
    #     'blobs': blobs,
    #     'archive': archive_stats,
    #     'blobs': blobs_stats,
    #     'core': core,
    #     'conversion': conversion
    # }
    # print(context)
    return render(request, 'status.html')

@login_required(login_url='/cp2/loginPage')
@csrf_protect
def ajax_add_demo(request):
    state = request.POST['State'].lower()
    title = request.POST['Title']
    demoid = request.POST['DemoId']
    response = {}
    
    settings = {'state': state, 'title': title, 'editorsdemoid': demoid}
    response_api = api_post("/api/demoinfo/add_demo", settings)
    result = response_api.json()

    settings = {'demo_id': editorsdemoid, 'editor_id': editor}
    api_post('/api/demoinfo/add_editor_to_demo', settings)
    if result.get('status') != 'OK':
        response['status'] = 'KO'
        response['message'] = result.get('error')
        return HttpResponse(json.dumps(response), 'application/json')
    else :
        response['status'] = 'OK'
        return HttpResponse(json.dumps(response), 'application/json')

@login_required(login_url='/cp2/loginPage')
def templates(request):
    return render(request, 'Templates.html')

@login_required(login_url='/cp2/loginPage')
@csrf_protect
def ajax_add_template(request):
    template_name = request.POST['templateName']
    settings = {'template_name' : template_name }
    result = api_post("/api/blobs/create_template", settings).json()

    if result['status'] == 'OK':
        return JsonResponse({
            'status': 'OK',
            'template_id': result['template_id']
        }, status=200)
    else :
        return JsonResponse({'status': 'KO', 'message': 'Unauthorized'}, status=401)

@never_cache
def showTemplates(request):
    template_id = request.GET['template_id']
    template_name = request.GET['template_name']

    template = api_post('/api/blobs/get_template_blobs', { 'template_id': template_id}).json()
    template_sets = template['sets']

    demos = api_post('/api/blobs/get_demos_using_the_template', { 'template_id': template_id }).json()
    demos_using_template = demos['demos']
    context = {
        'template_id': template_id,
        'template_name': template_name,
        'template_sets': template_sets,
        'demos_using_template': demos_using_template
    }
    return render(request, 'showTemplates.html', context)

@login_required(login_url = '/cp2/loginPage')
@csrf_protect
def ajax_delete_blob_template(request):
    template_id = request.POST['template_id']
    pos_set = request.POST['pos_set']
    blob_set = request.POST['blob_set']
    response = {}
    settings = {'template_id' : template_id, 'blob_set' : blob_set, 'pos_set' : pos_set }
    response_api = api_post("/api/blobs/remove_blob_from_template", settings)
    result = response_api.json()
    if result.get('status') != 'OK':
        response['status'] = 'KO'
        return HttpResponse(json.dumps(response), 'application/json')
    else :
        response['status'] = 'OK'
        return HttpResponse(json.dumps(response), 'application/json')

@login_required(login_url= 'cp2/loginPage')
def ajax_delete_blob_demo(request):
    demo_id = request.POST['demo_id']
    pos_set = request.POST['pos_set']
    blob_set = request.POST['blob_set']
    response = {}
    if user_can_edit_demo(request.user, demo_id):
        settings = {'demo_id' : demo_id, 'blob_set' : blob_set, 'pos_set' : pos_set }
        response_api = api_post("/api/blobs/remove_blob_from_demo", settings)
        result = response_api.json()
        if result.get('status') != 'OK':
            response['status'] = 'KO'
            return HttpResponse(json.dumps(response), 'application/json')
        else :
            response['status'] = 'OK'
            return HttpResponse(json.dumps(response), 'application/json')
    else:
        return render(request, 'Homepage.html')


@login_required(login_url = '/cp2/loginPage')
def ajax_delete_template(request):
    template_id = request.POST['template_id']
    response = {}
    settings = {'template_id' : template_id }
    response_api = api_post("/api/blobs/delete_template", settings)
    result = response_api.json()
    if result.get('status') != 'OK':
        response['status'] = 'KO'
        return HttpResponse(json.dumps(response), 'application/json')
    else :
        response['status'] = 'OK'
        return HttpResponse(json.dumps(response), 'application/json')
        

@login_required(login_url='/cp2/loginPage')
def CreateBlob(request):
    context = {}
    if 'demo_id' in request: # demo blob edit
        can_edit = user_can_edit_demo(request.GET['demo_id'])
        context = {
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

@login_required(login_url = '/cp2/loginPage')
def ajax_add_blob_demo(request):
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
        result = response_api.json()
        if result.get('status') != 'OK':
            response['status'] = 'KO'
            return HttpResponse(json.dumps(response), 'application/json')
        else :
            response['status'] = 'OK'
            return HttpResponse(json.dumps(response), 'application/json')
    else : 
        return render(request, 'Homepage.html')


@login_required(login_url = '/cp2/loginPage')
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
    result = response_api.json()
    if result.get('status') != 'OK':
        response['status'] = 'KO'
        return HttpResponse(json.dumps(response), 'application/json')
    else :
        response['status'] = 'OK'
        return HttpResponse(json.dumps(response), 'application/json')
    
@login_required(login_url= '/cp2/loginPage')
@never_cache
def detailsBlob(request):
    context = {}
    if 'demo_id' in request: # demo blob edit
        can_edit = user_can_edit_demo(request.GET['demo_id'])
        context = {
            'demo_id': request.GET['demo_id'],
        }
    else: #Template blob edit
        template_id = request.GET['template_id']
        template_name = request.GET['template_name']
        set_name = request.GET['set']
        blob_pos = request.GET['pos']
        blobs_response = api_post('/api/blobs/get_template_blobs', {'template_id': template_id}).json()
        sets = blobs_response['sets']
        for blobset in sets:
            if blobset['name'] == set_name and blob_pos in blobset['blobs']:
                blob = blobset['blobs'][blob_pos]
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
                    'thumbnail': blob['thumbnail'],
                    'vr': vr,
                }
                return render(request, 'detailsBlob.html', context)
        return JsonResponse({'status': 'OK', 'message': 'Blob not found'}, status=404)



@login_required(login_url = '/cp2/loginPage')
def ajax_edit_blob_template(request):
    new_blob_set = request.POST['SET']
    blob_set = request.POST['old_set']
    new_pos_set = request.POST['PositionSet']
    pos_set = request.POST['old_pos']
    title = request.POST['Title']
    credit = request.POST['Credit']
    template_id = request.POST['TemplateSelection']
    files = {}
    if 'VR' in request.FILES:
        files['vr'] = request.FILES['VR'].file
    
    response = {}
    settings = {'template_id' : template_id, 'blob_set' : blob_set, 'new_blob_set' : new_blob_set, 'pos_set' : pos_set, 'new_pos_set' : new_pos_set, 'title' : title, 'credit' : credit}
    response_api = api_post("/api/blobs/edit_blob_from_template",settings ,files )
    result = response_api.json()
    if result.get('status') != 'OK':
        response['status'] =  'KO'
        return HttpResponse(json.dumps(response), 'application/json')
    else :
        response['status'] = 'OK'
        return HttpResponse(json.dumps(response), 'application/json')

@login_required(login_url='/cp2/loginPage')
def showDemo(request):
    demo_id = request.GET['demo_id']
    title = request.GET['title']
    demoinfo_response = api_post('/api/demoinfo/get_ddl', { 'demo_id': demo_id }).json()
    ddl = None
    if demoinfo_response['status'] == 'OK':
        ddl = demoinfo_response['last_demodescription']

    can_edit = user_can_edit_demo(request.user, demo_id)

    context = {
        'demo_id': demo_id,
        'title': title,
        'ddl': ddl,
        'can_edit': can_edit
    }
    
    return render(request, 'showDemo.html', context)

@login_required(login_url='/cp2/loginPage')
def ajax_user_can_edit_demo(request):
    demo_id = request.POST['demoID']
    response = {}
    user_email = request.user
    print(user_email)
    if user_can_edit_demo(user_email, demo_id) :
        response['can_edit'] = True
        return HttpResponse(json.dumps(response), 'application/json')
    else :
        response['can_edit'] = False
        return HttpResponse(json.dumps(response), 'application/json')


@login_required(login_url='/cp2/loginPage')
def ajax_remove_vr(request, blob_id):
    settings = {'blob_id' : blob_id}
    response = {}
    response_api = api_post("/api/blobs/delete_vr_from_blob", settings)
    result = response_api.json()
    if result.get('status') == 'OK':
        response['status'] ='OK'
        return JsonResponse({'status': 'OK'}, status=200)
    else : 
        response['status'] = 'KO'
        return HttpResponse(json.dumps(response), 'application/json')

@login_required(login_url='/cp2/loginPage')
def ajax_show_DDL(request):
    demo_id = request.POST['demoID']
    settings = {'demo_id': demo_id}
    response = {}
    response_api = api_post("/api/demoinfo/get_ddl",settings )
    result = response_api.json()
    if result.get('status') != 'OK':
        return HttpResponse(json.dumps(result), 'application/json')
    else :
        response['status'] = 'OK'
        return HttpResponse(json.dumps(result), 'application/json')

@login_required(login_url='/cp2/loginPage')
def ajax_save_DDL(request):
    demo_id = request.POST['demo_id']
    ddl = request.POST['ddl']

    if user_can_edit_demo(request.user, demo_id):
        demoinfo_response = api_post('/api/demoinfo/save_ddl', {'demoid': demo_id}, json=ddl).json()
        return JsonResponse({'status': 'OK'}, status=200)
    else:
        return JsonResponse({'status': 'OK', 'message': 'Unauthorized'}, status=401)

@login_required(login_url='/cp2/loginPage')
def showBlobsDemo(request):
    return render(request, 'showBlobsDemo.html')

@login_required(login_url='/cp2/loginPage')
def demoExtras(request):
    demo_id = request.GET['demo_id']
    response = api_post('/api/demoinfo/get_demo_extras_info', {'demo_id': demo_id }).json()
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

@login_required(login_url='/cp2/loginPage')
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
        api_post('/api/demoinfo/add_demoextras', params= params, files= files).json()
    return HttpResponseRedirect(f'/cp2/demoExtras?demo_id={demo_id}')

@login_required(login_url='/cp2/loginPage')
def ajax_delete_demo_extras(request, demo_id):
    if user_can_edit_demo(request.user, demo_id):
        response = api_post('/api/demoinfo/delete_demoextras', { 'demo_id': demo_id }).json()
        print('alskdjaslkdj', response)
    return HttpResponseRedirect(f'/cp2/demoExtras?demo_id={demo_id}')

@login_required(login_url='/cp2/loginPage')
def ajax_add_template_to_demo(request):
    demo_id = request.POST['demoId']
    template_name = request.POST['template_name']
    settings = {'demo_id': demo_id, 'template_names': template_name}
    response = {}
    if user_can_edit_demo(request.user, demo_id):
        response_api = api_post("/api/blobs/add_templates_to_demo",settings)
        result = response_api.json()
        if result.get('status') != 'OK':
            response['status'] = 'KO'
            return HttpResponse(json.dumps(response), 'application/json')
        else :
            response['status'] = 'OK'
            return HttpResponse(json.dumps(response), 'application/json')
    else : 
        return render(request, 'Homepage.html')

@login_required(login_url='/cp2/loginPage')
def ajax_remove_template_to_demo(request):
    demo_id = request.POST['demoId']
    template_name = request.POST['template_name']
    settings = {'demo_id': demo_id, 'template_name': template_name}
    response = {}
    if user_can_edit_demo(request.user, demo_id):
        response_api = api_post("/api/blobs/remove_template_from_demo", settings)
    # print(response_api)
    # print("************" + response_api.content.decode("utf-8"))
        result = response_api.json()
    # print(result)
        if result.get('status') != 'OK':
            response['status'] = 'KO'
            return HttpResponse(json.dumps(response), 'application/json')
        else :
            response['status'] = 'OK'
            return HttpResponse(json.dumps(response), 'application/json')
    else : 
        return render(request, 'Homepage.html')

@login_required(login_url = '/cp2/loginPage')
def ajax_edit_blob_demo(request):
    new_blob_set = request.POST['SET']
    blob_set = request.POST['old_set']
    new_pos_set = request.POST['PositionSet']
    pos_set = request.POST['old_pos']
    title = request.POST['Title']
    credit = request.POST['Credit']
    demo_id = request.POST['demo_id']
    files = {}
    if 'VR' in request.FILES:
        files['vr'] = request.FILES['VR'].file
    if user_can_edit_demo(request.user, demo_id):
        print("OK")
        response = {}
        settings = {'demo_id' : demo_id, 'blob_set' : blob_set, 'new_blob_set' : new_blob_set, 'pos_set' : pos_set, 'new_pos_set' : new_pos_set, 'title' : title, 'credit' : credit}
        response_api = api_post("/api/blobs/edit_blob_from_demo",settings ,files )
    # print(response_api)
    # print(type(response_api))
    # print("************" + response_api.content.decode("utf-8"))
        result = response_api.json()
        if result.get('status') != 'OK':
            response['status'] =  'KO'
            return HttpResponse(json.dumps(response), 'application/json')
        else :
            response['status'] = 'OK'
            return HttpResponse(json.dumps(response), 'application/json')
    else :
        print("KO")
        return render(request, 'Homepage.html')

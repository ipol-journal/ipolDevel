from django.shortcuts import render, redirect
from django.http import HttpResponse, HttpResponseRedirect
from django.contrib.auth.decorators import login_required
from django.views.decorators.csrf import csrf_protect
from django.contrib.auth import logout, authenticate, login
from .forms import loginForm
import json, requests
from .utils import api_post, user_can_edit_demo
from django.contrib.auth.decorators import user_passes_test
from django.contrib.auth.models import User
from django.core.files.uploadedfile import SimpleUploadedFile




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
    NameTemplate = request.POST['nameTemplate']
    response = {}
    settings = {'template_name' : NameTemplate }
    response_api = api_post("/api/blobs/create_template", settings)
    result = response_api.json()
    if result.get('status') != 'OK':
        response['status'] = 'KO'
        return HttpResponse(json.dumps(response), 'application/json')
    else :
        response['status'] = 'OK'
        return HttpResponse(json.dumps(response), 'application/json')

def showTemplates(request):
    return render(request, 'showTemplates.html')

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
    if user_can_edit_demo(request.user.email, demo_id):
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
    return render(request, 'createBlob.html')

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
    if user_can_edit_demo(request.user.email, demo_id):
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
    response_api = api_post("/api/blobs/add_blob_to_template",settings , files)
    result = response_api.json()
    if result.get('status') != 'OK':
        response['status'] = 'KO'
        return HttpResponse(json.dumps(response), 'application/json')
    else :
        response['status'] = 'OK'
        return HttpResponse(json.dumps(response), 'application/json')
    
@login_required(login_url= '/cp2/loginPage')
def detailsBlob(request):
    return render(request, 'detailsBlob.html')


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
    demos = api_post('/api/demoinfo/demo_list_pagination_and_filter', {
        'qfilter': demo_id,
        'num_elements_page': 1,
        'page': 1
        }).json()
    
    demo = demos['demo_list'][0]
    title = demo['title']
    # canEdit = api_post('showDemo/ajax_user_can_edit_demo', { 'demo_id': demo_id })

    context = {
        "demo_id": demo_id,
        "title": title,
        # "canEditDemo": canEdit
    }
    print('context',context)
    return render(request, 'showDemo.html', context)

@login_required(login_url='/cp2/loginPage')
def ajax_user_can_edit_demo(request):
    demo_id = request.POST['demoID']
    response = {}
    user_email = request.user.email
    print(user_email)
    if user_can_edit_demo(user_email, demo_id) :
        response['can_edit'] = 'YES'
        return HttpResponse(json.dumps(response), 'application/json')
    else :
        response['can_edit'] = 'NO'
        return HttpResponse(json.dumps(response), 'application/json')


@login_required(login_url='/cp2/loginPage')
def ajax_remove_vr(request):
    blob_id = request.POST['blob_id']
    settings = {'blob_id' : blob_id}
    response = {}
    response_api = api_post("/api/blobs/delete_vr_from_blob", settings)
    result = response_api.json()
    if result.get('status') != 'OK':
        response['status'] ='KO'
        return HttpResponse(json.dumps(response), 'application/json')
    else : 
        response['status'] = 'OK'
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
        'extras_name': extras_name
    }
    return render(request, 'demoExtras.html', context)

@login_required(login_url='/cp2/loginPage')
@csrf_protect
def ajax_add_demo_extras(request):
    demo_id = request.POST['demo_id']
    file = request.POST['file']
    print(request.FILES)
    print(request.user.email, demo_id)
    if user_can_edit_demo(request.user.email, demo_id):
        response = api_post('/api/demoinfo/add_demoextras', { 
            'demo_id': demo_id,
            'demoextras': file,
            'demoextras_name': 'file.tar.gz'
            }).json()
        print('alskdjaslkdj', response)
    return HttpResponseRedirect(f'/cp2/demoExtras?demo_id={demo_id}')

@login_required(login_url='/cp2/loginPage')
def ajax_delete_demo_extras(request, demo_id):
    if user_can_edit_demo(request.user.email, demo_id):
        response = api_post('/api/demoinfo/delete_demoextras', { 'demo_id': demo_id }).json()
        print('alskdjaslkdj', response)
    return HttpResponseRedirect(f'/cp2/demoExtras?demo_id={demo_id}')

@login_required(login_url='/cp2/loginPage')
def ajax_add_template_to_demo(request):
    demo_id = request.POST['demoId']
    template_name = request.POST['template_name']
    settings = {'demo_id': demo_id, 'template_names': template_name}
    response = {}
    if user_can_edit_demo(request.user.email, demo_id):
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
    if user_can_edit_demo(request.user.email, demo_id):
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
    if user_can_edit_demo(request.user.email, demo_id):
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

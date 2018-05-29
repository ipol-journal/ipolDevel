from django.shortcuts import render, redirect
from django.http import HttpResponse, HttpResponseRedirect
from django.contrib.auth.decorators import login_required
from django.views.decorators.csrf import csrf_protect
from django.contrib.auth import logout, authenticate, login
from .forms import loginForm
from django.http import HttpRequest
import json, requests


@login_required(login_url='/cp2/loginPage')
def Homepage(request):
    return render(request, 'Homepage.html')

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
def addDemo(request):
    return render(request, 'addDemo.html')

@login_required(login_url='/cp2/loginPage')
@csrf_protect
def ajax_add_demo(request):
    state = request.POST['State'].lower()
    title = request.POST['Title']
    demoid = request.POST['DemoId']
    response = {}
    #i need to check the HOST_NAME in order to know if we are in production, integration, localhost instead of the "127.0.0.1"
    #in setting.py with the sentence "htttp://{HOST_NAME}/api/demoinfo/add_demo" like in the old CP
    #other pb with the socket and Gunicorn : "Ignoring EPIPE"
    #when i use requests do .json() to have a json 
    
    settings = {'state': state, 'title': title, 'editorsdemoid': demoid}
    response_api = requests.post("http://127.0.0.1/api/demoinfo/add_demo", params = settings)
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
    response_api = requests.post("http://127.0.0.1/api/blobs/create_template", params = settings)
    result = response_api.json()
    if result.get('status') != 'OK':
        response['status'] = 'KO'
        return HttpResponse(json.dumps(response), 'application/json')
    else :
        response['status'] = 'OK'
        return HttpResponse(json.dumps(response, 'application/json'))

@login_required(login_url='/cp2/loginPage')
def showTemplates(request):
    return render(request, 'showTemplates.html')



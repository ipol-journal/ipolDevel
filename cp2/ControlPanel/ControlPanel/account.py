from django.shortcuts import render, redirect
from django.http import HttpResponse, HttpResponseRedirect, JsonResponse
from django.urls import reverse
from django.contrib.auth.decorators import login_required
from django.views.decorators.csrf import csrf_protect
from django.contrib.auth import logout as logoutMethod, authenticate, login as loginMethod
from django.contrib.auth.models import User
from .forms import loginForm
from django.core.mail import send_mail
from django.contrib.auth.decorators import user_passes_test

from ControlPanel.settings import HOST_NAME

@csrf_protect
def loginPage(request):
    form = loginForm(request.POST or None)
    username = request.POST.get('username')
    password = request.POST.get('password')
    user = authenticate(request, username=username, password=password)
    if user is not None:
        loginMethod(request, user)
        return HttpResponseRedirect('/cp2/')
    else:
        return render(request, "login.html", {'form': form})

@login_required(login_url='login')
@csrf_protect
def signout(request):
    return render(request, 'signout.html')

@login_required(login_url='login')
@csrf_protect
def logout(request):
    logoutMethod(request)
    return redirect(reverse('login'))

def password_reset(request):
    return render(request, 'password/password_reset.html')

def ajax_send_password_recovery(request):
    user_email = request.POST.get('email')
    email_exists = User.objects.filter(email=user_email).exists()
    if email_exists:
        send_mail(
            'Subject here',
            'Here is the message.',
            'ipol@example.com',
            [user_email],
            fail_silently=False,
        )
    return render(request, 'login.html')

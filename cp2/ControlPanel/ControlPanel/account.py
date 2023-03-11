from django.shortcuts import render, redirect
from django.http import HttpResponse, HttpResponseRedirect
from django.urls import reverse
from django.contrib.auth.decorators import login_required
from django.views.decorators.csrf import csrf_protect
from django.contrib.auth import logout as logoutMethod, authenticate, login as loginMethod
from django.contrib.auth.forms import PasswordResetForm
from django.contrib.auth.models import User
from django.template.loader import render_to_string
from django.db.models.query_utils import Q
from django.utils.http import urlsafe_base64_encode
from django.contrib.auth.tokens import default_token_generator
from django.utils.encoding import force_bytes
from django.contrib import messages

from .forms import loginForm
from django.core.mail import BadHeaderError, send_mail
from smtplib import SMTPException

from .utils import api_post

import logging

logger = logging.getLogger(__name__)

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
    if request.method == "POST":
        password_reset_form = PasswordResetForm(request.POST)
        if password_reset_form.is_valid():
            data = password_reset_form.cleaned_data['email']
            associated_users = User.objects.filter(Q(email=data))
            if associated_users.exists():
                for user in associated_users:
                    subject = f'[{request.get_host()}]Password Reset Requested'
                    email_template_name = "password/password_reset_email.txt"
                    from_email = f'ipol@{request.get_host()}'
                    c = {
                    "email": user.email,
                    'domain': request.get_host(),
                    'site_name': request.get_host(),
                    "uid": urlsafe_base64_encode(force_bytes(user.pk)),
                    "user": user,
                    'token': default_token_generator.make_token(user),
                    'protocol': request.scheme,
                    }
                    email = render_to_string(email_template_name, c)
                    try:
                        send_mail(subject, email, from_email, [user.email], fail_silently=False)
                    except BadHeaderError:
                        logger.warning(f'Error sending email: {subject, email, from_email, [user.email]}')
                        return HttpResponse('Invalid header found.')
                    except SMTPException as e:
                        logger.warning('SMTP exception, error sending email: ', e)
                        print('There was an error sending an email: ', e)
                        return HttpResponse('Error sending email.')
                    return redirect('password_reset_done')

    password_reset_form = PasswordResetForm()
    return render(request=request, template_name="password/password_reset.html", context={"password_reset_form":password_reset_form})

@login_required(login_url='login')
@csrf_protect
def profile(request):
    user = request.user
    context = {
        "username": user.username,
        "email": user.email,
        "firstName": user.first_name,
        "lastName": user.last_name
    }
    return render(request=request, template_name="profile.html", context=context)

@login_required(login_url='login')
@csrf_protect
def save_profile(request):
    profiles = User.objects.filter(email=request.user.email)
    demoinfo_editor = api_post('/api/demoinfo/get_editor', {'email': request.POST.get('email', '')})
    new_email_exists = demoinfo_editor['editor']

    if not profiles.exists():
        messages.warning(request, 'The profile you are trying to modify does not exist')
        return HttpResponseRedirect('/cp2/profile')
    email_changed = request.user.email != request.POST.get('email', '')
    if new_email_exists and email_changed:
        messages.warning(request, 'New email is already in use.')
        return HttpResponseRedirect('/cp2/profile')
    if new_email_exists:
        for profile in profiles:
            profile.username = request.POST.get('username', '')
            profile.first_name = request.POST.get('firstName', '')
            profile.last_name = request.POST.get('lastName', '')
    else:
        for profile in profiles:
            profile.username = request.POST.get('username', '')
            profile.first_name = request.POST.get('firstName', '')
            profile.last_name = request.POST.get('lastName', '')
            profile.email = request.POST.get('email', '')

    profile.save()
    messages.success(request, 'Your profile has been changed successfully.')
    return HttpResponseRedirect('/cp2/profile')
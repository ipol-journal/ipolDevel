from django.shortcuts import render, redirect
from django.http import HttpResponse, HttpResponseRedirect, JsonResponse
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
                        return HttpResponse('Invalid header found.')
                    return redirect('password_reset_done')

    password_reset_form = PasswordResetForm()
    return render(request=request, template_name="password/password_reset.html", context={"password_reset_form":password_reset_form})

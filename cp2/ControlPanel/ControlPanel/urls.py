"""ControlPanel URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/2.0/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path
from django.conf.urls import url
from ControlPanel.view import Homepage, loginPage, signout, logoff, status, addDemo, ajax_add_demo, templates, showTemplates, ajax_add_template


urlpatterns = [
    path('cp2/admin/', admin.site.urls),
    path('cp2/', Homepage),
    path('cp2/loginPage', loginPage),
    path('cp2/signout', signout),
    path('cp2/logoff', logoff),
    path('cp2/status', status),
    path('cp2/addDemo/', addDemo),
    path('cp2/addDemo/ajax', ajax_add_demo),
    path('cp2/templates', templates),
    path('cp2/templates/ajax', ajax_add_template),
    path('cp2/showTemplates', showTemplates),
]

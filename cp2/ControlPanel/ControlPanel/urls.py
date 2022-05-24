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
from ControlPanel.view import *


urlpatterns = [
    path('cp2/admin/', admin.site.urls),
    path('cp2/', Homepage),
    path('cp2/loginPage', loginPage),
    path('cp2/signout', signout),
    path('cp2/logoff', logoff),
    path('cp2/status', status),
    path('cp2/addDemo/ajax', ajax_add_demo),
    path('cp2/templates', templates),
    path('cp2/templates/ajax', ajax_add_template),
    path('cp2/showTemplate', showTemplate),
    path('cp2/showTemplates/ajax', ajax_delete_blob_template),
    path('cp2/showTemplates/ajax_delete_template', ajax_delete_template),
    path('cp2/createBlob', CreateBlob),
    path('cp2/createBlob/ajax', ajax_add_blob_template),
    path('cp2/createBlob/ajax_demo', ajax_add_blob_demo),
    path('cp2/detailsBlob', detailsBlob),
    path('cp2/detailsBlob/ajax_template', ajax_edit_blob_template),
    path('cp2/detailsBlob/ajax_demo', ajax_edit_blob_demo),
    path('cp2/detailsBlob/ajax_remove_vr', ajax_remove_vr, name='remove_vr'),
    path('cp2/removeBlob/ajax_remove_blob_from_demo', ajax_remove_blob_from_demo, name='remove_blob_demo'),
    path('cp2/removeBlob/ajax_remove_blob_from_template', ajax_remove_blob_from_template, name='remove_blob_template'),
    path('cp2/showDemo', showDemo),
    path('cp2/showDemo/ajax_showDDL', ajax_show_DDL),
    path('cp2/showDemo/ajax_save_DDL', ajax_save_DDL, name='save_ddl'),
    path('cp2/showDemo/ajax_user_can_edit_demo', ajax_user_can_edit_demo),
    path('cp2/showBlobsDemo', showBlobsDemo),
    path('cp2/showBlobsDemo/ajax', ajax_delete_blob_demo),
    path('cp2/demoExtras', demoExtras),
    path('cp2/demoExtras/ajax_add_demo_extras', ajax_add_demo_extras, name='add_extras'),
    path('cp2/demoExtras/ajax_delete_demo_extras', ajax_delete_demo_extras, name='delete_extras'),
    path('cp2/showBlobsDemo/ajax_add_template_to_demo', ajax_add_template_to_demo),
    path('cp2/showBlobsDemo/ajax_remove_template_to_demo', ajax_remove_template_to_demo),
]



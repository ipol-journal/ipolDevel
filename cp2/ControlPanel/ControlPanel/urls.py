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
from ControlPanel.account import *
from ControlPanel.view import *
from django.contrib import admin
from django.contrib.auth import views as auth_views
from django.urls import include, path

urlpatterns = [
    path(
        "cp2/",
        include(
            [
                path("", homepage, name="homepage"),
                path(
                    "password_reset/",
                    password_reset,
                    name="password/password_reset.html",
                ),
                path(
                    "password_reset/done/",
                    auth_views.PasswordResetDoneView.as_view(
                        template_name="password/password_reset_done.html"
                    ),
                    name="password_reset_done",
                ),
                path(
                    "reset/<uidb64>/<token>/",
                    auth_views.PasswordResetConfirmView.as_view(
                        template_name="password/password_reset_confirm.html"
                    ),
                    name="password_reset_confirm",
                ),
                path(
                    "reset/done/",
                    auth_views.PasswordResetCompleteView.as_view(
                        template_name="password/password_reset_complete.html"
                    ),
                    name="password_reset_complete",
                ),
                path("admin", admin.site.urls),
                path("login", loginPage, name="login"),
                path("signout", signout),
                path("logout", logout),
                path("status", status),
                path("profile", profile, name="profile"),
                path("save_profile", save_profile, name="save_profile"),
                path("demo_editors", demo_editors, name="demo_editors"),
                path("add_demo_editor", add_demo_editor, name="add_demo_editor"),
                path(
                    "remove_demo_editor", remove_demo_editor, name="remove_demo_editor"
                ),
                path("addDemo/ajax", ajax_add_demo),
                path("removeDemo/ajax", ajax_delete_demo, name="delete_demo"),
                path("templates", templates),
                path("templates/ajax", ajax_add_template),
                path("showTemplate", showTemplate),
                path("showTemplates/ajax", ajax_delete_blob_template),
                path("showTemplates/ajax_delete_template", ajax_delete_template),
                path("createBlob", CreateBlob),
                path("createBlob/template", ajax_add_blob_template),
                path("createBlob/demo", ajax_add_blob_demo),
                path("detailsBlob", detailsBlob),
                path("detailsBlob/ajax_template", ajax_edit_blob_template),
                path("detailsBlob/ajax_demo", ajax_edit_blob_demo),
                path("detailsBlob/ajax_remove_vr", ajax_remove_vr, name="remove_vr"),
                path(
                    "removeBlob/ajax_remove_blob_from_demo",
                    ajax_remove_blob_from_demo,
                    name="remove_blob_demo",
                ),
                path(
                    "removeBlob/ajax_remove_blob_from_template",
                    ajax_remove_blob_from_template,
                    name="remove_blob_template",
                ),
                path("showDemo", showDemo),
                path("showDemo/ajax_showDDL", ajax_show_DDL),
                path("showDemo/ajax_save_DDL", ajax_save_DDL, name="save_ddl"),
                path("showDemo/ajax_user_can_edit_demo", ajax_user_can_edit_demo),
                path("showDemo/ajax_edit_demo", edit_demo, name="edit_demo"),
                path("showDemo/ddl_history", ddl_history, name="ddl_history"),
                path("showDemo/reset_ssh_key", reset_ssh_key),
                path("showBlobsDemo", showBlobsDemo),
                path("showBlobsDemo/ajax", ajax_delete_blob_demo),
                path(
                    "showBlobsDemo/ajax_add_template_to_demo", ajax_add_template_to_demo
                ),
                path(
                    "showBlobsDemo/ajax_remove_template_to_demo",
                    ajax_remove_template_to_demo,
                ),
                path("demoExtras", demoExtras),
                path(
                    "demoExtras/ajax_add_demo_extras",
                    ajax_add_demo_extras,
                    name="add_extras",
                ),
                path(
                    "demoExtras/ajax_delete_demo_extras",
                    ajax_delete_demo_extras,
                    name="delete_extras",
                ),
                path("showArchive", show_archive, name="archive"),
                path("showExperiment", show_experiment, name="showExperiment"),
                path(
                    "ajax_delete_experiment",
                    ajax_delete_experiment,
                    name="delete_experiment",
                ),
            ]
        ),
    )
]

from django.conf.urls import  url
from apps.controlpanel.views.Status import StatusView

from apps.controlpanel.views.archive_module import ArchiveDeleteExperimentView, \
        ArchiveDeleteExperimentFileView, ArchiveDeleteDemoView, \
        ArchivePageView, ExperimentDetails

from apps.controlpanel.views.blobs_module import ManageBlobsForDemoView, EditBlobFromDemoView,DemoBlobSaveInfo,RemoveBlobFromDemo, \
    RemoveTemplateFromDemo,AddBlobDemoView,AddBlobToDemo,AddTemplateToDemo,TemplatePageView, AddBlobTemplateView, \
    AddBlobToTemplate,RemoveBlobFromDemo, EditBlobFromTemplate, DeleteVRFromBlob, SaveBlobInfoFromTemplate, RemoveBlobFromTemplate, \
    TemplateListView,DeleteTemplate,CreateTemplate

from apps.controlpanel.views.demo import DemosView

from apps.controlpanel.views.demoinfo_module import DemoinfoDemosView, DemoinfoAuthorsView, DemoinfoEditorsView, \
    DemoinfoDeleteDemoView, DemoinfoGetDDLView, DemoinfoSaveDDLView, DemoinfoGetDemoView, DemoinfoSaveDemo, \
    DemoinfoDeleteAuthorView, DemoinfoUpdateDemo, DemoinfoGetAuthorView, DemoinfoSaveAuthorView, DemoinfoDemoEditionView, \
    DemoinfoGetDemoAuthorView, DemoinfoDeleteAuthorFromDemoView, DemoinfoAddExistingAuthorToDemoView, \
    DemoinfoAddNewAuthorToDemoView, DemoinfoDeleteEditorView, DemoinfoGetEditorView, DemoinfoSaveEditorView, \
    DemoinfoGetDemoEditorView, DemoinfoAddNewEditorToDemoView, RestoreDDL, DemoinfoDDLHistoryView, DemoinfoAddExistingEditorToDemoView, \
    DemoinfoDeleteEditorFromDemoView, DemoinfoGetDemoExtrasView, DemoinfoDeleteDemoExtrasView, DemoinfoAddDemoExtrasView


#Allouth
from vendor.allauth.customviews.profile import ProfileView
from django.conf.urls import  url
from django.contrib.auth.decorators import login_required
from vendor.allauth.customviews.account import MyLoginView, MySignupView, MyLogoutView, MyPasswordChangeView, \
        MyPasswordSetView, MyAccountInactiveView, MyEmailView, MyConfirmEmailView, MyPasswordResetView, \
        MyPasswordResetDoneView, MyPasswordResetFromKeyView, MyPasswordResetFromKeyDoneView, MyEmailVerificationSentView

__author__ = 'josearrecio'


urlpatterns = [



    # Common integrated view (mixes stuff from different modules and presents it together)
        #todo blobs should use stats
    url(r'^status/', StatusView.as_view(), name="ipol.cp.status"),
    url(r'^demos/', DemosView.as_view(), name="ipol.cp.demos"),

        ###################
    # Demoinfo module #
        ###################

        # DEMOS

        # Demo list
    url(r'^demoinfo_demos/', DemoinfoDemosView.as_view(), name="ipol.cp.demoinfo.demos"),
    url(r'^demo_edition/(?P<demo_id>\d+)/$', DemoinfoDemoEditionView.as_view(), name="ipol.cp.demoinfo.demo_edition"),
    url(r'^ajax_delete_demoinfo_demo/(?P<demo_id>[\-\d\w]+)/$', DemoinfoDeleteDemoView.as_view(), name="ipol.cp.demoinfo.delete_demo"),
        # Show the ddl form in a modal whith the ddl (ajax jq call)
    url(r'^ajax_get_demoinfo_ddl/(?P<demo_id>\d+)/$', DemoinfoGetDDLView.as_view(), name="ipol.cp.demoinfo.get_ddl"),
    # Process the edit/new ddl form  (ajax jq call)
    url(r'^ajax_save_demoinfo_ddl/', DemoinfoSaveDDLView.as_view(), name="ipol.cp.demoinfo.save_ddl"),
    url(r'^ddl_history/(?P<demo_id>\d+)/$', DemoinfoDDLHistoryView.as_view(), name="ipol.cp.demoinfo.ddl_history"),
    url(r'^ajax_restore_ddl/$', RestoreDDL.as_view(), name="ipol.cp.demoinfo.restore_ddl"),
    url(r'^ajax_get_demoinfo_demo/$', DemoinfoGetDemoView.as_view(), name="ipol.cp.demoinfo.create_demo"),
    url(r'^ajax_get_demoinfo_demo/(?P<demo_id>\d+)/$', DemoinfoGetDemoView.as_view(), name="ipol.cp.demoinfo.edit_demo"),
    url(r'^ajax_save_demoinfo_demo/', DemoinfoSaveDemo.as_view(), name="ipol.cp.demoinfo.save_demo"),
    url(r'^ajax_update_demoinfo_demo/', DemoinfoUpdateDemo.as_view(), name="ipol.cp.demoinfo.update_demo"),

        # AUTHORS

        # Author list
    url(r'^demoinfo_authors/', DemoinfoAuthorsView.as_view(), name="ipol.cp.demoinfo.authors"),
    url(r'^ajax_delete_demoinfo_author/(?P<author_id>\d+)/$', DemoinfoDeleteAuthorView.as_view(), name="ipol.cp.demoinfo.delete_author"),
    url(r'^ajax_get_demoinfo_author/$', DemoinfoGetAuthorView.as_view(), name="ipol.cp.demoinfo.create_author"),
    url(r'^ajax_get_demoinfo_author/(?P<author_id>\d+)/$', DemoinfoGetAuthorView.as_view(), name="ipol.cp.demoinfo.edit_author"),
    url(r'^ajax_save_demoinfo_author/', DemoinfoSaveAuthorView.as_view(), name="ipol.cp.demoinfo.save_author"),
        # Manage Demo's Authors add/remove/get
    url(r'^authors_of_demo/(?P<demo_id>\d+)/$', DemoinfoGetDemoAuthorView.as_view(), name="ipol.cp.demoinfo.get_demos_authors"),
        #save forms
    url(r'^ajax_add_demoinfo_existing_author_to_demo/', DemoinfoAddExistingAuthorToDemoView.as_view(), name="ipol.cp.demoinfo.add_existing_author_to_demo"),
    url(r'^ajax_add_demoinfo_new_author_to_demo/', DemoinfoAddNewAuthorToDemoView.as_view(), name="ipol.cp.demoinfo.add_new_author_to_demo"),
        #deletes author from demo, but does not delete the author itself
    url(r'^ajax_delete_demoinfo_author_from_demo/(?P<demo_id>\d+)/(?P<author_id>\d+)/$', DemoinfoDeleteAuthorFromDemoView.as_view(), name="ipol.cp.demoinfo.delete_author_from_demo"),


        #EDITORS

    # Editor list
    url(r'^demoinfo_editors/', DemoinfoEditorsView.as_view(), name="ipol.cp.demoinfo.editors"),
    url(r'^ajax_delete_demoinfo_editor/(?P<editor_id>\d+)/$', DemoinfoDeleteEditorView.as_view(), name="ipol.cp.demoinfo.delete_editor"),
    url(r'^ajax_get_demoinfo_editor/$', DemoinfoGetEditorView.as_view(), name="ipol.cp.demoinfo.create_editor"),
    url(r'^ajax_get_demoinfo_editor/(?P<editor_id>\d+)/$', DemoinfoGetEditorView.as_view(), name="ipol.cp.demoinfo.edit_editor"),
    url(r'^ajax_save_demoinfo_editor/', DemoinfoSaveEditorView.as_view(), name="ipol.cp.demoinfo.save_editor"),
        # Manage Demo's Editors add/remove/get
    url(r'^editors_of_demo/(?P<demo_id>\d+)/$', DemoinfoGetDemoEditorView.as_view(), name="ipol.cp.demoinfo.get_demos_editors"),
        #save forms
    url(r'^ajax_add_demoinfo_existing_editor_to_demo/', DemoinfoAddExistingEditorToDemoView.as_view(), name="ipol.cp.demoinfo.add_existing_editor_to_demo"),
    url(r'^ajax_add_demoinfo_new_editor_to_demo/', DemoinfoAddNewEditorToDemoView.as_view(), name="ipol.cp.demoinfo.add_new_editor_to_demo"),
        #deletes editor from demo, but does not delete the editor itself
    url(r'^ajax_delete_demoinfo_editor_from_demo/(?P<demo_id>\d+)/(?P<editor_id>\d+)/$', DemoinfoDeleteEditorFromDemoView.as_view(), name="ipol.cp.demoinfo.delete_editor_from_demo"),

        #DEMO EXTRAS
    #Demo extras list
    url(r'^demo_extras_of_demo/(?P<demo_id>\d+)/$', DemoinfoGetDemoExtrasView.as_view(), name="ipol.cp.demoinfo.get_demo_extras"),
    #Delete demo extra
    url(r'^ajax_delete_demo_extra_from_demo/(?P<demo_id>\d+)/$', DemoinfoDeleteDemoExtrasView.as_view(), name="ipol.cp.demoinfo.delete_demo_extra_from_demo"),
    #Delete demo extra
    url(r'^add_demo_extra_to_demo/(?P<demo_id>\d+)/$', DemoinfoAddDemoExtrasView.as_view(), name="ipol.cp.demoinfo.add_demo_extra_to_demo"),



    ###################
    # Archive module  #
    ###################

    # Menu option Archive Module:
    #todo, carefull, a demo can have negative id WTF!
    #todo list_demos should be nicer

    url(r'^archive_demo/(?P<id>[\-\d\w]+)/(?P<page>\d+)/$', ArchivePageView.as_view(), name="ipol.cp.archive.page"),
    url(r'^archive_demo/(?P<id>[\-\d\w]+)/$', ArchivePageView.as_view(), name="ipol.cp.archive.page"),
    url(r'^archive_demo/(?P<q>\d+)/$', ExperimentDetails.as_view(), name="ipol.cp.archive.experiment_details"),
    url(r'^archive_demo/', ExperimentDetails.as_view(), name="ipol.cp.archive.experiment_details"),

    #ajax calls
    url(r'^ajax_delete_archive_demo/(?P<demo_id>[\-\d\w]+)/$', ArchiveDeleteDemoView.as_view(), name="ipol.cp.archive.delete_demo"),
    url(r'^ajax_delete_experiment/(?P<experiment_id>\d+)/$',
        ArchiveDeleteExperimentView.as_view(), name="ipol.cp.archive.delete_experiment"),
    url(r'^ajax_delete_experiment_file/(?P<file_id>\d+)/$',
        ArchiveDeleteExperimentFileView.as_view(), name="ipol.cp.archive.delete_experiment_file"),



    ###################
    # Blobs module    #
    ###################

        #todo not much done here
    url(r'^blob_demo/(?P<id>[\-\d\w]+)/(?P<page>\d+)/$', ManageBlobsForDemoView.as_view(), name="ipol.cp.blobs.page"),
    url(r'^blob_demo/(?P<id>[\-\d\w]+)/$', ManageBlobsForDemoView.as_view(), name="ipol.cp.blobs.page"),

    url(r'^blob_demo/(?P<id>[\-\d\w]+)/$', EditBlobFromDemoView.as_view(), name="ipol.cp.blobs.blob_details"),
    url(r'^blob_demo/$', EditBlobFromDemoView.as_view(), name="ipol.cp.blobs.blob_details"),
    url(r'^add_blob_to_demo/(?P<id>[\-\d\w]+)/$', AddBlobDemoView.as_view(), name="ipol.cp.blobs.add_blob_to_demo_view"),
    url(r'^ajax_save_blob_info/$', DemoBlobSaveInfo.as_view(), name="ipol.cp.blobs.save_blob_info"),
    url(r'^ajax_remove_blob_from_demo/$', RemoveBlobFromDemo.as_view(), name="ipol.cp.blobs.remove_blob_from_demo"),
    url(r'^ajax_remove_template_from_demo/$', RemoveTemplateFromDemo.as_view(), name="ipol.cp.blobs.remove_template_from_demo"),
    url(r'^ajax_add_template_to_demo/$', AddTemplateToDemo.as_view(), name="ipol.cp.blobs.add_template_to_demo"),
    url(r'^ajax_add_blob_to_demo/$', AddBlobToDemo.as_view(), name="ipol.cp.blobs.add_blob_to_demo"),

    #Templates
    url(r'^blob_template/(?P<name>[\-\d\w]+)/$', TemplatePageView.as_view(), name="ipol.cp.template.page"),
    url(r'^add_blob_to_template/(?P<name>[\-\d\w]+)/$', AddBlobTemplateView.as_view(), name="ipol.cp.add_blob_to_template.page"),
    url(r'^ajax_add_blob_to_template/$', AddBlobToTemplate.as_view(), name="ipol.cp.blobs.add_blob_to_template"),
    url(r'^ajax_remove_blob_from_template/$', RemoveBlobFromTemplate.as_view(), name="ipol.cp.blobs.remove_blob_from_template"),
    url(r'^blob_template/$', EditBlobFromTemplate.as_view(), name="ipol.cp.blobs.edit_blob_template.page"),
    url(r'^ajax_delete_vr_from_blob/$', DeleteVRFromBlob.as_view(), name="ipol.cp.blobs.delete_vr_from_blob"),
    url(r'^ajax_save_blob_info_from_template/$', SaveBlobInfoFromTemplate.as_view(), name="ipol.cp.blobs.save_blob_info_from_template"),

    url(r'^templates_list/$', TemplateListView.as_view(), name="ipol.cp.blobs.templates_list.page"),
    url(r'^ajax_delete_template/$', DeleteTemplate.as_view(), name="ipol.cp.blobs.delete_template"),
    url(r'^ajax_create_template/$', CreateTemplate.as_view(), name="ipol.cp.blobs.create_template"),
    #####################
    # DemoRunner module #
    #####################

    ##########################
    # Demo Dispatcher module #
    ##########################

    # Demo (we will not be using this probably, but just in case, its the old code)

    ###########
    # allauth #
    ###########
    url(r'^login/$', MyLoginView.as_view(),name='account_login'),
        url(r"^signup/$", MySignupView.as_view(), name="account_signup"),
    url(r"^logout/$", MyLogoutView.as_view(), name="account_logout"),
    url(r"^password/change/$", login_required(MyPasswordChangeView.as_view()),name="account_change_password"),
    url(r"^password/set/$", login_required(MyPasswordSetView.as_view()), name="account_set_password"),
    url(r"^inactive/$", MyAccountInactiveView.as_view(), name="account_inactive"),
    # E-mail
    url(r"^email/$", MyEmailView.as_view(), name="account_email"),
    url(r"^confirm-email/$", MyEmailVerificationSentView.as_view(), name="account_email_verification_sent"),
    url(r"^confirm-email/(?P<key>\w+)/$", MyConfirmEmailView.as_view(), name="account_confirm_email"),
    # password reset
    url(r"^password/reset/$", MyPasswordResetView.as_view(), name="account_reset_password"),
    url(r"^password/reset/done/$", MyPasswordResetDoneView.as_view(), name="account_reset_password_done"),
    url(r"^password/reset/key/(?P<uidb36>[0-9A-Za-z]+)-(?P<key>.+)/$", MyPasswordResetFromKeyView.as_view(), name="account_reset_password_from_key"),
    url(r"^password/reset/key/done/$", MyPasswordResetFromKeyDoneView.as_view(), name="account_reset_password_from_key_done"),
    url(r'^profile/', login_required(ProfileView.as_view()), name="allauth.profile"),

    ###################
    # Docs            #
    ###################
    #todo, documentacion in the app would be nice to have! atfirst jut link pdf......


]

#SERVE STATIFILES FROM settings.STATIC_ROOT in LOCAL (in production staic files are served by apache...or similar)
#rmeber to run $  python manage.py collectstatic
# ifsettings.HOST == 'local' :   #if DEBUG is True it will be served automatically
#       #url must be difined in settings.STATIC_URL
#       urlpatterns += patterns('',url(r'^app_static/(?P<path>.*)$', 'django.views.static.serve', {'document_root': settings.STATIC_ROOT}))

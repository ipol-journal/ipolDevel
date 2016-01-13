from django.conf.urls import  url
from apps.controlpanel.views.Status import StatusView

from apps.controlpanel.views.archive_module import ArchiveShutdownView, ArchiveDeleteExperimentView, \
	ArchiveAddExpToTestDemoView, ArchiveDeleteExperimentFileView, ArchiveDemosView, ArchiveDeleteDemoView, \
	ArchivePageView

from apps.controlpanel.views.blobs_module import BlobsDemosView
from apps.controlpanel.views.demo import DemosView

from apps.controlpanel.views.demoinfo_module import DemoinfoDemosView, DemoinfoAuthorsView, DemoinfoEditorsView, \
    DemoinfoDeleteDemoView, DemoinfoGetDDLView, DemoinfoSaveDDLView, DemoinfoGetDemoView, DemoinfoSaveDemoView, \
    DemoinfoDeleteAuthorView, DemoinfoGetAuthorView, DemoinfoSaveAuthorView, \
	DemoinfoGetDemoAuthorView, DemoinfoDeleteAuthorFromDemoView, DemoinfoAddExistingAuthorToDemoView, \
	DemoinfoAddNewAuthorToDemoView, DemoinfoDeleteEditorView, DemoinfoGetEditorView, DemoinfoSaveEditorView, \
	DemoinfoGetDemoEditorView, DemoinfoAddNewEditorToDemoView, DemoinfoAddExistingEditorToDemoView, \
	DemoinfoDeleteEditorFromDemoView

__author__ = 'josearrecio'


urlpatterns = [



    # Common integrated view (mixes stuff from different modules and presents it together)
	#todo blobs should use stats
    url(r'^status/', StatusView.as_view(), name="ipol.cp.status"),
    url(r'^demos/', DemosView.as_view(), name="ipol.cp.demos"),

	###################
    # Demoinfo module #
	###################

	# Menu option Demoinfo Module: has threee tabs (demos, authors or editors), loads first tab by default, Demos
    # Each tab call the demoinfo module WS to create the list of demos, authors or editors, each tab has pagination and filters

	# DEMOS

	# Demo list
    url(r'^demoinfo_demos/', DemoinfoDemosView.as_view(), name="ipol.cp.demoinfo.demos"),
    url(r'^ajax_delete_demoinfo_demo/(?P<demo_id>[\-\d\w]+)/$', DemoinfoDeleteDemoView.as_view(), name="ipol.cp.demoinfo.delete_demo"),
	# Show the ddl form in a modal whith the ddl (ajax jq call)
    url(r'^ajax_get_demoinfo_ddl/(?P<demo_id>\d+)/$', DemoinfoGetDDLView.as_view(), name="ipol.cp.demoinfo.get_ddl"),
    # Process the edit/new ddl form  (ajax jq call)
    url(r'^ajax_save_demoinfo_ddl/', DemoinfoSaveDDLView.as_view(), name="ipol.cp.demoinfo.save_ddl"),
    url(r'^ajax_get_demoinfo_demo/$', DemoinfoGetDemoView.as_view(), name="ipol.cp.demoinfo.create_demo"),
    url(r'^ajax_get_demoinfo_demo/(?P<demo_id>\d+)/$', DemoinfoGetDemoView.as_view(), name="ipol.cp.demoinfo.edit_demo"),

    url(r'^ajax_save_demoinfo_demo/', DemoinfoSaveDemoView.as_view(), name="ipol.cp.demoinfo.save_demo"),

	# AUTHORS

	# Author list
    url(r'^demoinfo_authors/', DemoinfoAuthorsView.as_view(), name="ipol.cp.demoinfo.authors"),
    url(r'^ajax_delete_demoinfo_author/(?P<author_id>\d+)/$', DemoinfoDeleteAuthorView.as_view(), name="ipol.cp.demoinfo.delete_author"),
    url(r'^ajax_get_demoinfo_author/$', DemoinfoGetAuthorView.as_view(), name="ipol.cp.demoinfo.create_author"),
    url(r'^ajax_get_demoinfo_author/(?P<author_id>\d+)/$', DemoinfoGetAuthorView.as_view(), name="ipol.cp.demoinfo.edit_author"),
    url(r'^ajax_save_demoinfo_author/', DemoinfoSaveAuthorView.as_view(), name="ipol.cp.demoinfo.save_author"),
	# Manage Demo's Authors add/remove/get
	# todo this goes first, if miki likes this, do the same for editor
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
	# todo this goes first, if miki likes this, do the same for editor
    url(r'^editors_of_demo/(?P<demo_id>\d+)/$', DemoinfoGetDemoEditorView.as_view(), name="ipol.cp.demoinfo.get_demos_editors"),
	#save forms
    url(r'^ajax_add_demoinfo_existing_editor_to_demo/', DemoinfoAddExistingEditorToDemoView.as_view(), name="ipol.cp.demoinfo.add_existing_editor_to_demo"),
    url(r'^ajax_add_demoinfo_new_editor_to_demo/', DemoinfoAddNewEditorToDemoView.as_view(), name="ipol.cp.demoinfo.add_new_editor_to_demo"),
	#deletes editor from demo, but does not delete the editor itself
    url(r'^ajax_delete_demoinfo_editor_from_demo/(?P<demo_id>\d+)/(?P<editor_id>\d+)/$', DemoinfoDeleteEditorFromDemoView.as_view(), name="ipol.cp.demoinfo.delete_editor_from_demo"),



	###################
    # Archive module  #
	###################

	# Menu option Archive Module:
    #todo, carefull, a demo can have negative id WTF!
	#todo list_demos should be nicer
	#todo archive shoud use pagination, it doesnt now

    url(r'^archive_module/', ArchiveDemosView.as_view(), name="ipol.cp.archive.demos"),
    url(r'^archive_demo/(?P<id>[\-\d\w]+)/$', ArchivePageView.as_view(), name="ipol.cp.archive.page"),
  	#ajax calls
    url(r'^ajax_shutdown/', ArchiveShutdownView.as_view(), name="ipol.cp.archive.shutdown"),
    url(r'^ajax_add_exp_to_test_demo/', ArchiveAddExpToTestDemoView.as_view(), name="ipol.cp.archive.add_exp_to_test_demo"),
    url(r'^ajax_delete_archive_demo/(?P<demo_id>[\-\d\w]+)/$', ArchiveDeleteDemoView.as_view(), name="ipol.cp.archive.delete_demo"),
    url(r'^ajax_delete_experiment/(?P<experiment_id>\d+)/$',
        ArchiveDeleteExperimentView.as_view(), name="ipol.cp.archive.delete_experiment"),
    url(r'^ajax_delete_experiment_file/(?P<file_id>\d+)/$',
        ArchiveDeleteExperimentFileView.as_view(), name="ipol.cp.archive.delete_experiment_file"),



	###################
    # Blobs module    #
	###################
	#todo not much done here
    url(r'^blobs_module/', BlobsDemosView.as_view(), name="ipol.cp.blobs.demos"),

	###################
    # Proxy module    #
	###################

	#####################
    # DemoRunner module #
	#####################

	##########################
    # Demo Dispatcher module #
	##########################

    # Demo (we will not be using this probably, but just in case, its the old code)


	###################
    # Docs            #
	###################
    #todo, documentacion en la app! el pdf del latex al principio...



    #media
    #(r'^media/(?P<path>.*)$', 'django.views.static.serve',{'document_root': settings.MEDIA_ROOT, 'show_indexes': True}),
    #admin
    #url(r'^admin/', include(admin.site.urls)),
]

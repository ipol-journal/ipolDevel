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
	DemoinfoAddNewAuthorToDemoView

__author__ = 'josearrecio'


urlpatterns = [



    # Common integrated view (mixes stuff from different modules and presents it toghetrer)
    url(r'^status/', StatusView.as_view(), name="ipol.cp.status"),
    url(r'^demos/', DemosView.as_view(), name="ipol.cp.demos"),

	###################
    # Demoinfo module #
	###################

	# Demo list: pagina con tres pestanas, y me carga la primera llamando a demos
    # cada pestana pone acomo activa al ser seleccionada y se trae los datos del demoinfo
	# cada pestana tiene su vista y se trae los datos del demoinfo, aplica filtos y paginacion
	# cada pestana tiene su busqueda ajax=jquery y paginacion, es ecir, se llama a la vista con post por el form de busqueda
	# y se devuelven los datos filtrados,

	# DEMOS

	# Demo list
    url(r'^demoinfo_demos/', DemoinfoDemosView.as_view(), name="ipol.cp.demoinfo.demos"),
    # Delete demo (ajax jq call)
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

	#falta
	# lista de autores de una demo, ahora uso author_list
	#lista de autores q no son de la demo, para el form, nuevo ws!
	#borrar autor de demo, sin borrarlo de autores
    url(r'^ajax_delete_demoinfo_author_from_demo/(?P<author_id>\d+)/$', DemoinfoDeleteAuthorFromDemoView.as_view(), name="ipol.cp.demoinfo.delete_author_from_demo"),


	#EDITORS

    # Editor list
    url(r'^demoinfo_editors/', DemoinfoEditorsView.as_view(), name="ipol.cp.demoinfo.editors"),
	# Manage Demo's Editors add/remove/get

	###################
    # Archive module  #
	###################

    url(r'^archive_module/', ArchiveDemosView.as_view(), name="ipol.cp.archive.demos"),
    url(r'^demo_result_page/(?P<id>[\-\d\w]+)/$', ArchivePageView.as_view(), name="ipol.cp.archive.page"),
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


    #test
    #url(r'^test/', Test1.as_view(), name="photogallery.test"),
    #url(r'^test2/', Test2.as_view(), name="photogallery.test2"),



    #media
    #(r'^media/(?P<path>.*)$', 'django.views.static.serve',{'document_root': settings.MEDIA_ROOT, 'show_indexes': True}),
    #admin
    #url(r'^admin/', include(admin.site.urls)),
]

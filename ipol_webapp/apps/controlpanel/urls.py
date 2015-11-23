from django.conf.urls import patterns, url
from apps.controlpanel.views.Status import StatusView, ShutdownView
from apps.controlpanel.views.demo import  PageView, DemosView, DeleteExperimentView, AddExpToTestDemoView, \
    DeleteExperimentFileView, BlobsDemosView, ArchiveDemosView

__author__ = 'josearrecio'


urlpatterns = patterns('',



    # Comon integrated view

    url(r'^status/', StatusView.as_view(), name="ipol.cp.status"),
    url(r'^demos/', DemosView.as_view(), name="ipol.cp.demos"),

    # Archive module

    url(r'^archive_module/', ArchiveDemosView.as_view(), name="ipol.cp.archive.demos"),
    url(r'^demo_result_page/(?P<id>[\-\d\w]+)/$', PageView.as_view(), name="ipol.cp.archive.page"),
  	#ajax calls
    url(r'^ajax_shutdown/', ShutdownView.as_view(), name="ipol.cp.archive.shutdown"),
    url(r'^ajax_delete_experiment/(?P<experiment_id>\d+)/$',
        DeleteExperimentView.as_view(), name="ipol.cp.archive.delete_experiment"),
    url(r'^ajax_delete_experiment_file/(?P<file_id>\d+)/$',
        DeleteExperimentFileView.as_view(), name="ipol.cp.archive.delete_experiment_file"),
    url(r'^ajax_add_exp_to_test_demo/', AddExpToTestDemoView.as_view(), name="ipol.cp.archive.add_exp_to_test_demo"),


    # Blobs module

    url(r'^blobs_module/', BlobsDemosView.as_view(), name="ipol.cp.blobs.demos"),


    # Docs


    #test
    #url(r'^test/', Test1.as_view(), name="photogallery.test"),
    #url(r'^test2/', Test2.as_view(), name="photogallery.test2"),



    #media
    #(r'^media/(?P<path>.*)$', 'django.views.static.serve',{'document_root': settings.MEDIA_ROOT, 'show_indexes': True}),
    #admin
    #url(r'^admin/', include(admin.site.urls)),
)

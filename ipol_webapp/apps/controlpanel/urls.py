from django.conf.urls import patterns, url
from apps.controlpanel.views.Status import StatusView, ArchiveShutdownView
from apps.controlpanel.views.demo import  PageView, DemosView, ArchiveDeleteExperimentView, ArchiveAddExpToTestDemoView, \
    ArchiveDeleteExperimentFileView, BlobsDemosView, ArchiveDemosView, ArchiveDeleteDemoView

__author__ = 'josearrecio'


urlpatterns = patterns('',



    # Comon integrated view

    url(r'^status/', StatusView.as_view(), name="ipol.cp.status"),
    url(r'^demos/', DemosView.as_view(), name="ipol.cp.demos"),

    # Archive module

    url(r'^archive_module/', ArchiveDemosView.as_view(), name="ipol.cp.archive.demos"),
    url(r'^demo_result_page/(?P<id>[\-\d\w]+)/$', PageView.as_view(), name="ipol.cp.archive.page"),
  	#ajax calls
    url(r'^ajax_shutdown/', ArchiveShutdownView.as_view(), name="ipol.cp.archive.shutdown"),
    url(r'^ajax_add_exp_to_test_demo/', ArchiveAddExpToTestDemoView.as_view(), name="ipol.cp.archive.add_exp_to_test_demo"),
    url(r'^ajax_delete_demo/(?P<demo_id>[\-\d\w]+)/$', ArchiveDeleteDemoView.as_view(), name="ipol.cp.archive.delete_demo"),
    url(r'^ajax_delete_experiment/(?P<experiment_id>\d+)/$',
        ArchiveDeleteExperimentView.as_view(), name="ipol.cp.archive.delete_experiment"),
    url(r'^ajax_delete_experiment_file/(?P<file_id>\d+)/$',
        ArchiveDeleteExperimentFileView.as_view(), name="ipol.cp.archive.delete_experiment_file"),

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

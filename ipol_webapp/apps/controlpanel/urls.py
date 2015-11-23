from django.conf.urls import patterns, url
from apps.controlpanel.views.Status import StatusView, ShutdownView
from apps.controlpanel.views.demo import PageView1, PageView, DemosView, DeleteExperimentView, AddExpToTestDemoView

__author__ = 'josearrecio'


urlpatterns = patterns('',

    #test
    #url(r'^test/', Test1.as_view(), name="photogallery.test"),
    #url(r'^test2/', Test2.as_view(), name="photogallery.test2"),

    # Galerias de fotos (no uso las de photologue, no me gustan)
    # home
    url(r'^status/', StatusView.as_view(), name="ipol.cp.status"),
    url(r'^demos/', DemosView.as_view(), name="ipol.cp.demos"),

    url(r'^demo_result_page/(?P<id>[\-\d\w]+)/$', PageView.as_view(), name="ipol.cp.result.page"),
    url(r'^demo_result_page/', PageView1.as_view(), name="ipol.cp.page"),

	#ajax calls
    url(r'^ajax_shutdown/', ShutdownView.as_view(), name="ipol.cp.archive.shutdown"),
    url(r'^ajax_delete_experiment_web/(?P<experiment_id>\d+)/$',
        DeleteExperimentView.as_view(), name="ipol.cp.archive.delete_experiment_web"),

    url(r'^ajax_add_exp_to_test_demo/', AddExpToTestDemoView.as_view(), name="ipol.cp.archive.add_exp_to_test_demo"),


    #media
    #(r'^media/(?P<path>.*)$', 'django.views.static.serve',{'document_root': settings.MEDIA_ROOT, 'show_indexes': True}),
    #admin
    #url(r'^admin/', include(admin.site.urls)),
)

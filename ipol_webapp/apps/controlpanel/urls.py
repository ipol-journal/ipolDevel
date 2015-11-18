from django.conf.urls import patterns, url
from apps.controlpanel.views.demo import PageView1, PageView, DemosView

__author__ = 'josearrecio'


urlpatterns = patterns('',

    #test
    #url(r'^test/', Test1.as_view(), name="photogallery.test"),
    #url(r'^test2/', Test2.as_view(), name="photogallery.test2"),

    # Galerias de fotos (no uso las de photologue, no me gustan)
    # home
    url(r'^demos/', DemosView.as_view(), name="ipol.cp.demos"),

    url(r'^demo_result_page/(?P<id>[\-\d\w]+)/$', PageView.as_view(), name="ipol.cp.result.page"),
    url(r'^demo_result_page/', PageView1.as_view(), name="ipol.cp.page"),

    #media
    #(r'^media/(?P<path>.*)$', 'django.views.static.serve',{'document_root': settings.MEDIA_ROOT, 'show_indexes': True}),
    #admin
    #url(r'^admin/', include(admin.site.urls)),
)

from django.conf.urls import patterns, url
from apps.controlpanel.views.page import PageView

__author__ = 'josearrecio'


urlpatterns = patterns('',

    #test
    #url(r'^test/', Test1.as_view(), name="photogallery.test"),
    #url(r'^test2/', Test2.as_view(), name="photogallery.test2"),

    # Galerias de fotos (no uso las de photologue, no me gustan)
    # home
    url(r'^page/', PageView.as_view(), name="cp.page"),


    #media
    #(r'^media/(?P<path>.*)$', 'django.views.static.serve',{'document_root': settings.MEDIA_ROOT, 'show_indexes': True}),
    #admin
    #url(r'^admin/', include(admin.site.urls)),
)

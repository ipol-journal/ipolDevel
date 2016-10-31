"""ipol_webapp URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/1.8/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  url(r'^$', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  url(r'^$', Home.as_view(), name='home')
Including another URLconf
    1. Add an import:  from blog import urls as blog_urls
    2. Add a URL to urlpatterns:  url(r'^blog/', include(blog_urls))
"""


from django.conf.urls import include, url
from django.contrib import admin
from django.views.generic import RedirectView
from django.core.urlresolvers import reverse_lazy
from ipol_webapp.settings import ALLAUTH_GESTS

urlpatterns = [


    # home
	# url(r'^$',  Home.as_view(),name="ipol.home"),
	url(r'^cp/$',  RedirectView.as_view(url=reverse_lazy('account_login'),permanent=True),name="ipol.home"),

	# control panel app
	url(r'^cp/', include('apps.controlpanel.urls')),
	#url(r'^cp/', urls),

	# media  No media is stored in this app!
	#(r'^media/(?P<path>.*)$', 'django.views.static.serve',{'document_root': settings.MEDIA_ROOT, 'show_indexes': True}),

	# admin
	url(r'^cp/admin/', include(admin.site.urls)),

	#autocomplete_light
	#http://django-autocomplete-light.readthedocs.org/en/master/
	#http://django-autocomplete-light.readthedocs.org/en/master/autocomplete.html?highlight=shortcuts#examples
	#http://django-autocomplete-light.readthedocs.org/en/master/tutorial.html
	url(r'^autocomplete/', include('autocomplete_light.urls')),

]

# extender allauthviews con mi mixin para navbar,
# if ALLAUTH_GESTS:   #if DEBUG is True it will be served automatically
	# #ojo q la url debe ser la definida en settings.STATIC_URL

	# urlpatterns += patterns('',
     #    #deben estar antes del import de urls de allauth! sino se usarian esas urls.
	# 	url(r'^accounts/', include('vendor.allauth.urls')),
	# 	#No se necesario si no uso socialauth (no olvidar migs!)
	# 	#url(r'^accounts/', include('allauth.urls')),
	# )


	# urlpatterns_extra= [
     #    #deben estar antes del import de urls de allauth! sino se usarian esas urls.
	# 	url(r'^cp/', include('vendor.allauth.urls')),
	# 	#No se necesario si no uso socialauth (no olvidar migs!)
	# 	#url(r'^accounts/', include('allauth.urls')),
	# ]
	# urlpatterns =urlpatterns + urlpatterns_extra
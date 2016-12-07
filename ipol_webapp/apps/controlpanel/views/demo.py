from apps.controlpanel.mixings import NavbarReusableMixinMF

from django.contrib.auth.decorators import login_required
from django.utils.decorators import method_decorator
from django.views.generic import TemplateView
from django.http import HttpResponse
from apps.controlpanel.views.ipolwebservices.ipoldeserializers import DeserializePage, DeserializeDemoList, \
        DeserializeArchiveDemoList
from apps.controlpanel.views.ipolwebservices import ipolservices
import logging

logger = logging.getLogger(__name__)

__author__ = 'josearrecio'

#Utilities
# TODO NOT IMPLEMENTED YET, shoul be an integrated view of the system, now it just gets some blobs info and presents it
#VIEWS


class DemosView(NavbarReusableMixinMF,TemplateView):
        template_name = "demo_list.html"

        @method_decorator(login_required)
        def dispatch(self, *args, **kwargs):
                # para las pestanas

                self.request.session['menu'] = 'menu-demos'
                return super(DemosView, self).dispatch(*args, **kwargs)


        #http://reinout.vanrees.org/weblog/2014/05/19/context.html
        def result(self):
                result = None
                try:
                        #result = ipolservices.get_demo_list()
                        # se ordenan en el admin. order no es necesario


                        page_json = ipolservices.get_blobs_demo_list()
                        result = DeserializeDemoList(page_json)
                        #result = page_json


                except Exception as e:
                        msg="Error %s"%e
                        logger.error(msg)
                        print(msg)

                return result
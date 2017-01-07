from apps.controlpanel.mixings import NavbarReusableMixinMF

__author__ = 'josearrecio'

import logging
from django.views.generic import TemplateView
from apps.controlpanel.views.ipolwebservices import ipolservices
from apps.controlpanel.views.ipolwebservices.ipoldeserializers import DeserializeArchiveStatus, DeserializeDemoList, \
        DeserializeDemoinfoStatus, DeserializeProxyStatus
from ipol_webapp.settings import IPOL_SERVICES_MODULE_ACHIVE, IPOL_SERVICES_MODULE_BLOBS, IPOL_SERVICES_MODULE_DEMO, \
        IPOL_SERVICES_MODULE_DEMOINFO, IPOL_SERVICES_MODULE_PROXY
from django.contrib.auth.decorators import login_required
from django.utils.decorators import method_decorator
logger = logging.getLogger(__name__)



#View

class StatusView(NavbarReusableMixinMF,TemplateView):
    template_name = "stats.html"

    @method_decorator(login_required)
    def dispatch(self, *args, **kwargs):
        self.request.session['menu'] = 'menu-status'
        return super(StatusView, self).dispatch(*args, **kwargs)

    def get_proxy_module_stats(self):

        result = None
        try:
            # Demoinfo Stats
            proxy_stats_json = ipolservices.proxy_get_stats()
            result = DeserializeProxyStatus(proxy_stats_json)

            #print " get_proxy_module_stats result",result
            #result = page_json

        except Exception , e:
            msg="Error get_proxy_module_stats %s"%e
            print(msg)
            logger.error(msg)

        return result


    def get_demoinfo_module_stats(self):

        result = None
        try:
            # Demoinfo Stats
            demoinfo_stats_json = ipolservices.demoinfo_get_stats()
            result = DeserializeDemoinfoStatus(demoinfo_stats_json)
            #result = page_json

        except Exception , e:
            msg="Error get_demoinfo_module_stats %s"%e
            print(msg)
            logger.error(msg)

        return result


    def get_archive_module_stats(self):

        result = None
        try:
            # Archive Stats
            archive_stats_json = ipolservices.archive_get_stats()
            result = DeserializeArchiveStatus(archive_stats_json)
            #result = page_json

        except Exception , e:
            msg="Error get_archive_module_stats %s"%e
            print(msg)
            logger.error(msg)

        return result


    def get_blobs_module_stats(self):

        result = None
        try:

            blobs_demo_list_json = ipolservices.get_blobs_demo_list()
            result = DeserializeDemoList(blobs_demo_list_json)
            #result = blobs_json

        except Exception , e:
            msg="Error get_blobs_module_stats %s"%e
            print(msg)
            logger.error(msg)

        return result


    def get_demoinfo_machine(self):
        return IPOL_SERVICES_MODULE_DEMOINFO


    def get_archive_machine(self):
        return IPOL_SERVICES_MODULE_ACHIVE


    def get_blob_machine(self):
        return IPOL_SERVICES_MODULE_BLOBS


    def get_demo_machine(self):
        return IPOL_SERVICES_MODULE_DEMO


    def get_proxy_machine(self):
        return IPOL_SERVICES_MODULE_PROXY

    # def get_context_data(self, **kwargs):
    #         context = super(StatusView, self).get_context_data(**kwargs)
    #         self.request.session['menu'] = 'menu-status'
    #         return context

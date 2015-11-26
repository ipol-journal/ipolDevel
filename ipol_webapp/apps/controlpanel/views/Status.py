from apps.controlpanel.mixings import NavbarReusableMixinMF

__author__ = 'josearrecio'

import logging
from django.views.generic import TemplateView
from apps.controlpanel.views.ipolwebservices import ipolservices
from django.http import HttpResponse
from apps.controlpanel.views.ipolwebservices.ipoldeserializers import DeserializeStatus, DeserializeDemoList
from ipol_webapp.settings import IPOL_SERVICES_MODULE_ACHIVE, IPOL_SERVICES_MODULE_BLOBS, IPOL_SERVICES_MODULE_DEMO
from django.contrib.auth.decorators import login_required
from django.utils.decorators import method_decorator
logger = logging.getLogger(__name__)



#Utilities


#Views
class StatusView(NavbarReusableMixinMF,TemplateView):
	template_name = "stats.html"

	@method_decorator(login_required)
	def dispatch(self, *args, **kwargs):
		return super(StatusView, self).dispatch(*args, **kwargs)

	def get_archive_module_stats(self):

		result = None
		try:
			# Archive Stats
			archive_stats_json = ipolservices.archive_get_stats()
			result = DeserializeStatus(archive_stats_json)
			#result = page_json

		except Exception , e:
			msg="Error %s"%e
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
			msg="Error %s"%e
			print(msg)
			logger.error(msg)

		return result

	def get_archive_machine(self):
		return IPOL_SERVICES_MODULE_ACHIVE

	def get_blob_machine(self):
		return IPOL_SERVICES_MODULE_BLOBS

	def get_demo_machine(self):
		return IPOL_SERVICES_MODULE_DEMO

class ArchiveShutdownView(NavbarReusableMixinMF,TemplateView):

	@method_decorator(login_required)
	def dispatch(self, *args, **kwargs):
		return super(ArchiveShutdownView, self).dispatch(*args, **kwargs)

	def render_to_response(self, context, **response_kwargs):
		#just return the JSON from the ws, this json has no interesting data, no template is needed
		result= ipolservices.archive_shutdown()
		if result == None:
			msg="ShutdownView: Something went wrong using archive shutdown WS"
			logger.error(msg)
			raise ValueError(msg)


		return HttpResponse(result, content_type='application/json')




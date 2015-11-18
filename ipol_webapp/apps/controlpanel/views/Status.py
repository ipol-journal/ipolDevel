from apps.controlpanel.views.ipolwebservices.ipoldeserializers import DeserializeStatus
from ipol_webapp.settings import IPOL_SERVICES_MODULE_ACHIVE, IPOL_SERVICES_MODULE_BLOBS

__author__ = 'josearrecio'

import logging

from django.views.generic import TemplateView
from rest_framework import serializers
from django.utils.six import BytesIO
from rest_framework.parsers import JSONParser

from apps.controlpanel.views.ipolwebservices import ipolservices

logger = logging.getLogger(__name__)



#Utilities


#Views
class StatusView(TemplateView):
	# template_name = "photogallery/video.html"
	template_name = "stats.html"

	def dispatch(self, *args, **kwargs):
		return super(StatusView, self).dispatch(*args, **kwargs)


	#http://reinout.vanrees.org/weblog/2014/05/19/context.html
	def get_archive_module_stats(self):

		print("STATUS get_archive_module_stats")
		result =None
		try:
			# Archive Stats
			archive_json = ipolservices.get_stats()
			result = DeserializeStatus(archive_json)
			#result = page_json

		except Exception , e:
			msg="Error %s"%e
			print(msg)
			logger.error(msg)

		return result

	def get_blobs_module_stats(self):

		print("STATUS get_blobs_module_stats")

		result =None
		try:

			blobs_json = ipolservices.get_demo_list()
			#result = DeserializeDemoList(page_json)
			result = blobs_json

		except Exception , e:
			msg="Error %s"%e
			print(msg)
			logger.error(msg)

		return result

	#http://reinout.vanrees.org/weblog/2014/05/19/context.html
	def get_archive_machine(self):
		return IPOL_SERVICES_MODULE_ACHIVE
	def get_blob_machine(self):
		return IPOL_SERVICES_MODULE_BLOBS

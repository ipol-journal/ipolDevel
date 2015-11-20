from django.http import HttpResponse
from django.shortcuts import render_to_response
import simplejson
from apps.controlpanel.views.ipolwebservices.ipoldeserializers import DeserializeStatus, DeserializeDemoList
from ipol_webapp.settings import IPOL_SERVICES_MODULE_ACHIVE, IPOL_SERVICES_MODULE_BLOBS

__author__ = 'josearrecio'

import logging

from django.views.generic import TemplateView, View
from rest_framework import serializers
from django.utils.six import BytesIO
from rest_framework.parsers import JSONParser

from apps.controlpanel.views.ipolwebservices import ipolservices

logger = logging.getLogger(__name__)



#Utilities


#Views
class StatusView(TemplateView):
	template_name = "stats.html"

	def dispatch(self, *args, **kwargs):
		return super(StatusView, self).dispatch(*args, **kwargs)

	#http://reinout.vanrees.org/weblog/2014/05/19/context.html
	def get_archive_module_stats(self):

		print("STATUS get_archive_module_stats")
		result = None
		try:
			# Archive Stats
			archive_stats_json = ipolservices.get_stats()
			result = DeserializeStatus(archive_stats_json)
			#result = page_json

		except Exception , e:
			msg="Error %s"%e
			print(msg)
			logger.error(msg)

		return result

	def get_blobs_module_stats(self):

		print("STATUS get_blobs_module_stats")

		result = None
		try:

			blobs_demo_list_json = ipolservices.get_demo_list()
			result = DeserializeDemoList(blobs_demo_list_json)
			#result = blobs_json

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

#JAK todo add security, only loggede users
class ShutdownView(TemplateView):

	def render_to_response(self, context, **response_kwargs):
		#just return the JSON from the ws, this json has no interesting data, no template is needed
		result= ipolservices.archive_shutdown()
		if result == None:
			msg="ShutdownView: Something went wrong using archive shutdown WS"
			logger.error(msg)
			raise ValueError(msg)
		print result

		return HttpResponse(result, content_type='application/json')




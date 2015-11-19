from apps.controlpanel.views.ipolwebservices.ipoldeserializers import DeserializePage, DeserializeDemoList


__author__ = 'josearrecio'

from datetime import datetime
import logging

from django.shortcuts import render
from django.views.generic import TemplateView
from rest_framework import serializers
from django.utils.six import BytesIO
from rest_framework.parsers import JSONParser

from apps.controlpanel.views.ipolwebservices import ipolservices

logger = logging.getLogger(__name__)



#Utilities


#VIEWS


class PageView1(TemplateView):
	# template_name = "photogallery/video.html"
	template_name = "demo_test_result_page.html"

	def dispatch(self, *args, **kwargs):
		# para las pestanas
		#self.request.session['menu'] = 'menu-'
		return super(PageView1, self).dispatch(*args, **kwargs)


	#http://reinout.vanrees.org/weblog/2014/05/19/context.html
	def result(self):
		result =None
		try:
			result = ipolservices.get_page(-1,1)
			# se ordenan en el admin. order no es necesario
			print("result1")
			print(result)
		except Exception as e:
			print(e)
		return result

class PageView(TemplateView):
	# template_name = "photogallery/video.html"
	template_name = "demo_result_page.html"

	def dispatch(self, *args, **kwargs):
		return super(PageView, self).dispatch(*args, **kwargs)


	#http://reinout.vanrees.org/weblog/2014/05/19/context.html
	def result(self):
		id = self.kwargs['id']
		#todo validate id, debe ser un numero
		#print(id)

		result =None
		try:
			print(" demo_id: %d"%int(id))

			#obtengo el jsonpara la pagina 1
			page_json = ipolservices.get_page(int(id),1)

			result = DeserializePage(page_json)


		except Exception , e:
			msg="Error %s"%e
			logger.error(msg)

		return result

class DemosView(TemplateView):
	template_name = "demo_list.html"

	def dispatch(self, *args, **kwargs):
		# para las pestanas
		#self.request.session['menu'] = 'menu-'
		return super(DemosView, self).dispatch(*args, **kwargs)


	#http://reinout.vanrees.org/weblog/2014/05/19/context.html
	def result(self):
		result =None
		try:
			#result = ipolservices.get_demo_list()
			# se ordenan en el admin. order no es necesario


			page_json = ipolservices.get_demo_list()
			result = DeserializeDemoList(page_json)
			#result = page_json


		except Exception as e:
			print(e)
		return result







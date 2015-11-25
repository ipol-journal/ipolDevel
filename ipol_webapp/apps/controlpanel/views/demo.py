__author__ = 'josearrecio'

from django.views.generic import TemplateView
from django.http import HttpResponse
from apps.controlpanel.views.ipolwebservices.ipoldeserializers import DeserializePage, DeserializeDemoList, \
	DeserializeArchiveDemoList
from apps.controlpanel.views.ipolwebservices import ipolservices
import logging

logger = logging.getLogger(__name__)


#Utilities

#VIEWS

#JAK todo add security, only loggede users

class PageView(TemplateView):
	# template_name = "photogallery/video.html"
	template_name = "demo_result_page.html"

	def dispatch(self, *args, **kwargs):
		return super(PageView, self).dispatch(*args, **kwargs)


	#http://reinout.vanrees.org/weblog/2014/05/19/context.html
	def result(self):
		demo_id = self.kwargs['id']
		#todo validate id, debe ser un numero?
		#print(id)

		result =None
		try:
			print(" demo_id: %d"%int(demo_id))

			page_json = ipolservices.archive_get_page(int(demo_id),1)
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

class BlobsDemosView(TemplateView):
	template_name = "blobs.html"

	def dispatch(self, *args, **kwargs):
		# para las pestanas
		#self.request.session['menu'] = 'menu-'
		return super(BlobsDemosView, self).dispatch(*args, **kwargs)


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

class ArchiveDemosView(TemplateView):
	template_name = "archive.html"

	def dispatch(self, *args, **kwargs):
		# para las pestanas
		#self.request.session['menu'] = 'menu-'
		return super(ArchiveDemosView, self).dispatch(*args, **kwargs)

	def list_demos(self):
		result = None
		try:
			page_json = ipolservices.archive_demo_list()
			result = DeserializeArchiveDemoList(page_json)

		except Exception as e:
			msg="Error %s"%e
			logger.error(msg)
			print(msg)

		return result

class ArchiveDeleteExperimentView(TemplateView):

	def render_to_response(self, context, **response_kwargs):
		#just return the JSON from the ws, this json has no interesting data, no template is needed

		try:
			experiment_id = int(self.kwargs['experiment_id'])
		except ValueError:
			msg= "Id is not an integer"
			logger.error(msg)
			raise ValueError(msg)

		result= ipolservices.archive_delete_experiment(experiment_id)
		if result == None:
			msg="DeleteExperimentView: Something went wrong using archive WS"
			logger.error(msg)
			raise ValueError(msg)


		return HttpResponse(result, content_type='application/json')

class ArchiveDeleteDemoView(TemplateView):

	def render_to_response(self, context, **response_kwargs):
		#just return the JSON from the ws, no template is needed

		try:
			demo_id = int(self.kwargs['demo_id'])
		except ValueError:
			msg= "Id is not an integer"
			logger.error(msg)
			raise ValueError(msg)

		result= ipolservices.archive_delete_demo(demo_id)
		if result == None:
			msg="ArchiveDeleteDemoView: Something went wrong using archive WS"
			logger.error(msg)
			raise ValueError(msg)


		return HttpResponse(result, content_type='application/json')

class ArchiveDeleteExperimentFileView(TemplateView):

	def render_to_response(self, context, **response_kwargs):
		#just return the JSON from the ws, no template is needed

		try:
			demo_id = int(self.kwargs['file_id'])
		except ValueError:
			msg= "Id is not an integer"
			logger.error(msg)
			raise ValueError(msg)

		result= ipolservices.archive_delete_file(demo_id)
		if result == None:
			msg="DeleteFileView: Something went wrong using archive WS"
			logger.error(msg)
			raise ValueError(msg)


		return HttpResponse(result, content_type='application/json')

class ArchiveAddExpToTestDemoView(TemplateView):

	def render_to_response(self, context, **response_kwargs):
		#just return the JSON from the ws, no template is needed

		result= ipolservices.archive_add_experiment_to_test_demo()
		if result == None:
			msg="AddExpToTestDemoView: Something went wrong using archive WS"
			logger.error(msg)
			raise ValueError(msg)

		return HttpResponse(result, content_type='application/json')


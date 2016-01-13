import json
from apps.controlpanel.mixings import NavbarReusableMixinMF

from django.contrib.auth.decorators import login_required
from django.utils.decorators import method_decorator
from django.views.generic import TemplateView
from django.http import HttpResponse
from apps.controlpanel.views.ipolwebservices.ipoldeserializers import DeserializeArchiveDemoList, DeserializePage, \
	DeserializeDemoList, DeserializeDemoinfoDemoList
from apps.controlpanel.views.ipolwebservices import ipolservices
import logging

logger = logging.getLogger(__name__)

__author__ = 'josearrecio'

#todo remove, this is used in terminal app
class ArchiveShutdownView(NavbarReusableMixinMF,TemplateView):

	@method_decorator(login_required)
	def dispatch(self, *args, **kwargs):
		return super(ArchiveShutdownView, self).dispatch(*args, **kwargs)

	def render_to_response(self, context, **response_kwargs):
		#just return the JSON from the ws, this json has no interesting data, no template is needed
		result= ipolservices.archive_shutdown()
		if result is None:
			msg="ShutdownView: Something went wrong using archive shutdown WS"
			logger.error(msg)
			raise ValueError(msg)


		return HttpResponse(result, content_type='application/json')


class ArchiveDemosView(NavbarReusableMixinMF,TemplateView):

	@method_decorator(login_required)
	def dispatch(self, *args, **kwargs):
		return super(ArchiveDemosView, self).dispatch(*args, **kwargs)

	template_name = "archive.html"

	def dispatch(self, *args, **kwargs):
		# para las pestanas
		#self.request.session['menu'] = 'menu-'
		return super(ArchiveDemosView, self).dispatch(*args, **kwargs)

	def list_demos(self):
		result = None
		result2 = None
		#for special demo with id= -1 for testing in archive
		archivetestdemo=False
		try:
			#get demos from archive module
			page_json = ipolservices.archive_demo_list()
			result = DeserializeArchiveDemoList(page_json)

			#get demo info for those demos from demoinfo module
			if result:
				idlist=list()

				for d in result.demo_list:
					demoid= d.demo_id
					#special case demo -1 in archive, this Id will not exist in demoinfo module
					if demoid > 0 and isinstance( demoid, ( int, long ) ):
						idlist.append(demoid)
					else:
						archivetestdemo = True
				result2json = ipolservices.demoinfo_demo_list_by_demoeditorid(idlist)
				if result2json:
					result2 = DeserializeDemoinfoDemoList(result2json)
				else:
					# I expect a dict for template
					result2 = {"status": "KO","error": "No demos in archive"}


			print "result2",result2


		except Exception as e:
			msg="Error %s"%e
			logger.error(msg)
			print(msg)

		return result2,archivetestdemo




class ArchiveDeleteExperimentView(NavbarReusableMixinMF,TemplateView):

	@method_decorator(login_required)
	def dispatch(self, *args, **kwargs):
		return super(ArchiveDeleteExperimentView, self).dispatch(*args, **kwargs)

	def render_to_response(self, context, **response_kwargs):
		#just return the JSON from the ws, this json has no interesting data, no template is needed

		try:
			experiment_id = int(self.kwargs['experiment_id'])
		except ValueError:
			msg= "Id is not an integer"
			logger.error(msg)
			raise ValueError(msg)

		result= ipolservices.archive_delete_experiment(experiment_id)
		if result is None:
			msg="DeleteExperimentView: Something went wrong using archive WS"
			logger.error(msg)
			raise ValueError(msg)


		return HttpResponse(result, content_type='application/json')


class ArchiveDeleteDemoView(NavbarReusableMixinMF,TemplateView):

	@method_decorator(login_required)
	def dispatch(self, *args, **kwargs):
		return super(ArchiveDeleteDemoView, self).dispatch(*args, **kwargs)

	def render_to_response(self, context, **response_kwargs):
		#just return the JSON from the ws, no template is needed

		try:
			demo_id = int(self.kwargs['demo_id'])
		except ValueError:
			msg= "Id is not an integer"
			logger.error(msg)
			raise ValueError(msg)

		result= ipolservices.archive_delete_demo(demo_id)
		if result is None:
			msg="ArchiveDeleteDemoView: Something went wrong using archive WS"
			logger.error(msg)
			raise ValueError(msg)


		return HttpResponse(result, content_type='application/json')


class ArchiveDeleteExperimentFileView(NavbarReusableMixinMF,TemplateView):

	@method_decorator(login_required)
	def dispatch(self, *args, **kwargs):
		return super(ArchiveDeleteExperimentFileView, self).dispatch(*args, **kwargs)

	def render_to_response(self, context, **response_kwargs):
		#just return the JSON from the ws, no template is needed

		try:
			demo_id = int(self.kwargs['file_id'])
		except ValueError:
			msg= "Id is not an integer"
			logger.error(msg)
			raise ValueError(msg)

		result= ipolservices.archive_delete_file(demo_id)
		if result is None:
			msg="DeleteFileView: Something went wrong using archive WS"
			logger.error(msg)
			raise ValueError(msg)


		return HttpResponse(result, content_type='application/json')


class ArchiveAddExpToTestDemoView(NavbarReusableMixinMF,TemplateView):

	@method_decorator(login_required)
	def dispatch(self, *args, **kwargs):
		return super(ArchiveAddExpToTestDemoView, self).dispatch(*args, **kwargs)

	def render_to_response(self, context, **response_kwargs):
		#just return the JSON from the ws, no template is needed

		result= ipolservices.archive_add_experiment_to_test_demo()
		if result is None:
			msg="AddExpToTestDemoView: Something went wrong using archive WS"
			logger.error(msg)
			raise ValueError(msg)

		return HttpResponse(result, content_type='application/json')


class ArchivePageView(NavbarReusableMixinMF,TemplateView):
	template_name = "demo_result_page.html"

	@method_decorator(login_required)
	def dispatch(self, *args, **kwargs):
		return super(ArchivePageView, self).dispatch(*args, **kwargs)


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





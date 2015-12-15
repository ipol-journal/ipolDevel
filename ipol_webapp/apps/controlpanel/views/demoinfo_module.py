from django.core.paginator import Paginator, PageNotAnInteger, EmptyPage
from django.http import HttpResponse
from apps.controlpanel.mixings import NavbarReusableMixinMF

from django.contrib.auth.decorators import login_required
from django.utils.decorators import method_decorator
from django.views.generic import TemplateView
from apps.controlpanel.views.ipolwebservices.ipoldeserializers import DeserializeArchiveDemoList, \
	DeserializeDemoinfoDemoList
from apps.controlpanel.views.ipolwebservices import ipolservices
import logging

logger = logging.getLogger(__name__)

__author__ = 'josearrecio'


PAGINATION_ITEMS_PER_PAGE=2

class DemoinfoDemosView(NavbarReusableMixinMF,TemplateView):
	template_name = "demoinfo/demoinfo_demos.html"


	@method_decorator(login_required)
	def dispatch(self, *args, **kwargs):
		# para las pestanas
		self.request.session['topmenu'] = 'topmenu-demoinfo-demos'
		return super(DemoinfoDemosView, self).dispatch(*args, **kwargs)



	def get_context_data(self, **kwargs):

		#get context
		context = super(DemoinfoDemosView, self).get_context_data(**kwargs)

		try:
			#get data from WS
			page_json = ipolservices.demoinfo_demo_list()
			result = DeserializeDemoinfoDemoList(page_json)

			list_demos= result.demo_list
			status = result.status


			print "list_demos", list_demos

			#filter result
			query = self.request.GET.get('q')
			print "query",query
			list_demos_filtered = list()
			if query:
				for demo in list_demos:
					print "demo: ",demo
					print "demo: ",str(demo)
					if query in demo.title or query in demo.abstract :
						print "ok"
						list_demos_filtered.append(demo)

				list_demos=list_demos_filtered
			context['q'] = query



			#pagination of result
			paginator = Paginator(list_demos, PAGINATION_ITEMS_PER_PAGE)
			page = self.request.GET.get('page')
			try:
				list_demos = paginator.page(page)
			except PageNotAnInteger:
				# If page is not an integer, deliver first page.
				list_demos = paginator.page(1)
			except EmptyPage:
				# If page is out of range (e.g. 9999), deliver last page of results.
				list_demos = paginator.page(paginator.num_pages)

			#send context vars for template
			context['status'] = status
			context['list_demos'] = list_demos

		except Exception as e:
			msg=" DemoinfoDemosView Error %s "%e
			logger.error(msg)
			print(msg)



		return context


	# def list_demos(self, request):
	# 	result = None
	#
	# 	print "list_demos"
	# 	try:
	# 		page_json = ipolservices.demoinfo_demo_list()
	# 		result = DeserializeDemoinfoDemoList(page_json)
	#
	# 	except Exception as e:
	# 		msg=" DemoinfoDemosView Error %s "%e
	# 		logger.error(msg)
	# 		print(msg)
	#
	#
	# 	#pagination
	# 	paginator = Paginator(result, PAGINATION_ITEMS_PER_PAGE)
	# 	page = request.GET.get('page')
	# 	try:
	# 		result = paginator.page(page)
	# 	except PageNotAnInteger:
	# 		# If page is not an integer, deliver first page.
	# 		result = paginator.page(1)
	# 	except EmptyPage:
	# 		# If page is out of range (e.g. 9999), deliver last page of results.
	# 		result = paginator.page(paginator.num_pages)
	# 	return result


class DemoinfoDeleteDemoView(NavbarReusableMixinMF,TemplateView):

	@method_decorator(login_required)
	def dispatch(self, *args, **kwargs):
		return super(DemoinfoDeleteDemoView, self).dispatch(*args, **kwargs)

	def post(self, request, *args, **kwargs):
			context = super(DemoinfoDeleteDemoView, self).get_context_data(**kwargs)
			#todo could validate a form to get hard_delete checkbox from user
			try:
				demo_id = int(self.kwargs['demo_id'])
			except ValueError:
				msg= "Id is not an integer"
				logger.error(msg)
				raise ValueError(msg)

			result= ipolservices.demoinfo_delete_demo(demo_id,hard_delete = False)
			if result == None:
				msg="DemoinfoDeleteDemoView: Something went wrong using demoinfo WS"
				logger.error(msg)
				raise ValueError(msg)

			print result

			return HttpResponse(result, content_type='application/json')


class DemoinfoGetDDLView(NavbarReusableMixinMF,TemplateView):

	@method_decorator(login_required)
	def dispatch(self, *args, **kwargs):
		return super(DemoinfoGetDDLView, self).dispatch(*args, **kwargs)

	def post(self, request, *args, **kwargs):
			context = super(DemoinfoGetDDLView, self).get_context_data(**kwargs)
			#todo could validate a form to get hard_delete checkbox from user
			try:
				demo_id = int(self.kwargs['demo_id'])
			except ValueError:
				msg= "Id is not an integer"
				logger.error(msg)
				raise ValueError(msg)

			result= ipolservices.demoinfo_delete_demo(demo_id,hard_delete = False)
			if result == None:
				msg="DemoinfoDeleteDemoView: Something went wrong using demoinfo WS"
				logger.error(msg)
				raise ValueError(msg)

			print result

			return HttpResponse(result, content_type='application/json')




class DemoinfoAuthorsView(NavbarReusableMixinMF,TemplateView):
	template_name = "demoinfo/demoinfo_authors.html"


	@method_decorator(login_required)
	def dispatch(self, *args, **kwargs):
		# para las pestanas
		self.request.session['topmenu'] = 'topmenu-demoinfo-authors'
		return super(DemoinfoAuthorsView, self).dispatch(*args, **kwargs)

	def list_authors(self):
		result = None
		print "list_demos"
		try:
			page_json = ipolservices.demoinfo_author_list()
			result = DeserializeDemoinfoDemoList(page_json)

		except Exception as e:
			msg=" DemoinfoDemosView Error %s "%e
			logger.error(msg)
			print(msg)

		return result

class DemoinfoEditorsView(NavbarReusableMixinMF,TemplateView):
	template_name = "demoinfo/demoinfo_editors.html"


	@method_decorator(login_required)
	def dispatch(self, *args, **kwargs):
		# para las pestanas
		self.request.session['topmenu'] = 'topmenu-demoinfo-editors'
		return super(DemoinfoEditorsView, self).dispatch(*args, **kwargs)

	def list_editors(self):
		result = None
		print "list_demos"
		try:
			page_json = ipolservices.demoinfo_demo_list()
			result = DeserializeDemoinfoDemoList(page_json)

		except Exception as e:
			msg=" DemoinfoDemosView Error %s "%e
			logger.error(msg)
			print(msg)

		return result
__author__ = 'josearrecio'

from django.shortcuts import render
from django.views.generic import TemplateView, DetailView
import services
import simplejson


class PageView2(TemplateView):
	template_name = "demo_result_page.html"

	def get(self,request):
		r = services.get_page(1,1)
		return render(request, 'demo_result_page.html',r)



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
			result = services.get_page(-1,1)
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
		print(id)


		result =None
		try:
			print("id: %d"%int(id))
			result = services.get_page(int(id),1)
			# se ordenan en el admin. order no es necesario
			print("result")
			print(result)
		except Exception as e:
			print(e)
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
			result = services.get_demo_list()
			# se ordenan en el admin. order no es necesario

		except Exception as e:
			print(e)
		return result


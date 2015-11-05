__author__ = 'josearrecio'
from django.shortcuts import render
from django.views.generic import TemplateView
import services



class PageView2(TemplateView):
	template_name = "demo_page.html"

	def get(self,request):
		r = services.get_page(1,1)
		return render(request,'demo_page.html',r)



class PageView(TemplateView):
	# template_name = "photogallery/video.html"
	template_name = "demo_page.html"

	def dispatch(self, *args, **kwargs):
		# para las pestanas
		#self.request.session['menu'] = 'menu-'
		return super(PageView, self).dispatch(*args, **kwargs)


	#http://reinout.vanrees.org/weblog/2014/05/19/context.html
	def result(self):
		result =None
		try:
			result = services.get_page(1,1)
			# se ordenan en el admin. order no es necesario
			print("result")
			print(result)
		except Exception as e:
			print(e)
		return result
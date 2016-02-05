from django.contrib.auth.decorators import login_required
from django.utils.decorators import method_decorator
from django.views.generic import TemplateView
from apps.controlpanel.mixings import NavbarReusableMixinMF

__author__ = 'josearrecio'

# TODO TEST HelloWorld simple view example

class Home(NavbarReusableMixinMF,TemplateView):
	template_name = "home.html"

	@method_decorator(login_required)
	def dispatch(self, *args, **kwargs):
		return super(Home, self).dispatch(*args, **kwargs)

	def get_context_data(self, **kwargs):
		# Call the base Test first to get a context
		context = super(Home, self).get_context_data(**kwargs)

		context['myvar'] = ['hello','world']

		return context


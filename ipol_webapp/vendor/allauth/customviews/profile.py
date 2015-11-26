from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.views.generic import TemplateView
from apps.controlpanel.mixings import NavbarReusableMixinMF

__author__ = 'josearrecio'




class ProfileView(NavbarReusableMixinMF,TemplateView):
	#ojo, lo encontrara en vendor pq este esta en templates dir en el settings.
	template_name = "account/profile.html"

	def dispatch(self, *args, **kwargs):
		return super(ProfileView, self).dispatch(*args, **kwargs)

	def get_context_data(self, **kwargs):
		# Call the base Test first to get a context
		context = super(ProfileView, self).get_context_data(**kwargs)
		#para las pestanas
		self.request.session['menu'] = 'menu-private-profile'

		return context
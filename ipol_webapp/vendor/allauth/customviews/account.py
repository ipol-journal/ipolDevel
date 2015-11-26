from allauth.account.views import LoginView, SignupView, LogoutView, PasswordChangeView, PasswordSetView, \
	AccountInactiveView, EmailView, EmailVerificationSentView, ConfirmEmailView, PasswordResetView, \
	PasswordResetDoneView, PasswordResetFromKeyView, PasswordResetFromKeyDoneView
from apps.controlpanel.mixings import NavbarReusableMixinMF

__author__ = 'josearrecio'

# Necesitaba pasar el mixin a unas clases definidas en allauth

class MyLoginView(NavbarReusableMixinMF,LoginView):
	def get_context_data(self, **kwargs):
		context = super(MyLoginView, self).get_context_data(**kwargs)
		self.request.session['menu'] = 'menu-login'
		return context


class MyLogoutView(NavbarReusableMixinMF,LogoutView):
	def get_context_data(self, **kwargs):
		context = super(MyLogoutView, self).get_context_data(**kwargs)
		self.request.session['menu'] = 'menu-private-logout'
		return context

class MySignupView(NavbarReusableMixinMF,SignupView):
	pass

class MyPasswordChangeView(NavbarReusableMixinMF,PasswordChangeView):
	pass

class MyPasswordSetView(NavbarReusableMixinMF,PasswordSetView):
	pass

class MyAccountInactiveView(NavbarReusableMixinMF,AccountInactiveView):
	pass

class MyEmailView(NavbarReusableMixinMF,EmailView):
	pass

class MyEmailVerificationSentView(NavbarReusableMixinMF,EmailVerificationSentView):
	pass

class MyConfirmEmailView(NavbarReusableMixinMF,ConfirmEmailView):
	pass

class MyPasswordResetView(NavbarReusableMixinMF,PasswordResetView):
	pass

class MyPasswordResetDoneView(NavbarReusableMixinMF,PasswordResetDoneView):
	pass

class MyPasswordResetFromKeyView(NavbarReusableMixinMF,PasswordResetFromKeyView):
	pass

class MyPasswordResetFromKeyDoneView(NavbarReusableMixinMF,PasswordResetFromKeyDoneView):
	pass


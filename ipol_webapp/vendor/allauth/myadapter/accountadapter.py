__author__ = 'josearrecio'
from allauth.account.adapter import DefaultAccountAdapter
from django.conf import settings
from django.shortcuts import resolve_url


class AccountAdapter(DefaultAccountAdapter):


	def get_login_redirect_url(self, request):

		assert request.user.is_authenticated()
		url = settings.LOGIN_REDIRECT_URL
		return resolve_url(url)
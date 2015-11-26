from vendor.allauth.customviews.profile import ProfileView

__author__ = 'josearrecio'
from django.conf.urls import patterns,  url
from django.contrib.auth.decorators import login_required
from vendor.allauth.customviews.account import MyLoginView, MySignupView, MyLogoutView, MyPasswordChangeView, \
	MyPasswordSetView, MyAccountInactiveView, MyEmailView, MyConfirmEmailView, MyPasswordResetView, \
	MyPasswordResetDoneView, MyPasswordResetFromKeyView, MyPasswordResetFromKeyDoneView, MyEmailVerificationSentView

urlpatterns = patterns('',
	#extender el login con mi mixin para navbar, deben estar antes del import de urls de allauth! sino se usarian esas urls.
	url(r'^login/$', MyLoginView.as_view(),name='account_login'),
	url(r"^signup/$", MySignupView.as_view(), name="account_signup"),
    url(r"^logout/$", MyLogoutView.as_view(), name="account_logout"),
    url(r"^password/change/$", login_required(MyPasswordChangeView.as_view()),name="account_change_password"),
    url(r"^password/set/$", login_required(MyPasswordSetView.as_view()), name="account_set_password"),
    url(r"^inactive/$", MyAccountInactiveView.as_view(), name="account_inactive"),
    # E-mail
    url(r"^email/$", MyEmailView.as_view(), name="account_email"),
    url(r"^confirm-email/$", MyEmailVerificationSentView.as_view(), name="account_email_verification_sent"),
    url(r"^confirm-email/(?P<key>\w+)/$", MyConfirmEmailView.as_view(), name="account_confirm_email"),
    # password reset
    url(r"^password/reset/$", MyPasswordResetView.as_view(), name="account_reset_password"),
    url(r"^password/reset/done/$", MyPasswordResetDoneView.as_view(), name="account_reset_password_done"),
    url(r"^password/reset/key/(?P<uidb36>[0-9A-Za-z]+)-(?P<key>.+)/$", MyPasswordResetFromKeyView.as_view(), name="account_reset_password_from_key"),
    url(r"^password/reset/key/done/$", MyPasswordResetFromKeyDoneView.as_view(), name="account_reset_password_from_key_done"),

    url(r'^profile/', login_required(ProfileView.as_view()), name="allauth.profile"),

)
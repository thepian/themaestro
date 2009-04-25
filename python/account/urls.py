from django.conf.urls.defaults import *
from django.contrib.auth import views as auth_views
from account import views

urlpatterns = patterns('',
    url(r'^email$', views.email, name="acct_email"),
    url(r'^signup$', views.signup, name="acct_signup"),
    url(r'^login$', views.login, name="acct_login"),
    #TODO logout = clear openid session, logout, add 'you were logged out' message, go to next or /
    url(r'^password_change$', views.password_change, name="acct_passwd"),
    url(r'^password_reset$', views.password_reset, name="acct_passwd_reset"),
    url(r'^timezone$', views.timezone_change, name="acct_timezone_change"),
    url(r'^logout$', auth_views.logout, {"template_name": "account/logout.html"}, name="acct_logout"),

    url(r'^confirm_email/(\w+)/$', views.confirm_email, name="acct_confirm_email"),
    url(r'^username_autocomplete$', views.username_autocomplete),
    url(r'^suggest_username$', views.suggest_username),

    url(r'^profiles$', views.profiles, name="user_profiles"),
    url(r'^profile$', views.private_profile, name="private_profile"),
    url(r'^(\w+)/$', views.profile, name="user_profile"),
)

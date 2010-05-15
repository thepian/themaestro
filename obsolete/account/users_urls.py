from django.conf.urls.defaults import *
from django.contrib.auth import views as auth_views
from account import views

urlpatterns = patterns('',
    url(r'^$', views.profiles, name="user_profiles"),
    url(r'^(\w+)/$', views.profile, name="user_profile"),
)

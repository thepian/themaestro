from theapps.sitemaps.urls.defaults import *
from django.conf import settings
from django.views.generic.simple import direct_to_template
from django.contrib.syndication.views import feed as feed_view

urlpatterns = patterns('',
    url(r'^$', direct_to_template, {"template": "homepage.html"}, name="home"),
    
    url(r'^account/', include('account.urls')),
    url(r'^users/', include('account.users_urls')),
    #url(r'^comments/', include('threadedcomments.urls')),
    url(r'^i18n/', include('django.conf.urls.i18n')),

    #url(r'^thepian/', include('theapps.about.urls')),
    url(r'^about/', include('about.urls')),
    #url(r'^samples/', include('theapps.samples.urls')),
    
    url(r'^test(?P<template>\w+/\w+\.\w+)', direct_to_template),
)

from django.contrib import admin
admin.autodiscover()

urlpatterns += patterns('',
    url(r'^admin/doc/', include('django.contrib.admindocs.urls')),
    url(r'^admin/filebrowser/', include('filebrowser.urls')),
    url(r'^admin/(.*)', admin.site.root, name="admin"),
    url(r'^grappelli/', include('grappelli.urls')),
)


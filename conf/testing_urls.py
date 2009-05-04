from theapps.sitemaps.urls.defaults import *
from django.conf import settings
from theapps.sitemaps import views as sitemap_views

from urls import *

sitemaps = {}

urlpatterns += patterns('',
    url(r'^sitemap$', sitemap_views.sitemap_page, {'sitemaps': sitemaps}, name="sitemap"),
    url(r'^sitemap.xml$', sitemap_views.sitemap, {'sitemaps': sitemaps}, name="sitemap.xml"),
    url(r'^robots.txt$', sitemap_views.robots_txt),
)


from theapps.sitemaps.urls.defaults import *
from django.conf import settings
from django.views.generic.simple import direct_to_template
from django.contrib.syndication.views import feed as feed_view

from theapps.sitemaps import GenericSitemap, views as sitemap_views
from theapps.blog.sitemap import BlogSitemap

#info_dict = { 'queryset': Tag.objects.all() }
info_dict = { 'queryset':[] }

#from zwitschern.feeds import TweetFeed
#feed_dict = {"feed_dict": {
#    'tweets': TweetFeed,
#}}


sitemaps = {
    'blog': BlogSitemap,
    #'tags': GenericSitemap(info_dict, priority=0.5, changefreq='daily'),
    }

urlpatterns = patterns('',
    url(r'^$', direct_to_template, {"template": "homepage.html"}, name="home"),
    
    url(r'^blog/', include('theapps.blog.urls')),
    url(r'^account/', include('theapps.account.urls')),
    url(r'^users/', include('theapps.account.users_urls')),
    #url(r'^invitations/', include('friends_app.urls')),
    #url(r'^notices/', include('notification.urls')),
    #url(r'^messages/', include('messages.urls')),
    #url(r'^announcements/', include('announcements.urls')),
    url(r'^comments/', include('threadedcomments.urls')),
    url(r'^i18n/', include('django.conf.urls.i18n')),

    url(r'^thepian/', include('theapps.about.urls')),
    url(r'^about/', include('about.urls')),
    url(r'^samples/', include('theapps.samples.urls')),

    #url(r'^feeds/(.*)/$', feed_view, feed_dict),
    url(r'^sitemap$', sitemap_views.sitemap_page, {'sitemaps': sitemaps}, name="sitemap"),
    url(r'^sitemap.xml$', sitemap_views.sitemap, {'sitemaps': sitemaps}, name="sitemap.xml"),
    url(r'^robots.txt$', sitemap_views.robots_txt),
)

from django.contrib import admin
admin.autodiscover()

urlpatterns += patterns('',
    (r'^admin/doc/', include('django.contrib.admindocs.urls')),
    url(r'^admin/(.*)', admin.site.root, name="admin"),
)


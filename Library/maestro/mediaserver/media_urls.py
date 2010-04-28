from django.conf.urls.defaults import *

from views import * 

from theapps.media import media_urls

urlpatterns = media_urls.urlpatterns + patterns('',
    url(r'^css/(?P<file_name>.*\.css)$', generate_css),
    url(r'^js/(?P<file_name>.*\.js)$', generate_js),
    #url(r'',static_fallback),
)
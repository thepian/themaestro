from django.conf.urls.defaults import *
from django.views.generic.simple import direct_to_template

urlpatterns = patterns('',
    url(r'^$', direct_to_template, {"template": "about/about.html"}, name="about"),
    url(r'^values$', direct_to_template, {"template": "about/values.html"}, name="values"),
    url(r'^others$', direct_to_template, {"template": "about/others.html"}, name="others"),
    
    url(r'^advertise$', direct_to_template, {"template": "about/advertise.html"}, name="advertise"),
    url(r'^rss$', direct_to_template, {"template": "about/rss.html"}, name="about_rss"),
    url(r'^terms$', direct_to_template, {"template": "about/terms.html"}, name="terms"),
    url(r'^privacy$', direct_to_template, {"template": "about/privacy.html"}, name="privacy"),
    url(r'^contact$', direct_to_template, {"template": "about/contact.html"}, name="contact"),
)

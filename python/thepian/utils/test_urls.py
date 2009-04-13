from urls import *

def test_conversion():
    assert regex2robots(r"^$") == ""
    assert regex2robots(r"^blog/") == "blog/"
    assert regex2robots(r"^blog/$") == "blog/"
    assert regex2robots(r"^blog$") == "blog"
    assert regex2robots(r"^/blog") == "blog/" #Not sure if this is what we want
    assert regex2robots(r"^/blog/") == "blog/" #Not sure if this is what we want
    assert regex2robots(r'^site_media/(?P<path>.*)$') == "site_media/"    
    assert regex2robots(r'^feeds/(.*)/$') == "feeds/" 
    assert regex2robots(r'^accept/(\w+)/$') == "accept/"
    assert regex2robots(r'^(\d+)/$') == ""
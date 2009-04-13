"""
sources holds a tuple of modules each with a source tree of assets. The modules are decorated with
utility functions for manipulating
"""
try:
    from django.conf import settings
    #import default_setings
    #settings.amend_defaults(**default_settings.__dict__)
    
    _sources = []
    for app in settings.INSTALLED_APPS:
        if app != "devonly":
            try:
                mod = __import__(app + ".assets", {}, {}, ['assets'])
                _sources.append(mod)
            except:
                pass
    global sources
    sources = tuple(_sources)
except:
    pass
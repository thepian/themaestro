import default_settings
import theapps
theapps.amend_default_settings(default_settings)

def inject_devonly(settings):
    from thepian.conf import structure
    if structure.DEVELOPING:
        print 'Enabling devonly development'
        if 'devonly' not in settings.INSTALLED_APPS:
            settings.INSTALLED_APPS = list(settings.INSTALLED_APPS) + ['devonly']
        if not hasattr(settings,'URLCONFS'):            
            settings.URLCONFS = { 'www': settings.ROOT_URLCONF }
        if 'media' not in settings.URLCONFS:
            settings.URLCONFS['media'] = 'devonly.media_urls'
        import django.views.debug
        import theapps.supervisor.debug
        django.views.debug.technical_404_response = theapps.supervisor.debug.technical_404_response
   

    
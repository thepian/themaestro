from optparse import make_option
from django.core.management.base import BaseCommand, CommandError

#TODO consider calling:
#from django.core.management import setup_environ
#from conf import settings
#setup_environ(settings)

    
def tweak_django():
    tweak_django_conf()
    tweak_django_auth()
    add_themaestro()
    
def tweak_django_conf():
    from django import conf
    
    class Settings(conf.Settings):
        def __init__(self, settings_module):
            super(Settings,self).__init__(settings_module)
            self.amend_app_defaults()
            
        def amend_app_defaults(self):
            import imp
            for app in self.INSTALLED_APPS:
                try:
                    f,p,d = imp.find_module("%s.default_settings" % app)
                    print p
                except ImportError:
                    pass
                    
        def nilzh(self):
            #for app in self.INSTALLED_APPS:
            #    try:
            #        mod = __import__(app, {}, {}, [''])
            #        print 'imported',app
            #    except ImportError, e:
            #        raise ImportError("Django Application: %s cannot be imported, %s" % (app,e.message))
                    
            for app in self.INSTALLED_APPS:
                try:
                    defaults = __import__("%s.default_settings" % app, {}, {}, [''])
                    for setting in dir(defaults):
                        if setting == setting.upper() and not hasattr(self,setting):
                            print 'adding default ',app+'.'+setting
                            setattr(self,setting,getattr(defaults,setting))
                except ImportError:
                    pass
                
    # patching the Settings class
    #conf.Settings = Settings
            
    
def tweak_django_auth():
    pass
    
def add_themaestro():
    from django.conf import settings
    from thepian.conf import structure
    print settings.DEBUG, settings.MEDIA_URL

    print 'Enabling maestro development'
    if 'themaestro' not in settings.INSTALLED_APPS:
        settings.INSTALLED_APPS = list(settings.INSTALLED_APPS) + ['themaestro']
    if not hasattr(settings,'URLCONFS'):            
        settings.URLCONFS = { 'www': settings.ROOT_URLCONF }
    if 'media' not in settings.URLCONFS:
        settings.URLCONFS['media'] = 'themaestro.media_urls'
    import django.views.debug
    import themaestro.debug
    django.views.debug.technical_404_response = themaestro.debug.technical_404_response
    
    
 
class DjangoCommand(BaseCommand):
    option_list = BaseCommand.option_list + (
        make_option('--cluster', help='The name of the active cluster'),
        )
        
    def execute(self,*args,**options):
        tweak_django()
        super(DjangoCommand,self).execute(*args,**options)
from optparse import make_option
from django.core.management.base import BaseCommand, CommandError

#TODO move to django command class 
try:
    if 'DJANGO_SETTINGS_MODULE' not in os.environ:
        os.environ['DJANGO_SETTINGS_MODULE'] = 'settings'
    from thepian.conf import settings
    from django.conf import settings as django_settings
    #TODO is configured already?
    django_settings.configure(**settings.__dict__)
except Exception,e:
    pass
    
    
def tweak_django():
    tweak_django_conf()
    tweak_django_auth()
    add_themaestro()
    
def tweak_django_conf():
    pass
    
def tweak_django_auth():
    pass
    
def add_themaestro():
    from django.conf import settings
    from thepian.conf import structure

    print 'Enabling maestro development'
    if 'themaestro' not in settings.INSTALLED_APPS:
        settings.INSTALLED_APPS = list(settings.INSTALLED_APPS) + ['themaestro']
    if not hasattr(settings,'URLCONFS'):            
        settings.URLCONFS = { 'www': settings.ROOT_URLCONF }
    if 'media' not in settings.URLCONFS:
        settings.URLCONFS['media'] = 'themaestro.media_urls'
    #TODO if more shards add     
    import django.views.debug
    import themaestro.debug
    django.views.debug.technical_404_response = themaestro.debug.technical_404_response
    
    
 
class DjangoCommand(BaseCommand):
    option_list = BaseCommand.option_list + (
        make_option('--cluster', help='The name of the active cluster'),
        )
        
    requires_machine = True
        
    def execute(self,*args,**options):
        add_themaestro()
        super(DjangoCommand,self).execute(*args,**options)
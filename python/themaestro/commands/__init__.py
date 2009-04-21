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
        
    def execute(self,*args,**options):
        add_themaestro()
        super(DjangoCommand,self).execute(*args,**options)
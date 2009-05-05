import os, sys, site

from thepian.cmdline import COMMANDS, determine_settings_module
from thepian.cmdline.importer import MetaImporter

from thepian.conf.project_tree import find_basedir

def maestro_execute_from_command_line(argv=None):
    """
    A simple method that runs a ManagementUtility.
    """
    from os.path import realpath
    script_file_name=realpath((argv or sys.argv)[0])
    try:
        project_directory = find_basedir(os.getcwd())[1]
    except Exception,e:
        print e, ':: will use Thepian Maestro as project'
        from os.path import dirname
        project_directory = dirname(dirname(script_file_name))
        
#    importer = MetaImporter()
#    importer.alternates['conf'] = [project_directory]
#    sys.meta_path.insert(0,importer)
#    from thepian.conf import use_dependency
#    try:
#        import conf.dependency
#        importer.alternates.update(conf.dependency.MODULES)
#        use_dependency(conf.dependency)
#    except ImportError:
#        pass

    from thepian.conf import structure, use_structure, use_default_structure
    structure.SCRIPT_PATH = script_file_name
    try:
        from os.path import join
        sys.path.insert(0,join(project_directory,"conf")) #TODO too simplistic, use real project tree
        import structure as conf_structure
        use_structure(conf_structure)
        site.addsitedir(structure.PYTHON_DIR)
    except ImportError:
        use_default_structure()
     
    
    structure.COMMAND_VARIABLE_PREFIX = "MAESTRO" 
    from thepian.conf import use_settings, settings
    use_settings(determine_settings_module(argv or sys.argv))
    import django.conf 
    django.conf.settings.configure(**settings.__dict__)

    COMMANDS.execute(argv)

def django_execute_from_command_line(argv=None):
    """
    A simple method that runs a ManagementUtility.
    """
    from os.path import realpath
    script_file_name=realpath((argv or sys.argv)[0])
    try:
        project_directory = find_basedir(os.getcwd())[1]
    except:
        #TODO exlude project based commands
        from os.path import dirname
        project_directory = dirname(dirname(script_file_name))
        
    from thepian.conf import structure, use_structure, use_default_structure
    structure.SCRIPT_PATH = script_file_name
    try:
        from os.path import join
        sys.path.insert(0,join(project_directory,"conf")) #TODO too simplistic, use real project tree
        import structure as conf_structure
        use_structure(conf_structure)
        site.addsitedir(structure.PYTHON_DIR)
    except ImportError:
        use_default_structure()

    structure.COMMAND_VARIABLE_PREFIX = "MAESTRO" 
    settings_module = determine_settings_module(argv or sys.argv)
    from thepian.conf import use_settings, settings
    use_settings(settings_module)

    import django.conf
    django.conf.settings.configure(**settings.__dict__)
    import django.core.management
    django.core.management.execute_from_command_line(argv)



from optparse import make_option
from django.core.management.base import BaseCommand, CommandError

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
import os,sys

def execute_from_command_line(argv=None):
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
        import structure as conf_structure
        use_structure(conf_structure)
        import site
        site.addsitedir(structure.PYTHON_DIR)
    except ImportError:
        use_default_structure()
     
    if not 'MAESTRO_SETTINGS_MODULE' in os.environ: 
        os.environ['MAESTRO_SETTINGS_MODULE'] = 'development' #TODO development vs production
    #os.environ['DJANGO_SETTINGS_MODULE'] = 'thepian.conf.settings'
    from thepian.conf import use_settings, settings
    use_settings(os.environ['MAESTRO_SETTINGS_MODULE'])
    
    from django.core.management import setup_environ, execute_from_command_line
    
    from django.conf import settings as django_settings
    django_settings.configure(**settings.__dict__)
    #setup_environ(settings)
    execute_from_command_line(argv)


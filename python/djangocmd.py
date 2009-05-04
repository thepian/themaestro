import os,sys

from thepian.conf.project_tree import find_basedir
from thepian.cmdline import determine_settings_module

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

    structure.COMMAND_VARIABLE_PREFIX = "MAESTRO" 
    settings_module = determine_settings_module(argv or sys.argv)
    from thepian.conf import use_settings, settings
    use_settings(settings_module)

    import django.conf
    django.conf.settings.configure(**settings.__dict__)
    import django.core.management
    django.core.management.execute_from_command_line(argv)


from optparse import make_option, OptionParser

help = 'Run a trial with tornado'
args = '[?]'
option_list = ()

def get_version():
    return 0.1

def create_parser(prog_name, subcommand):
    usage = '%%prog %s [options] %s' % (subcommand, args)
    usage = '%s\n\n%s' % (usage, help)
    return OptionParser(prog=prog_name,
                        usage=usage,
                        version=get_version(),
                        option_list=option_list)

from thepian.conf.project_tree import find_basedir

def execute_from_command_line(argv=None):
    """
    A simple method that runs a ManagementUtility.
    """
    import os, sys
    from os.path import realpath
    script_file_name=realpath((argv or sys.argv)[0] or sys.executable)
    try:
        project_directory = find_basedir(os.getcwd())[1]
    except Exception,e:
        print e, ':: will use Thepian Maestro as project'
        #TODO rather than fail if used outside a project, use thepian.config as project?
        #TODO exlude project based commands
        from os.path import dirname
        project_directory = dirname(dirname(script_file_name))
        
    from thepian.conf import structure, use_structure, use_default_structure
    structure.SCRIPT_PATH = script_file_name
    try:
        import structure as conf_structure
        use_structure(conf_structure)
        #obsolete
        site.addsitedir(structure.PYTHON_DIR)
    except ImportError:
        use_default_structure()
     
    from thepian.conf import use_settings
    use_settings(structure.determine_settings_module())

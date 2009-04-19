import os
import sys

from base import BaseCommand, CommandError, Cmds
from importer import MetaImporter

from thepian.conf.project_tree import find_basedir


COMMANDS = Cmds()

def execute_from_command_line(argv=None):
    """
    A simple method that runs a ManagementUtility.
    """
    from os.path import realpath
    script_file_name=realpath(sys.argv[0])
    try:
        project_directory = find_basedir(os.getcwd())[1]
    except:
        #TODO rather than fail if used outside a project, use thepian.config as project?
        #TODO exlude project based commands
        from os.path import dirname
        project_directory = dirname(dirname(script_file_name))
        
    importer = MetaImporter()
    importer.alternates['conf'] = [project_directory]
    sys.meta_path.insert(0,importer)
    from thepian.conf import use_dependency
    try:
        import conf.dependency
        importer.alternates.update(conf.dependency.MODULES)
        use_dependency(conf.dependency)
    except ImportError:
        pass

    from thepian.conf import structure, use_structure, use_default_structure
    structure.SCRIPT_PATH = script_file_name
    try:
        import conf.structure
        use_structure(conf.structure)
        import site
        site.addsitedir(structure.PYTHON_DIR)
    except ImportError:
        use_default_structure()
     
    os.environ['DJANGO_SETTINGS_MODULE'] = 'conf.settings'

    COMMANDS.execute(argv)

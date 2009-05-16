"""Thepian command line

Allows easy implementation of commands with a subcommand structure.
It scans top level packages for submodules named `commands`. Any modules in `commands` are expected to implement a Command class.

"""
#TODO https://launchpad.net/lamson

import os, sys, site

from base import BaseCommand, CommandError, Cmds, determine_settings_module
from importer import MetaImporter

from thepian.conf.project_tree import find_basedir

COMMANDS = Cmds()

def execute_from_command_line(argv=None):
    """
    A simple method that runs a ManagementUtility.
    """
    from os.path import realpath
    script_file_name=realpath((argv or sys.argv)[0])
    try:
        project_directory = find_basedir(os.getcwd())[1]
    except Exception,e:
        print e, ':: will use Thepian Maestro as project'
        #TODO rather than fail if used outside a project, use thepian.config as project?
        #TODO exlude project based commands
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
     
    from thepian.conf import use_settings
    use_settings(determine_settings_module(argv or sys.argv))

    COMMANDS.execute(argv)

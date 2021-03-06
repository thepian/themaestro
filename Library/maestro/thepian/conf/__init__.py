"""
Structure and configuration for Thepian.

It can be used independent of Django
"""
import sys, os
from os.path import dirname,abspath,realpath,join,split,exists,expanduser,isfile

from thepian.conf.base import Machine, Structure, Dependency, Settings
from thepian.conf.project_tree import find_basedir, make_project_tree, ensure_target_tree    

dependency = Dependency()

def use_dependency(mod):
    dependency.blend(mod)

structure = Structure() 

def use_cwd_structure():
    """Used by the shell to run of the current sys.path and merge a structure.py module into
    the thepian.conf.structure object."""
    script_file_name = realpath(sys.argv[0] or sys.executable)
    try:
        project_directory = find_basedir(os.getcwd())[1]
        conf_dir = join(project_directory,"conf")
        if exists(conf_dir):
            sys.path.append(conf_dir)
    except Exception,e:
        print e, ':: will use Thepian Maestro as project'
        project_directory = find_basedir(script_file_name)

    try:
        import structure as conf_structure
        use_structure(conf_structure)
    except ImportError:
        use_default_structure()

def use_default_structure():
    """Used by the shell to run of the current sys.path and merge a structure.py module into
    the thepian.conf.structure object."""
    script_file_name = realpath(sys.argv[0] or sys.executable)
    structure.SCRIPT_PATH = script_file_name
    structure.apply_basedir(*find_basedir(abspath(structure.SCRIPT_PATH)))

def use_structure(mod):
    """Used by the shell to run of the current sys.path and merge a structure.py module into
    the thepian.conf.structure object."""
    structure.apply_basedir(*find_basedir(dirname(abspath(mod.__file__))))
    structure.blend(mod)
    
def use_cluster(name):
    structure.set_cluster(structure.CLUSTERS.get(name,structure.CLUSTERS['live']))
    
def adopt_structure(new_structure):
    """Adopt an imported structure as the thepian.conf.structure, use with care.
    Used by spawn-/runnode command to adopt the current repo structure"""
    global structure
    structure =  new_structure
    
# index of loaded structures indexed by sha1(structure_name:basedir)
# the module will be loaded under sys.modules[sha1 key]
_already_imported = {}

def import_structure(directory,structure_name='structure'):
    """Make a structure object based on thepian.conf.global_structure and structure variables
    found in the file specified.
    directory Current directory, or some other directory in the repository
    """
    import imp, hashlib

    repo_dir, basedir, repo_type = find_basedir(directory)
    k = hashlib.sha1(structure_name + ":" + basedir).hexdigest()
    if k in _already_imported:
        return _already_imported[k]
        
    struct = Structure()  
    struct.apply_basedir(repo_dir, basedir, repo_type)

    f, filename, description = imp.find_module(structure_name,[struct.CONF_DIR])
    if not f:
        raise ImportError, "ad hoc structure, %s not found in %s" % (structure_name,struct.CONF_DIR)
    try:
        mod = imp.load_module("thepian.conf."+k, f, filename, description)
        struct.blend(mod)
        _already_imported[k] = struct
    finally:
        f.close()
        return struct
        
def create_structure(directory,structure_name="structure",extended=False):
    """Make a structure object based on thepian.conf.global_structure. Then create skeleton 
    structure in directory. This doesn't import and blend structure.py, which can be done
    afterwards.
    directory - Must be the exact project directory. Normally ~/Sites/<project>
    extended - Should the extended tree be created?
    """
    import hashlib

    directory = expanduser(directory)
    repo_dir = join(directory,"src")
    basedir = join(directory,"src","main")
    k = hashlib.sha1(structure_name + ":" + basedir).hexdigest()
    if k in _already_imported:
        return _already_imported[k]

    struct = Structure()  
    make_project_tree(directory,extended)
    struct.apply_basedir(repo_dir, basedir, "src")
    
    _already_imported[k] = struct
    return struct

def create_site_structure(site_name,structure_name="structure"):
    """Make a structure object based on thepian.conf.global_structure. Then create skeleton 
    structure in directory. This doesn't import and blend structure.py, which can be done
    afterwards.
    directory - Must be the exact project directory. Normally ~/Sites/<project>
    extended - Should the extended tree be created?
    """
    import hashlib

    directory = expanduser(join("/Sites",site_name))
    release_directory = join("/Sites",site_name)
    k = hashlib.sha1(structure_name + ":" + directory).hexdigest()
    if k in _already_imported:
        return _already_imported[k]
        
    struct = Structure()  
    make_project_tree(directory,single=True)
    struct.apply_basedir(directory, directory, "single")
    
    _already_imported[k] = struct
    return struct

settings = Settings()

def use_settings(mod):
    if isinstance(mod,basestring):
        mod = __import__(mod, {}, {}, [])
    settings.blend(mod)
    
def handle_default_options(options):
    """
    Include any default options that all commands should accept
    here so that ManagementUtility can handle them before searching
    for user commands.
    """
    if options.cluster:
        use_cluster(options.cluster)
    if options.settings:
        os.environ['%s_SETTINGS_MODULE' % structure.COMMAND_VARIABLE_PREFIX] = options.settings
    if options.pythonpath:
        sys.path.insert(0, options.pythonpath)

    

__all__ = [ 'structure', 'use_structure', 'import_structure', 'adopt_structure', 'create_structure',
            'create_site_structure','dependency', 'use_dependency', 'settings', 'use_settings', 'handle_default_options']
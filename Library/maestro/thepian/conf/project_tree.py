import re
import os,fs
from os.path import dirname,abspath,join,split,exists,expanduser,isfile

TARGET_DIRECTORY_STRUCTURE = (
    join('target','website','css'),
    join('target','website','js'),
    join('target','mediasite','css'),
    join('target','mediasite','js'),
    join('target','mediasite','images'),
    join('target','mediasite','fonts'),
    join('target','mediasite','objects'),
    join('target','mediasite','renderings'),
    join('target','apisite','js'),
)

RELEASE_DIRECTORY_STRUCTURE = (
    join('release','bin'),
    join('release','conf'),
    join('release','dist'),
    join('release','python'),
    join('release','templates'),
    join('release','website'),
    join('release','mediasite'),
)

SITE_DIRECTORY_STRUCTURE = (
    'bin',
    'as',
    'css',
    'js',
    'python',
    'website',
    'mediasite',
    'templates',
) + TARGET_DIRECTORY_STRUCTURE

DIRECTORY_STRUCTURE = (
    join('src','main','as'),
    join('src','main','bin'),
    join('src','main','conf'),
    join('src','main','css'),
    join('src','main','js'),
    join('src','main','website'),
    join('src','main','mediasite'),
    join('src','main','python'),
    join('src','main','templates'),
    
    join('src','lib','python'),

    'uploads',
    'downloads',
    'data',
    'design',
    'log',
    
) + TARGET_DIRECTORY_STRUCTURE + RELEASE_DIRECTORY_STRUCTURE

SIMPLE_DIRECTORY_STRUCTURE = (
    join('src','as'),
    join('src','bin'),
    join('src','conf'),
    join('src','css'),
    join('src','js'),
    join('src','website'),
    join('src','mediasite'),
    join('src','python'),
    join('src','templates'),
    
    'uploads',
    'downloads',
    'data',
    'design',
    'log',
    
) + TARGET_DIRECTORY_STRUCTURE + RELEASE_DIRECTORY_STRUCTURE

EXTENDED_DIRECTORY_STRUCTURE = (
    join('src','main','cpp'),
    join('src','main','java'),
    join('src','main','java-resources','META-INF'),
    join('src','main','java-resources','WEB-INF'),

    join('src','extras','conf'),
    join('src','extras','java'),
    join('src','extras','root'),
    join('src','extras','templates'),

    join('target','classes'),
    join('target','test-classes'),
    
    join('release','extras','conf'),
    join('release','extras','test-classes'),
    join('release','extras','templates'),
    join('release','extras','website','WEB-INF','classes'),
    join('release','website'),
)

# Name of the hidden directory managed by git, overridden in some tests
GIT_DIR_NAME = ".git"

class StructureError(Exception):
    pass

class ProjectTree(object):
    """Defines a project as a directory tree on disk. 
    It is a representation independent of the actual
    file structure.
    """
    
    #TODO refactor DEVELOPING to be settings dependent
    
    # Enclosing project directory or ? ()
    PROJECT_DIR = None

    REPO_DIR = None

    # Source directory on dev machine, or base directory in production
    SOURCE_DIR = None

    # Target directory on dev machine, or base directory in production
    TARGET_DIR = None

    # Release directory on dev machine, or base directory in production
    RELEASE_DIR = None

    # Uploads directory on dev machine under project, or /var/uploads in production
    UPLOADS_DIR = None

    # Downloads directory on dev machine under project, or /var/downloads in production
    DOWNLOADS_DIR = None

    # Workspace directory on dev machine, or sites directory in production
    SITES_DIR = None

    # Configuration directory where structure.py is located
    CONF_DIR = None

    PYTHON_DIR = None
    TEMPLATES_DIR = None

    # Tuple of website roots. On dev machine it has sources and target. In production just the release
    WEBSITE_DIRS = None

    # Tuple of mediasite roots. On dev machine it has sources and target. In production just the release
    MEDIASITE_DIRS = None

    def __repr__(self):
        return """
project %(PROJECT_NAME)s (type %(REPO_TYPE)s)        
source %(SOURCE_DIR)s
target %(TARGET_DIR)s
release %(RELEASE_DIR)s
u/d/l %(UPLOADS_DIR)s %(DOWNLOADS_DIR)s %(LOG_DIR)s
""" % self.__dict__        

    def apply_basedir(self, repo_dir, basedir, repo_type):
        """Apply the directory structure found by find_basedir
        """
        #TODO detect extended structures
        self.REPO_TYPE = repo_type
        if repo_type == 'single':
            self.apply_single_basedir(repo_dir,basedir)
            self.DEVELOPING = True
        elif repo_type == 'src':
            self.apply_source_basedir(repo_dir,basedir)
            self.DEVELOPING = True
        else:
            self.apply_release_basedir(repo_dir,basedir)
            self.DEVELOPING = False

    def apply_single_basedir(self,repo_dir,basedir):
        self.REPO_DIR = repo_dir 

        self.CONF_DIR = join(basedir, "conf")
        self.PYTHON_DIR = join(basedir,"python")
        self.JS_DIR = join(basedir,"js")
        self.CSS_DIR = join(basedir,"css")
        self.TEMPLATES_DIR = join(basedir,"templates")
        self.SAMPLE_TEMPLATES_DIR = join(self.PYTHON_DIR,"theapps","samples","templates")  

        self.LIB_DIR = join(self.REPO_DIR,"python")
        self.PROJECT_NAME = split(self.REPO_DIR)[1]
        self.PROJECT_DIR = self.REPO_DIR
        self.SOURCE_DIR = self.REPO_DIR
        self.TARGET_DIR = join(self.PROJECT_DIR,"target")
        self.RELEASE_DIR = join(self.PROJECT_DIR,"release")
        self.UPLOADS_DIR = join("/var","uploads",self.PROJECT_NAME)
        self.DOWNLOADS_DIR = join("/var","downloads",self.PROJECT_NAME)
        self.BACKUPS_DIR = join("/var","backups",self.PROJECT_NAME)
        self.LOG_DIR = join("/var","log",self.PROJECT_NAME)
        self.SITES_DIR = dirname(self.PROJECT_DIR)
        self.WEBSITE_DIRS = fs.filterdirs((
            join(basedir,"root"), 
            join(basedir,"website"), 
            join(self.TARGET_DIR,"website"),
            ))
        self.MEDIASITE_DIRS = fs.filterdirs((
            join(basedir,"root"), 
            join(basedir,"mediasite"), 
            join(self.TARGET_DIR,"mediasite"),
            ))
        self.TOOLS_DIR = expanduser("~/Sites/tools")
        self.PID_DIR = join("/var/run",self.PROJECT_NAME)
        
        from fs import filters
        dirs = fs.listdir(self.PROJECT_DIR, filters=(filters.fnmatch("*site"),filters.only_directories,))
        dirs.sort() # just to make sure
        self.SITE_DIRS = dirs
        
    def apply_source_basedir(self,repo_dir,basedir):
        self.REPO_DIR = repo_dir 

        self.CONF_DIR = join(basedir, "conf")
        self.PYTHON_DIR = join(basedir,"python")
        self.JS_DIR = join(basedir,"js")
        self.CSS_DIR = join(basedir,"css")
        self.TEMPLATES_DIR = join(basedir,"templates")
        self.SAMPLE_TEMPLATES_DIR = join(self.PYTHON_DIR,"theapps","samples","templates")  

        d = split(basedir)
        if d[-1] == 'main':
            self.LIB_DIR = join(self.REPO_DIR,"lib","python")
        else:
            self.LIB_DIR = join(self.REPO_DIR,"python")
        self.PROJECT_NAME = split(dirname(self.REPO_DIR))[1]
        self.PROJECT_DIR = dirname(self.REPO_DIR)
        self.SOURCE_DIR = self.REPO_DIR
        self.TARGET_DIR = join(self.PROJECT_DIR,"target")
        self.RELEASE_DIR = join(self.PROJECT_DIR,"release")
        self.UPLOADS_DIR = join(self.PROJECT_DIR,"uploads")
        self.DOWNLOADS_DIR = join(self.PROJECT_DIR,"downloads")
        self.BACKUPS_DIR = join(self.PROJECT_DIR,"backups")
        self.LOG_DIR = join(self.PROJECT_DIR,"log")
        self.SITES_DIR = dirname(self.PROJECT_DIR)
        self.WEBSITE_DIRS = fs.filterdirs((
            join(basedir,"root"), 
            join(basedir,"website"), 
            join(self.TARGET_DIR,"website"),
            ))
        self.MEDIASITE_DIRS = fs.filterdirs((
            join(basedir,"root"), 
            join(basedir,"mediasite"), 
            join(self.TARGET_DIR,"mediasite"),
            ))
        self.TOOLS_DIR = expanduser("~/Sites/tools")
        self.PID_DIR = join("/var/run",self.PROJECT_NAME)
        
    def apply_release_basedir(self,repo_dir,basedir):
        self.REPO_DIR = repo_dir 

        self.CONF_DIR = join(basedir, "conf")
        self.PYTHON_DIR = join(basedir,"python")
        self.JS_DIR = join(basedir,"js")
        self.CSS_DIR = join(basedir,"css")
        self.TEMPLATES_DIR = join(basedir,"templates")
        self.SAMPLE_TEMPLATES_DIR = join(self.PYTHON_DIR,"theapps","samples","templates")  

        d = split(basedir)

        if d[-1] == "release":
            d = split(dirname(basedir))
        self.PROJECT_NAME = d[-1]
        self.PROJECT_DIR = basedir
        self.SOURCE_DIR = basedir
        self.LIB_DIR = self.PYTHON_DIR
        self.TOOLS_DIR = expanduser("~/tools")
        self.TARGET_DIR = basedir
        self.RELEASE_DIR = basedir
        self.UPLOADS_DIR = join("/var","uploads",self.PROJECT_NAME)
        self.DOWNLOADS_DIR = join("/var","downloads",self.PROJECT_NAME)
        self.BACKUPS_DIR = join("/var","backups",self.PROJECT_NAME)
        self.LOG_DIR = join("/var","log",self.PROJECT_NAME)
        self.SITES_DIR = dirname(self.PROJECT_DIR)
        self.WEBSITE_DIRS = (join(basedir,"website"),)
        self.MEDIASITE_DIRS = (join(basedir,"mediasite"),)
        self.PID_DIR = join("/var/run",self.PROJECT_NAME)




def is_basedir(basedir):
    """ Returns (git_dir,basedir) if this is a basedir otherwise an ('','')
    If it is a basedir but not within a repository ('',basedir) is returned
    If it is a repository but not a basedir (basedir,'') is returned
    
    conf and python directories and setup.py are used to identify basedir, one or the other must exist.

    ** Usage **
    >>> import thepian.conf
    >>> import os
    >>> import thepian.conf.project_tree
    >>> thepian.conf.project_tree.GIT_DIR_NAME = "git"
    >>> is_basedir(os.path.join(os.path.dirname(thepian.conf.test.__file__),'samples', 'single_sample'))
    ('/Sites/themaestro/python/thepian/conf/test/samples/single_sample', '/Sites/themaestro/python/thepian/conf/test/samples/single_sample')
    >>> is_basedir(os.path.join(os.path.dirname(thepian.conf.test.__file__),'samples','no_repo_sample'))
    ('', '/Sites/themaestro/python/thepian/conf/test/samples/no_repo_sample')
    >>> is_basedir(os.path.join(os.path.dirname(thepian.conf.test.__file__),'samples', 'simple_sample','src'))
    ('/Sites/themaestro/python/thepian/conf/test/samples/simple_sample/src', '/Sites/themaestro/python/thepian/conf/test/samples/simple_sample/src')
    >>> is_basedir(os.path.join(os.path.dirname(thepian.conf.test.__file__),'samples', 'simple_sample','src','conf'))
    ('', '')
    """
    conf_dir = join(basedir, "conf")
    python_dir = join(basedir, "python")
    setup_py = join(basedir, "setup.py")
    if exists(conf_dir) or exists(python_dir) or exists(setup_py):
        if exists(join(basedir,GIT_DIR_NAME)):
            return (basedir,basedir)
        above = dirname(basedir)
        if exists(join(above,GIT_DIR_NAME)):
            return (above,basedir)
        else:
            return ('',basedir)
    else:
        if exists(join(basedir,GIT_DIR_NAME)):
            if exists(join(basedir,"main","conf")) or exists(join(basedir,"main","python")):
                return (basedir,join(basedir,"main"))
            return (basedir,'')
        else:
            return '', ''
    
def find_basedir(basedir):
    """Finds the git and base directories in basedir or ancestor
    return (git,base,type) type being 'single'/'src'/'release'/'' 
    """
    #TODO switch to returning (project,repo,base,type)
    while len(basedir) > 0 and not basedir is "/":
        git,base = is_basedir(basedir)
        if git and base:
            lead,end = split(git)
            if end in ['src','release']:
                return git, base, end
            else:
                return git,base, 'single'
        if not git and base: raise StructureError, "Command must be used from within a source or release repository"
        if git and not base: raise StructureError, "No base directory found within the repository %s"  % git
        basedir = dirname(basedir)
    raise Exception, "Command must be used from within a source, release or production repository"

def make_project_tree(directory,extended=False,simple=False,single=False):
    from thepian.utils import makedirs_tree
    if single:
        makedirs_tree(directory,SITE_DIRECTORY_STRUCTURE)
    elif simple:
        makedirs_tree(directory, SIMPLE_DIRECTORY_STRUCTURE)
    else:
        makedirs_tree(directory,DIRECTORY_STRUCTURE)
        if extended:
            makedirs_tree(directory, EXTENDED_DIRECTORY_STRUCTURE)
            
def ensure_target_tree(directory,extended=False):
    from thepian.utils import makedirs_tree
    makedirs_tree(directory,TARGET_DIRECTORY_STRUCTURE)
    
        

    
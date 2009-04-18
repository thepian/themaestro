import re
import os,fs
from os.path import dirname,abspath,join,split,exists,expanduser,isfile

SITE_DIRECTORY_STRUCTURE = (
    'bin',
    'as',
    'css',
    'js',
    'python',
    'website',
    'mediasite',
    'templates',

    join('target','website','css'),
    join('target','website','js'),
    join('target','mediasite','css'),
    join('target','mediasite','js'),
    join('target','mediasite','images'),
    join('target','mediasite','fonts'),
    join('target','mediasite','objects'),
    join('target','mediasite','renderings'),

)

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

    join('target','website','css'),
    join('target','website','js'),
    join('target','mediasite','css'),
    join('target','mediasite','js'),
    join('target','mediasite','images'),
    join('target','mediasite','fonts'),
    join('target','mediasite','objects'),
    join('target','mediasite','renderings'),

    join('release','bin'),
    join('release','conf'),
    join('release','dist'),
    join('release','python'),
    join('release','templates'),
    join('release','website'),
    join('release','mediasite'),

    'uploads',
    'downloads',
    'data',
    'design',
    'log',
    
)

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
    
    join('target','website','css'),
    join('target','website','js'),
    join('target','mediasite','css'),
    join('target','mediasite','js'),
    join('target','mediasite','images'),
    join('target','mediasite','fonts'),
    join('target','mediasite','objects'),
    join('target','mediasite','renderings'),

    join('release','bin'),
    join('release','conf'),
    join('release','dist'),
    join('release','python'),
    join('release','templates'),
    join('release','website'),
    join('release','mediasite'),

    'uploads',
    'downloads',
    'data',
    'design',
    'log',
    
)

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

class StructureError(Exception):
    pass

class ProjectTree(object):
    # stub to be expanded
    
    #TODO refactor DEVELOPING to be settings dependent
    
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
    """
    conf_dir = join(basedir, "conf")
    python_dir = join(basedir, "python")
    if exists(conf_dir) and exists(python_dir):
        if exists(join(basedir,".git")):
            return (basedir,basedir)
        above = dirname(basedir)
        if exists(join(above,".git")):
            return (above,basedir)
        else:
            return ('',basedir)
    else:
        if exists(join(basedir,".git")):
            if exists(join(basedir,"main","conf")) and exists(join(basedir,"main","python")):
                return (basedir,join(basedir,"main"))
            return (basedir,'')
        else:
            return '', ''
    
def find_basedir(basedir):
    """Finds the git and base directories in basedir or ancestor
    return (git,base,type) type being 'src'/'release'/'' 
    """
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
        

    
import thepian.conf.project_tree
from thepian.conf.project_tree import *

from os.path import join,dirname
no_repo_sample = join(dirname(__file__),"samples","no_repo_sample")
simple_sample = join(dirname(__file__),"samples","simple_sample")
single_sample = join(dirname(__file__),"samples","single_sample")

def test_tree():
    tree = ProjectTree()
    tree.apply_basedir("/Sites/themaestro",'/Sites/themaestro','single')
    assert "/Sites/themaestro/conf" == tree.CONF_DIR
    assert "/Sites/themaestro/python" == tree.PYTHON_DIR
    assert "/Sites/themaestro/js" == tree.JS_DIR
    assert "/Sites/themaestro/css" == tree.CSS_DIR
    assert "/Sites/themaestro/templates" == tree.TEMPLATES_DIR
    assert "/Sites/themaestro/website" in tree.WEBSITE_DIRS
    assert "/Sites/themaestro/mediasite" in tree.MEDIASITE_DIRS
    assert "/Sites/themaestro/root" not in tree.WEBSITE_DIRS
    assert "/Sites/themaestro/root" not in tree.MEDIASITE_DIRS
    assert "/Sites/themaestro/target" == tree.TARGET_DIR
    assert "/Sites/themaestro/release" == tree.RELEASE_DIR
    assert "/Sites" == tree.SITES_DIR
    
    #self.UPLOADS_DIR = join("/var","uploads",self.PROJECT_NAME)
    #self.DOWNLOADS_DIR = join("/var","downloads",self.PROJECT_NAME)
    #self.BACKUPS_DIR = join("/var","backups",self.PROJECT_NAME)
    #self.LOG_DIR = join("/var","log",self.PROJECT_NAME)
    #self.TOOLS_DIR = expanduser("~/Sites/tools")
    #self.PID_DIR = join("/var/run",self.PROJECT_NAME)
    
def test_find_basedir():
    thepian.conf.project_tree.GIT_DIR_NAME = "git"

    # Root of single project
    repo,base,t = find_basedir(single_sample)
    assert single_sample == repo
    assert single_sample == base
    assert "single" == t
    
    # Subdir of single project
    repo,base,t = find_basedir(join(single_sample,"conf"))
    assert single_sample == repo
    assert single_sample == base
    assert "single" == t

    # src root of simple project
    repo,base,t = find_basedir(join(simple_sample,"src"))
    assert join(simple_sample,"src") == repo
    assert join(simple_sample,"src") == base
    assert t == "src"
    
    # Subdir of src root of simple project
    repo,base,t = find_basedir(join(simple_sample,"src","conf"))
    assert join(simple_sample,"src") == repo
    assert join(simple_sample,"src") == base
    assert t == "src"
    
    # release root of simple project
    repo,base,t = find_basedir(join(simple_sample,"release"))
    assert join(simple_sample,"release") == repo
    assert join(simple_sample,"release") == base
    assert t == "release"
    
    
from thepian.conf.project_tree import ProjectTree

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
    
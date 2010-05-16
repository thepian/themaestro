import fs,os
import stat
from thepian.conf import structure

features = {}

class Feature(object):
    name = None
    pid_path = None
    found = False
    
    def __init__(self,structure):
        pass
        
    def __unicode__(self):
        return 'Feature %s' % (self.name,)
    
    def reload(self):
        pass


def describe_features(self):
    return [u'features detected....'] + [unicode(features[f]) for f in features]
    
PID_DIRECTORIES = ('/opt/local/var/run','/var/run')

ETC_DIRECTORIES = ('/etc','/usr/local/etc','/opt/local/etc')

def determine_installation():
    """Determine nginx, logrotate, spread toolkit, memcached, postgresql
    """
    structure.USR_BIN_DIR = fs.first_exists(('/usr/local/bin','/usr/bin'))
    
    if not isdir(structure.LOG_DIR):
        structure.INCOMPLETE = "Log directory missing, %s" % structure.LOG_DIR
    elif not isdir(structure.UPLOADS_DIR):
        structure.INCOMPLETE = "Uploads directory missing, %s" % structure.UPLOADS_DIR
    elif not isdir(structure.DOWNLOADS_DIR):
        structure.INCOMPLETE = "Log directory missing, %s" % structure.DOWNLOADS_DIR
    #TODO check database


def ensure_areas():
    """Hook up the installation to make the project available
    Make sure directories are present
    """
    uploads_area.require_directory(structure.UPLOADS_DIR)
    downloads_area.require_directory(structure.DOWNLOADS_DIR)
    backups_area.require_directory(structure.BACKUPS_DIR)
    log_area.require_directory(structure.LOG_DIR)
    pid_area.require_directory(structure.PID_DIR)

def install_features():
    for name in structure.FEATURES:
        module = __import__('maestro.config.%s' % name,{},{},[''])
        if hasattr(module,'install') and callable(module.install):
            module.install()

    from maestro.config.nginx import nginx_enabled, update_local_nginx, symlink_local_nginx, nginx_installed

    #sock_dir = "/var/tmp/django"
    #import fs,os,stat
    #fs.makedirs(sock_dir)
    #os.chmod(sock_dir,0777)

    #TODO make sure memcached couchdb are started
    


def require_directory(path, uid, gid, mod = stat.S_IRUSR+stat.S_IWUSR+stat.S_IXUSR+stat.S_IRGRP+stat.S_IWGRP+stat.S_IXGRP+stat.S_IROTH+stat.S_IXOTH):
    """default mod = user:rwx group:rwx other:rx"""
    fs.makedirs(path)
    os.chown(path, uid, gid)
    os.chmod(path, mod)

class FileArea(object):
    """Area on filesystem with particular access requirements
    """    
    user = "henrikvendelbo"
    group = "wheel"
    base = "/Sites"
    
    def __init__(self,user,group):
        self.user = user
        self.group = group

    def apply(self):
        from grp import getgrnam
        from pwd import getpwnam
        uname, upass, self.uid, nop, nop, nop, nop = getpwnam(self.user)
        gname, gpass, self.gid, nop = getgrnam(self.group)    
        
    def require_directory(self,path,**kwargs):
        if not hasattr(self,'uid') or not hasattr(self,'gid'):  
            self.apply()
        require_directory(path, self.uid, self.gid,**kwargs)

uploads_area = FileArea(structure.machine.data['shard_user'],structure.machine.data['shard_group'])
downloads_area = FileArea(structure.machine.data['shard_user'],structure.machine.data['shard_group'])
etc_area = FileArea(structure.machine.data['etc_user'],structure.machine.data['etc_group'])
pid_area = FileArea(structure.machine.data['log_user'],structure.machine.data['log_group'])
log_area = FileArea(structure.machine.data['log_user'],structure.machine.data['log_group'])
backups_area = FileArea(structure.machine.data['log_user'],structure.machine.data['log_group'])



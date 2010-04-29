import os, imp, net, fs
from os.path import dirname,abspath,join,split,exists,expanduser,isfile,isdir
from pwd import getpwnam,getpwuid
from grp import getgrnam
from subprocess import Popen

import global_structure
import global_settings
from project_tree import ProjectTree, ensure_target_tree

from UserDict import UserDict

import stat

def require_directory(path, uid, gid, mod = stat.S_IRUSR+stat.S_IWUSR+stat.S_IXUSR+stat.S_IRGRP+stat.S_IWGRP+stat.S_IXGRP+stat.S_IROTH+stat.S_IXOTH):
    """default mod = user:rwx group:rwx other:rx"""
    fs.makedirs(path)
    os.chown(path, uid, gid)
    os.chmod(path, mod)

class FileArea(object):
    """Area on filesystem with particular access requirements
    """    
    user = "thepian"
    group = "thepian"
    base = "/Sites"
    
    def __init__(self,user,group):
        self.user = user
        self.group = group

    def apply(self):
        uname, upass, self.uid, nop, nop, nop, nop = getpwnam(self.user)
        gname, gpass, self.gid, nop = getgrnam(self.group)    
        
    def require_directory(self,path,**kwargs):
        if not hasattr(self,'uid') or not hasattr(self,'gid'):  
            self.apply()
        require_directory(path, self.uid, self.gid,**kwargs)
        
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

class HostsFeature(Feature):
    name = "hosts"
    
    def __init__(self,structure):
        etc_file = "/etc/hosts"
        if exists(etc_file):
            self.ETC_FILE = etc_file
            self.found = True

class NginxFeature(Feature):
    name = "nginx"

    def __init__(self,structure):
        for etc in structure.ETC_DIRECTORIES:
            etc_file = join(etc,'nginx','nginx.conf')
            if exists(etc_file):
                self.ETC_FILE = etc_file
                self.NGINX_ETC_DIR = join(etc,'nginx')
                self.NGINX_SITES_ENABLED = join(etc, 'nginx', 'sites-enabled')
                self.NGINX_SITES_AVAILABLE = join(etc, 'nginx', 'sites-available')
                self.found = True
                break
                
        for d in structure.PID_DIRECTORIES:
            if (exists(join(d,"nginx.pid"))):
                self.pid_path = join(d,"nginx.pid")
                break

    def reload(self):
        if self.pid_path:
            sp = Popen('kill -HUP `cat %s`' % self.pid_path,env=None,shell=True)
            sts = os.waitpid(sp.pid, 0)            
        
    
class MemcachedFeature(Feature):
    name = "memcached"
    
class SpreadFeature(Feature):
    pass
    
class PostgresFeature(Feature):
    pass
    
class DjangoMailerFeature(Feature):
    pass
    
class DjangoWebFeature(Feature):
    pass



class Machine(UserDict):

    public_acces = False

    def __init__(self,structure,server=None,cluster=None):
        #self.structure = structure
        if server:
            self.data = server.copy()
            _cluster = self.CLUSTER = cluster or structure.CLUSTERS[server.get('cluster')] or structure.CLUSTERS.get('live',structure.FALLBACK_CLUSTER)
            self.known = True
            self.public_access = server.get('domains',False)
        else:
            self.data = {
                'mac' : net.get_mac_address_hex(),
                'pool_ip' : net.get_ip4_address(),
                'own_ip' : net.get_ip4_address(),
                'nick' : 'unknown',
            }
            _cluster = self.CLUSTER = cluster or structure.CLUSTERS.get('live',structure.FALLBACK_CLUSTER)
            self.known = False
        self.data.update(_cluster)

        if self.data['shard_user'] == '~': self.data['shard_user'] = structure.PROJECT_NAME
        if self.data['etc_user'] == '~': self.data['etc_user'] = structure.PROJECT_NAME
        if self.data['log_user'] == '~': self.data['log_user'] = structure.PROJECT_NAME
        self.DOMAINS = [name.strip('.') for name in self.data['domains']]  
        if self.known:
            self.NICK = self.data['NICK']
            

        self.effective_uid = os.getuid()
        self.effective_user = getpwuid(self.effective_uid)[0]
        self.uploads_area = FileArea(self.data['shard_user'],self.data['shard_group'])
        self.downloads_area = FileArea(self.data['shard_user'],self.data['shard_group'])
        self.etc_area = FileArea(self.data['etc_user'],self.data['etc_group'])
        self.pid_area = FileArea(self.data['log_user'],self.data['log_group'])
        self.log_area = FileArea(self.data['log_user'],self.data['log_group'])
        self.backups_area = FileArea(self.data['log_user'],self.data['log_group'])

    #def __getitem__(self,index):
    #    print 'looking up machine[%s]' % index
    #    return self.data[index]

    #def get(self,index,d=None):
    #    return self.data.get(index,d)
        
    def describe(self):
        return [
            u'cluster=%s mac=%s nick=%s pool=%s own=%s' % (self.data['cluster'],self.data['mac'],self.data['nick'],self.data['pool_ip'],self.data['own_ip']),
            u'domains: %s' % self.data['domains']
        ]

    def to_cookie_domain(self,http_host):
        s = http_host.split(".")
        if s[0] in ['media','www']: #TODO improve test to work off configuration
            del s[0]
        return ".".join(s)


class Structure(ProjectTree):
    """
    {sites_dir}/{project_dir}/../bin
    {sites_dir}/{project_dir}/../conf/structure.py
    {sites_dir}/{project_dir}/../conf - conf_dir
    {sites_dir}/{project_dir}/../website - root_dir & root_dirs
    
    
    >>> import global_structure
    >>> global_structure.DEFAULT_SETTING = 'some value'
    >>> structure = Structure()
    >>> structure.DEFAULT_SETTING
    'some value'
    
    """
    
    __file__ = None
    #__package__ = None
    __doc__ = None

    # Name of the structure module used as the basis for conf.structure
    STRUCTURE_MODULE = None

    # Generated from SHARD_AFFINITY by inverting the dict
    AFFINITY_TO_SHARD = {}

    # NginX directory locations to use on this machine
    NGINX_ETC_DIR = None
    NGINX_SITES_ENABLED = None
    NGINX_SITES_AVAILABLE = None

    INCOMPLETE = None
    #TODO consider:
    # source_tree = ProjectTree
    # release_tree
    # live_tree
    
    CLUSTER = None

    # Prefix that makes up the name of the os.environ variable which points to the settings.py to use
    COMMAND_VARIABLE_PREFIX = "THEPIAN"
    
    def __init__(self):
        # update this dict from global structure (but only for ALL_CAPS settings)
        for name in dir(global_structure):
            if name == name.upper():
                setattr(self, name, getattr(global_structure, name))

    def __getattr__(self, name):
        if self._machine:
            if hasattr(self._machine,name):
                return getattr(self._machine,name)
            if name in self._machine:
                return self._machine[name]
        raise AttributeError('Attribute "%s" not found' % name)

    def __getitem__(self,index):
        if not hasattr(self,index):
            raise AttributeError("Attribute '%s' not found using structure[..]" % index)
        return getattr(self,index)

    def ensure_target_dirs(self):
        """Check the project for directories in the target tree, and create any that are missing"""
        #TODO check to see if project type is extended
        ensure_target_tree(self.PROJECT_DIR)
        
    def determine_installation(self):
        """Determine nginx, logrotate, spread toolkit, memcached, postgresql
        """
        self.USR_BIN_DIR = fs.first_exists(('/usr/local/bin','/usr/bin'))
        self.features = {}
        hosts = HostsFeature(self)
        if hosts.found:
            self.features['hosts'] = hosts
        nginx = NginxFeature(self)
        if nginx.found:
            self.features['nginx'] = nginx
        memcached = MemcachedFeature(self)
        if memcached.found:
            self.features['memcached'] = memcached
        spread = SpreadFeature(self)
        if spread.found:
            self.features['spread'] = spread
        postgres = PostgresFeature(self)
        if postgres.found:
            self.features['postgres'] = postgres
        django_mailer = DjangoMailerFeature(self)
        if django_mailer.found:
            self.features['django_mailer'] = django_mailer
        django_web = DjangoWebFeature(self)
        if django_web.found:
            self.features['django_web'] = django_web
        
        for etc in self.ETC_DIRECTORIES:
            if exists(join(etc,'nginx','nginx.conf')):
                self.NGINX_ETC_DIR = join(etc,'nginx')
                self.NGINX_SITES_ENABLED = join(etc, 'nginx', 'sites-enabled')
                self.NGINX_SITES_AVAILABLE = join(etc, 'nginx', 'sites-available')
                break;
                
        if not isdir(self.LOG_DIR):
            self.INCOMPLETE = "Log directory missing, %s" % self.LOG_DIR
        elif not isdir(self.UPLOADS_DIR):
            self.INCOMPLETE = "Uploads directory missing, %s" % self.UPLOADS_DIR
        elif not isdir(self.DOWNLOADS_DIR):
            self.INCOMPLETE = "Log directory missing, %s" % self.DOWNLOADS_DIR
        #TODO check database

    def hook_installation(self):
        """Hook up the installation to make the project available
        Make sure directories are present
        """
        self.machine.uploads_area.require_directory(self.UPLOADS_DIR)
        self.machine.downloads_area.require_directory(self.DOWNLOADS_DIR)
        self.machine.backups_area.require_directory(self.BACKUPS_DIR)
        self.machine.log_area.require_directory(self.LOG_DIR)
        self.machine.pid_area.require_directory(self.PID_DIR)
        if self.NGINX_ETC_DIR:
            self.machine.etc_area.require_directory(self.NGINX_SITES_ENABLED)
            self.machine.etc_area.require_directory(self.NGINX_SITES_AVAILABLE)

    def blend(self, mod):
        """Blend a module into the structure, usually used to blend conf.structure into thepian.conf.structure"""
        # Copy module attributes to self
        # Settings that should be converted into tuples if they're mistakenly entered
        # as strings.
        self.__file__ = mod.__file__
        # self.__package__ = mod.__package__
        self.__doc__ = mod.__doc__
        if hasattr(mod,'__path__'):
            self.__path__ = mod.__path__
        for name in dir(mod):
            if name == name.upper():
                value = getattr(mod, name)
                if name in self.TUPLE_STRUCTURE and type(value) == str:
                    value = (value,) # In case the user forgot the comma.
                setattr(self, name, value)

        # Create a map from affinity number to shard name
        self.AFFINITY_TO_SHARD = {}
        for name in self.SHARD_AFFINITY:
            shard = self.SHARD_AFFINITY[name]
            for id in shard: self.AFFINITY_TO_SHARD[id] = name


    def get_all_members(self):
        return dir(self)

    _machine = None

    def get_macs(self):
        """return a list of mac adresses found on this machine as 8 hex digits"""
        return [mac.replace(':','').lstrip("0") for mac in net.get_mac_addresses()]
        
    def set_cluster(self,cluster):
        self.CLUSTER = cluster
        macs = self.get_macs()
        for server in self.SERVERS:
            if server['mac'] in macs:
                #print 'set_cluster', cluster, server, self
                self._machine = Machine(self, server=server, cluster=cluster)
                return
        self._machine = Machine(self,cluster=cluster)
        
    def describe(self):
        if self._machine:
            return self._machine

        macs = self.get_macs()
        for server in self.SERVERS:
            if server['mac'] in macs:
                self._machine = Machine(self, server=server)
                self.CLUSTER = self._machine.CLUSTER
                return self._machine
        print "Warning: machine not recognised"    
        self._machine = Machine(self)
        self.CLUSTER = self._machine.CLUSTER

        return self._machine

    description = property(describe)
    machine = property(describe)

    features = {}
        
    def describe_features(self):
        return [u'features detected....'] + [unicode(self.features[f]) for f in self.features]
        
    def get_subdomain_list(self):
        """ pairs of (subdomain,type)"""
        return [('www','www'),(self.MEDIA_SUBDOMAIN,'media')] +  [(sub,'shard') for sub in self.SHARD_NAMES + self.DEDICATED_SHARD_NAMES]
    subdomain_list = property(get_subdomain_list)

    def get_base_domain(self,request_meta):
        """Translates from the currently served domain (such as www.example.com) to a base domain (such as .example.com)
        On any live site the front end web server is responsible for passing the requested hostname

        request_meta is the dict describing headers passed with the request. For django it's request.META
        """
        served_domain = request_meta.get(self.HTTP_HOST_VARIABLE) or self.DEFAULT_HOSTNAME
        bits = served_domain.split('.')
        if bits[0] in self.SHARD_NAMES or bits[0] in ('www','media'):
            bits[0] = ''
        return ".".join(bits)
        #TODO improve domain conversion

    def get_shard_subdomain(self,number):
        """Translates a shard number into a subdomain name"""
        l = len(self.SHARD_NAMES)
        return self.AFFINITY_TO_SHARD.get(number) or self.SHARD_NAMES[number % l]
        
    def determine_settings_module(self):
        """Determine name of settings module based on THEPIAN_SETTINGS_MODULE environment variable or equivalent
        """
        if not '%s_SETTINGS_MODULE' % self.COMMAND_VARIABLE_PREFIX in os.environ: 
            os.environ['%s_SETTINGS_MODULE' % self.COMMAND_VARIABLE_PREFIX] = 'development' #TODO development vs production
        return os.environ['%s_SETTINGS_MODULE' % self.COMMAND_VARIABLE_PREFIX]

    

class Dependency(object):
    
    MODULES = {}
    MODULE_PATHS = {}
    TUPLE_STRUCTURE = ()
    
    def blend(self,mod):
        # Copy module attributes to self
        # Settings that should be converted into tuples if they're mistakenly entered as strings.
        for name in dir(mod):
            if name == name.upper():
                value = getattr(mod, name)
                if name in self.TUPLE_STRUCTURE and isinstance(value,basestring):
                    value = (value,) # In case the user forgot the comma.
                setattr(self, name, value)
                
        for mn in self.MODULES: 
            paths = self.MODULES[mn]
            try:
                f,pathname,description = imp.find_module(mn,paths)
                self.MODULE_PATHS[mn] = pathname
            except ImportError:
                return None

class Settings(object):
    """Used to hold settings in thepian.conf.settings
    
    >>> import global_settings
    >>> global_settings.DEFAULT_SETTING = 'some value'
    >>> settings = Settings()
    >>> settings.DEFAULT_SETTING
    'some value'
    """
    
    __file__ = None
    
    def __init__(self):
        # update this dict from global structure (but only for ALL_CAPS settings)
        for name in dir(global_settings):
            if name == name.upper():
                setattr(self, name, getattr(global_settings, name))

    def blend(self, mod):
        """Blend a module into the structure, usually used to blend conf.development or conf.production into thepian.conf.settings"""
        self.__file__ = mod.__file__
        # self.__package__ = mod.__package__
        self.__doc__ = mod.__doc__
        if hasattr(mod,'__path__'):
            self.__path__ = mod.__path__
        # Copy module attributes to self
        # Settings that should be converted into tuples if they're mistakenly entered
        # as strings.
        for name in dir(mod):
            if name == name.upper():
                value = getattr(mod, name)
                if name in self.TUPLE_STRUCTURE and type(value) == str:
                    value = (value,) # In case the user forgot the comma.
                setattr(self, name, value)
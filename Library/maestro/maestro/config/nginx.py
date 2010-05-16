from __future__ import with_statement
import fs, os, sys
from os.path import exists, dirname, join, split
from subprocess import Popen, PIPE

from thepian.conf import structure, settings
from thepian.conf.project_tree import ProjectTree

from base import features, Feature, ETC_DIRECTORIES, PID_DIRECTORIES
from base import log_area

def install():
    """Called by install_features() if listed in structure.FEATURES"""
    
        # etc_area.require_directory(structure.NGINX_SITES_ENABLED)
        # etc_area.require_directory(structure.NGINX_SITES_AVAILABLE)
    
    # is this needed? fs.symlink(structure.SCRIPT_PATH,'/usr/local/bin/maestro',replace=True)
    nginx_installed()
    print 'installing nginx feature', settings.DEVELOPING
    if settings.DEVELOPING:
        #TODO link in User Sites directory
        from os.path import join,exists,expanduser
        fs.symlink(structure.PROJECT_DIR,join(expanduser("~/Sites"),structure.PROJECT_NAME))

        dev_name = join(structure.CONF_DIR,"dev.nginx.conf")
        if not exists(dev_name):
            servers_contents = nginx_enabled(cluster_name="dev",release_project_dir=False)
            with open(dev_name, 'w') as nginx_conf:
                nginx_conf.writelines(servers_contents)               
        dev_name = join(structure.CONF_DIR,"staged.nginx.conf")
        if not exists(dev_name):
            servers_contents = nginx_enabled(cluster_name="staged",release_project_dir=False)
            with open(dev_name, 'w') as nginx_conf:
                nginx_conf.writelines(servers_contents)

    symlink_local_nginx()
    
    
class NginxFeature(Feature):
    name = "nginx"

    def __init__(self,structure):
        for etc in ETC_DIRECTORIES:
            etc_file = join(etc,'nginx','nginx.conf')
            if exists(etc_file):
                self.ETC_FILE = etc_file
                self.NGINX_ETC_DIR = join(etc,'nginx')
                self.NGINX_SITES_ENABLED = join(etc, 'nginx', 'sites-enabled')
                self.NGINX_SITES_AVAILABLE = join(etc, 'nginx', 'sites-available')
                self.found = True
                break
                
        for d in PID_DIRECTORIES:
            if (exists(join(d,"nginx.pid"))):
                self.pid_path = join(d,"nginx.pid")
                break

    def reload(self):
        if self.pid_path:
            sp = Popen('kill -HUP `cat %s`' % self.pid_path,env=None,shell=True)
            sts = os.waitpid(sp.pid, 0)            
        

# register nginx in features
nginx = NginxFeature(structure)
if nginx.found:
    features["nginx"] = nginx


CONF_DIRS = [
    '/opt/local/etc/nginx/',
    '/usr/local/etc/nginx/',
    '/usr/local/etc/nginx/',
    '/usr/etc/nginx/',
]

EXAMPLE_MIME_TYPES = [
    '/opt/local/etc/nginx/mime.types',
    '/usr/local/etc/nginx/mime.types',
    '/usr/local/etc/nginx/mime.types',
    '/usr/etc/nginx/mime.types',
]

# proxy_intercept_errors on;
# recursive_error_pages on;

def _make_from_examples():
    # Check that there is an 'mime.types' and 'nginx.conf' file to load
    # TODO try nginx prefix first
    for d in CONF_DIRS:
        if exists(d):
            if not exists(d+"nginx.conf") and exists(d+"nginx.conf.example"):
                # fs.copy_file(p+"nginx.conf.example",p+"nginx.conf")
                Popen("sudo cp %s %s" % (p+"nginx.conf.example",p+"nginx.conf"), shell=True).communicate()
                print >>sys.stderr, "Created %s nginx.conf from example, please review A.S.A.P." % d
                break
            if not exists(d+"mime.types") and exists(d+"mime.types.example"):
                # fs.copy_file(p+"mime.types.example",p+"mime.types")
                Popen("sudo cp %s %s" % (d+"mime.types.example",d+"mime.types"), shell=True).communicate()
                print >>sys.stderr, "Created %s mime.types from example, please review A.S.A.P." % d
                break
            return d
    return None
    
    
def nginx_ensure_installed():
    nginx_path = Popen('which nginx', shell=True, stdout=PIPE).communicate()[0]
    if not nginx_path:
        raise EnvironmentError(1,'Please install nginx')

    d = _make_from_examples()
    
def nginx_installed():

    nginx_path = Popen('which nginx', shell=True, stdout=PIPE).communicate()[0]
    if not nginx_path:
        raise EnvironmentError(1,'Please install nginx')
    # print 'nginx', nginx_path

        
    # Check that there is an 'nginx.conf' file to load
    # Check that there is an 'mime.types' file to load
    d = _make_from_examples()
    
    # Check that there is a 'enabled' directory
    
    # Check that there is an 'error.log' file
        
    # TODO how to run -t while nginx is loaded
    
    #run 'sudo nginx -t' and verify result
    output,stderr = Popen('sudo nginx -t', shell=True, stdin=PIPE, stdout=PIPE, stderr=PIPE).communicate()

    #the configuration file /opt/local/etc/nginx/nginx.conf syntax is ok
    #configuration file /opt/local/etc/nginx/nginx.conf test is successful
    # print syntax
    print >>sys.stderr, str(stderr) #, str(stderr)
    #raise EnvironmentError(2,output) #"nginx isn't properly configured"

    if d is not None:
        fs.makedirs("/opt/local/etc/nginx/sites-enabled")       #TODO correct access attributes
    #TODO make sure nginx.conf end with an include enabled/*.conf
    
    #TODO nginx started
    # sudo launchctl -W load org.macports.nginx.plist
    # sudo launchctl start org.macports.nginx
    

def nginx_enabled(cluster_name=None,release_project_dir=None):
    """ Construct lines for the nginx enable configuration
    cluster_name By default use the cluster provided by 'structure.machine'
    release_project_dir By default use the project dir provided by 'structure'
    """
    cluster = cluster_name and structure.CLUSTERS[cluster_name] or structure.machine
    if release_project_dir:
        dirs = ProjectTree()
        basedir = join("/Sites",structure.PROJECT_NAME)
        dirs.apply_release_basedir(basedir,basedir)
    else:
        dirs = structure

    shard_domain = cluster['domains'][0]
    variables = { 
        'cluster_name': cluster_name,
        'cluster': structure.CLUSTERS[cluster_name],
        'shard_names': structure.SHARD_NAMES,
        'shards': [ dict(name=sn,domain="%s.%s" % (sn,shard_domain)) for sn in structure.SHARD_NAMES if not sn == "media" ],
        'dirs':dirs,
        'nginx_feature': features["nginx"],
        
        'project_name': structure.PROJECT_NAME,
        'domain':cluster['domains'][0],
        'port': cluster.get('upstream_port'),
        'socket': cluster.get('upstream_socket'),
        'protocol': cluster.get('upstream_protocol'),
        'log_dir': dirs.LOG_DIR, 
        'uploads_dir': dirs.UPLOADS_DIR,
        'downloads_dir': dirs.DOWNLOADS_DIR,
        'website_one': dirs.WEBSITE_DIRS[0], 
        'website_two': dirs.WEBSITE_DIRS[-1],
        'mediasite_one': dirs.MEDIASITE_DIRS[0], 
        'mediasite_two': dirs.MEDIASITE_DIRS[-1],
        'www_domains': ' '.join(['www.'+name for name in cluster['domains']]),
        'media_domains': ' '.join(['media.'+name for name in cluster['domains']]),
        'base_domains': ' '.join(cluster['domains']),
        'star_domains': ' '.join(['*.'+name for name in cluster['domains']]),
    }
    
    from django.template.loader import render_to_string
    rendered = render_to_string('themaestro/conf/nginxserver.conf', variables)

    return [rendered]
    
    
def symlink_local_nginx(cluster_names=('staged','dev')):
    for cluster_name in cluster_names:
        cluster = structure.CLUSTERS[cluster_name]
        enabled_conf_path = join(features["nginx"].NGINX_SITES_ENABLED, cluster['domains'][0]+".conf")
        conf_path = join(structure.CONF_DIR,"%s.nginx.conf" % cluster_name)
        fs.symlink(conf_path,enabled_conf_path,replace=True)
    
    fastcgi_path = join(features["nginx"].NGINX_ETC_DIR,'fastcgi.conf')
    geo_path = join(features["nginx"].NGINX_ETC_DIR,'geo.conf')
    fs.symlink(join(structure.CONF_DIR,'nginx.fastcgi.conf'),fastcgi_path,replace=True)
    #TODO fs.symlink(join(structure.CONF_DIR,'nginx.geo.conf'),fastcgi_path,replace=True)
    log_area.require_directory(structure.LOG_DIR)
    features["nginx"].reload()
    
def update_local_nginx(conf_lines):
    """ Save lines to local nginx enabled configuration and restart nginx
    """
    enabled_conf_path = join(features["nginx"].NGINX_SITES_ENABLED, structure.PROJECT_NAME+".local.conf")
    try:
        with open(enabled_conf_path,"w") as conf_file:
            conf_file.writelines(servers)
        # TODO make globally readable
#            if uid and gid:
#                os.chown(path, uid, gid)
        log_area.require_directory(structure.LOG_DIR)
        features["nginx"].reload()
        return
    except:
        raise Warning("Use sudo to modify %s" % feature.ETC_FILE)
    

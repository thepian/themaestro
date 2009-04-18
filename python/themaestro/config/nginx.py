from __future__ import with_statement
import fs
from os.path import exists, dirname, join, split

from thepian.conf import structure
from thepian.conf.project_tree import ProjectTree

from themaestro.conf import templates

# proxy_intercept_errors on;
# recursive_error_pages on;

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
        'nginx_feature': structure.features['nginx'],
        
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
        enabled_conf_path = join(structure.features['nginx'].NGINX_SITES_ENABLED, cluster['domains'][0]+".conf")
        conf_path = join(structure.CONF_DIR,"%s.nginx.conf" % cluster_name)
        fs.symlink(conf_path,enabled_conf_path,replace=True)
    
    fastcgi_path = join(structure.features['nginx'].NGINX_ETC_DIR,'fastcgi.conf')
    geo_path = join(structure.features['nginx'].NGINX_ETC_DIR,'geo.conf')
    fs.symlink(join(structure.CONF_DIR,'nginx.fastcgi.conf'),fastcgi_path,replace=True)
    #TODO fs.symlink(join(structure.CONF_DIR,'nginx.geo.conf'),fastcgi_path,replace=True)
    structure.machine.log_area.require_directory(structure.LOG_DIR)
    structure.features['nginx'].reload()
    
def update_local_nginx(conf_lines):
    """ Save lines to local nginx enabled configuration and restart nginx
    """
    enabled_conf_path = join(structure.features['nginx'].NGINX_SITES_ENABLED, structure.PROJECT_NAME+".local.conf")
    try:
        with open(enabled_conf_path,"w") as conf_file:
            conf_file.writelines(servers)
        # TODO make globally readable
#            if uid and gid:
#                os.chown(path, uid, gid)
        structure.machine.log_area.require_directory(structure.LOG_DIR)
        structure.features['nginx'].reload()
        return
    except:
        raise Warning("Use sudo to modify %s" % feature.ETC_FILE)
    

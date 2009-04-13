from __future__ import with_statement
from os.path import exists
from thepian.cmdline.base import ThepianCommand
from thepian.conf import structure
from optparse import make_option

from devonly.config.hosts import updated_hosts
from devonly.config.nginx import nginx_enabled, update_local_nginx, symlink_local_nginx

"""
hosts = Replace all DOMAINS entries in /etc/hosts with fresh ones
"""

class Command(ThepianCommand):
    option_list = ThepianCommand.option_list + (
        make_option('--restart', action='store_true', dest='restart', default=False,
            help='Tells Thepian to restart affected services if configuration changed.'),
    )
    help = 'Enables the dev/staged domains, linking the configuration files in conf'
    args = ''
    
    def handle(self, *modulenames, **options):
        from os.path import join
        try:
            hosts = updated_hosts(change_file=True)

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
            structure.machine.pid_area.require_directory(structure.PID_DIR)
            #sock_dir = "/var/tmp/django"
            #import fs,os,stat
            #fs.makedirs(sock_dir)
            #os.chmod(sock_dir,0777)
        except Warning, e:
            print self.style.NOTICE(e.message)
        except IOError, e:
            print self.style.ERROR(e.message)
            
        
        #TODO
        #self.require_directory(self.servers_dir, etc_uid, etc_gid, machine='nginx configuration directory')
        #self.require_directory(self.shards_dir, shard_uid, shard_gid, machine='shards root directory')
        

    
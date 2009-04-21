from __future__ import with_statement
from os.path import exists
from themaestro.commands import DjangoCommand
from thepian.conf import structure,settings
from optparse import make_option

from themaestro.config.hosts import updated_hosts
from themaestro.config.nginx import nginx_enabled, update_local_nginx, symlink_local_nginx

"""
hosts = Replace all DOMAINS entries in /etc/hosts with fresh ones
"""

class Command(DjangoCommand):
    option_list = DjangoCommand.option_list + (
        make_option('--restart', action='store_true', dest='restart', default=False,
            help='Tells Thepian to restart affected services if configuration changed.'),
    )
    help = 'Enables the directories and configuration needed for the developement/production environment'
    args = ''
    
    def handle(self, *modulenames, **options):
        try:
            #TODO create <project>/log dir for nginx 
            structure.machine.uploads_area.require_directory(structure.UPLOADS_DIR)
            structure.machine.downloads_area.require_directory(structure.DOWNLOADS_DIR)
            structure.machine.log_area.require_directory(structure.LOG_DIR)
            structure.machine.pid_area.require_directory(structure.PID_DIR)
            #sock_dir = "/var/tmp/django"
            #import fs,os,stat
            #fs.makedirs(sock_dir)
            #os.chmod(sock_dir,0777)

            if settings.DEVELOPING:
                from os.path import join
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
        except Warning, e:
            print self.style.NOTICE(e.message)
        except IOError, e:
            print self.style.ERROR(e.message)
            
        

    
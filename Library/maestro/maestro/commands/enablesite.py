from __future__ import with_statement
import fs
from thepian.conf import structure,settings
from optparse import make_option, OptionParser

from maestro.config.hosts import updated_hosts
from maestro.config.nginx import nginx_enabled, update_local_nginx, symlink_local_nginx, nginx_installed

"""
hosts = Replace all DOMAINS entries in /etc/hosts with fresh ones
"""

class Command(object):
    option_list = (
        # make_option('--restart', action='store_true', dest='restart', default=False,
        #     help='Tells Thepian to restart affected services if configuration changed.'),
    )
    help = 'Enables the directories and configuration needed for the developement/production environment'
    args = ''
    
    def get_version(self):
        return 0.1
        
    def create_parser(self, prog_name, subcommand):
        usage = '%%prog %s [options] %s' % (subcommand, self.args)
        usage = '%s\n\n%s' % (usage, self.help)
        return OptionParser(prog=prog_name,
                            usage=usage,
                            version=self.get_version(),
                            option_list=self.option_list)

    def __call__(self, *modulenames, **options):
        #TODO make sure memcached couchdb are started
        try:
            # is this needed? fs.symlink(structure.SCRIPT_PATH,'/usr/local/bin/maestro',replace=True)
            nginx_installed()
            #TODO create <project>/log dir for nginx 
            structure.ensure_target_dirs()
            structure.machine.uploads_area.require_directory(structure.UPLOADS_DIR)
            structure.machine.downloads_area.require_directory(structure.DOWNLOADS_DIR)
            structure.machine.log_area.require_directory(structure.LOG_DIR)
            structure.machine.pid_area.require_directory(structure.PID_DIR)
            #sock_dir = "/var/tmp/django"
            #import fs,os,stat
            #fs.makedirs(sock_dir)
            #os.chmod(sock_dir,0777)

            if settings.DEVELOPING:
                #TODO link in User Sites directory
                from os.path import join,exists,expanduser
                fs.symlink(structure.PROJECT_DIR,join(expanduser("~/Sites"),structure.PROJECT_NAME))
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
            
        


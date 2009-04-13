from __future__ import with_statement
#from thepian.cmdline.base import BaseCommand
from theapps.utils.djangoextras import DjangoCommand, CommandError
from os.path import join, exists
from optparse import make_option
import sys,os

from thepian.conf import structure
from devonly.conf import templates
from devonly.config.secrets import make_secrets
from devonly.config.nginx import nginx_enabled

class Command(DjangoCommand):
    option_list = DjangoCommand.option_list + (
        make_option('--verbosity', action='store', dest='verbosity', default='1',
            type='choice', choices=['0', '1', '2'],
            help='Verbosity level; 0=minimal output, 1=normal output, 2=all output'),
        make_option('--nochange', action='store_true', dest='nochange', default=False,
            help='Tells Thepian to NOT make changes of any kind.'),
    )
    help = 'Creates any missing conf files'
    args = ''
    
    def handle(self, *test_labels, **options):
        
        nochange = options.get('nochange',False)
        
        # Create a random SECRET_KEY hash, and put it in the main settings.
        main_secrets_file = join(structure.CONF_DIR, 'secrets.py')

        if not exists(main_secrets_file):
            if nochange:
                print 'secrets.py file missing'
            else:
                secrets_contents = make_secrets()
                with open(main_secrets_file, 'w') as secrets:
                    secrets.writelines(secrets_contents)

        servers_contents = nginx_enabled(cluster_name="live",release_project_dir=True)
        with open(join(structure.CONF_DIR,"live.nginx.conf"), 'w') as nginx_conf:
            nginx_conf.writelines(servers_contents)
            
        servers_contents = nginx_enabled(cluster_name="staged",release_project_dir=False)
        with open(join(structure.CONF_DIR,"staged.nginx.conf"), 'w') as nginx_conf:
            nginx_conf.writelines(servers_contents)
            
        servers_contents = nginx_enabled(cluster_name="dev",release_project_dir=False)
        with open(join(structure.CONF_DIR,"dev.nginx.conf"), 'w') as nginx_conf:
            nginx_conf.writelines(servers_contents)
            
            

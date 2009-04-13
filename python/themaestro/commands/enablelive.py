from __future__ import with_statement
from fs import symlink
from os.path import exists
from thepian.cmdline.base import ThepianCommand
from thepian.conf import structure
from optparse import make_option

from liveonly.config.nginx import symlink_local_nginx

"""
hosts = Replace all DOMAINS entries in /etc/hosts with fresh ones
"""

class Command(ThepianCommand):
    option_list = ThepianCommand.option_list + (
        make_option('--restart', action='store_true', dest='restart', default=False,
            help='Tells Thepian to restart affected services if configuration changed.'),
    )
    help = 'Enables the live domains, linking the configuration files in conf'
    args = ''
    
    def handle(self, *modulenames, **options):
        from os.path import join
        try:
            structure.machine.uploads_area.require_directory(structure.UPLOADS_DIR)
            structure.machine.downloads_area.require_directory(structure.DOWNLOADS_DIR)
            structure.machine.log_area.require_directory(structure.LOG_DIR)
            structure.machine.pid_area.require_directory(structure.PID_DIR)
            symlink_local_nginx()
                
        except Warning, e:
            print self.style.NOTICE(e.message)
        except IOError, e:
            print self.style.ERROR(e.message)
            
        
        

    
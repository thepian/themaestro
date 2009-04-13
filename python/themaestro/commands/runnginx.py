from thepian.cmdline.base import BaseCommand
from optparse import make_option
import sys,os
from os.path import exists,join,expanduser
from thepian.utils import *

class Command(BaseCommand):
    option_list = BaseCommand.option_list + (
        make_option('--verbosity', action='store', dest='verbosity', default='1',
            type='choice', choices=['0', '1', '2'],
            help='Verbosity level; 0=minimal output, 1=normal output, 2=all output'),
    )
    help = 'Ensure that the nginx server is running'
    args = ''
    
    nginx_plist = '/Library/LaunchDaemons/org.macports.nginx.plist'
    
    def handle(self, *test_labels, **options):
        from thepian.conf import structure
        
        if exists(self.nginx_plist):
            os.system('sudo launchctl load -w %s' % self.nginx_plist)
        else:
            print 'Cannot determine server control method'
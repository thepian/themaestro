from thepian.cmdline.base import BaseCommand
from optparse import make_option
import sys,os
from thepian.utils import *

class Command(BaseCommand):
    option_list = BaseCommand.option_list + (
        make_option('--verbosity', action='store', dest='verbosity', default='1',
            type='choice', choices=['0', '1', '2'],
            help='Verbosity level; 0=minimal output, 1=normal output, 2=all output'),
    )
    help = 'Specifies the host identity'
    args = ''
    
    def handle(self, *args, **options):
        from thepian.conf import structure
        
        print get_mac_addresses()
        print 'mac  '+get_mac_address_hex()
        print 'ip   '+get_ip4_address()
        if structure.machine.known:
            machine = structure.machine
            print 'name '+machine['nick'] + ' in ' + machine['cluster']
            print 'as   '+ ' '.join(machine['domains'] or [])

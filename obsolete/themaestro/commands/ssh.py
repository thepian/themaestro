from __future__ import with_statement

from thepian.cmdline.base import BaseCommand
from optparse import make_option
import sys,os
from thepian.utils import *
from thepian.utils.ssh import CryptoKey, get_authorized_keys, get_known_hosts, get_local_keys
from os.path import expanduser

class Command(BaseCommand):
    option_list = BaseCommand.option_list + (
        make_option('--verbosity', action='store', dest='verbosity', default='1',
            type='choice', choices=['0', '1', '2'],
            help='Verbosity level; 0=minimal output, 1=normal output, 2=all output'),
    )
    help = 'Manage ssh setup'
    args = 'add_machine'
    
    def handle(self, *modulenames, **options):
        for label in modulenames:
            (self.handlers.get(label,self.no_handler))(self,**options)

    def handle_show(self, **options):
        from thepian.conf import structure
        
        print 'Local SSH keys:'
        local = get_local_keys()
        for r in local:
            print r.condense(), r.key_type, r.user, getattr(r,'mac'), getattr(r,'username')
        print ''
        print 'Known hosts:'
        known = get_known_hosts()
        for k in known:
            print k.condense(), k.hosts
        print ''
        print 'Authorized keys:'
        auth_keys = get_authorized_keys()
        for key in auth_keys:
            print key.condensed, 'user', key.user, key.username, key.mac or ''
        print ''
        
    def handle_add_machine(self, **options):
        from thepian.conf import structure
        
        with open(expanduser('~/.ssh/id_rsa.pub')) as pub_key_file:
            pub_type, pub_key, pub_name = pub_key_file.readline().strip("\n").split(' ')
        structure.USERS = structure.USERS + ({
            'pub_rsa': pub_key.strip('=='),
            'mac': hex(uuid.getnode())[2:-1],
        },)
        #TODO Scan all id_.*\.pub files


    handlers = {
        'add_machine': handle_add_machine,
        'show': handle_show,
    }
    
    def no_handler(self,*args,**argm):
        print 'not implemented'


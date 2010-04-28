from __future__ import with_statement

import os
from os.path import expanduser, join

class CryptoKey(object):
    
    type_to_pub = {
        'ssh_rsa':'pub_rsa', 'ssh_dsa':'pub_dsa'
    }
    def normalise_type(self, t):
        return t.replace('+','_').replace('-','_')
        
    def __init__(self, key_type, key, user, hosts=''):
        self.key_type = self.normalise_type(key_type)
        self.key, self.user, self.hosts = key.strip('=='), user, hosts
        pub = self.type_to_pub.get(self.key_type,self.key_type)

        from thepian.conf import structure
        for u in structure.USERS:
            if u.get(pub) == self.key:
                self.mac = u.get('mac')
                self.username = u.get('username')
                
    def condense(self):
        return self.key[0:8] + '..' + self.key[-8:]
        
    condensed = property(condense)
                
def get_local_keys(ssh_dir='~/.ssh', file_name = r'id_.*\.pub'):
    key_files = [n for n in os.listdir(expanduser(ssh_dir)) if n.startswith('id_') and n.endswith('.pub')]
    res = []
    for fn in key_files:
        with open(join(expanduser(ssh_dir), fn)) as pub_key_file:
            res.append( CryptoKey(*pub_key_file.readline().strip("\n").split(' ')) )

    return res
        
def get_authorized_keys(file_name = '~/.ssh/authorized_keys2'):
    res = []
    with open(expanduser(file_name)) as keys:
        res = [CryptoKey(*key_line.strip('\n').split(' ')) for key_line in keys]
    return res

def get_known_hosts(file_name = "~/.ssh/known_hosts"):
    res = []
    with open(expanduser(file_name)) as known_file:
        for host in known_file:
            known_hosts, known_type, known_key = host.strip('\n').split(' ')
            res.append( CryptoKey(known_type, known_key, '', hosts=known_hosts) )
    return res


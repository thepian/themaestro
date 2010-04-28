from __future__ import with_statement
from thepian.cmdline.base import RemoteCommand
from optparse import make_option
import sys,os,uuid, select, fs
from os.path import join, exists, expanduser
from thepian.utils import *
from binascii import hexlify, b2a_base64

def run(t, cmd):
	'Open channel on transport, run command, capture output and return'
	out = ''
	chan = t.open_session()
	chan.setblocking(0)

	chan.exec_command(cmd)

	### Read when data is available
	while select.select([chan,], [], []):
		x = chan.recv(1024)
		if not x: break
		out += x
		select.select([],[],[],.1)
	
	chan.close()
	return out

def combine_keystring(user_dict):
    #TODO support multiple protocols
    return 'ssh-rsa ' + user_dict['pub_rsa'] + '== ' + user_dict['username'] + '@' + user_dict['machine'] + '\n'

class Command(RemoteCommand):
    #option_list = RemoteCommand.option_list + (,)
    help = 'Adds thepian to path locally and Uploads Thepian Configuration to remote hosts specified'
    
    def handle_local(self,options):
        from thepian.conf import structure
        fs.symlink(join(structure.PROJECT_DIR,"thepian"),join(structure.USR_BIN_DIR,"thepian"), replace=False)
        
    def handle_remote(self, transport, hostname, options):
        from thepian.conf import structure
        import paramiko

        'todo: /etc/init.d/memcached start'
        try:
            transport.start_client()
            server_key = transport.get_remote_server_key()
            # check server's host key -- this is important.
            #if --new make sure unknown, and add to known. else ensure known
            if not self.keys.has_key(hostname) or not self.keys[hostname].has_key(server_key.get_name()):
                if options['new']:
                    self.keys.add(hostname, server_key.get_name(), server_key)
                    #TODO update known_hosts instead
                    self.keys.save('~/.ssh/new_known_hosts')
                else:
                    print '*** WARNING: Unknown host key!', hostname
                    return
            elif self.keys[hostname][server_key.get_name()] != server_key:
                print '*** WARNING: Host key has changed!!!', hostname
                return
            else:
                print '*** Host key OK.', hostname

            
            # authenticate with password or public key
            username = options.get('user',self.username)
            password = options.get('password')
            if password:
                transport.auth_password(username or self.username, password)
            else:
                transport.auth_publickey(username, self.publickey)
        
            sftp = paramiko.SFTPClient.from_transport(transport)
            try:
                sftp.mkdir('.ssh/',mode=0770)
            except IOError, e:
                if str(e) != "Failure":
                    print 'cant make .ssh', e, type(e)
                
            #run(transport,'touch .ssh/authorized_keys2')
            authd_users = map(combine_keystring, structure.USERS)
            remote_keys = sftp.open('.ssh/authorized_keys2', mode='w+')
            remote_keys.writelines(authd_users)
            remote_keys.flush()
            remote_keys.close()
            
            # TODO upload /etc/apt/sources.list
            # need version without cd-rom
            print run(transport,'apt-get -qy install git-core git-doc curl mc')

            sftp.close()
            return
            sshdir = sftp.listdir('~/.ssh')
            print sshdir
            if len(filter(lambda i:i == 'authorized_keys2', sshdir)) == 0:
                print 'no auth file'
            stat = sftp.stat('~/.ssh/authorized_keys2')
            dir(stat)
            with sftp.open('~/.ssh/authorized_keys2', mode='a+') as remote_keys:
                lines = remote_keys.readlines()
                m = filter(lambda i: i == self.my_rsa_pub_line, lines)
                if len(m) > 0:
                    print 'Public RSA key is already authorized'
        
            #print run(transport, 'ls')
        except paramiko.SSHException:
            print '*** SSH negotiation failed.'
        except paramiko.BadAuthenticationType:
            print '*** Bad Authentication Type'
        except paramiko.AuthenticationException:
            print '*** Authentication Refused'
        except IOError,e:
            print '*** IO error',e

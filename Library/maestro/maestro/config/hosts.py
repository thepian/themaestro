from __future__ import with_statement
import os, socket, datetime
from os.path import exists, isfile, join
from thepian.conf import structure

from base import features, Feature


def install():
    """Called by install_features() if listed in structure.FEATURES"""
    from thepian.conf import settings
    if settings.DEVELOPING:
        hosts = updated_hosts(change_file=True)

class HostsFeature(Feature):
    name = "hosts"
    
    def __init__(self,structure):
        etc_file = "/etc/hosts"
        if exists(etc_file):
            self.ETC_FILE = etc_file
            self.found = True

# register hosts in features
hosts = HostsFeature(structure)
if hosts.found:
    features["hosts"] = hosts


    
def make_domain_list(domain,shard_names):
    return [(sub+"."+domain,sub) for sub in ('www',structure.MEDIA_SUBDOMAIN) + tuple(shard_names)]

def updated_hosts(change_file=False):
    domains = list(structure.CLUSTERS['dev']['domains']) + list(structure.CLUSTERS['staged']['domains'])
    
    if not os.access(features["hosts"].ETC_FILE,os.R_OK):
        raise IOError("Need to be able to read %s" % features["hosts"].ETC_FILE)
            
    newhosts = []
    with open(features["hosts"].ETC_FILE,"r") as hosts_file:
        hosts = hosts_file.readlines()
        for line in hosts:
            s = line.split()
            skip = False
            if len(s):
                if s[0].startswith("### Modified by Thepian"):
                    skip = True
                if not s[0].startswith("#"):
                    try:
                        socket.inet_aton(s[0]) # make sure its an ip hostname definition line
                        for name in domains:
                            if s[-1].endswith(name):
                                skip = True
                    except Exception, e:
                        pass #print e
            if not skip: newhosts.append(line)
    
        newhosts.insert(0,'### Modified by Thepian %s\n' % datetime.datetime.today().isoformat(' '))
        for public_domain in domains:
            newhosts.extend( ["127.0.0.1\t" + name + '\n' 
                for name,sub in make_domain_list(
                    public_domain.strip("."),
                    structure.SHARD_NAMES  + structure.DEDICATED_SHARD_NAMES
                    )
                ] )
               
    if change_file:
        try:
            with open(features["hosts"].ETC_FILE,"w") as hosts_file:
                hosts_file.writelines(newhosts)
            return
        except:
            raise Warning("Use sudo to modify %s" % feature.ETC_FILE)
    return newhosts
    

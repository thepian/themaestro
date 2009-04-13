from __future__ import with_statement
import os, socket, datetime
#from warnings import Warning
#from devonly.conf import templates

from thepian.conf import structure
    
def make_domain_list(domain,shard_names):
    return [(sub+"."+domain,sub) for sub in ('www',structure.MEDIA_SUBDOMAIN) + tuple(shard_names)]

def updated_hosts(change_file=False):
    feature = structure.features['hosts']
    domains = list(structure.CLUSTERS['dev']['domains']) + list(structure.CLUSTERS['staged']['domains'])
    
    if not os.access(feature.ETC_FILE,os.R_OK):
        raise IOError("Need to be able to read %s" % feature.ETC_FILE)
            
    newhosts = []
    with open(feature.ETC_FILE,"r") as hosts_file:
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
            with open(feature.ETC_FILE,"w") as hosts_file:
                hosts_file.writelines(newhosts)
            return
        except:
            raise Warning("Use sudo to modify %s" % feature.ETC_FILE)
    return newhosts
    

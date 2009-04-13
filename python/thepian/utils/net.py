import binascii,socket

# loopback?,network?,nas?,internet?
INTERFACES = {
    'lo' : (True,False,False,False),'lo0' : (True,False,False,False),'lo1' : (True,False,False,False),'lo2' : (True,False,False,False),
    
    'fw0' : (False,False,True,False), 'fw1' : (False,False,True,False), 'fw2' : (False,False,True,False),
    
    'en0' : (False,True,False,True),'en1' : (False,True,False,True),'en2' : (False,True,False,True),'en3' : (False,True,False,True),'en4' : (False,True,False,True),
    'en5' : (False,True,False,True),'en6' : (False,True,False,True),'en7' : (False,True,False,True),'en8' : (False,True,False,True),'en9' : (False,True,False,True),
    
    'eth0' : (False,True,False,True),'eth0:1' : (False,True,False,True),'eth0:2' : (False,True,False,True),'eth0:3' : (False,True,False,True),'eth0:4' : (False,True,False,True),
    'eth0:5' : (False,True,False,True),'eth0:6' : (False,True,False,True),'eth0:7' : (False,True,False,True),
    
    'eth1' : (False,True,False,True),'eth1:1' : (False,True,False,True),'eth1:2' : (False,True,False,True),'eth1:3' : (False,True,False,True),'eth1:4' : (False,True,False,True),
    'eth1:5' : (False,True,False,True),'eth1:6' : (False,True,False,True),'eth1:7' : (False,True,False,True),
    
    'eth2' : (False,True,False,True),'eth2:1' : (False,True,False,True),'eth2:2' : (False,True,False,True),'eth2:3' : (False,True,False,True),'eth2:4' : (False,True,False,True),
    'eth2:5' : (False,True,False,True),'eth2:6' : (False,True,False,True),'eth2:7' : (False,True,False,True),
}

def get_ip4_addresses(ifname=None):
    try:
        import netifaces
        if ifname:
            return (netifaces.ifaddresses(ifname)[2][0]['addr'],)
        else:
            addresses = []
            for ifce in netifaces.interfaces():
                if_props = INTERFACES.get(ifce) or (False,False,False,False)
                if_addrs = netifaces.ifaddresses(ifce)
                #print ifce, if_addrs, if_props
                mac = if_addrs.get(17) or if_addrs.get(18)
                ip4 = if_addrs.get(2)
                ip6 = if_addrs.get(30)
                if if_props[1] and if_props[3] and ip4:
                    addresses.append(ip4[0]['addr'])
            return addresses
    except Exception, e:
        return (socket.gethostbyname(socket.gethostname()),)
        
def get_ip4_address(ifname=None):
    return get_ip4_addresses(ifname)[0]

def get_mac_addresses(ifname=None,ignore_nas=True,with_ip4=False):
    """By default ignore stuff like firewire"""
    try:
        import netifaces
        if ifname:
            info = netifaces.ifaddresses(ifname)
            return ((info.get(18) or info.get(17))[0]['addr'],)
        else:
            addresses = []
            for ifce in netifaces.interfaces():
                if_props = INTERFACES.get(ifce) or (False,False,False,False)
                if_addrs = netifaces.ifaddresses(ifce)
                #print ifce, if_addrs, if_props
                if ignore_nas and if_props[2]: continue
                if not if_props[1]: continue
                ip4 = if_addrs.get(2)
                ip6 = if_addrs.get(30)
                if with_ip4 and not ip4: continue
                mac = if_addrs.get(17) or if_addrs.get(18)
                if mac:
                    addresses.append(mac[0]['addr'])
            return addresses
    except Exception, e:
        import uuid
        # bit primitive, and not stable on mac
        m = hex(uuid.getnode())[2:-1].zfill(12)
        return ( ':'.join((m[0:1],m[2:3],m[4:5],m[6:7],m[8:9],m[10:11])), )

def get_mac_address(ifname=None,ignore_nas=True,with_ip4=False):
    return get_mac_addresses(ifname)[0]
    
def get_mac_address_hex():
    return get_mac_address().replace(':','').lstrip('0')
    
def ip4_to_ip6(ip4):
    ip_hex = binascii.hexlify(socket.inet_aton(ip4))
    return '2002:0000:0000:0000:0000:0000:%s:%s' % (ip_hex[:4],ip_hex[4:]) 
    
    
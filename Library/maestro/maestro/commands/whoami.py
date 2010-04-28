import sys,os,net

class Command(object):
    option_list = ()
    help = 'Specifies the host identity'
    args = ''
    
    def handle(self, *args, **options):
        from thepian.conf import structure
        
        print net.get_mac_addresses()
        print 'mac  '+net.get_mac_address_hex()
        print 'ip   '+net.get_ip4_address()
        if structure.machine.known:
            machine = structure.machine
            print 'name '+machine['NICK'] + ' in ' + machine['cluster']
            print 'as   '+ ' '.join(machine['domains'] or [])

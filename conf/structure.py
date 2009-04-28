# This is a settings file used by the shard-admin.py

ADMINS = (
    ('Henrik Vendelbo', 'hvendelbo.dev@googlemail.com'),
)

DEFAULT_SITE_TITLE = "Thepian Maestro Site"
DEFAULT_HOSTNAME = "www.themaestro.local"

CLUSTERS = {
    'live': { 'domains': ('themaestro.thepia.net',), 
        'media':'media.themaestro.thepia.net',
        'upstream_protocol': 'fastcgi', 'upstream_port': '8881', 
        'upstream_socket': '/tmp/themaestro', 'EMAIL_HOST':'localhost',
        'shard_user':'thepian', 'shard_group':'thepian',
        'etc_user':'thepian', 'etc_group':'thepian',
        'log_user':'www-data','log_group':'adm'
        }, 
    'staged': { 'domains': ('themaestro.local',), 
        'media':'media.themaestro.local', 'EMAIL_HOST':'localhost',
        'upstream_protocol': 'fastcgi', 'upstream_port': '8881', 
        'upstream_socket': '/tmp/themaestro',
        'shard_user':'thepian', 'shard_group':'thepian',
        'etc_user':'thepian', 'etc_group':'thepian',
        'log_user':'thepian','log_group':'nobody'
        },
    'dev': { 'domains': ('themaestro.dev.local',), 
        'media':'media.themaestro.dev.local',
        'upstream_protocol': 'http', 'upstream_port': '8000', 
        'EMAIL_HOST':'smtp.ntlworld.com',
        'shard_user':'root', 'shard_group':'admin',
        'etc_user':'root', 'etc_group':'admin',
        'log_user':'root','log_group':'nobody'
        }, 
}


#? simple division shard= subdomain, cluster = domain, site = tld ?? sites = ('net','com', 'co.uk')
SERVERS = (
    { 'mac':'1cb374a89f', 'pool_ip':'192.168.9.104', 'own_ip':'192.168.9.94', 'cluster':'dev', 'NICK': "imac2", },
    { 'mac':'1b639c1367', 'pool_ip':'192.168.9.104', 'own_ip':'192.168.9.94', 'cluster':'dev', 'NICK': "imac", },
    { 'mac':'1b63aa4556', 'pool_ip':'192.168.9.105', 'own_ip':'192.168.9.95', 'cluster':'dev', 'NICK': "tinkerbell", },
    { 'mac':'16a45', 'pool_ip':'192.168.9.105', 'own_ip':'192.168.9.95', 'cluster':'dev', 'NICK': "tinkerbell", },

    { 'mac':'1e8c6bd607', 'pool_ip':'83.170.98.113', 'own_ip':'83.170.93.136', 'cluster':'live', 'NICK': "s1", 'shards': ('aa','ab','ac','ad','ae','af','ag','ah','ai','aj','ak','al',) },
    { 'mac':'1b639c13??1', 'pool_ip':'192.168.9.61', 'own_ip':'192.168.9.51', 'cluster':'test', 'NICK': "test1", 'shards': ('aa','ab','ac','ad','ae','af',) },
    { 'mac':'1b639c13??2', 'pool_ip':'192.168.9.62', 'own_ip':'192.168.9.52', 'cluster':'test', 'NICK': "test2", 'shards': ('ag','ah','ai','aj','ak','al',) },
    { 'mac':'1b639c13??3', 'pool_ip':'192.168.9.63', 'own_ip':'192.168.9.53', 'cluster':'test', 'NICK': "test3", 'shards': ('aa','ab','ac','ad','ae','af',) },
    { 'mac':'1b639c13??4', 'pool_ip':'192.168.9.64', 'own_ip':'192.168.9.54', 'cluster':'test', 'NICK': "test4", 'shards': ('ag','ah','ai','aj','ak','al',) },
)

DEV_MACHINES = ('192.168.9.94', '192.168.9.95')

SHARD_NAMES = ('media',)

AFFINITY_SECRET = 'y!tv568)ouw7ixt85)vfq#9*r7^#sr1)p%o0m45e#bmn3td0_u'

ETC_SYMLINKS = (
    ('nginx.fastcgi.conf','%(NGINX_ETC_DIR)s/fastcgi.conf'),
    ('nginx.geo.conf','%(NGINX_ETC_DIR)s/geo.conf'),
    ('extra.nginx.conf','%(NGINX_SITES_ENABLED)s/extra.nginx.conf'),
    ('live.nginx.conf','%(NGINX_SITES_ENABLED)s/live.%(PROJECT_NAME)s.conf'),
)
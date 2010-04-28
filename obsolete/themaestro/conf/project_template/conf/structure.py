# This is a settings file used by the shard-admin.py

ADMINS = (
    ('Henrik Vendelbo', 'hvendelbo.dev@googlemail.com'),
)

DEFAULT_SITE_TITLE = "{{ project_name }} Site"
DEFAULT_HOSTNAME = "www.{{ project_name }}.local"

CLUSTERS = {
    'live': { 'domains': ('{{ project_name }}.com','{{ project_name }}.net','{{ project_name }}.thepia.net',), 
        'media':'media.{{ project_name }}.thepia.net',
        'upstream_protocol': 'fastcgi', 'upstream_port': '{{ django_port }}', 
        'upstream_socket': '/tmp/{{ project_name }}', 'email_host':'localhost',
        'shard_user':'thepian', 'shard_group':'thepian',
        'etc_user':'thepian', 'etc_group':'thepian',
        'log_user':'www-data','log_group':'adm'
        }, 
    'staged': { 'domains': ('{{ project_name }}.staged.local',), 
        'media':'media.{{ project_name }}.staged.local',
        'upstream_protocol': 'fastcgi', 'upstream_port': '{{ django_port }}', 
        'upstream_socket': '/tmp/{{ project_name }}',
        'shard_user':'thepian', 'shard_group':'thepian',
        'etc_user':'thepian', 'etc_group':'thepian',
        'log_user':'thepian','log_group':'nobody'
        },
    'dev': { 'domains': ('{{ project_name }}.local',), 
        'media':'media.{{ project_name }}.local',
        'upstream_protocol': 'http', 'upstream_port': '8000', 'email_host':'smtp.ntlworld.com',
        'shard_user':'root', 'shard_group':'admin',
        'etc_user':'root', 'etc_group':'admin',
        'log_user':'root','log_group':'nobody'
        }, 
}


#? simple division shard= subdomain, cluster = domain, site = tld ?? sites = ('net','com', 'co.uk')
SERVERS = (
    { 'mac':'1cb374a89f', 'pool_ip':'192.168.9.104', 'own_ip':'192.168.9.94', 'cluster':'dev', 'nick': "imac2", },
    { 'mac':'1b639c1367', 'pool_ip':'192.168.9.104', 'own_ip':'192.168.9.94', 'cluster':'dev', 'nick': "imac", },
    { 'mac':'1b63aa4556', 'pool_ip':'192.168.9.105', 'own_ip':'192.168.9.95', 'cluster':'dev', 'nick': "tinkerbell", },

    { 'mac':'1e8c6bd607', 'pool_ip':'83.170.98.113', 'own_ip':'83.170.93.136', 'cluster':'live', 'nick': "s1", 'shards': ('aa','ab','ac','ad','ae','af','ag','ah','ai','aj','ak','al',) },
    { 'mac':'1b639c13??1', 'pool_ip':'192.168.9.61', 'own_ip':'192.168.9.51', 'cluster':'test', 'nick': "test1", 'shards': ('aa','ab','ac','ad','ae','af',) },
    { 'mac':'1b639c13??2', 'pool_ip':'192.168.9.62', 'own_ip':'192.168.9.52', 'cluster':'test', 'nick': "test2", 'shards': ('ag','ah','ai','aj','ak','al',) },
    { 'mac':'1b639c13??3', 'pool_ip':'192.168.9.63', 'own_ip':'192.168.9.53', 'cluster':'test', 'nick': "test3", 'shards': ('aa','ab','ac','ad','ae','af',) },
    { 'mac':'1b639c13??4', 'pool_ip':'192.168.9.64', 'own_ip':'192.168.9.54', 'cluster':'test', 'nick': "test4", 'shards': ('ag','ah','ai','aj','ak','al',) },
)

DEV_MACHINES = {{ dev_machines }}

SHARD_NAMES = ('aa','ab','ac','ad','ae','af','ag','ah','ai','aj','ak','al',)

# Allows you to tie a particular affinity number to a shard name
# By default the shard is determined by: number % len(SHARD_NAMES)
SHARD_AFFINITY = {
#    'aa' : (1, 2, 3, 4),
#    'ak' : (5,77,222)
}

AFFINITY_SECRET = ''

ETC_SYMLINKS = (
    ('nginx.fastcgi.conf','%(NGINX_ETC_DIR)s/fastcgi.conf'),
    ('nginx.geo.conf','%(NGINX_ETC_DIR)s/geo.conf'),
    ('extra.nginx.conf','%(NGINX_SITES_ENABLED)s/extra.nginx.conf'),
    ('live.nginx.conf','%(NGINX_SITES_ENABLED)s/live.%(PROJECT_NAME)s.conf'),
)
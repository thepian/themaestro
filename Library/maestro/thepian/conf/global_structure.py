# This is a settings file used by the site-admin.py and shard.py

REPOSITORIES_PATH = "/repositories"

FEATURES = ()

TUPLE_STRUCTURE = ("CLUSTERS", "SERVERS", "DEV_MACHINES", "SHARD_NAMES", "DEDICATED_SHARD_NAMES" )

# Must be defined by the project. Must contain at least one cluster definition. The first entry is used as the default for unknown servers/nodes
CLUSTERS = {}

# Fallback cluster (possibly being removed in the future)
# Default for machine if CLUSTERS are not overridden in structure.py
FALLBACK_CLUSTER = { 'domains': ('thepian-config.net',),
    'upstream_protocol': 'http', 'upstream_port': '8000',
    'shard_user':'root', 'shard_group':'admin',
    'etc_user':'root', 'etc_group':'admin',
    'log_user':'root','log_group':'nobody'
    } 


# Must be defined by the project. Must contain an entry for each machine in the cluster
SERVERS = ()

# Names of META data passed with the request, TODO support tuples of possible names
HTTP_HOST_VARIABLE = "HTTP_HOST"
HTTP_COUNTRY_VARIABLE = "HTTP_COUNTRY"

DEFAULT_SITE_TITLE = "The Thepia Site"

# Default HOSTNAME if not supplied by the http webserver
DEFAULT_HOSTNAME = "www.thepia.local"

MEDIA_SUBDOMAIN = 'media'

# Used by create command to build settings.py
ADMIN_NAME = "Henrik Vendelbo"
ADMIN_EMAIL = "hvendelbo.dev@googlemail.com"

THEPIAN_EMAIL = "thepian@thepia.com"

# Used by create command to build structure.py and settings.py
DEV_MACHINES = ('192.168.9.94','192.168.9.95',)

DJANGO_PORT = 8881

MEDIASERVER_PORT = 8889

# Used by thepian.conf.Affinity to assign a random affinity number
# This number cannot be changed once a cluster is deployed, it is also restricted to an 64k integer
# The square root is taken to spread it on two directory levels
AFFINITY_NUMBER_MAX = 9 * 9 * 16 * 25 
AFFINITY_NUMBER_SPLIT = 3 * 3 * 4 * 5

# The number of names should be evenly divisible into the AFFINITY_NO_MAX
SHARD_NAMES = ('aa','ab','ac','ad','ae','af','ag','ah','ai','aj','ak','al',)

# These are shards which are dedicated to specific afinity numbers defined by SHARD_AFFINITY
DEDICATED_SHARD_NAMES = ()

# Allows you to tie a particular affinity number to a shard name
# By default the shard is determined by: number % len(SHARD_NAMES)
SHARD_AFFINITY = {
#    'aa' : (1, 2, 3, 4),
#    'ak' : (5,77,222)
}

#TODO factor out
AFFINITY_EXPIRY = "Mdy, 01-Jan-2038 00:00:00 GMT"

# Used to encode affinity checksum, this must be overridden in structure.py for anything going live
AFFINITY_SECRET = "some random number"

THUMBNAIL_PROCESSORS = (
    'thepian.assets.processors.colorspace',
    'thepian.assets.processors.autocrop',
    'thepian.assets.processors.scale_and_crop',
    'thepian.assets.processors.filters',
)

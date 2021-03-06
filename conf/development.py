DEVELOPING = True
DEBUG = DEVELOPING
TEMPLATE_DEBUG = DEBUG
EMAIL_DEBUG = DEBUG
# Record page generation statistics and put spread, then pull on demand, flagging page with identifier
TRACE = DEBUG

DATABASE_ENGINE = 'sqlite3'
DATABASE_NAME = '/Sites/themaestro/devdb'
DATABASE_USER = ''
DATABASE_PASSWORD = ''
DATABASE_HOST = ''
DATABASE_PORT = ''

DOMAINS = ('themaestro.dev.local',)
MEDIA_DOMAIN = 'media.themaestro.dev.local'

from settings import *

MEDIA_URL = 'http://media.themaestro.dev.local'
ADMIN_MEDIA_PREFIX = MEDIA_URL+'/admin/'
TEMPLATE_DIRS = (
    # Put strings here, like "/home/html/django_templates" or "C:/www/django/templates".
    # Always use forward slashes, even on Windows.
    # Don't forget to use absolute paths, not relative paths.
    '/Sites/themaestro/templates',
)
EMAIL_HOST = 'smtp.ntlworld.com'
SERVER_EMAIL = "tinkerbell@thepia.net"
INTERNAL_IPS = INTERNAL_IPS + ('192.168.9.95',)

try:
    from thepian.conf import structure
    from os.path import join

    DATABASE_NAME = join(structure.PROJECT_DIR,'devdb')
    TEMPLATE_DIRS = (
        structure.TEMPLATES_DIR,
        # structure.SAMPLE_TEMPLATES_DIR,
    )
    INTERNAL_IPS = INTERNAL_IPS + structure.DEV_MACHINES
    FILEBROWSER_PATH_SERVER = structure.DOWNLOADS_DIR + "/"
    #print FILEBROWSER_PATH_SERVER
    FILEBROWSER_URL_WWW = MEDIA_URL
    #SUBDOMAINS = structure.SHARD_NAMES + ('www','media')
except Exception,e:
    pass
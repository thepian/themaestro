#from thepian.conf import structure

from os.path import join

DEVELOPING = True
DEBUG = DEVELOPING
TEMPLATE_DEBUG = DEBUG
EMAIL_DEBUG = DEBUG
# Record page generation statistics and put spread, then pull on demand, flagging page with identifier
TRACE = DEBUG

DATABASE_ENGINE = 'sqlite3'
#DATABASE_NAME = join(structure.PROJECT_DIR,'devdb')
DATABASE_NAME = '/Users/hvendelbo/Sites/themaestro/devdb'
DATABASE_USER = ''
DATABASE_PASSWORD = ''
DATABASE_HOST = ''
DATABASE_PORT = ''

from settings import *

#MEDIA_URL = structure.machine.MEDIA_URL
MEDIA_URL = 'http://media.themaestro.dev.local'
ADMIN_MEDIA_PREFIX = MEDIA_URL+'/admin/'
TEMPLATE_DIRS = (
    # Put strings here, like "/home/html/django_templates" or "C:/www/django/templates".
    # Always use forward slashes, even on Windows.
    # Don't forget to use absolute paths, not relative paths.
    #structure.TEMPLATES_DIR,
    '/Users/hvendelbo/Sites/themaestro/templates',
    # structure.SAMPLE_TEMPLATES_DIR,
)
#EMAIL_HOST = structure.machine.EMAIL_HOST
EMAIL_HOST = 'smtp.ntlworld.com'
#SERVER_EMAIL = structure.machine.NICK + "@thepia.net"
SERVER_EMAIL = "tinkerbell@thepia.net"
#INTERNAL_IPS = INTERNAL_IPS + structure.DEV_MACHINES
INTERNAL_IPS = INTERNAL_IPS + ('192.168.9.95',)
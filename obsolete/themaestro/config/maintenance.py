from __future__ import with_statement
from os.path import join
import codecs
from thepian.conf import structure

SETTING_NAMES = ('MEDIA_URL','SITE_TITLE')

def create_maintenance():
    from django.template.loader import render_to_string
    from django.conf import settings
    variables = { }
    for n in SETTING_NAMES: variables[n] = getattr(settings,n)
    variables['MEDIA_URL'] = structure.CLUSTERS['live']['media']
    rendered = render_to_string('503.html', variables)
    maintenance_path = join(structure.TARGET_DIR,"website","503.html")
    with codecs.open(maintenance_path,"w","utf-8") as m_file:
        m_file.write(rendered)

from os.path import join
from django import template
from django.utils.safestring import mark_safe
from django.conf import settings

register = template.Library()

def openid_icon(user):
    return ''
    from django_openid.models import UserOpenidAssociation
    oid = u'%s' % user.active_openid
    #TODO change this silly implementation
    matches = [u.openid == oid for u in UserOpenidAssociation.objects.filter(user=user)]
    if any(matches):
        return mark_safe(u'<img src="%s" alt="Logged in with OpenID" />' % join(settings.MEDIA_URL,'openid-icon.png'))
    else:
        return u''
register.simple_tag(openid_icon)
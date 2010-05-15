from django.contrib import admin
from django.contrib.auth.models import User
from models import ActivationRecord, EmailAddress, EmailConfirmation, Profile
from django.utils.translation import ugettext_lazy as _

admin.site.register(EmailAddress)
admin.site.register(EmailConfirmation)
admin.site.register(Profile)

from django.contrib.auth.models import Group
from django.contrib.auth.admin import UserAdmin


class ActivationRecordAdmin(admin.ModelAdmin):
    list_display = ('user', 'date')
    search_fields = ('user',)
    list_filter = ('user', 'date')

admin.site.register(ActivationRecord,ActivationRecordAdmin)

class AccountUserAdmin(UserAdmin):
    fieldsets = (
        (None, {'fields': ('username', 'password')}),
        (_('OpenID'), {'fields': ('openid','only_openid')}),
        (_('Personal info'), {'fields': ('first_name', 'last_name', 'profile_type')}),
        (_('Permissions'), {'fields': ('is_staff', 'is_active', 'is_superuser', 'user_permissions')}),
        (_('Important dates'), {'fields': ('last_login', 'date_joined')}),
        (_('Groups'), {'fields': ('groups',)}),
    )
    list_display = ('username', 'openid', 'only_openid', 'first_name', 'last_name', 'is_staff','profile_type')
    list_filter = ('is_staff', 'is_superuser')
    search_fields = ('username', 'first_name', 'last_name', 'openid')

admin.site.register(User,AccountUserAdmin)

try:
    from django_openid.models import UserOpenidAssociation
    admin.site.register(UserOpenidAssociation)
except ImportError:
    pass
from django.db import models
from django.core.exceptions import ImproperlyConfigured
from django.conf import settings
from django.contrib.auth.models import get_hexdigest, check_password, Group, Permission, UserTemplate, UNUSABLE_PASSWORD
from django.utils.translation import ugettext_lazy as _

from datetime import datetime, timedelta
import urllib

from theapps.supervisor.fields import *
from managers import UserManager

PROFILE_MODEL_CHOICES = [(c,c) for c in settings.AUTH_PROFILE_MODELS]    
        
class User(UserTemplate):
    """Users within the Django authentication system are represented by this model.

    Username and password are required. Other fields are optional.
    """
    id = IdentityField(_('userid'), auto_generate=True, primary_key=True, 
        help_text=_("Combination of visiting ip, current time and random"))
    username = models.CharField(_('username'), max_length=30, unique=True, 
        help_text=_("Required. 30 characters or fewer. Alphanumeric characters only (letters, digits and underscores)."))
    openid = models.CharField(_('primary openid'),max_length=255, 
        help_text=_("Having a primary allows a quick OpenID login"), blank=True)
    only_openid = models.BooleanField(_("only use openid"), default=False, 
        help_text=_("If set password login isn't allowed, only using an openid."))
    first_name = models.CharField(_('first name'), max_length=30, blank=True, 
        help_text=_("Real first name"))
    last_name = models.CharField(_('last name'), max_length=30, blank=True, 
        help_text=_("Real last name"))
    password = models.CharField(_('password'), max_length=128, 
        help_text=_("Use '[algo]$[salt]$[hexdigest]' or use the <a href=\"password/\">change password form</a>."))
    is_staff = models.BooleanField(_('staff status'), default=False, 
        help_text=_("Designates whether the user can log into this admin site."))
    is_active = models.BooleanField(_('active'), default=True, 
        help_text=_("Designates whether this user should be treated as active. Unselect this instead of deleting accounts."))
    is_superuser = models.BooleanField(_('superuser status'), default=False, 
        help_text=_("Designates that this user has all permissions without explicitly assigning them."))
    profile_type = models.CharField(_("profile type"),max_length=50,blank=True,choices=PROFILE_MODEL_CHOICES,
        help_text=_("The model used as a profile"))
    last_login = models.DateTimeField(_('last login'), default=datetime.now)
    date_joined = models.DateTimeField(_('date joined'), default=datetime.now)
    groups = models.ManyToManyField(Group, verbose_name=_('groups'), blank=True,
        help_text=_("In addition to the permissions manually assigned, this user will also get all permissions granted to each group he/she is in."))
    user_permissions = models.ManyToManyField(Permission, verbose_name=_('user permissions'), blank=True)
    #TODO created on device affinity
    
    objects = UserManager()

    class Meta:
        app_label = "auth"
        db_table = "account_user"

    def save(self):
        if not hasattr(self,"id") or  not self.id:
            self.id = generate_identity()
            
        super(User,self).save()

    def __unicode__(self):
        return self.username

    def get_absolute_url(self):
        return "/users/%s/" % urllib.quote(smart_str(self.username))

    def get_full_name(self):
        "Returns the first_name plus the last_name, with a space in between."
        full_name = u'%s %s' % (self.first_name, self.last_name)
        return full_name.strip()

    def set_password(self, raw_password):
        import random
        algo = 'sha1'
        salt = get_hexdigest(algo, str(random.random()), str(random.random()))[:5]
        hsh = get_hexdigest(algo, salt, raw_password)
        self.password = '%s$%s$%s' % (algo, salt, hsh)

    def check_password(self, raw_password):
        """
        Returns a boolean of whether the raw_password was correct. Handles
        encryption formats behind the scenes.
        """
        # Backwards-compatibility check. Older passwords won't include the
        # algorithm or salt.
        if '$' not in self.password:
            is_correct = (self.password == get_hexdigest('md5', '', raw_password))
            if is_correct:
                # Convert the password to the new, more secure format.
                self.set_password(raw_password)
                self.save()
            return is_correct
        return check_password(raw_password, self.password)

    def set_unusable_password(self):
        # Sets a value that will never be a valid hash
        self.password = UNUSABLE_PASSWORD

    def has_usable_password(self):
        return self.password != UNUSABLE_PASSWORD
        
    def get_email(self):
        primary = self.emailaddress_set.filter(primary=True)[:1]
        return len(primary) == 1 and primary[0].email or None
    email = property(get_email)

    def email_user(self, subject, message, from_email=None):
        "Sends an e-mail to this User."
        #TODO use the EmailAddressManager
        from django.core.mail import send_mail
        send_mail(subject, message, from_email, [self.email])
        
    def get_profile_model(self):
        """
        Returns the model class for the user. Raises SiteProfileNotAvailable if this site does not allow profiles."""
        from django.contrib.auth.models import SiteProfileNotAvailable
        if self.profile_type:
            app_label, model_name = self.profile_type.split('.')
        else:
            from django.conf import settings
            if not settings.AUTH_PROFILE_MODULE:
                raise SiteProfileNotAvailable
            app_label, model_name = settings.AUTH_PROFILE_MODULE.split('.')
        try:
            return models.get_model(app_label, model_name)
        except (ImportError, ImproperlyConfigured):
            raise SiteProfileNotAvailable
        
    def get_profile(self):
        """
        Returns site-specific profile for this user. Raises
        SiteProfileNotAvailable if this site does not allow profiles.
        """
        if not hasattr(self, '_profile_cache'):
            from django.contrib.auth.models import SiteProfileNotAvailable
            try:
                self._profile_cache = self.get_profile_model()._default_manager.get(user__id__exact=self.id)
            except (ImportError, ImproperlyConfigured):
                raise SiteProfileNotAvailable
        return self._profile_cache

    
    def get_or_create_profile(self):
        model = self.get_profile_model()
        assert model, "User %s cannot determine profile model of type %s" % (self.pk,self.profile_type)
        try:
            return model._default_manager.get(user__id__exact=self.id)
        except model.DoesNotExist:
            p = model()
            p.user = self
            p.save()
            self._profile_cache = p
            return p
    
    def get_active_openid(self):
        return None
    active_openid = property(get_active_openid)
    

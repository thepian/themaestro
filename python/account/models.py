from django.db import models, IntegrityError
from django.template.loader import render_to_string
from django.conf import settings
from django.contrib.auth.models import Group, Permission

from django.utils.translation import ugettext_lazy as _

from datetime import datetime, timedelta
from random import random
import hashlib

from django.core.urlresolvers import reverse

from thepian.conf import structure

# favour django-mailer but fall back to django.core.mail
try:
    from mailer import send_mail
except ImportError:
    from django.core.mail import send_mail
try:
    import pytz
    TIMEZONE_CHOICES = zip(pytz.common_timezones, pytz.common_timezones)
except ImportError:
    TIMEZONE_CHOICES = {}
    
from managers import *

ACTIVATION_RECORD_TYPES = (('A', 'Activation'),
                       ('R', 'Password reset'),
                       ('E', 'Email change'),
                       ('C', 'Comment approve')
                       )

class ActivationRecord(models.Model):
    """Record that holds activation_key generated upon user registration"""
    user = models.ForeignKey("auth.User")
    activation_key = models.CharField(max_length=40)
    date = models.DateTimeField(auto_now_add=True)
    type = models.CharField(max_length=1, choices=ACTIVATION_RECORD_TYPES)

    objects = models.Manager()
    registrations = RegistrationManager()
    #resets = ResetManager()
    #emails = EmailManager()
    #approvals = ApprovalManager()

    def __unicode__(self):
        return u"%s record for %s" % (self.get_type_display(), self.user.email)

    @property
    def expired(self):
        """
        Determines whether this Profile's activation key has expired,
        based on the value of the setting ``ACTIVATION_RECORD_DAYS``.

        Set ``ACTIVATION_RECORD_DAYS`` in 0 to disable expiring
        """
        if hasattr(settings,"ACTIVATION_RECORD_DAYS"):
            expiration_date = timedelta(days=settings.ACTIVATION_RECORD_DAYS)
            return self.date + expiration_date <= datetime.now()
        else:
            return False

    class Meta:
        db_table = 'account_activation'
        verbose_name = _('activation record')
        verbose_name_plural = _('activation records')

# this code based in-part on django-registration


#TODO http://code.djangoproject.com/changeset/8283
#TODO http://code.djangoproject.com/changeset/8280

class EmailAddressManager(models.Manager):

    def add_email(self, user, email):
        try:
            email_address = self.create(user=user, email=email)
            EmailConfirmation.objects.send_confirmation(email_address)
            return email_address
        except IntegrityError:
            return None

    def get_primary(self, user):
        try:
            return self.get(user=user, primary=True)
        except EmailAddress.DoesNotExist:
            return None


class EmailAddress(models.Model):
    
    user = models.ForeignKey("auth.User")
    email = models.EmailField()
    verified = models.BooleanField(default=False)
    primary = models.BooleanField(default=False)
    
    objects = EmailAddressManager()
    
    def set_as_primary(self, conditional=False):
        old_primary = EmailAddress.objects.get_primary(self.user)
        if old_primary:
            if conditional:
                return False
            old_primary.primary = False
            old_primary.save()
        self.primary = True
        self.save()
        return True
    
    def __unicode__(self):
        return u"%s (%s)" % (self.email, self.user)
    
    class Meta:
        unique_together = (
            ("user", "email"),
        )
    




class EmailConfirmationManager(models.Manager):
    
    def confirm_email(self, confirmation_key):
        try:
            confirmation = self.get(confirmation_key=confirmation_key)
        except self.model.DoesNotExist:
            return None
        if not confirmation.key_expired():
            email_address = confirmation.email_address
            email_address.verified = True
            email_address.set_as_primary(conditional=True)
            email_address.save()
            return email_address
    
    def send_confirmation(self, email_address):
        salt = hashlib.sha1(str(random())).hexdigest()[:5]
        confirmation_key = hashlib.sha1(salt + email_address.email).hexdigest()
        site = structure.machine.get_default_site()
        activate_url = u"http://%s%s" % (
            site.domain,
            reverse("acct_confirm_email", args=(confirmation_key,))
        )
        vars = {
        "site": site,
        "user": email_address.user,
        "activate_url": activate_url,
        }
        subject = render_to_string("account/email_confirmation_subject.txt", vars)
        message = render_to_string("account/email_confirmation_message.txt", vars)
        send_mail(subject, message, settings.DEFAULT_FROM_EMAIL, [email_address.email])
        
        return self.create(email_address=email_address, sent=datetime.now(), confirmation_key=confirmation_key)
    
    def delete_expired_confirmations(self):
        for confirmation in self.all():
            if confirmation.key_expired():
                confirmate.delete()

class EmailConfirmation(models.Model):
    
    email_address = models.ForeignKey(EmailAddress)
    sent = models.DateTimeField()
    confirmation_key = models.CharField(max_length=40)
    
    objects = EmailConfirmationManager()
    
    def key_expired(self):
        expiration_date = self.sent + timedelta(days=settings.EMAIL_CONFIRMATION_DAYS)
        return expiration_date <= datetime.now()
    key_expired.boolean = True
    
    def __unicode__(self):
        return u"confirmation for %s" % self.email_address
    

class MinimumProfile(models.Model):
    user = models.ForeignKey("auth.User", unique=True, verbose_name=_('user'))
    name = models.CharField(_('name'), max_length=50, null=True, blank=True,help_text=_("Public name"))
    nick = models.SlugField(_("nick name"), help_text=_('Used in urls'), unique=True)
    area = models.CharField(_("geographic area"),max_length=35)
    #TODO language
    
    class Meta:
        abstract = True
        
    def set_defaults(self):
        from django.template.defaultfilters import slugify
        if not self.name:
            self.name = " ".join((self.user.first_name,self.user.last_name))
        if not self.nick:
            self.nick = (self.name and len(self.name)>1 and slugify(self.name)) or self.user.username
        if not self.area:
            pass #TODO determine from ip of user

class Profile(MinimumProfile):
    # move to personal/talent app
    # current picture, picture history, thumbnail props
    about = models.TextField(_('about'), null=True, blank=True)
    location = models.CharField(_('location'), max_length=40, null=True, blank=True)
    website = models.URLField(_('website'), null=True, blank=True)
    blogrss = models.URLField(_('blog rss/atom'), null=True, blank=True)
    timezone = models.CharField(_('timezone'), max_length=100,
        choices=TIMEZONE_CHOICES, default=settings.TIME_ZONE)
    
    def __unicode__(self):
        return self.name or self.nick
        
    def __repr__(self):
        return unicode(self)

    class Meta:
        verbose_name = _('profile')
        verbose_name_plural = _('profiles')
        
    def save(self):
        if not self.pk:
            self.set_defaults()
        super(Profile,self).save()



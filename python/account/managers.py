import re
from datetime import datetime, timedelta

from django.conf import settings
from django.db import models, IntegrityError
from django.contrib.auth.models import UserManager as DefaultUserManager

from theapps.supervisor.fields import generate_identity

class UserManager(DefaultUserManager):

    def suggest_user(self, username, email, name):
        """Suggest usernames based on registration information
        
        Returns (username_available,username_list)"""
        if len(name.split(' '))>0:
            sp = name.split(' ')
            first_name = sp[0].lower()
            last_name = sp[-1].lower()
        else:
            first_name = name.lower()
            last_name = ''
        try:
            email_user = re.match("([^@]+)@.*",email).group(1)
        except Exception,e:
            email_user = email
    
        available = True
        if username is not None:
            if len(self.filter(username=username)[:1]) > 0:
                available = False
        suggest_src = [ first_name, email_user, first_name[:1]+last_name,first_name+'_'+last_name,first_name+last_name, last_name ]
        # TODO add with increasing numbers
        suggest = []
        for s in suggest_src:
            if len(self.filter(username=s)) == 0: # TODO strip those with illegal signs or blank
                suggest.append(s)
                
        return available, suggest
        
        
    def create_user(self, username, email, password=None, name=None):
        "Creates and saves a User with the given username, e-mail and password."
        now = datetime.now()
        if username == "thepian":
            id = self.THEPIAN_USER_PK
        else:
            id = generate_identity()
        
        if name:
            first_name = name.split(' ')[0]
            last_name = name.split(' ')[-1]
        else:
            first_name = ''
            last_name = ''
        user = self.model(id, username, '', False, first_name, last_name, 'placeholder', False, True, False, '', now, now)
        if password:
            user.set_password(password)
        else:
            user.set_unusable_password()
        user.save()
        if email:
            user.emailaddress_set.create(email=email.strip().lower(),primary=True)
        return user

    THEPIAN_USER_PK = "2002000000000000000000007f000001000455a06adc9f97648f"

class RegistrationManager(models.Manager):
    """
    Custom manager for the ActionRecord.
    Holds registrations.
    """

    def get_query_set(self):
        """Custom queryset"""
        return super(RegistrationManager, self).get_query_set().filter(type='A')

    def activate_user(self, activation_key):
        """
        Given the activation key, makes a User's account active if the
        activation key is valid and has not expired.

        Returns the User if successful, or False if the account was
        not found or the key had expired.
        """
        # Make sure the key we're trying conforms to the pattern of a
        # SHA1 hash; if it doesn't, no point even trying to look it up
        # in the DB.
        if re.match('[a-f0-9]{40}', activation_key):
            try:
                record = self.get(activation_key=activation_key)
            except self.model.DoesNotExist:
                return False
            if not record.expired:
                # Account exists and has a non-expired key. Activate it.
                user = record.user
                user.is_active = True
                user.save()
                for comment in user.comments.filter(approved=False):
                    comment.approved = True
                    comment.save()
                record.delete()
                return user
        return False

    def create_inactive_user(self, name, email, password, site='', send_email=True):
        """
        Creates a new User and a new ActionRecord for that
        User, generates an activation key, and mails it.

        Pass ``send_email=False`` to disable sending the email.

        You can disable email_sending in settings: DISABLE_REGISTRATION_EMAIL=True

        """
        from django.contrib.auth.models import User
        send_email = not getattr(settings, 'DISABLE_REGISTRATION_EMAIL', False)

        # Create the user.
        new_user = User(username=email.replace('@', '-'), email=email, first_name=name)
        new_user.set_password(password)
        new_user.is_active = False
        new_user.site = site
        new_user.save()

        # Generate a salted SHA1 hash to use as a key.
        salt = sha.new(str(random.random())).hexdigest()[:5]
        activation_key = sha.new(salt+slugify(new_user.email)).hexdigest()

        # And finally create the record.
        new_record = self.create(user=new_user,
                                 activation_key=activation_key,
                                 type='A')
        if send_email:
            if Site._meta.installed:
                current_site = Site.objects.get_current()
            else:
                current_site = RequestSite(request) #TODO import Site/RequestSite ?
            current_domain = current_site.domain
            subject = "Activate your new account at %s" % current_domain
            message_template = loader.get_template('accounts/activation_email.txt')
            message_context = Context({ 'site_url': '%s://%s' % (settings.SITE_PROTOCOL, current_domain),
                                        'activation_key': activation_key,
                                        'expiration_days': settings.ACTION_RECORD_DAYS,
                                        'password': password,
                                        'user': new_user})
            message = message_template.render(message_context)
            new_user.email_user(subject, message, settings.DEFAULT_FROM_EMAIL)
        return new_user

    def create_user(self, name, email, password, site='', send_email=True, openid=None):
        """
        Create a new User, activate it, send email about password

        You can disable email_sending in settings: DISABLE_REGISTRATION_EMAIL=True
        """
        send_email = send_email and not getattr(settings, 'DISABLE_REGISTRATION_EMAIL', False)

        # Create the user.
        if openid:
            username = openid[7:37]
        else:
            username = email.replace('@', '-')
        new_user = User(username=username, email=email, first_name=name)
        new_user.set_password(password)
        new_user.is_active = True
        new_user.site = site
        new_user.save()

        if send_email:
            current_domain = Site.objects.get_current().domain
            subject = "Your new account at %s has been created" % current_domain
            message_template = loader.get_template('accounts/created_email.txt')
            message_context = Context({'site_url': '%s://%s' % (settings.SITE_PROTOCOL, current_domain),
                                        'password': password,
                                        'user': new_user})
            message = message_template.render(message_context)
            new_user.email_user(subject, message, settings.DEFAULT_FROM_EMAIL)
        return new_user

    def delete_expired_users(self):
        """
        Removes unused records and their associated accounts.

        This is provided largely as a convenience for maintenance
        purposes; if a ActionRecord's key expires without the
        account being activated, then both the ActionRecord and
        the associated User become clutter in the database, and (more
        importantly) it won't be possible for anyone to ever come back
        and claim the username. For best results, set this up to run
        regularly as a cron job.

        It is not so important for this (byteflow) application,
        because only email is important here.

        If you have a User whose account you want to keep in the
        database even though it's inactive (say, to prevent a
        troublemaker from accessing or re-creating his account), just
        delete that User's ActionRecord and this method will
        leave it alone.

        """
        for record in self.all():
            if record.expired:
                user = record.user
                if not user.is_active:
                    user.delete()


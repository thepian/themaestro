import re
import sha
import random
import datetime

from pytils.translit import slugify
from django.db import models
from django.contrib.sites.models import Site
from django.contrib.auth.models import User
from django.template import Context, loader
from django.conf import settings


class ResetManager(models.Manager):
    """
    Custom manager for ActionRecord.
    Holds password resets.
    """

    def get_query_set(self):
        """Custom queryset"""
        return super(ResetManager, self).get_query_set().filter(type='R')

    def password_reset(self, activation_key, send_email=True):
        """
        Given activation key will reset user password and mail it to
        user's email if key is valid and not expired.

        Returns the User if successful, or None if the account was
        not found or the key had expired.

        Pass ``send_email=False`` to disable sending the email.
        """
        # Make sure the key we're trying conforms to the pattern of a
        # SHA1 hash; if it doesn't, no point even trying to look it up
        # in the DB.
        if not re.match('[a-f0-9]{40}', activation_key):
            return None
        try:
            record = self.get(activation_key=activation_key)
        except self.model.DoesNotExist:
            return None
        if record.expired:
            return None
        # Key valid and not expired. Reset password.
        user = record.user
        import os, binascii
        password = binascii.b2a_base64(os.urandom(6)).strip()
        user.set_password(password)
        user.save()
        if send_email:
            from django.core.mail import send_mail
            current_domain = Site.objects.get_current().domain
            subject = "Your password at %s resetted" % current_domain
            message_template = loader.get_template('accounts/resetted_email.txt')
            message_context = Context({ 'site_url': '%s://%s/' % (settings.SITE_PROTOCOL, current_domain),
                                        'password': password,
                                        'user': user})
            message = message_template.render(message_context)
            user.email_user(subject, message, settings.DEFAULT_FROM_EMAIL)
        record.delete()
        return user

    def create_password_reset(self, user, send_email=True):
        """
        Create ActionRecord for password reset and mails link
        with activation key to user's email.

        Pass ``send_email=False`` to disable sending the email.
        """
        # Generate a salted SHA1 hash to use as a key.
        salt = sha.new(str(random.random())).hexdigest()[:5]
        activation_key = sha.new(salt+user.email).hexdigest()

        # And finally create the record.
        record, created = self.get_or_create(user=user,
                                             type='R',
                                             defaults={'activation_key': activation_key})

        if send_email:
            from django.core.mail import send_mail
            current_domain = Site.objects.get_current().domain
            subject = "Reset your password at %s" % current_domain
            message_template = loader.get_template('accounts/reset_email.txt')
            message_context = Context({ 'site_url': '%s://%s/' % (settings.SITE_PROTOCOL, current_domain),
                                        'activation_key': record.activation_key,
                                        'expiration_days': settings.ACTION_RECORD_DAYS,
                                        'user': user})
            message = message_template.render(message_context)
            user.email_user(subject, message, settings.DEFAULT_FROM_EMAIL)
        return record

    def delete_expired_records(self):
        """Removes unused expired password reset records"""
        for record in self.all():
            if record.expired:
                record.delete()

class EmailManager(models.Manager):
    """
    Custom manager for ActionRecord model.
    Holds email changes.
    """
    def get_query_set(self):
        """Custom queryset, returns only ActionRecords for password resets"""
        return super(EmailManager, self).get_query_set().filter(type='E')

    def change_email(self, activation_key):
        """
        Given activation key will change user email if key
        is valid and not expired.

        Returns the User if successful, or None if the account was
        not found or the key had expired.
        """
        # Make sure the key we're trying conforms to the pattern of a
        # SHA1 hash; if it doesn't, no point even trying to look it up
        # in the DB.
        if not re.match('[a-f0-9]{40}', activation_key):
            return None
        try:
            record = self.get(activation_key=activation_key)
        except self.model.DoesNotExist:
            return None
        if record.expired:
            return None
        # Key valid and not expired. Change email.
        user = record.user
        if user.email_new:
            user.email = user.email_new
            user.email_new = ''
        user.save()
        record.delete()
        return user

    def create_email_change(self, user, new_email, send_email=True):
        """
        Create ActionRecord for email change and mails link
        with activation key to user's email.

        Pass ``send_email=False`` to disable sending the email.
        """
        # Generate a salted SHA1 hash to use as a key.
        salt = sha.new(str(random.random())).hexdigest()[:5]
        activation_key = sha.new(salt+user.email).hexdigest()

        # And finally create the record.
        user.email_new = new_email
        user.save()
        record, created = self.get_or_create(user=user,
                                             type='E',
                                             defaults={'activation_key': activation_key})

        if send_email:
            current_domain = Site.objects.get_current().domain
            subject = "Change your email address at %s" % current_domain
            message_template = loader.get_template('accounts/password_reset.txt')
            message_context = Context({'site_url': '%s://%s/' % (settings.SITE_PROTOCOL, current_domain),
                                       'activation_key': record.activation_key,
                                       'expiration_days': settings.ACTION_RECORD_DAYS,
                                       'user': user})
            message = message_template.render(message_context)
            user.email_user(subject, message, settings.DEFAULT_FROM_EMAIL)
        return record

    def delete_expired_records(self):
        """Removes unused expired password reset records"""
        for record in self.all():
            if record.expired:
                record.delete()


class ApprovalManager(models.Manager):
    """Custom manager for ActionRecord. Holds comment approving"""

    def get_query_set(self):
        """Custom queryset, returns only ActionRecords for comment approvals"""
        return super(ApprovalManager, self).get_query_set().filter(type='C')

    def send_approval(self, comment, send_email=True):
        """Sends approval request for non-approved comment."""
        if comment.approved:
            return

        # Generate a salted SHA1 hash to use as a key.
        salt = sha.new(str(random.random())).hexdigest()[:5]
        activation_key = sha.new(salt+comment.user.email.encode('utf-8')).hexdigest()

        record = self.create(user=comment.user, type='C', activation_key=activation_key)

        if send_email:
            current_domain = Site.objects.get_current().domain
            subject = "Approve your comment at %s" % current_domain
            message_template = loader.get_template('accounts/approve_comment.txt')
            message_context = Context({'site_url': '%s://%s' % (settings.SITE_PROTOCOL, current_domain),
                                        'activation_key': record.activation_key,
                                        'expiration_days': settings.ACTION_RECORD_DAYS,
                                        'user': comment.user})
            message = message_template.render(message_context)
            comment.user.email_user(subject, message)
        return record

    def approve_comment(self, activation_key):
        if re.match('[a-f0-9]{40}', activation_key):
            try:
                record = self.get(activation_key=activation_key)
            except self.model.DoesNotExist:
                return False
            if not record.expired:
                for comment in record.user.comments.filter(approved=False):
                    comment.approved = True
                    comment.save()
                record.delete()
                return comment
            else:
                record.delete()
        return False


    def delete_expired_records(self):
        """Removes unused expired comment approve records"""
        for record in self.all():
            if record.expired:
                record.delete()

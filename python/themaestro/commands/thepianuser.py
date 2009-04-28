"""
Management utility to create thepian superuser.
"""

import os
import re
import sys
from optparse import make_option
from django.contrib.auth.models import User, check_password
from django.core.management.base import BaseCommand, CommandError
from django.template.loader import render_to_string

from django.conf import settings
from thepian.conf import structure

from django.core.mail import send_mail

RE_VALID_USERNAME = re.compile('\w+$')

class Command(BaseCommand):
    option_list = BaseCommand.option_list + (
        make_option('--username', dest='username', default=None,
            help='Specifies the username for the superuser.'),
        make_option('--email', dest='email', default=None,
            help='Specifies the email address for the superuser.'),
        make_option('--noemail', action='store_true', dest='noemail', default=False,
            help='Tells Thepian to NOT send any email.'),
    )
    help = 'Used to ensure the thepian superuser. Use the label reset to force a password reset'

    def handle(self, *args, **options):
        username = options.get('username', None) or 'thepian'
        email = options.get('email', None) or structure.THEPIAN_EMAIL
        from_email = structure.machine.MACHINE_EMAIL
        password = User.objects.make_random_password()

        try:
            superuser = User.objects.filter(username=username)[0:1].get()
            already_there = True
        except User.DoesNotExist,e:
            superuser = User.objects.create_superuser(username, email, password)
            already_there = False
            
        if "reset" in args or not already_there:
            if already_there:
                superuser.set_password(password)
                superuser.save()
            subject = "Thepian kode: %s = %s" % (structure.DEFAULT_HOSTNAME,password)
            message = render_to_string("account/created_superuser.txt", {
                "user": superuser,
                "new_password": password,
                "structure": structure,
            })
            if options.get("noemail",False):
                print "Superuser created succesfully, code %s" % password
            else:
                send_mail(subject, message, from_email, [email])
                print "Superuser created successfully. thepian notified about %s" % password
        else:
            print "log in as superuser thepian, email=%s id=%s" % (superuser.email,superuser.id)

from django import forms
from django.template.loader import render_to_string
from django.conf import settings
from django.utils.translation import ugettext_lazy as _, ugettext

import re
alnum_re = re.compile(r'^\w+$') 
# favour django-mailer but fall back to django.core.mail
try:
    from mailer import send_mail
except ImportError:
    from django.core.mail import send_mail

from django.contrib.auth import authenticate, login
from django.contrib.auth.models import User

from theapps.utils.forms import Form
from models import EmailAddress
from fields import *

try:
    import pytz
    TIMEZONE_CHOICES = zip(pytz.common_timezones, pytz.common_timezones)
except ImportError:
    print 'Failed to import pytz, no timezone choices available'
    TIMEZONE_CHOICES = {'UTC':'UTC'}
    
class LoginForm(Form):
    
    username = forms.CharField(label=_("Username"), max_length=30, widget=forms.TextInput())
    password = forms.CharField(label=_("Password"), widget=forms.PasswordInput(render_value=False))
    
    user = None
    
    def clean(self):
        if self._errors:
            return
        user = authenticate(username=self.cleaned_data["username"], password=self.cleaned_data["password"])
        if user:
            if user.is_active:
                self.user = user
            else:
                raise forms.ValdidationError(_("This account is currently inactive."))
        else:
            raise forms.ValidationError(_("The username and/or password you specified are not correct."))
        return self.cleaned_data
    
    def login(self, request):
        if self.is_valid():
            login(request, self.user)
            request.user.message_set.create(message=ugettext(u"Successfully logged in as %(username)s.") % {'username': self.user.username})
            return True
        return False

class SignupForm(Form):
    name = forms.CharField(label=_("Full name"), max_length=50, widget=forms.TextInput(attrs={"size":30}))
    email = forms.EmailField(label=_("Email"), required=False, widget=forms.TextInput(attrs={"size":30}))
    username = forms.CharField(label=_("Username"), max_length=30, widget=TextWithSuggestionsInput())
    password1 = forms.CharField(label=_("Password"), widget=forms.PasswordInput(render_value=False))
    password2 = forms.CharField(label=_("Password (again)"), widget=forms.PasswordInput(render_value=False))
    confirmation_key = forms.CharField(max_length=40, required=False, widget=forms.HiddenInput())
    
    def clean_username(self):
        if not alnum_re.search(self.cleaned_data["username"]):
            raise forms.ValidationError(_("Usernames can only contain letters, numbers and underscores."))
        try:
            user = User.objects.get(username__exact=self.cleaned_data["username"])
        except User.DoesNotExist:
            return self.cleaned_data["username"]
        raise forms.ValidationError(_("This username is already taken. Please choose another."))
    
    def clean(self):
        if "password1" in self.cleaned_data and "password2" in self.cleaned_data:
            if self.cleaned_data["password1"] != self.cleaned_data["password2"]:
                raise forms.ValidationError(_("You must type the same password each time."))
        return self.cleaned_data
    
    def save(self):
        name = self.cleaned_data["name"]
        username = self.cleaned_data["username"]
        email = self.cleaned_data["email"]
        password = self.cleaned_data["password1"]
        if self.cleaned_data["confirmation_key"]:
            try:
                #TODO change to ActivationRecord & tickets
                join_invitation = JoinInvitation.objects.get(confirmation_key = self.cleaned_data["confirmation_key"])
                confirmed = True
            except JoinInvitation.DoesNotExist:
                confirmed = False
        else:
            confirmed = False
        
        if confirmed:
            if email == join_invitation.contact.email:
                new_user = User.objects.create_user(username, email, password, name=name)
                new_user.message_set.create(message=ugettext(u"Your email address has already been verified"))
                # already verified so can just create
                EmailAddress(user=new_user, email=email, verified=True, primary=True).save()
            else:
                new_user = User.objects.create_user(username, "", password, name=name)
                if email:
                    new_user.message_set.create(message=ugettext(u"Confirmation email sent to %(email)s") % {'email': email})
                    EmailAddress.objects.add_email(new_user, email)
            join_invitation.accept(new_user)
            return username, password # required for authenticate()
        else:
            new_user = User.objects.create_user(username, "", password, name=name)
            if email:
                new_user.message_set.create(message=ugettext(u"Confirmation email sent to %(email)s") % {'email': email})
                EmailAddress.objects.add_email(new_user, email)
            return username, password # required for authenticate()
    
    def as_dl(self):
        "Returns this form rendered as HTML <dt>s and <dd>s -- excluding the <dl></dl>."
        return self._html_output(u'<dt>%(label)s</dt> <dd>%(errors)s%(field)s%(help_text)s</dd>', u'<dd>%s</dd>', '</dd>', u' %s', False)
            

class UserForm(Form):
    
    def __init__(self, *args, **kwargs):
        if "user" in kwargs:
            self.user = kwargs["user"]
            del kwargs["user"]
        super(UserForm, self).__init__(*args, **kwargs)

class ProfileForm(UserForm):
    
    def __init__(self, *args, **kwargs):
        super(ProfileForm, self).__init__(*args, **kwargs)
        self.profile = self.user.get_profile()


class AddEmailForm(UserForm):
    
    email = forms.EmailField(label=_("Email"), required=True, widget=forms.TextInput(attrs={'size':'30'}))
    
    def clean_email(self):
        try:
            EmailAddress.objects.get(user=self.user, email=self.cleaned_data["email"])
        except EmailAddress.DoesNotExist:
            return self.cleaned_data["email"]
        raise forms.ValidationError(_("This email address already associated with this account."))
    
    def save(self):
        self.user.message_set.create(message=ugettext(u"Confirmation email sent to %(email)s") % {'email': self.cleaned_data["email"]})
        return EmailAddress.objects.add_email(self.user, self.cleaned_data["email"])


class ChangePasswordForm(UserForm):
    
    oldpassword = forms.CharField(label=_("Current Password"), widget=forms.PasswordInput(render_value=False))
    password1 = forms.CharField(label=_("New Password"), widget=forms.PasswordInput(render_value=False))
    password2 = forms.CharField(label=_("New Password (again)"), widget=forms.PasswordInput(render_value=False))
    
    def clean_oldpassword(self):
        if not self.user.check_password(self.cleaned_data.get("oldpassword")):
            raise forms.ValidationError(_("Please type your current password."))
        return self.cleaned_data["oldpassword"]
    
    def clean_password2(self):
        if "password1" in self.cleaned_data and "password2" in self.cleaned_data:
            if self.cleaned_data["password1"] != self.cleaned_data["password2"]:
                raise forms.ValidationError(_("You must type the same password each time."))
        return self.cleaned_data["password2"]
    
    def save(self):
        self.user.set_password(self.cleaned_data['password1'])
        self.user.save()
        self.user.message_set.create(message=ugettext(u"Password successfully changed."))


class ResetPasswordForm(Form):
    
    email = forms.EmailField(label=_("Email"), required=True, widget=forms.TextInput(attrs={'size':'30'}))
    
    def clean_email(self):
        if EmailAddress.objects.filter(email__iexact=self.cleaned_data["email"], verified=True).count() == 0:
            raise forms.ValidationError(_("Email address not verified for any user account"))
        return self.cleaned_data["email"]
    
    def save(self):
        for user in User.objects.filter(email__iexact=self.cleaned_data["email"]):
            new_password = User.objects.make_random_password()
            user.set_password(new_password)
            user.save()
            subject = _("Password reset")
            message = render_to_string("account/password_reset_message.txt", {
                "user": user,
                "new_password": new_password,
            })
            send_mail(subject, message, settings.DEFAULT_FROM_EMAIL, [user.email])
        return self.cleaned_data["email"]

class ChangeTimezoneForm(ProfileForm):
    
    timezone = forms.ChoiceField(label=_("Timezone"), required=True, choices=TIMEZONE_CHOICES)
    
    def __init__(self, *args, **kwargs):
        super(ChangeTimezoneForm, self).__init__(*args, **kwargs)
        self.initial.update({"timezone": self.profile.timezone})
    
    def save(self):
        self.profile.timezone = self.cleaned_data["timezone"]
        self.profile.save()
        self.user.message_set.create(message=ugettext(u"Timezone successfully updated."))

from account.models import Profile

class ProfileForm(forms.ModelForm):

    class Meta:
        model = Profile
        exclude = ('user', 'timezone')



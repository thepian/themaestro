import re
from django.shortcuts import render_to_response, get_object_or_404
from django.http import HttpResponseRedirect, HttpResponse, HttpResponseForbidden
from django.template import RequestContext
from django.views.decorators.cache import cache_page, never_cache, cache_control

from django.core.urlresolvers import reverse
from django.conf import settings
from django.utils import simplejson
from django.utils.translation import ugettext_lazy as _, ugettext

from django.contrib.auth import authenticate, login as auth_login
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User

from models import Profile
from forms import ProfileForm

from forms import SignupForm, AddEmailForm, LoginForm, ChangePasswordForm, ResetPasswordForm, ChangeTimezoneForm
from models import EmailAddress, EmailConfirmation



def login(request):
    redirect_to = request.REQUEST.get("next", reverse("private_profile"))
    if request.method == "POST":
        form = LoginForm(request.POST)
        if form.login(request):
            return HttpResponseRedirect(redirect_to)
    else:
        form = LoginForm()
    return render_to_response("account/login.html", {
        "form": form,
    }, context_instance=RequestContext(request))

def signup(request):
    if request.method == "POST":
        form = SignupForm(request.POST)
        if form.is_valid():
            username, password = form.save()
            user = authenticate(username=username, password=password)
            auth_login(request, user)
            request.user.message_set.create(message=_("Successfully logged in as %(username)s.") % {'username': user.username})
            return HttpResponseRedirect("/")
    else:
        form = SignupForm()
    return render_to_response("account/signup.html", {
        "form": form,
    }, context_instance=RequestContext(request))

@login_required
def email(request):
    if request.method == "POST" and request.user.is_authenticated():
        if request.POST["action"] == "add":
            add_email_form = AddEmailForm(request.user, request.POST)
            if add_email_form.is_valid():
                add_email_form.save()
                add_email_form = AddEmailForm() # @@@
        else:
            add_email_form = AddEmailForm()
            if request.POST["action"] == "send":
                email = request.POST["email"]
                try:
                    email_address = EmailAddress.objects.get(user=request.user, email=email)
                    request.user.message_set.create(message="Confirmation email sent to %s" % email)
                    EmailConfirmation.objects.send_confirmation(email_address)
                except EmailAddress.DoesNotExist:
                    pass
            elif request.POST["action"] == "remove":
                email = request.POST["email"]
                try:
                    email_address = EmailAddress.objects.get(user=request.user, email=email)
                    email_address.delete()
                    request.user.message_set.create(message="Removed email address %s" % email)
                except EmailAddress.DoesNotExist:
                    pass
            elif request.POST["action"] == "primary":
                email = request.POST["email"]
                email_address = EmailAddress.objects.get(user=request.user, email=email)
                email_address.set_as_primary()
    else:
        add_email_form = AddEmailForm()
    
    return render_to_response("account/email.html", {
        "add_email_form": add_email_form,
    }, context_instance=RequestContext(request))

@login_required
def password_change(request):
    if request.method == "POST":
        password_change_form = ChangePasswordForm(request.user, request.POST)
        if password_change_form.is_valid():
            password_change_form.save()
            password_change_form = ChangePasswordForm(request.user)
    else:
        password_change_form = ChangePasswordForm(request.user)
    return render_to_response("account/password_change.html", {
        "password_change_form": password_change_form,
    }, context_instance=RequestContext(request))
password_change = login_required(password_change)

def password_reset(request):
    if request.method == "POST":
        password_reset_form = ResetPasswordForm(request.POST)
        if password_reset_form.is_valid():
            email = password_reset_form.save()
            return render_to_response("account/password_reset_done.html", {
                "email": email,
            }, context_instance=RequestContext(request))
    else:
        password_reset_form = ResetPasswordForm()
    
    return render_to_response("account/password_reset.html", {
        "password_reset_form": password_reset_form,
    }, context_instance=RequestContext(request))

@login_required
def timezone_change(request):
    if request.method == "POST":
        form = ChangeTimezoneForm(request.user, request.POST)
        if form.is_valid():
            form.save()
    else:
        form = ChangeTimezoneForm(request.user)
    return render_to_response("account/timezone_change.html", {
        "form": form,
    }, context_instance=RequestContext(request))

def username_autocomplete(request):
    if request.user.is_authenticated():
        q = request.GET.get("q")
        content = []
        response = HttpResponse("\n".join(content))
    else:
        response = HttpResponseForbidden()
    setattr(response, "djangologging.suppress_output", True)
    return response

@never_cache
def suggest_username(request):
    """
    suggestion1, suggestion2
    available (is the username chosen available)
    """
    username = request.GET.get('username','')
    available, suggest = User.objects.suggest_user(
        username=username, 
        email = request.GET.get('email',''),
        name=request.GET.get('name','')
        )
    print available
    print suggest
    available_text = available and ugettext('The username is available') or ugettext('The username is already taken!')
    return HttpResponse(simplejson.dumps({'suggest': suggest,'available':available,'available_text':available_text, 'username':username}), 'text/javascript')


def confirm_email(request, confirmation_key):
    confirmation_key = confirmation_key.lower()
    email_address = EmailConfirmation.objects.confirm_email(confirmation_key)
    return render_to_response("account/confirm_email.html", {
        "email_address": email_address,
    }, context_instance=RequestContext(request))

def profiles(request):
    return render_to_response("account/profiles.html", {
        "users": User.objects.all().order_by("-date_joined"),
    }, context_instance=RequestContext(request))

@login_required
def private_profile(request, template_name="account/private_profile.html"):
    """    if request.method == "POST":
        if request.POST["action"] == "update":
            profile_form = ProfileForm(request.POST, instance=request.user.get_profile())
            profile = profile_form.save(commit=False)
            profile.user = request.user
            profile.save()
"""
    user = request.user
    profile_form = ProfileForm(instance=user.get_or_create_profile())
    
    return render_to_response(template_name, {
        "is_me":True,
        "profile": user.get_profile(),
        "profile_form": profile_form,
    }, context_instance=RequestContext(request))


def profile(request, nickname, template_name = "account/profile.html"):
    profile = get_object_or_404(Profile, nick = nickname)
    if request.user.is_authenticated():
        if request.user == profile.user:
            is_me = True
        else:
            is_me = False
    else:
        is_me = False


    if is_me:
        if request.method == "POST":
            if request.POST["action"] == "update":
                profile_form = ProfileForm(request.POST, instance=profile)
                profile = profile_form.save(commit=False)
                profile.save()
        profile_form = ProfileForm(instance=profile)
    else:
        profile_form = None

    return render_to_response(template_name, {
        "profile": profile,
        "profile_form": profile_form,
        "is_me": is_me,
        "other_user": profile.user,
    }, context_instance=RequestContext(request))

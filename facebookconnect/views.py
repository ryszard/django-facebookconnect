# Copyright 2008-2009 Brian Boyer, Ryan Mark, Angela Nitzke, Joshua Pollock,
# Stuart Tiffen, Kayla Webley and the Medill School of Journalism, Northwestern
# University.
#
# This file is part of django-facebookconnect.
#
# django-facebookconnect is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# django-facebookconnect is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
#You should have received a copy of the GNU General Public License
#along with django-facebookconnect.  If not, see <http://www.gnu.org/licenses/>.

import logging
import sha, random

from django.http import HttpResponse, HttpResponseRedirect
from django.template import RequestContext
from django.core.urlresolvers import reverse
from django.shortcuts import render_to_response
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.forms import AuthenticationForm
from django.contrib.auth.models import User
from django.conf import settings

from facebookconnect.models import FacebookProfile

def facebook_login(request):
    if request.method == "POST":
        logging.debug("FBC: OK logging in...")
        if request.POST.get('next',False) and request.POST['next']:
            next = request.POST['next']
        else:
            next = getattr(settings,'LOGIN_REDIRECT_URL','/')
        user = authenticate(request=request)
        logging.debug(user)
        logging.debug(request.facebook.uid)
        if user is not None:
            if user.is_active:
                login(request, user)
                # Redirect to a success page.
                logging.debug("FBC: Redirecting to %s" % next)
                if request.is_ajax():
                    return HttpResponse("true")
                return HttpResponseRedirect(next)
            else:
                logging.debug("FBC: This account is disabled.")
                raise FacebookAuthError('This account is disabled.')
        elif request.facebook.uid:
            #we have to set this user up
            try:
                user = User.objects.get(username=request.facebook.uid)
            except User.DoesNotExist:
                user = User(username=request.facebook.uid)
                user.set_unusable_password()
                user.save()
                profile = FacebookProfile(user=user, facebook_id=request.facebook.uid)
                profile.save()
                logging.info("FBC: Added user and profile for %s!" % request.facebook.uid)
            login(request, user)
            if request.is_ajax():
                return HttpResponse("OK")
            return HttpResponseRedirect(next)
    else:
        return HttpResponse("TODO")

    # logging.debug("FBC: Got redirected here")
#     url = reverse('auth_login')
#     if request.GET.get('next',False):
#         url += "?next=%s" % request.GET['next']
#     return HttpResponseRedirect(url)

def facebook_logout(request):
    logout(request)
    if getattr(request,'facebook',False):
        request.facebook.session_key = None
        request.facebook.uid = None
    return HttpResponseRedirect(getattr(settings,'LOGOUT_REDIRECT_URL','/'))

class FacebookAuthError(Exception):
    def __init__(self, message):
        self.message = message
    def __str__(self):
        return repr(self.message)

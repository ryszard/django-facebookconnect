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

try:
    import json
except ImportError:
    import simplejson as json

from django.http import HttpResponse, HttpResponseRedirect, HttpResponseNotAllowed, HttpResponseForbidden
from django.template import RequestContext
from django.core.urlresolvers import reverse
from django.shortcuts import render_to_response
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.forms import AuthenticationForm
from django.contrib.auth.models import User
from django.conf import settings

from facebookconnect.models import FacebookProfile

class JSONResponse(HttpResponse):
    def __init__(self, content=None, status=None):
        content = json.dumps(content)
        super(JSONResponse, self).__init__(content=content,
                                           status=status,
                                           content_type="application/json")

def ensure_login(request):
    """This view should be called only by login_required when the user
    is not logged in. If the call was non-ajax, acts as
    facebook_login.

    """
    if request.is_ajax():
        return JSONResponse({'status': False,
                             'reason': 'login-required',
                             'verbose_reason': 'You must be logged in to access this resource'})

    else:
        return facebook_login(request)

def facebook_login(request):
    user = authenticate(request=request)
    if user is None or not user.is_active:
        verbose_reason="Some problem with authentication"
        if request.is_ajax():
            return JSONResponse(dict(status=False,
                                     reason="authentication",
                                     verbose_reason=verbose_reason),
                                status=403,)
        else:
            return HttpResponseForbidden(verbose_reason)

    login(request, user)

    if request.is_ajax():
        return JSONResponse(dict(status=True))

    next = request.GET.get('next', getattr(settings,'LOGIN_REDIRECT_URL','/'))
    return HttpResponseRedirect(next)



def facebook_logout(request):
    logging.debug('FBC Login: logging out user %r' % request.user)
    logout(request)
    if getattr(request,'facebook',False):
        request.facebook.session_key = None
        request.facebook.uid = None
    if request.is_ajax():
        return JSONResponse(dict(status=True))
    next = request.GET.get('next', getattr(settings,'LOGOUT_REDIRECT_URL','/'))
    return HttpResponseRedirect(next)

class FacebookAuthError(Exception):
    def __init__(self, message):
        self.message = message
    def __str__(self):
        return repr(self.message)

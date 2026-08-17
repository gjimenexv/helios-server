"""
server_ui specific views
"""

import copy

from django.conf import settings
from django.http import HttpResponseRedirect
from django.utils.http import url_has_allowed_host_and_scheme

import helios_auth.views as auth_views
from helios.models import Election
from helios.security import can_create_election
from helios_auth.security import check_csrf, get_user
from . import glue
from .view_utils import render_template

glue.glue()  # actually apply glue helios.view <-> helios.signals


def get_election():
  return None
  
def home(request):
  # load the featured elections
  featured_elections = Election.get_featured()
  
  user = get_user(request)
  create_p = can_create_election(request)

  if create_p:
    elections_administered = Election.get_by_user_as_admin(user, archived_p=False, limit=5)
  else:
    elections_administered = None

  if user:
    elections_voted = Election.get_by_user_as_voter(user, limit=5)
  else:
    elections_voted = None
 
  auth_systems = copy.copy(settings.AUTH_ENABLED_SYSTEMS)
  try:
    auth_systems.remove('password')
  except: pass

  login_box = auth_views.login_box_raw(request, return_url="/", auth_systems=auth_systems)

  return render_template(request, "index", {'elections': featured_elections,
                                            'elections_administered' : elections_administered,
                                            'elections_voted' : elections_voted,
                                            'create_p':create_p,
                                            'login_box' : login_box})
  
def about(request):
  return render_template(request, "about")

def docs(request):
  return render_template(request, "docs")

def faq(request):
  return render_template(request, "faq")

def privacy(request):
  return render_template(request, "privacy")


def set_language(request):
  check_csrf(request)

  language_code = request.POST.get('language')
  next_url = request.POST.get('next') or request.META.get('HTTP_REFERER') or '/'

  if not url_has_allowed_host_and_scheme(url=next_url, allowed_hosts={request.get_host()},
                                          require_https=request.is_secure()):
    next_url = '/'

  response = HttpResponseRedirect(next_url)

  if language_code and language_code in dict(settings.LANGUAGES):
    response.set_cookie(
      settings.LANGUAGE_COOKIE_NAME, language_code,
      max_age=settings.LANGUAGE_COOKIE_AGE,
      path=settings.LANGUAGE_COOKIE_PATH,
      domain=settings.LANGUAGE_COOKIE_DOMAIN,
      secure=settings.LANGUAGE_COOKIE_SECURE,
      httponly=settings.LANGUAGE_COOKIE_HTTPONLY,
      samesite=settings.LANGUAGE_COOKIE_SAMESITE,
    )

  return response


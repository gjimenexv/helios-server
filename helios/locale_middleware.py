"""
Language selection for Helios.
"""

from django.conf import settings
from django.middleware.locale import LocaleMiddleware
from django.utils import translation


class SiteDefaultLocaleMiddleware(LocaleMiddleware):
  """
  Like Django's LocaleMiddleware, but the browser does not get a vote.

  Django's version picks a language from, in order: the language cookie, the
  Accept-Language header, and finally settings.LANGUAGE_CODE. For an election
  site that header is the wrong input: the site runs in one language, voters
  were emailed in that language by the Celery worker (which has no header to
  read and so always uses LANGUAGE_CODE), and a voter whose browser happens
  to ask for English would otherwise land on an English page from a Spanish
  email.

  So this drops the Accept-Language step. An explicit choice in the language
  switcher still wins -- that sets the language cookie, which is checked
  first -- and everyone else gets the site default.
  """

  def process_request(self, request):
    chosen = request.COOKIES.get(settings.LANGUAGE_COOKIE_NAME)

    if chosen in dict(settings.LANGUAGES):
      language = chosen
    else:
      language = settings.LANGUAGE_CODE

    translation.activate(language)
    request.LANGUAGE_CODE = translation.get_language()

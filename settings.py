
# a massive hack to see if we're testing, in which case we use different settings
import sys

import json
import os

import ldap
from django_auth_ldap.config import LDAPSearch

TESTING = 'test' in sys.argv

# go through environment variables and override them
def get_from_env(var, default):
    if not TESTING and var in os.environ:
        return os.environ[var]
    else:
        return default

DEBUG = (get_from_env('DEBUG', '1') == '1')

# add admins of the form: 
#    ('Ben Adida', 'ben@adida.net'),
# if you want to be emailed about errors.
admin_email = get_from_env('ADMIN_EMAIL', None)
if admin_email:
    ADMINS = [(get_from_env('ADMIN_NAME', ''), admin_email)]
else:
    ADMINS = []

MANAGERS = ADMINS

# is this the master Helios web site?
MASTER_HELIOS = (get_from_env('MASTER_HELIOS', '0') == '1')

# show ability to log in? (for example, if the site is mostly used by voters)
# if turned off, the admin will need to know to go to /auth/login manually
SHOW_LOGIN_OPTIONS = (get_from_env('SHOW_LOGIN_OPTIONS', '1') == '1')

# sometimes, when the site is not that social, it's not helpful
# to display who created the election
SHOW_USER_INFO = (get_from_env('SHOW_USER_INFO', '1') == '1')

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': 'helios',
        'CONN_MAX_AGE': 600,
    },
}

# override if we have an env variable
if get_from_env('DATABASE_URL', None):
    import dj_database_url
    DATABASES['default'] = dj_database_url.config(
        conn_max_age=600,
        ssl_require=(get_from_env('DATABASE_SSL_REQUIRE', '1') == '1'),
    )
    DATABASES['default']['ENGINE'] = 'django.db.backends.postgresql'

# explicitly set the default auto-created primary field to silence warning models.W042
DEFAULT_AUTO_FIELD = 'django.db.models.AutoField'

# Local time zone for this installation. Choices can be found here:
# http://en.wikipedia.org/wiki/List_of_tz_zones_by_name
# although not all choices may be available on all operating systems.
#
# This is the STORAGE zone, and it must stay UTC. Helios keeps naive
# datetimes (USE_TZ = False), and it writes them two different ways: model
# fields with auto_now_add use Django's timezone.now(), while the election
# lifecycle fields are set with datetime.utcnow(). Those two agree only when
# TIME_ZONE is UTC. With anything else -- this used to be
# 'America/Los_Angeles' -- a ballot's cast_at lands hours away from the
# election's own opening and closing times, and the two disagree on screen.
#
# The zone elections are *displayed and scheduled* in is ELECTION_TIME_ZONE
# below. Change that one, never this one.
TIME_ZONE = 'UTC'

USE_TZ = False

# Wall clock of the elections this installation runs. An administrator who
# schedules a close for 18:00 means 18:00 here, and every voter sees that
# same 18:00 regardless of where they are. See helios/timezone_utils.py.
ELECTION_TIME_ZONE = get_from_env('ELECTION_TIME_ZONE', 'America/Costa_Rica')

# Language code for this installation. All choices can be found here:
# http://www.i18nguy.com/unicode/language-identifiers.html
#
# This is also the language of everything sent by the Celery worker (voter
# credentials, reminders, tally notices): those render outside a request, so
# no language is active and Django falls back to this value.
LANGUAGE_CODE = get_from_env('LANGUAGE_CODE', 'es')

# The test suite asserts on the English wording of pages and emails, so it
# pins the language rather than following whatever this installation's default
# happens to be. Same reasoning as get_from_env's TESTING short-circuit above.
if TESTING:
    LANGUAGE_CODE = 'en'

SITE_ID = 1

# If you set this to False, Django will make some optimizations so as not
# to load the internationalization machinery.
USE_I18N = True

# Languages available for voters/admins to pick via the language switcher.
# Language is chosen per-session/cookie (LocaleMiddleware), not via URL
# prefix, so existing election cast_urls are unaffected.
LANGUAGES = [
    ('en', 'English'),
    ('es', 'Español'),
]

LOCALE_PATHS = [
    os.path.join(os.path.dirname(__file__), 'locale'),
]

# Absolute path to the directory that holds user-uploaded media (election
# logos, voter files, etc.). Set below, once ROOT_PATH is defined.
MEDIA_ROOT = ''

# URL that handles the media served from MEDIA_ROOT. Make sure to use a
# trailing slash if there is a path component (optional in other cases).
MEDIA_URL = '/user_media/'

# URL prefix for admin media -- CSS, JavaScript and images. Make sure to use a
# trailing slash.
# Examples: "http://foo.com/media/", "/media/".
STATIC_URL = '/media/'

# Make this unique, and don't share it with anybody.
SECRET_KEY = get_from_env('SECRET_KEY', 'replaceme')

# Secret key for HMAC confirmation codes (separate from Django SECRET_KEY)
EMAIL_OPTOUT_SECRET = get_from_env('EMAIL_OPTOUT_SECRET', 'replace-with-secure-random-key')

# If debug is set to false and ALLOWED_HOSTS is not declared, django raises  "CommandError: You must set settings.ALLOWED_HOSTS if DEBUG is False."
# If in production, you got a bad request (400) error
#More info: https://docs.djangoproject.com/en/1.7/ref/settings/#allowed-hosts (same for 1.6)

ALLOWED_HOSTS = get_from_env('ALLOWED_HOSTS', 'localhost').split(",")

# Secure Stuff
if get_from_env('SSL', '0') == '1':
    SECURE_SSL_REDIRECT = True
    SESSION_COOKIE_SECURE = True

    # tuned for Heroku
    SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")

SESSION_COOKIE_HTTPONLY = True

# Set this explicitly rather than relying on the Django default: it is a load-bearing
# part of our CSRF defense, since Helios does its own CSRF checking (check_csrf) rather
# than using Django's CsrfViewMiddleware. 'Lax' keeps the session cookie off every
# cross-site POST and off cross-site GET subresources (images, iframes, fetch), while
# still allowing ordinary inbound links to Helios to stay logged in.
SESSION_COOKIE_SAMESITE = get_from_env('SESSION_COOKIE_SAMESITE', 'Lax')

# let's go with one year because that's the way to do it now
STS = False
if get_from_env('HSTS', '0') == '1':
    STS = True
    # we're using our own custom middleware now
    # SECURE_HSTS_SECONDS = 31536000
    # not doing subdomains for now cause that is not likely to be necessary and can screw things up.
    # SECURE_HSTS_INCLUDE_SUBDOMAINS = True

SECURE_BROWSER_XSS_FILTER = True
SECURE_CONTENT_TYPE_NOSNIFF = True

# Content Security Policy Configuration (django-csp)
# https://django-csp.readthedocs.io/
#
# 'unsafe-inline' and 'unsafe-eval' are required due to legacy inline scripts,
# onclick handlers, and jQuery JSON eval usage. Future improvement: use nonces.

CSP_DEFAULT_SRC = ("'self'",)
CSP_SCRIPT_SRC = ("'self'", "'unsafe-inline'", "'unsafe-eval'")
CSP_STYLE_SRC = ("'self'", "'unsafe-inline'")
CSP_IMG_SRC = ("'self'", "data:")
CSP_FONT_SRC = ("'self'",)
CSP_CONNECT_SRC = ("'self'",)
CSP_WORKER_SRC = ("'self'", "blob:")
CSP_FORM_ACTION = ("'self'",)
CSP_FRAME_ANCESTORS = ("'self'",)
CSP_BASE_URI = ("'self'",)
CSP_OBJECT_SRC = ("'none'",)

# Set CSP_REPORT_ONLY=1 to test without enforcing
if get_from_env('CSP_REPORT_ONLY', '0') == '1':
    CSP_REPORT_ONLY = True
else:
    CSP_REPORT_ONLY = False

# Optional: URI to receive CSP violation reports
_csp_report_uri = get_from_env('CSP_REPORT_URI', None)
if _csp_report_uri:
    CSP_REPORT_URI = _csp_report_uri

SILENCED_SYSTEM_CHECKS = ['urls.W002']

MIDDLEWARE = [
    # secure a bunch of things
    'django.middleware.security.SecurityMiddleware',
    'helios.security.HSTSMiddleware',
    'csp.middleware.CSPMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
    # 'django.middleware.csrf.CsrfViewMiddleware',

    'django.contrib.sessions.middleware.SessionMiddleware',
    # Site default wins over the browser's Accept-Language header; only the
    # language switcher (which sets the language cookie) overrides it.
    'helios.locale_middleware.SiteDefaultLocaleMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
]

ROOT_URLCONF = 'urls'

ROOT_PATH = os.path.dirname(__file__)

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'APP_DIRS': True,
        'DIRS': [
            ROOT_PATH,
            os.path.join(ROOT_PATH, 'templates'),
            # os.path.join(ROOT_PATH, 'helios/templates'),  # covered by APP_DIRS:True
            # os.path.join(ROOT_PATH, 'helios_auth/templates'),  # covered by APP_DIRS:True
            # os.path.join(ROOT_PATH, 'server_ui/templates'),  # covered by APP_DIRS:True
        ],
        'OPTIONS': {
            'debug': DEBUG,
            'context_processors': [
                'django.template.context_processors.i18n',
            ],
        }
    },
]

INSTALLED_APPS = (
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.sites',
    'anymail',
    ## HELIOS stuff
    'helios_auth',
    'helios',
    'server_ui',
)

# Email backend configuration
# In development mode, set EMAIL_USE_CONSOLE=1 to print emails to stdout
if DEBUG and get_from_env('EMAIL_USE_CONSOLE', '0') == '1':
    EMAIL_BACKEND = 'django.core.mail.backends.console.EmailBackend'

ANYMAIL = {
    "MAILGUN_API_KEY": get_from_env('MAILGUN_API_KEY', None),
    "MAILGUN_SENDER_DOMAIN": get_from_env('MAILGUN_SENDER_DOMAIN', None),
}

# Mailgun overrides console backend if configured
if ANYMAIL["MAILGUN_API_KEY"]:
    EMAIL_BACKEND = "anymail.backends.mailgun.EmailBackend"

##
## HELIOS
##


MEDIA_ROOT = ROOT_PATH + "media/"

# a relative path where voter upload files are stored
VOTER_UPLOAD_REL_PATH = "voters/%Y/%m/%d"


# Who every notification comes from: voter credentials, reminders, tally
# notices, trustee mail. Upstream shipped Helios's own author here, so an
# installation that forgot to set DEFAULT_FROM_EMAIL sent mail claiming to be
# from a stranger; the default below is this installation's own address.
#
# On a provider that binds the envelope to the authenticated account -- Gmail
# does -- this address is only honoured if EMAIL_HOST_USER is that same
# account, or an alias it has verified. Changing it here without changing the
# SMTP credentials gets the From header silently rewritten back.
DEFAULT_FROM_EMAIL = get_from_env('DEFAULT_FROM_EMAIL', 'ecs2026espacioseguro@gmail.com')
DEFAULT_FROM_NAME = get_from_env('DEFAULT_FROM_NAME', 'Espacio Seguro ECS 2026')
SERVER_EMAIL = '%s <%s>' % (DEFAULT_FROM_NAME, DEFAULT_FROM_EMAIL)

LOGIN_URL = '/auth/'
LOGOUT_ON_CONFIRMATION = True

# The two hosts are here so the main site can be over plain HTTP
# while the voting URLs are served over SSL.
URL_HOST = get_from_env("URL_HOST", "http://localhost:8000").rstrip("/")

# IMPORTANT: you should not change this setting once you've created
# elections, as your elections' cast_url will then be incorrect.
# SECURE_URL_HOST = "https://localhost:8443"
SECURE_URL_HOST = get_from_env("SECURE_URL_HOST", URL_HOST).rstrip("/")

# election stuff
SITE_TITLE = get_from_env('SITE_TITLE', 'Helios Voting')
MAIN_LOGO_URL = get_from_env('MAIN_LOGO_URL', '/static/logo.png')
ALLOW_ELECTION_INFO_URL = (get_from_env('ALLOW_ELECTION_INFO_URL', '0') == '1')

# site-wide default branding colors, used whenever an election doesn't set
# its own primary_color/accent_color. See helios/branding.py.
DEFAULT_PRIMARY_COLOR = get_from_env('DEFAULT_PRIMARY_COLOR', '#1a73e8')
DEFAULT_ACCENT_COLOR = get_from_env('DEFAULT_ACCENT_COLOR', '#d93025')

# FOOTER links
FOOTER_LINKS = json.loads(get_from_env('FOOTER_LINKS', '[]'))
FOOTER_LOGO_URL = get_from_env('FOOTER_LOGO_URL', None)

WELCOME_MESSAGE = get_from_env('WELCOME_MESSAGE', "This is the default message")

HELP_EMAIL_ADDRESS = get_from_env('HELP_EMAIL_ADDRESS', 'help@heliosvoting.org')

AUTH_TEMPLATE_BASE = "server_ui/templates/base.html"
HELIOS_TEMPLATE_BASE = "server_ui/templates/base.html"
HELIOS_ADMIN_ONLY = False
HELIOS_VOTERS_UPLOAD = True
HELIOS_VOTERS_EMAIL = True

# Number of weeks after tallying when voter emails should be disabled
HELIOS_VOTER_EMAIL_CUTOFF_WEEKS = int(get_from_env('HELIOS_VOTER_EMAIL_CUTOFF_WEEKS', '3'))

# Voter credentials: a voter never receives a password by email. They receive a
# single-use link, valid for this many hours, on which they set their own
# password. Only hashes of both the token and the password are ever stored.
HELIOS_VOTER_TOKEN_EXPIRY_HOURS = int(get_from_env('HELIOS_VOTER_TOKEN_EXPIRY_HOURS', '336'))
HELIOS_VOTER_PASSWORD_MIN_LENGTH = int(get_from_env('HELIOS_VOTER_PASSWORD_MIN_LENGTH', '8'))

# are elections private by default?
HELIOS_PRIVATE_DEFAULT = False

# authentication systems enabled
# AUTH_ENABLED_SYSTEMS = ['password','facebook', 'google', 'yahoo']
AUTH_ENABLED_SYSTEMS = get_from_env('AUTH_ENABLED_SYSTEMS',
                                    get_from_env('AUTH_ENABLED_AUTH_SYSTEMS', 'ldap,password,google,facebook')
                                    ).split(",")

# Add development login in debug mode
if DEBUG:
    AUTH_ENABLED_SYSTEMS = ['devlogin'] + AUTH_ENABLED_SYSTEMS

AUTH_DEFAULT_SYSTEM = get_from_env('AUTH_DEFAULT_SYSTEM', get_from_env('AUTH_DEFAULT_AUTH_SYSTEM', None))

# google
GOOGLE_CLIENT_ID = get_from_env('GOOGLE_CLIENT_ID', '')
GOOGLE_CLIENT_SECRET = get_from_env('GOOGLE_CLIENT_SECRET', '')

# facebook
FACEBOOK_APP_ID = get_from_env('FACEBOOK_APP_ID','')
FACEBOOK_API_KEY = get_from_env('FACEBOOK_API_KEY','')
FACEBOOK_API_SECRET = get_from_env('FACEBOOK_API_SECRET','')

# LinkedIn
LINKEDIN_CLIENT_ID = get_from_env('LINKEDIN_CLIENT_ID', '')
LINKEDIN_CLIENT_SECRET = get_from_env('LINKEDIN_CLIENT_SECRET', '')

# CAS (for universities)
CAS_USERNAME = get_from_env('CAS_USERNAME', "")
CAS_PASSWORD = get_from_env('CAS_PASSWORD', "")
CAS_ELIGIBILITY_URL = get_from_env('CAS_ELIGIBILITY_URL', "")
CAS_ELIGIBILITY_REALM = get_from_env('CAS_ELIGIBILITY_REALM', "")

# GitHub
GH_CLIENT_ID = get_from_env('GH_CLIENT_ID', '')
GH_CLIENT_SECRET = get_from_env('GH_CLIENT_SECRET', '')

# Gitlab
GITLAB_CLIENT_ID = get_from_env('GITLAB_CLIENT_ID', "")
GITLAB_CLIENT_SECRET = get_from_env('GITLAB_CLIENT_SECRET', "")

# email server
EMAIL_HOST = get_from_env('EMAIL_HOST', 'localhost')
EMAIL_PORT = int(get_from_env('EMAIL_PORT', "2525"))
EMAIL_HOST_USER = get_from_env('EMAIL_HOST_USER', '')
EMAIL_HOST_PASSWORD = get_from_env('EMAIL_HOST_PASSWORD', '')
EMAIL_USE_TLS = (get_from_env('EMAIL_USE_TLS', '0') == '1')

# to use AWS Simple Email Service
# in which case environment should contain
# AWS_ACCESS_KEY_ID and AWS_SECRET_ACCESS_KEY
if get_from_env('EMAIL_USE_AWS', '0') == '1':
    EMAIL_BACKEND = 'django_ses.SESBackend'

# set up logging
import logging

logging.basicConfig(
    level=logging.DEBUG if TESTING else logging.INFO,
    format='%(asctime)s %(levelname)s %(message)s'
)

# set up celery
CELERY_BROKER_URL = get_from_env('CELERY_BROKER_URL', 'amqp://localhost')
if TESTING:
    CELERY_TASK_ALWAYS_EAGER = True
else:
    CELERY_TASK_ALWAYS_EAGER = (get_from_env('CELERY_TASK_ALWAYS_EAGER', '0') == '1')

# Rollbar Error Logging
ROLLBAR_ACCESS_TOKEN = get_from_env('ROLLBAR_ACCESS_TOKEN', None)
if ROLLBAR_ACCESS_TOKEN:
  print("setting up rollbar")
  MIDDLEWARE += ['rollbar.contrib.django.middleware.RollbarNotifierMiddleware',]
  ROLLBAR = {
    'access_token': ROLLBAR_ACCESS_TOKEN,
    'environment': 'development' if DEBUG else 'production',  
  }


# ldap
# see configuration example at https://pythonhosted.org/django-auth-ldap/example.html
AUTH_LDAP_SERVER_URI = "ldap://ldap.forumsys.com" # replace by your Ldap URI
AUTH_LDAP_BIND_DN = "cn=read-only-admin,dc=example,dc=com"
AUTH_LDAP_BIND_PASSWORD = "password"
AUTH_LDAP_USER_SEARCH = LDAPSearch("dc=example,dc=com",
    ldap.SCOPE_SUBTREE, "(uid=%(user)s)"
)

AUTH_LDAP_USER_ATTR_MAP = {
    "first_name": "givenName",
    "last_name": "sn",
    "email": "mail",
}

AUTH_LDAP_BIND_AS_AUTHENTICATING_USER = True

AUTH_LDAP_ALWAYS_UPDATE_USER = False

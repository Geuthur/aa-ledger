# Every setting in base.py can be overloaded by redefining it here.
from .base import *

SECRET_KEY = os.environ.get("AA_SECRET_KEY")
SITE_NAME = os.environ.get("AA_SITENAME")
SITE_URL = "http://localhost:8000"
CSRF_TRUSTED_ORIGINS = [SITE_URL]
DEBUG = True
DATABASES["default"] = {
    "ENGINE": "django.db.backends.mysql",
    "NAME": os.environ.get("AA_DB_NAME"),
    "USER": os.environ.get("AA_DB_USER"),
    "PASSWORD": os.environ.get("AA_DB_PASSWORD"),
    "HOST": os.environ.get("AA_DB_HOST"),
    "PORT": os.environ.get("AA_DB_PORT", "3306"),
    "OPTIONS": {"charset": os.environ.get("AA_DB_CHARSET", "utf8mb4")},
}

# Register an application at https://developers.eveonline.com for Authentication
# & API Access and fill out these settings. Be sure to set the callback URL
# to https://example.com/sso/callback substituting your domain for example.com
# Logging in to auth requires the publicData scope (can be overridden through the
# LOGIN_TOKEN_SCOPES setting). Other apps may require more (see their docs).

ESI_SSO_CLIENT_ID = os.environ.get("ESI_SSO_CLIENT_ID")
ESI_SSO_CLIENT_SECRET = os.environ.get("ESI_SSO_CLIENT_SECRET")
ESI_SSO_CALLBACK_URL = f"{SITE_URL}/sso/callback"
ESI_USER_CONTACT_EMAIL = os.environ.get(
    "ESI_USER_CONTACT_EMAIL"
)  # A server maintainer that CCP can contact in case of issues.

# By default emails are validated before new users can log in.
# It's recommended to use a free service like SparkPost or Elastic Email to send email.
# https://www.sparkpost.com/docs/integrations/django/
# https://elasticemail.com/resources/settings/smtp-api/
# Set the default from email to something like 'noreply@example.com'
# Email validation can be turned off by uncommenting the line below. This can break some services.
REGISTRATION_VERIFY_EMAIL = False
# EMAIL_HOST = os.environ.get("AA_EMAIL_HOST", "")
# EMAIL_PORT = os.environ.get("AA_EMAIL_PORT", 587)
# EMAIL_HOST_USER = os.environ.get("AA_EMAIL_HOST_USER", "")
# EMAIL_HOST_PASSWORD = os.environ.get("AA_EMAIL_HOST_PASSWORD", "")
# EMAIL_USE_TLS = os.environ.get("AA_EMAIL_USE_TLS", True)
# DEFAULT_FROM_EMAIL = os.environ.get("AA_DEFAULT_FROM_EMAIL", "")

ROOT_URLCONF = "myauth.urls"
WSGI_APPLICATION = "myauth.wsgi.application"


# remove static root so files are served without collectstatic
# STATIC_ROOT = "/var/www/myauth/static/"
del STATIC_ROOT

BROKER_URL = f"redis://{os.environ.get('AA_REDIS', 'redis:6379')}/0"
CACHES = {
    "default": {
        "BACKEND": "django_redis.cache.RedisCache",
        "LOCATION": f"redis://{os.environ.get('AA_REDIS', 'redis:6379')}/1",  # change the 1 here to change the database used
    }
}


# Add any additional apps to this list.
INSTALLED_APPS += [
    # https://allianceauth.readthedocs.io/en/latest/features/apps/index.html
    # 'allianceauth.corputils',
    # 'allianceauth.fleetactivitytracking',
    # 'allianceauth.optimer',
    # 'allianceauth.permissions_tool',
    # 'allianceauth.srp',
    # 'allianceauth.timerboard',
    # https://allianceauth.readthedocs.io/en/latest/features/services/index.html
    # 'allianceauth.services.modules.discord',
    # 'allianceauth.services.modules.discourse',
    # 'allianceauth.services.modules.ips4',
    # 'allianceauth.services.modules.openfire',
    # 'allianceauth.services.modules.mumble',
    # An example of running mumble with authenticator in docker can be found here
    # https://github.com/Solar-Helix-Independent-Transport/allianceauth-docker-mumble
    # 'allianceauth.services.modules.phpbb3',
    # 'allianceauth.services.modules.smf',
    # 'allianceauth.services.modules.teamspeak3',
    # 'allianceauth.services.modules.xenforo',
    "ledger",
    "eveuniverse",
    "corpstats",
    "corptools",
    "memberaudit",
    "debug_toolbar",
    "taskmonitor",
]

#######################################
# Add any custom settings below here. #
#######################################

MIDDLEWARE.insert(0, "debug_toolbar.middleware.DebugToolbarMiddleware")

DEBUG_TOOLBAR_CONFIG = {
    "SHOW_TOOLBAR_CALLBACK": lambda request: True,
}

CELERYBEAT_SCHEDULE["memberaudit_run_regular_updates"] = {
    "task": "memberaudit.tasks.run_regular_updates",
    "schedule": crontab(minute=0, hour="*/1"),
}

CELERYBEAT_SCHEDULE["moonmining_run_regular_updates"] = {
    "task": "moonmining.tasks.run_regular_updates",
    "schedule": crontab(minute="*/10"),
}
CELERYBEAT_SCHEDULE["moonmining_run_report_updates"] = {
    "task": "moonmining.tasks.run_report_updates",
    "schedule": crontab(minute=30, hour="*/1"),
}
CELERYBEAT_SCHEDULE["moonmining_run_value_updates"] = {
    "task": "moonmining.tasks.run_calculated_properties_update",
    "schedule": crontab(minute=30, hour=3),
}

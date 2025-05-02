"""
Test settings
"""

########################################################
# local.py settings
# Every setting in base.py can be overloaded by redefining it here.

from .base import *

PACKAGE = "ledger"

# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/1.10/howto/static-files/
# STATICFILES_DIRS = [os.path.join(PROJECT_DIR, f"{PACKAGE}/static")]
STATICFILES_DIRS = [
    f"{PACKAGE}/static",
]

SITE_URL = "http://localhost:8000"
CSRF_TRUSTED_ORIGINS = [SITE_URL]

DISCORD_BOT_TOKEN = "My_Dummy_Token"
# These are required for Django to function properly. Don't touch.
ROOT_URLCONF = "testauth.urls"
WSGI_APPLICATION = "testauth.wsgi.application"
SECRET_KEY = "DUMMY"

# This is where css/images will be placed for your webserver to read
STATIC_ROOT = "/var/www/testauth/static/"

# Change this to change the name of the auth site displayed
# in page titles and the site header.
SITE_NAME = "testauth"

# Change this to enable/disable debug mode, which displays
# useful error messages but can leak sensitive data.
DEBUG = False
LOGGING = None

NOTIFICATIONS_REFRESH_TIME = 30
NOTIFICATIONS_MAX_PER_USER = 50

# Enter credentials to use MySQL/MariaDB. Comment out to use sqlite3
DATABASES["default"] = {
    "ENGINE": "django.db.backends.mysql",
    "NAME": "alliance_auth",
    "USER": "root",
    "PASSWORD": "temp_password_aa_tox_tests",
    "HOST": "127.0.0.1",
    "PORT": "3306",
    "OPTIONS": {"charset": "utf8mb4"},
}

# Add any additional apps to this list.
INSTALLED_APPS += [
    "allianceauth.corputils",
    PACKAGE,
    "eveuniverse",
]
# By default, apps are prevented from having public views for security reasons.
# If you want to allow specific apps to have public views,
# you can put their names here (same name as in INSTALLED_APPS).
#
# Note:
#   » The format is the same as in INSTALLED_APPS
#   » The app developer must explicitly allow public views for his app
APPS_WITH_PUBLIC_VIEWS = []

# ------------------------------------------------------------------------------------ #
#
#                                  ESI Settings
#
# ------------------------------------------------------------------------------------ #
# Register an application at
# https://developers.eveonline.com for Authentication
# & API Access and fill out these settings.
# Be sure to set the callback URL
# to https://example.com/sso/callback
# substituting your domain for example.com
# Logging in to auth requires the publicData
# scope (can be overridden through the
# LOGIN_TOKEN_SCOPES setting).
# Other apps may require more (see their docs).
ESI_SSO_CLIENT_ID = "dummy"
ESI_SSO_CLIENT_SECRET = "dummy"
ESI_SSO_CALLBACK_URL = "http://127.0.0.1:8000"
ESI_USER_CONTACT_EMAIL = "devgeuthur@gmail.com"

# ------------------------------------------------------------------------------------ #
#
#                                E-Mail Settings
#
# ------------------------------------------------------------------------------------ #
# By default, emails are validated before new users can log in.
# It's recommended to use a free service like SparkPost
# or Elastic Email to send email.
# Https://www.sparkpost.com/docs/integrations/django/
# https://elasticemail.com/resources/settings/smtp-api/
# Set the default from email to something like 'noreply@example.com'
# Email validation can be turned off by uncommenting the line below.
# This can break some services.
REGISTRATION_VERIFY_EMAIL = False
EMAIL_HOST = ""
EMAIL_PORT = 587
EMAIL_HOST_USER = ""
EMAIL_HOST_PASSWORD = ""
EMAIL_USE_TLS = True
DEFAULT_FROM_EMAIL = ""

#######################################
# Add any custom settings below here. #
#######################################

CELERYBEAT_SCHEDULE["ledger_character_audit_update_all"] = {
    "task": "ledger.tasks.update_all_characters",
    "schedule": crontab(minute=0, hour="*/1"),
}
CELERYBEAT_SCHEDULE["ledger_corporation_audit_update_all"] = {
    "task": "ledger.tasks.update_all_corps",
    "schedule": crontab(minute=0, hour="*/1"),
}
CELERYBEAT_SCHEDULE["ledger_check_planetary_alarms"] = {
    "task": "ledger.tasks.check_planetary_alarms",
    "schedule": crontab(minute=0, hour="*/3"),
}

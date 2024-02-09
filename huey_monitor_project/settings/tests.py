# flake8: noqa: E405
"""
    Settings used to run tests
"""
from huey_monitor_project import huey_tests_instance
from huey_monitor_project.settings.prod import *  # noqa


ALLOWED_HOSTS = ['testserver']


# Huey Configuration
# ----------------------------------------------------------------------------
HUEY = huey_tests_instance.HUEY


# _____________________________________________________________________________
# Manage Django Project

INSTALLED_APPS.append('manage_django_project')

# _____________________________________________________________________________


DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': ':memory:',
    }
}

SECRET_KEY = 'No individual secret for tests ;)'

DEBUG = True

# Speedup tests by change the Password hasher:
PASSWORD_HASHERS = ('django.contrib.auth.hashers.MD5PasswordHasher',)

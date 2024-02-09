# flake8: noqa: E405

"""
    Django settings for local development
"""

import os as __os

from huey_monitor_project import huey_tests_instance
from huey_monitor_project.settings.prod import *  # noqa


# Huey-Monitor settings
# ----------------------------------------------------------------------------

# Use default SignalInfoModelAdmin.list_filter:
HUEY_MONITOR_SIGNAL_INFO_MODEL_LIST_FILTER = None

# Use default TaskModelAdmin.list_filter:
HUEY_MONITOR_TASK_MODEL_LIST_FILTER = None


# Huey Configuration
# ----------------------------------------------------------------------------
HUEY = huey_tests_instance.HUEY


# Django settings
# ----------------------------------------------------------------------------


# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = True


# Serve static/media files for local development:
SERVE_FILES = True


# Required for the debug toolbar to be displayed:
INTERNAL_IPS = ('127.0.0.1', '0.0.0.0', 'localhost')

ALLOWED_HOSTS = INTERNAL_IPS

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': str(BASE_PATH / 'huey_monitor-database.sqlite3'),
        # https://docs.djangoproject.com/en/dev/ref/databases/#database-is-locked-errors
        'timeout': 30,
    }
}


# _____________________________________________________________________________

if __os.environ.get('AUTOLOGIN') != '0':
    # Auto login for dev. server:
    MIDDLEWARE = MIDDLEWARE.copy()
    MIDDLEWARE += ['django_tools.middlewares.local_auto_login.AlwaysLoggedInAsSuperUserMiddleware']

# _____________________________________________________________________________
# Manage Django Project

INSTALLED_APPS.append('manage_django_project')

# _____________________________________________________________________________
# Django-Debug-Toolbar


INSTALLED_APPS.append('debug_toolbar')
MIDDLEWARE.append('debug_toolbar.middleware.DebugToolbarMiddleware')

DEBUG_TOOLBAR_PATCH_SETTINGS = True
from debug_toolbar.settings import CONFIG_DEFAULTS as DEBUG_TOOLBAR_CONFIG  # noqa


# Disable some more panels that will slow down the page:
DEBUG_TOOLBAR_CONFIG['DISABLE_PANELS'].add('debug_toolbar.panels.sql.SQLPanel')
DEBUG_TOOLBAR_CONFIG['DISABLE_PANELS'].add('debug_toolbar.panels.cache.CachePanel')

# don't load jquery from ajax.googleapis.com, just use django's version:
DEBUG_TOOLBAR_CONFIG['JQUERY_URL'] = STATIC_URL + 'admin/js/vendor/jquery/jquery.min.js'

DEBUG_TOOLBAR_CONFIG['SHOW_TEMPLATE_CONTEXT'] = True
DEBUG_TOOLBAR_CONFIG['SHOW_COLLAPSED'] = True  # Show toolbar collapsed by default.
DEBUG_TOOLBAR_CONFIG['SHOW_TOOLBAR_CALLBACK'] = 'huey_monitor_project.middlewares.djdt_show'

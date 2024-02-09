import os
import sys as __sys

from huey_monitor_project import huey_docker_instance
from huey_monitor_project.settings.local import *  # noqa


# _____________________________________________________________________________
# Huey Configuration
HUEY = huey_docker_instance.HUEY

# _____________________________________________________________________________
# Database
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': os.environ.get('DB_NAME'),
        'USER': os.environ.get('DB_USER'),
        'PASSWORD': os.environ.get('DB_PASS'),
        'HOST': os.environ.get('DB_HOST'),
        'PORT': os.environ.get('DB_PORT'),
        'DEBUG_NAME': 'default',
        'CONN_MAX_AGE': 600,
    },
}
print(f'Use Database: {DATABASES["default"]["NAME"]!r}', file=__sys.stderr)

# # _____________________________________________________________________________
# # Django debug toolbar
# def always_show_toolbar(request):
#     return True
#
#
# DEBUG_TOOLBAR_CONFIG = {
#     'SHOW_COLLAPSED': True,
#     'SHOW_TEMPLATE_CONTEXT': True,
#     'SHOW_TOOLBAR_CALLBACK': always_show_toolbar,
# }

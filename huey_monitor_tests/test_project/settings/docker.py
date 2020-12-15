import os

from huey_monitor_tests.test_project import huey_docker_instance
from huey_monitor_tests.test_project.settings.base import *  # noqa


# Huey Configuration
# ----------------------------------------------------------------------------
HUEY = huey_docker_instance.HUEY

# Database
# https://docs.djangoproject.com/en/2.2/ref/settings/#databases

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

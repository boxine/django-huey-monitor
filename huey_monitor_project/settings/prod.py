"""
    Base Django settings
"""

import logging
from pathlib import Path as __Path

from django.utils.translation import gettext_lazy as _


###############################################################################

# Build paths relative to the project root:
BASE_PATH = __Path(__file__).parent.parent.parent
print(f'BASE_PATH:{BASE_PATH}')
assert __Path(BASE_PATH, 'huey_monitor_project').is_dir()

###############################################################################


# Huey-Monitor settings
# ----------------------------------------------------------------------------

# e.g.: override SignalInfoModelAdmin.list_filter:
HUEY_MONITOR_SIGNAL_INFO_MODEL_LIST_FILTER = ('task__name', 'signal_name', 'thread', 'hostname')

# e.g.: override TaskModelAdmin.list_filter:
HUEY_MONITOR_TASK_MODEL_LIST_FILTER = ('name', 'state__signal_name', 'state__thread', 'state__hostname')


# Django settings
# ----------------------------------------------------------------------------


# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = False

# Serve static/media files by Django?
# In production the Webserver should serve this!
SERVE_FILES = False


# SECURITY WARNING: keep the secret key used in production secret!
__SECRET_FILE = __Path(BASE_PATH, 'secret.txt').resolve()
if not __SECRET_FILE.is_file():
    print(f'Generate {__SECRET_FILE}')
    from secrets import token_urlsafe as __token_urlsafe

    __SECRET_FILE.write_text(__token_urlsafe(128))

SECRET_KEY = __SECRET_FILE.read_text().strip()


# Application definition

INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    #
    'bx_django_utils',
    #
    'huey.contrib.djhuey',  # https://github.com/coleifer/huey
    'huey_monitor_project.test_app',
    'huey_monitor.apps.HueyMonitorConfig',
]

ROOT_URLCONF = 'huey_monitor_project.urls'
WSGI_APPLICATION = 'huey_monitor_project.wsgi.application'

AUTHENTICATION_BACKENDS = [
    'django.contrib.auth.backends.ModelBackend',
]

MIDDLEWARE = [
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.locale.LocaleMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
    'django.middleware.security.SecurityMiddleware',
]

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        "DIRS": [],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
                'django.template.context_processors.i18n',
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.template.context_processors.media',
                'django.template.context_processors.csrf',
                'django.template.context_processors.tz',
                'django.template.context_processors.static',
                'huey_monitor.context_processors.huey_monitor_version_string',
            ],
        },
    },
]


DEFAULT_AUTO_FIELD = 'django.db.models.AutoField'

# _____________________________________________________________________________
# Internationalization

LANGUAGE_CODE = 'en'

LANGUAGES = [
    ('de', _('German')),
    ('en', _('English')),
]
USE_I18N = True
USE_L10N = True
TIME_ZONE = 'Europe/Paris'
USE_TZ = True

# _____________________________________________________________________________
# Static files (CSS, JavaScript, Images)

STATIC_URL = '/static/'
STATIC_ROOT = str(__Path(BASE_PATH, 'static'))

MEDIA_URL = '/media/'
MEDIA_ROOT = str(__Path(BASE_PATH, 'media'))


# _____________________________________________________________________________
# Cache Backend

CACHES = {
    'default': {
        'BACKEND': 'django.core.cache.backends.locmem.LocMemCache',
        'LOCATION': 'unique-snowflake',
    }
}


# _____________________________________________________________________________
# cut 'pathname' in log output

old_factory = logging.getLogRecordFactory()


def cut_path(pathname, max_length):
    if len(pathname) <= max_length:
        return pathname
    return f'...{pathname[-(max_length - 3):]}'


def record_factory(*args, **kwargs):
    record = old_factory(*args, **kwargs)
    record.cut_path = cut_path(record.pathname, 30)
    return record


logging.setLogRecordFactory(record_factory)

# -----------------------------------------------------------------------------

LOGGING = {
    'version': 1,
    'disable_existing_loggers': True,
    'formatters': {
        'colored': {  # https://github.com/borntyping/python-colorlog
            '()': 'colorlog.ColoredFormatter',
            'format': (
                '%(log_color)s%(asctime)s'
                ' %(levelname)8s %(processName)s %(threadName)s'
                ' %(cut_path)s:%(lineno)-3s %(message)s'
            ),
        }
    },
    'handlers': {'console': {'class': 'colorlog.StreamHandler', 'formatter': 'colored'}},
    'loggers': {
        '': {'handlers': ['console'], 'level': 'INFO', 'propagate': False},
        'django': {'handlers': ['console'], 'level': 'INFO', 'propagate': False},
        'huey': {'handlers': ['console'], 'level': 'INFO', 'propagate': False},
        'huey_monitor': {'handlers': ['console'], 'level': 'DEBUG', 'propagate': False},
        'huey_monitor_tests': {'handlers': ['console'], 'level': 'DEBUG', 'propagate': False},
    },
}

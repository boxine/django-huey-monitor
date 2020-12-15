import sys as __sys

from huey_monitor_tests.test_project import huey_tests_instance
from huey_monitor_tests.test_project.settings.base import *  # noqa


# Huey Configuration
# ----------------------------------------------------------------------------
HUEY = huey_tests_instance.HUEY


DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': str(BASE_DIR / 'test-db.sqlite3'),  # noqa: F405
        # https://docs.djangoproject.com/en/dev/ref/databases/#database-is-locked-errors
        'timeout': 30,
    }
}
print(f'Use Database: {DATABASES["default"]["NAME"]!r}', file=__sys.stderr)

STATIC_ROOT = str(BASE_DIR / 'static')  # noqa: F405
MEDIA_ROOT = str(BASE_DIR / 'media')  # noqa: F405

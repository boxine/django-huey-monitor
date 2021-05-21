from django.core import checks
from django.core.checks import Warning
from django.test import SimpleTestCase, override_settings


class SystemChecksTestCase(SimpleTestCase):
    def test_checks(self):
        errors = checks.run_checks()
        assert errors == []

        with override_settings(INSTALLED_APPS=[
            'django.contrib.admin',
            'django.contrib.auth',
            'django.contrib.contenttypes',
            'django.contrib.messages',
            'huey_monitor',
        ]):
            errors = checks.run_checks()
            assert errors == [Warning(
                '"bx_django_utils" not in INSTALLED_APPS',
                id='huey_monitor.E001',
            )]

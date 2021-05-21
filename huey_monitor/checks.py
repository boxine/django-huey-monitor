from django.conf import settings
from django.core.checks import Warning, register


@register()
def huey_monitor_check(app_configs, **kwargs):
    errors = []

    if 'bx_django_utils' not in settings.INSTALLED_APPS:
        # bx_django_utils is needed for "humanize_time" template library
        # See: https://github.com/boxine/django-huey-monitor/issues/21
        errors.append(
            Warning(
                '"bx_django_utils" not in INSTALLED_APPS',
                id='huey_monitor.E001',
            )
        )

    return errors

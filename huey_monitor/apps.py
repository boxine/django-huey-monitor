from django.apps import AppConfig
from django.utils.translation import gettext_lazy as _


class HueyMonitorConfig(AppConfig):
    name = 'huey_monitor'
    verbose_name = _('huey Monitor')

    def ready(self):
        # register huey tasks
        import huey_monitor.tasks  # noqa

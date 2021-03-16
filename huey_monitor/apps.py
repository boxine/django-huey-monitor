from django.apps import AppConfig
from django.utils.translation import gettext_lazy as _


class HueyMonitorConfig(AppConfig):
    name = 'huey_monitor'
    verbose_name = _('Huey Monitor')

    def ready(self):
        """
        register our checks and huey tasks:
        """
        import huey_monitor.checks  # noqa
        import huey_monitor.tasks  # noqa

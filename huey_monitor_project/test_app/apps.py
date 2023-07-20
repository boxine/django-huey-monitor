from django.apps import AppConfig


class HueyMonitorTestAppConfig(AppConfig):
    name = 'huey_monitor_project.test_app'
    verbose_name = 'huey monitor test app'

    def ready(self):
        # register huey tasks
        import huey_monitor_project.test_app.tasks  # noqa

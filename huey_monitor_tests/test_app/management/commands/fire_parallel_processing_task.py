from django.core.management import BaseCommand

from huey_monitor_tests.test_app.tasks import parallel_task


class Command(BaseCommand):
    help = 'Just fire "parallel processing" Huey Task'

    def handle(self, *args, **options):
        parallel_task(
            task_num=3  # Create three "worker" tasks
        )

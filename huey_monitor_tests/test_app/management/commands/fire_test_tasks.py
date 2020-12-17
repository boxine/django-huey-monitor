from pathlib import Path

from django.core.management import BaseCommand

from huey_monitor_tests.test_app.tasks import delay_task, out_of_memory_task, raise_error_task, retry_and_lock_task


class Command(BaseCommand):
    help = 'Just fire some Huey Tasks to fill the database a little bit ;)'

    def handle(self, *args, **options):
        delay_task(name='test sleep 1', sleep=3)
        raise_error_task(
            error_class_name='TypeError',
            msg='test type error exception'
        )
        retry_and_lock_task(info='1', sleep=5)

        if Path('/.dockerenv').exists():
            out_of_memory_task()
        else:
            print('Skip out of memory task outside docker container ;)')

        delay_task(name='test sleep 10', sleep=10)
        raise_error_task(
            error_class_name='SystemError',
            msg='test system error exception'
        )
        delay_task(name='test sleep 60', sleep=60)
        retry_and_lock_task(info='2', sleep=10)
        retry_and_lock_task(info='3', sleep=20)

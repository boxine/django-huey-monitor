from django.core.management import BaseCommand

from huey_monitor.models import SignalInfoModel, TaskModel


class Command(BaseCommand):
    help = 'Delete all django-huey-monitor data'

    def print_delete_info(self, delete_info):
        for model_name, count in delete_info.items():
            self.stdout.write(f'{count} {model_name!r} entries deleted')

    def handle(self, *args, **options):
        self.stdout.write('Delete all Task/Signal model entries...')

        delete_info = SignalInfoModel.objects.all().delete()[1]
        self.print_delete_info(delete_info)

        # Delete tasks without signals, too:
        delete_info = TaskModel.objects.all().delete()[1]
        self.print_delete_info(delete_info)

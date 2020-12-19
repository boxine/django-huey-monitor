from django.core.management import BaseCommand

from huey_monitor.models import SignalInfoModel


class Command(BaseCommand):
    help = 'Delete all django-huey-monitor data'

    def handle(self, *args, **options):
        self.stdout.write('Delete all Task/Signal model entries...')
        delete_info = SignalInfoModel.objects.all().delete()[1]
        for model_name, count in delete_info.items():
            self.stdout.write(f'{count} {model_name!r} entries deleted')

import os

from django.contrib.auth import get_user_model
from django.contrib.staticfiles.management.commands.runserver import Command as RunServerCommand
from django.core.management import call_command


class Command(RunServerCommand):
    """
    Expand django.contrib.staticfiles runserver
    """
    help = "Setup test project and run django developer server"

    def verbose_call(self, command, *args, **kwargs):
        self.stderr.write("_" * 79)
        self.stdout.write(f"Call {command!r} with: {args!r} {kwargs!r}")
        call_command(command, *args, **kwargs)

    def handle(self, *args, **options):

        if "RUN_MAIN" not in os.environ:
            # RUN_MAIN added by auto reloader, see: django/utils/autoreload.py

            # Create migrations for our test app
            # But these migrations should never commit!
            # On changes: Just delete the SQLite file and start fresh ;)
            self.verbose_call("makemigrations")

            self.verbose_call("migrate")

            # django.contrib.staticfiles.management.commands.collectstatic.Command
            self.verbose_call("collectstatic", interactive=False, link=True)

            User = get_user_model()
            user, created = User.objects.get_or_create(username='test')
            user.is_active = True
            user.is_staff = True
            user.is_superuser = True
            if created:
                user.set_password('test123')
            user.save()

        print('\n')
        print('_' * 100)
        print('Test super user:')
        print(' * username: "test"')
        print(' * password: "test123"')
        print('\n')

        super().handle(*args, **options)

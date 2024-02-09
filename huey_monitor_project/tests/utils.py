import shutil
from pathlib import Path
from unittest import TestCase

# https://github.com/jedie/django-tools
from django_tools.unittest_utils.django_command import DjangoCommandMixin


class ForRunnersCommandTestCase(DjangoCommandMixin, TestCase):
    @classmethod
    def setUpClass(cls):
        # installed via setup.py entry points !
        cls.huey_monitor_bin = shutil.which("huey_monitor")
        cls.manage_bin = shutil.which("manage")

    def _call_huey_monitor(self, cmd, **kwargs):
        huey_monitor_path = Path(self.huey_monitor_bin)
        return self.call_manage_py(
            cmd=cmd,
            manage_dir=str(huey_monitor_path.parent),
            manage_py=huey_monitor_path.name,  # Python 3.5 needs str()
            **kwargs,
        )

    def _call_manage(self, cmd, **kwargs):
        manage_path = Path(self.manage_bin)
        return self.call_manage_py(
            cmd=cmd, manage_dir=str(manage_path.parent), manage_py=manage_path.name, **kwargs  # Python 3.5 needs str()
        )

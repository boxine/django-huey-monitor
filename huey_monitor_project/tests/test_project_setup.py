import re
import subprocess
from unittest import TestCase

from bx_py_utils.auto_doc import assert_readme_block
from bx_py_utils.path import assert_is_dir, assert_is_file
from bx_py_utils.test_utils.unittest_utils import assert_no_flat_tests_functions
from django.conf import settings
from django.core.cache import cache
from django.core.management import call_command
from manage_django_project.management.commands import code_style
from manageprojects.test_utils.project_setup import check_editor_config, get_py_max_line_length
from packaging.version import Version

from huey_monitor import __version__
from manage import BASE_PATH


def strip_ansi(text):
    return re.sub(r'\033\[[;?0-9]*[a-zA-Z]', '', text)


def assert_text_block_in_readme(text_block: str, marker: str):
    README_PATH = BASE_PATH / 'README.md'
    assert_is_file(README_PATH)

    text_block = f'```\n{text_block.strip()}\n```'
    assert_readme_block(
        readme_path=README_PATH,
        text_block=text_block,
        start_marker_line=f'[comment]: <> (✂✂✂ auto generated {marker} start ✂✂✂)',
        end_marker_line=f'[comment]: <> (✂✂✂ auto generated {marker} end ✂✂✂)',
    )


class ProjectSetupTestCase(TestCase):
    def test_project_path(self):
        project_path = settings.BASE_PATH
        assert_is_dir(project_path)
        assert_is_dir(project_path / 'huey_monitor')
        assert_is_dir(project_path / 'huey_monitor_project')

        self.assertEqual(project_path, BASE_PATH)

    def test_cache(self):
        # django cache should work in tests, because some tests "depends" on it
        cache_key = 'a-cache-key'
        self.assertIs(cache.get(cache_key), None)
        cache.set(cache_key, 'the cache content', timeout=1)
        self.assertEqual(cache.get(cache_key), 'the cache content', f'Check: {settings.CACHES=}')
        cache.delete(cache_key)
        self.assertIs(cache.get(cache_key), None)

    def test_settings(self):
        self.assertEqual(settings.SETTINGS_MODULE, 'huey_monitor_project.settings.tests')
        middlewares = [entry.rsplit('.', 1)[-1] for entry in settings.MIDDLEWARE]
        assert 'AlwaysLoggedInAsSuperUserMiddleware' not in middlewares
        assert 'DebugToolbarMiddleware' not in middlewares

    def test_version(self):
        self.assertIsNotNone(__version__)

        version = Version(__version__)  # Will raise InvalidVersion() if wrong formatted
        self.assertEqual(str(version), __version__)

        manage_bin = BASE_PATH / 'manage.py'
        assert_is_file(manage_bin)

        output = subprocess.check_output([manage_bin, 'version'], text=True)
        self.assertIn(__version__, output)

    def test_manage(self):
        manage_bin = BASE_PATH / 'manage.py'
        assert_is_file(manage_bin)

        output = subprocess.check_output([manage_bin, 'project_info'], text=True)
        self.assertIn('huey_monitor_project', output)
        self.assertIn('huey_monitor_project.settings.local', output)
        self.assertIn('huey_monitor_project.settings.tests', output)
        self.assertIn(__version__, output)

        output = subprocess.check_output([manage_bin, 'check'], text=True)
        self.assertIn('System check identified no issues (0 silenced).', output)

        output = subprocess.check_output([manage_bin, 'makemigrations'], text=True)
        self.assertIn("No changes detected", output)

    def test_code_style(self):
        call_command(code_style.Command())

    def test_check_editor_config(self):
        check_editor_config(package_root=BASE_PATH)

        max_line_length = get_py_max_line_length(package_root=BASE_PATH)
        self.assertEqual(max_line_length, 119)

    def test_no_ignored_test_function(self):
        # In the past we used pytest ;)
        # Check if we still have some flat test function that will be not executed by unittests
        assert_no_flat_tests_functions(BASE_PATH / 'huey_monitor')
        assert_no_flat_tests_functions(BASE_PATH / 'huey_monitor_project')

    def test_make_help(self):
        raw_output = subprocess.check_output(['make', 'help'], cwd=BASE_PATH, text=True)
        raw_output = strip_ansi(raw_output)
        output = []
        for line in raw_output.splitlines():
            if 'Entering directory' in line or 'Leaving directory' in line:
                continue
            output.append(line.strip())
        output = '\n'.join(output)
        self.assertIn('install huey monitor package\n', output)
        assert_text_block_in_readme(text_block=output, marker='make help')

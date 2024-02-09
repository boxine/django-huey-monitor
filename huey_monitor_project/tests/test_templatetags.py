from unittest.mock import patch

from django.test import SimpleTestCase
from huey import MemoryHuey

from huey_monitor.templatetags.huey_monitor import huey_counts_info


class HueyMonitorTemplateTagsTestCase(SimpleTestCase):
    def test_huey_counts_info(self):
        with patch('huey_monitor.templatetags.huey_monitor.HUEY', MemoryHuey()):
            html = huey_counts_info()
        self.assertHTMLEqual(html, '<p>Huey counts: Pending: 0, Scheduled: 0, Result: 0</p>')

    def test_huey_counts_info_redis_down(self):
        class HueyError:
            def __getattribute__(self, item):
                raise OSError('Redis down!')

        with patch('huey_monitor.templatetags.huey_monitor.HUEY', HueyError()), self.assertLogs(
            'huey_monitor'
        ) as logs:
            html = huey_counts_info()

        self.assertHTMLEqual(html, '<p>Huey counts: (OSError: Redis down!)</p>')
        log_message = logs.output[0]
        self.assertIn('Traceback', log_message)
        self.assertIn('raise OSError', log_message)

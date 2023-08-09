from unittest.mock import patch

from django.test import SimpleTestCase
from huey import MemoryHuey

from huey_monitor.templatetags.huey_monitor import huey_counts_info


class HueyMonitorTemplateTagsTestCase(SimpleTestCase):
    def test_huey_counts_info(self):
        with patch('huey_monitor.templatetags.huey_monitor.HUEY', MemoryHuey()):
            html = huey_counts_info()
        self.assertHTMLEqual(html, '<p>Huey counts: Pending: 0, Scheduled: 0, Result: 0</p>')

from django.test import TestCase
from model_bakery import baker

from huey_monitor.models import TaskModel


class HueyMonitorModelsTestCase(TestCase):
    def test_human_percentage(self):
        instance = baker.make(TaskModel, progress_count=10, total=None)
        self.assertIs(instance.human_percentage(), None)
        instance.total = 100
        self.assertEqual(instance.human_percentage(), '10%')

from unittest import mock

from bx_django_utils.test_utils.cache import MockCache

from bx_py_utils.test_utils.datetime import parse_dt
from django.core.cache import cache
from django.test import TestCase
from django.utils import timezone
from model_bakery import baker

from huey_monitor.models import SignalInfoModel, TaskModel
from huey_monitor.progress_cache import inc_task_progress
from huey_monitor_tests.tests.utils import ClearCacheMixin


class ModelTestCase(ClearCacheMixin, TestCase):
    def test_task_model(self):
        with MockCache() as cache_mock:
            instance = TaskModel(
                name='foo_task',
                task_id='00000000-0000-0000-0000-000000000001'
            )
            assert str(instance) == 'foo_task: None (Main task)'
            instance.full_clean()
            instance.save()
            instance = TaskModel.objects.get(task_id='00000000-0000-0000-0000-000000000001')
            assert str(instance) == 'foo_task: None (Main task)'
            assert instance.executing_dt is None
            assert instance.total_progress_count is None
            assert instance.human_percentage() is None
            assert instance.human_progress() is None
            assert instance.human_throughput() is None
            assert instance.human_progress_string() == ''
            assert instance.human_unit() is None

            assert cache_mock.data == {}

            with mock.patch.object(timezone, 'now', return_value=parse_dt('2000-01-01T00:00:00+0000')):
                instance.state = baker.make(
                    SignalInfoModel,
                    task=instance,
                    signal_name='executing',
                )
            instance.save()
            instance = TaskModel.objects.get(task_id='00000000-0000-0000-0000-000000000001')
            assert str(instance) == 'foo_task: executing (Main task)'
            assert instance.state.create_dt == parse_dt('2000-01-01T00:00:00+0000')
            assert instance.executing_dt == parse_dt('2000-01-01T00:00:00+0000')
            assert instance.total_progress_count == 0
            assert instance.human_percentage() is None
            assert instance.human_progress() == '0.00it'
            assert instance.human_throughput() is None
            assert instance.human_progress_string() == ''
            assert instance.human_unit() is None

            instance.total = 10
            instance.unit = 'parsecs'
            instance.save()
            instance = TaskModel.objects.get(task_id='00000000-0000-0000-0000-000000000001')
            assert instance.executing_dt == parse_dt('2000-01-01T00:00:00+0000')
            assert instance.total_progress_count == 0
            assert instance.human_percentage() == '0%'
            assert instance.human_progress() == '0.00parsecs'
            assert instance.human_throughput() is None
            assert instance.human_progress_string() == ''
            assert instance.human_unit() is None

            # Simulate a running task with 5/10 progress:

            assert cache_mock.data == {}

            with mock.patch.object(timezone, 'now', return_value=parse_dt('2000-01-01T00:00:05+0000')):
                inc_task_progress(task_id='00000000-0000-0000-0000-000000000001', progress_count=5)

            assert cache_mock.data == {
                'HueyMonitor-progress-00000000-0000-0000-0000-000000000001': 5,
                'HueyMonitor-timestamp-00000000-0000-0000-0000-000000000001': (
                    parse_dt('2000-01-01T00:00:05+0000')
                )
            }

            instance = TaskModel.objects.get(task_id='00000000-0000-0000-0000-000000000001')
            assert instance.executing_dt == parse_dt('2000-01-01T00:00:00+0000')
            assert instance.total_progress_count == 5
            assert instance.human_percentage() == '50%'
            assert instance.human_progress() == '5.00parsecs'
            assert instance.human_throughput() == '1.0\xa0seconds/parsecs'
            assert instance.human_progress_string() == '5/10parsecs 50% 1.0\xa0seconds/parsecs'

            # Simulate a completed task:
            cache_mock.data.clear()
            with mock.patch.object(timezone, 'now', return_value=parse_dt('2000-01-01T00:12:00+0000')):
                instance.state = baker.make(
                    SignalInfoModel,
                    task=instance,
                    signal_name='complete',
                )
            instance.finished = True
            instance.progress_count = 10
            instance.save()
            instance = TaskModel.objects.get(task_id='00000000-0000-0000-0000-000000000001')
            assert instance.state.create_dt == parse_dt('2000-01-01T00:12:00+0000')
            assert instance.executing_dt == parse_dt('2000-01-01T00:00:00+0000')
            assert instance.total_progress_count == 10
            assert instance.human_percentage() == '100%'
            assert instance.human_progress() == '10.0parsecs'
            assert instance.human_throughput() == '1.2\xa0minutes/parsecs'
            assert instance.human_progress_string() == '10/10parsecs 100% 1.2\xa0minutes/parsecs'

            assert cache_mock.data == {}

    def test_zero_division(self):
        instance = baker.make(
            TaskModel,
            name='foo_task',
            finished=True,
            total=10,
            progress_count=0,
        )
        with mock.patch.object(timezone, 'now', return_value=parse_dt('2000-01-01T00:00:00+0000')):
            baker.make(
                SignalInfoModel,
                task=instance,
                signal_name='executing',
            )
        with mock.patch.object(timezone, 'now', return_value=parse_dt('2000-01-01T00:00:05+0000')):
            instance.state = baker.make(
                SignalInfoModel,
                task=instance,
                signal_name='complete',
            )
        instance.save()
        instance.full_clean()

        instance = TaskModel.objects.get(pk=instance.pk)
        assert str(instance) == 'foo_task: 0/10it 0% (Main task)'
        assert instance.executing_dt == parse_dt('2000-01-01T00:00:00+0000')
        assert instance.human_throughput() is None  # no ZeroDivisionError
        assert instance.human_progress_string() == '0/10it 0%'

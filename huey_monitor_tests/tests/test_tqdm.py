import datetime
import time
import warnings
from pathlib import Path
from unittest import mock

from bx_django_utils.test_utils.datetime import MockDatetimeGenerator
from bx_py_utils.test_utils.datetime import parse_dt
from django.core.exceptions import ValidationError
from django.test import SimpleTestCase, TestCase
from django.utils import timezone
from huey.api import Result, Task

import huey_monitor
from huey_monitor.models import SignalInfoModel, TaskModel
from huey_monitor.tqdm import ProcessInfo
from huey_monitor_tests.test_app.tasks import linear_processing_task, parallel_task
from huey_monitor_tests.tests.utils import ClearCacheMixin


BASE_PATH = Path(huey_monitor.__file__).parent


class SleepMock:
    def __init__(self):
        self.call_count = 0
        self.progress_info = []

    def __call__(self, *args, **kwargs):
        self.add_iteration()

    def add_iteration(self):
        assert TaskModel.objects.count() == 1
        instance = TaskModel.objects.all().first()

        executing_dt = instance.executing_dt
        assert executing_dt == parse_dt('2000-01-01T00:00:02+0000')

        self.progress_info.append(
            [instance.total_progress_count, instance.elapsed_sec, str(instance)]
        )
        self.call_count += 1


class ProcessInfoTestCase(ClearCacheMixin, TestCase):
    def test_linear_processing_task(self):
        sleep_mock = SleepMock()

        offset = datetime.timedelta(seconds=1)
        with mock.patch.object(timezone, 'now', MockDatetimeGenerator(offset=offset)),\
                mock.patch.object(time, 'sleep', sleep_mock):
            linear_processing_task(desc='Foo Bar', total=10)

        assert sleep_mock.call_count == 10

        assert TaskModel.objects.count() == 1
        instance = TaskModel.objects.all().first()
        assert instance.finished is True
        assert instance.progress_count == 10
        assert instance.executing_dt == parse_dt('2000-01-01T00:00:02+0000')
        assert instance.last_update_dt == parse_dt('2000-01-01T00:00:14+0000')
        assert instance.elapsed_sec == 12

        signals = list(SignalInfoModel.objects.values_list('signal_name', flat=True))
        assert signals == ['executing', 'complete']

        # Call again, because time.sleep() are called before process_info.update(n=1) to the 100%
        sleep_mock.add_iteration()

        info = sleep_mock.progress_info
        assert info == [
            [0, None, 'Foo Bar: executing (Main task)'],
            [1, 2.0, 'Foo Bar: 1/10it 10% 2.0\xa0seconds/it (Main task)'],
            [2, 3.0, 'Foo Bar: 2/10it 20% 1.5\xa0seconds/it (Main task)'],
            [3, 4.0, 'Foo Bar: 3/10it 30% 1.3\xa0seconds/it (Main task)'],
            [4, 5.0, 'Foo Bar: 4/10it 40% 1.2\xa0seconds/it (Main task)'],
            [5, 6.0, 'Foo Bar: 5/10it 50% 1.2\xa0seconds/it (Main task)'],
            [6, 7.0, 'Foo Bar: 6/10it 60% 1.2\xa0seconds/it (Main task)'],
            [7, 8.0, 'Foo Bar: 7/10it 70% 1.1\xa0seconds/it (Main task)'],
            [8, 9.0, 'Foo Bar: 8/10it 80% 1.1\xa0seconds/it (Main task)'],
            [9, 10.0, 'Foo Bar: 9/10it 90% 1.1\xa0seconds/it (Main task)'],
            [10, 12.0, 'Foo Bar: 10/10it 100% 1.2\xa0seconds/it (Main task)']
        ]

    def test_progress_info_without_desc(self):
        sleep_mock = SleepMock()

        offset = datetime.timedelta(seconds=1)
        with mock.patch.object(timezone, 'now', MockDatetimeGenerator(offset=offset)),\
                mock.patch.object(time, 'sleep', sleep_mock):
            linear_processing_task(desc=None, total=3)

        assert sleep_mock.call_count == 3

        assert TaskModel.objects.count() == 1
        instance = TaskModel.objects.all().first()
        assert instance.finished is True
        assert instance.parent_task_id is None  # It's a main task
        assert instance.executing_dt == parse_dt('2000-01-01T00:00:02+0000')
        assert instance.last_update_dt == parse_dt('2000-01-01T00:00:07+0000')
        assert instance.elapsed_sec == 5.0
        assert instance.progress_count == 3

        # Call again, because time.sleep() are called before process_info.update(n=1) to the 100%
        sleep_mock.add_iteration()

        info = sleep_mock.progress_info
        assert info == [
            [None, None, 'linear_processing_task: executing (Main task)'],
            [1, 2.0, 'linear_processing_task: 1/3it 33% 2.0\xa0seconds/it (Main task)'],
            [2, 3.0, 'linear_processing_task: 2/3it 67% 1.5\xa0seconds/it (Main task)'],
            [3, 5.0, 'linear_processing_task: 3/3it 100% 1.7\xa0seconds/it (Main task)']
        ]

    def test_progress_info_without_total(self):
        sleep_mock = SleepMock()

        offset = datetime.timedelta(seconds=1)
        with mock.patch.object(timezone, 'now', MockDatetimeGenerator(offset=offset)),\
                mock.patch.object(time, 'sleep', sleep_mock):
            linear_processing_task(desc='Without total', total=3, no_total=True)

        # Add the last entry, executed after time.sleep() so not captured, yet:
        sleep_mock.add_iteration()

        info = sleep_mock.progress_info
        assert info == [
            [None, None, 'Without total: executing (Main task)'],
            [1, 2.0, 'Without total: 1it 2.0\xa0seconds/it (Main task)'],
            [2, 3.0, 'Without total: 2it 1.5\xa0seconds/it (Main task)'],
            [3, 5.0, 'Without total: 3it 1.7\xa0seconds/it (Main task)']
        ]

    def test_parallel_task(self):
        assert TaskModel.objects.count() == 0

        class TimeSleepNoop:
            def __call__(self, *args, **kwargs):
                pass

        offset = datetime.timedelta(seconds=1)
        with mock.patch.object(timezone, 'now', MockDatetimeGenerator(offset=offset)),\
                mock.patch.object(time, 'sleep', TimeSleepNoop()):
            task_result = parallel_task(
                total=10,
                task_num=2
            )

        assert TaskModel.objects.count() == 3

        assert isinstance(task_result, Result)
        main_task_id = task_result.task.id

        main_task_instance = TaskModel.objects.get(pk=main_task_id)
        assert main_task_instance.total == 10
        assert main_task_instance.finished is True
        assert main_task_instance.progress_count == 10
        assert main_task_instance.total_progress_count == 10

        sub_tasks = TaskModel.objects.filter(parent_task=main_task_instance).order_by('update_dt')
        values = list(
            sub_tasks.values_list('name', 'state__signal_name', 'finished', 'progress_count')
        )
        assert values == [
            ('parallel_sub_task', 'complete', True, 5),
            ('parallel_sub_task', 'complete', True, 5)
        ]

        # Note: The MockDatetimeGenerator doesn't iterate on every task call!
        # So we get irregular values here ;)

        assert main_task_instance.executing_dt == parse_dt('2000-01-01T00:00:02+0000')
        assert main_task_instance.last_update_dt == parse_dt('2000-01-01T00:00:26+0000')
        assert main_task_instance.human_progress_string() == '10/10it 100% 2.4\xa0seconds/it'
        assert str(main_task_instance) == (
            'parallel_task: 10/10it 100% 2.4\xa0seconds/it (Main task)'
        )

        # Note: Huey is in immediate mode, so the tasks executes synchronously!

        sub_tasks1 = sub_tasks[0]
        assert sub_tasks1.total == 5
        assert sub_tasks1.finished is True
        assert sub_tasks1.progress_count == 5
        assert sub_tasks1.total_progress_count == 5
        assert sub_tasks1.human_progress_string() == '5/5it 100% 1.6\xa0seconds/it'
        assert str(sub_tasks1) == (
            'parallel_sub_task: 5/5it 100% 1.6\xa0seconds/it (Sub task of parallel_task)'
        )

        sub_tasks2 = sub_tasks[1]
        assert sub_tasks2.total == 5
        assert sub_tasks2.finished is True
        assert sub_tasks2.progress_count == 5
        assert sub_tasks2.total_progress_count == 5
        assert sub_tasks2.human_progress_string() == '5/5it 100% 1.6\xa0seconds/it'
        assert str(sub_tasks2) == (
            'parallel_sub_task: 5/5it 100% 1.6\xa0seconds/it (Sub task of parallel_task)'
        )

    def test_process_description_overlong(self):
        TaskModel.objects.create(task_id='00000000-0000-0000-0000-000000000001')

        # Test with current max length:
        max_length = TaskModel._meta.get_field('desc').max_length
        assert max_length == 64

        task = Task(id='00000000-0000-0000-0000-000000000001')

        # Set max length description:
        with self.assertLogs('huey_monitor.tqdm') as logs:
            ProcessInfo(task, desc='X' * max_length)
            instance = TaskModel.objects.get()
            assert instance.desc == 'X' * max_length

        assert logs.output == [
            (
                'INFO:huey_monitor.tqdm:Init TaskModel Task'
                ' - XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX'
                ' 0/Noneit (divisor: 1000)'
            )
        ]

        # Overlong description should be cut:
        msg = (
            '["Process info description overlong:'
            ' \'YYYYYYYYYYYYYYYYYYYYYYYYYYYYYYYYYYYYYYYYYYYYYYYYYYYYYYYYYYYYYYYYY\'"]'
        )
        with self.assertRaisesMessage(ValidationError, msg):
            ProcessInfo(task, desc='Y' * (max_length + 1), total=999)

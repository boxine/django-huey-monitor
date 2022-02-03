import datetime
import time
from pathlib import Path
from unittest import mock

from bx_django_utils.test_utils.datetime import MockDatetimeGenerator
from bx_py_utils.test_utils.datetime import parse_dt
from django.core.exceptions import ValidationError
from django.test import TestCase
from django.utils import timezone
from huey.api import Result, Task

import huey_monitor
from huey_monitor.models import SignalInfoModel, TaskModel
from huey_monitor.tqdm import ProcessInfo
from huey_monitor_tests.test_app.tasks import linear_processing_task, parallel_task


BASE_PATH = Path(huey_monitor.__file__).parent


class SleepMock:
    def __init__(self):
        self.count = 0
        self.progress_info = []

    def __call__(self, *args, **kwargs):
        self.add_iteration()

    def add_iteration(self):
        assert TaskModel.objects.count() == 1
        instance = TaskModel.objects.all().first()

        executing_dt = instance.executing_dt
        assert executing_dt == parse_dt('2000-01-01T00:00:02+0000')

        self.progress_info.append([self.count, instance.elapsed_sec, str(instance)])

        self.count += 1


class ProcessInfoTestCase(TestCase):
    def test_linear_processing_task(self):
        sleep_mock = SleepMock()

        offset = datetime.timedelta(seconds=1)
        with mock.patch.object(timezone, 'now', MockDatetimeGenerator(offset=offset)),\
                mock.patch.object(time, 'sleep', sleep_mock):
            linear_processing_task(desc='Foo Bar', total=10)

        signals = list(SignalInfoModel.objects.values_list('signal_name', flat=True))
        assert signals == ['executing', 'complete']

        # Add the last entry, executed after time.sleep() so not captured, yet:
        sleep_mock.add_iteration()

        info = sleep_mock.progress_info
        assert info == [
            [0, 1.0, 'Foo Bar: 0/10it 0% 0/it (Main task)'],
            [1, 2.0, 'Foo Bar: 1/10it 10% 2.0\xa0seconds/it (Main task)'],
            [2, 3.0, 'Foo Bar: 2/10it 20% 1.5\xa0seconds/it (Main task)'],
            [3, 4.0, 'Foo Bar: 3/10it 30% 1.3\xa0seconds/it (Main task)'],
            [4, 5.0, 'Foo Bar: 4/10it 40% 1.2\xa0seconds/it (Main task)'],
            [5, 6.0, 'Foo Bar: 5/10it 50% 1.2\xa0seconds/it (Main task)'],
            [6, 7.0, 'Foo Bar: 6/10it 60% 1.2\xa0seconds/it (Main task)'],
            [7, 8.0, 'Foo Bar: 7/10it 70% 1.1\xa0seconds/it (Main task)'],
            [8, 9.0, 'Foo Bar: 8/10it 80% 1.1\xa0seconds/it (Main task)'],
            [9, 10.0, 'Foo Bar: 9/10it 90% 1.1\xa0seconds/it (Main task)'],
            [10, 13.0, 'Foo Bar: 10/10it 100% 1.3\xa0seconds/it finished (Main task)'],
        ]

    def test_progress_info_without_desc(self):
        sleep_mock = SleepMock()

        offset = datetime.timedelta(seconds=1)
        with mock.patch.object(timezone, 'now', MockDatetimeGenerator(offset=offset)),\
                mock.patch.object(time, 'sleep', sleep_mock):
            linear_processing_task(desc=None, total=3)

        # Add the last entry, executed after time.sleep() so not captured, yet:
        sleep_mock.add_iteration()

        info = sleep_mock.progress_info
        assert info == [
            [0, 1.0, 'linear_processing_task: 0/3it 0% 0/it (Main task)'],
            [1, 2.0, 'linear_processing_task: 1/3it 33% 2.0\xa0seconds/it (Main task)'],
            [2, 3.0, 'linear_processing_task: 2/3it 67% 1.5\xa0seconds/it (Main task)'],
            [3, 6.0, 'linear_processing_task: 3/3it 100% 2.0\xa0seconds/it finished (Main task)'],
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
            [0, 1.0, 'Without total: 0it 0/it (Main task)'],
            [1, 2.0, 'Without total: 1it 2.0\xa0seconds/it (Main task)'],
            [2, 3.0, 'Without total: 2it 1.5\xa0seconds/it (Main task)'],
            [3, 6.0, 'Without total: 3it 2.0\xa0seconds/it finished (Main task)'],
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
        assert main_task_instance.human_progress_string() == (
            '10/10it 100% 2.5 seconds/it finished'
        )
        assert str(main_task_instance) == (
            'parallel_task: 10/10it 100% 2.5 seconds/it finished (Main task)'
        )

        sub_tasks = TaskModel.objects.filter(parent_task=main_task_instance).order_by('update_dt')
        values = list(sub_tasks.values_list('name', 'state__signal_name'))
        assert values == [
            ('parallel_sub_task', 'complete'),
            ('parallel_sub_task', 'complete')
        ]

        # Note: Huey is in immediate mode, so the tasks executes synchronously!

        sub_tasks1 = sub_tasks[0]
        assert sub_tasks1.human_progress_string() == '5/5it 100% 1.8 seconds/it finished'
        assert str(sub_tasks1) == (
            'parallel_sub_task: 5/5it 100% 1.8 seconds/it finished (Sub task of parallel_task)'
        )

        sub_tasks2 = sub_tasks[1]
        assert sub_tasks2.human_progress_string() == '5/5it 100% 1.8 seconds/it finished'
        assert str(sub_tasks2) == (
            'parallel_sub_task: 5/5it 100% 1.8 seconds/it finished (Sub task of parallel_task)'
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

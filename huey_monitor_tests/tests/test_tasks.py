from django.test import TestCase
from huey.api import Result

from huey_monitor.models import SignalInfoModel, TaskModel
from huey_monitor_tests.test_app.tasks import main_task


class TasksTestCase(TestCase):

    def test_main_sub_task(self):
        assert TaskModel.objects.count() == 0
        assert SignalInfoModel.objects.count() == 0

        task_result = main_task()

        assert TaskModel.objects.count() == 4
        assert SignalInfoModel.objects.count()

        assert isinstance(task_result, Result)
        task_id = task_result.task.id

        main_task_instance = TaskModel.objects.get(pk=task_id)
        assert str(main_task_instance) == 'main_task: complete (Main task)'

        sub_tasks = TaskModel.objects.filter(parent_task=main_task_instance).order_by('-update_dt')
        values = list(sub_tasks.values_list('name', 'state__signal_name'))
        assert values == [
            ('sub_task', 'complete'),
            ('sub_task', 'error'),
            ('sub_task', 'complete')
        ]
        errored_sub_task = sub_tasks[1]
        assert errored_sub_task.state.exception_line == 'This sub task should be raise an error ;)'

from bx_py_utils.test_utils.html_assertion import HtmlAssertionMixin
from django.contrib.auth.models import User
from django.test import TestCase

from huey_monitor.models import SignalInfoModel, TaskModel
from huey_monitor_tests.test_app.tasks import delay_task, raise_error_task


class HueyMonitorTestCase(HtmlAssertionMixin, TestCase):

    @classmethod
    def setUpTestData(cls):
        """Load initial data for the TestCase."""
        cls.superuser = User.objects.create_superuser(
            username='test',
            email='',
            password='t'
        )

    def test_delay_task(self):
        assert TaskModel.objects.count() == 0
        assert SignalInfoModel.objects.count() == 0

        delay_task(name='test-delay', sleep=0.001)

        assert TaskModel.objects.count() == 1
        task_model_instance = TaskModel.objects.first()

        signals = list(SignalInfoModel.objects.order_by('create_dt').values_list(
            'task_id', 'signal_name', 'exception_line'
        ))
        assert signals == [
            (task_model_instance.pk, 'executing', ''),
            (task_model_instance.pk, 'complete', ''),
        ]

        assert task_model_instance.state.signal_name == 'complete'
        url = f'/admin/huey_monitor/taskmodel/{task_model_instance.pk}/change/'
        assert task_model_instance.admin_link() == url

        self.client.force_login(self.superuser)
        response = self.client.get(url)
        assert response.status_code == 200
        self.assertTemplateUsed(response, 'admin/change_form.html')
        self.assert_html_parts(response, parts=(
            '<title>View Task | Django site admin</title>',

            '<div class="readonly">delay_task</div>',

            '<td>complete</td>',
            '<td>executing</td>',
        ))

    def test_raise_error_task(self):
        assert TaskModel.objects.count() == 0
        assert SignalInfoModel.objects.count() == 0

        raise_error_task(
            error_class_name='AssertionError',
            msg='This is a test exception'
        )

        assert TaskModel.objects.count() == 1

        signals = list(SignalInfoModel.objects.order_by('create_dt').values_list(
            'signal_name', 'exception_line'
        ))
        assert signals == [
            ('executing', ''),
            ('error', 'This is a test exception'),
        ]

        error_signal = SignalInfoModel.objects.get(signal_name='error')
        url = f'/admin/huey_monitor/signalinfomodel/{error_signal.pk}/change/'
        assert error_signal.admin_link() == url

        self.client.force_login(self.superuser)
        response = self.client.get(url)
        assert response.status_code == 200
        self.assertTemplateUsed(response, 'admin/change_form.html')
        self.assert_html_parts(response, parts=(
            '<title>View Task Signal | Django site admin</title>',

            '<div class="readonly">error</div>',
            '<div class="readonly">This is a test exception</div>',

            'Traceback (most recent call last):',
            'AssertionError: This is a test exception',
        ))

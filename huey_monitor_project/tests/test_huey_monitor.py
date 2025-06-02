from bx_django_utils.test_utils.html_assertion import HtmlAssertionMixin
from django import VERSION as DJANGO_VERSION
from django.contrib.auth.models import User
from django.test import TestCase, override_settings

from huey_monitor.models import SignalInfoModel, TaskModel
from huey_monitor_project.test_app.tasks import delay_task, raise_error_task


class HueyMonitorTestCase(HtmlAssertionMixin, TestCase):
    @classmethod
    def setUpTestData(cls):
        """Load initial data for the TestCase."""
        cls.superuser = User.objects.create_superuser(username='test', email='', password='t')

    def test_delay_task(self):
        assert TaskModel.objects.count() == 0
        assert SignalInfoModel.objects.count() == 0

        delay_task(name='test-delay', sleep=0.001)

        assert TaskModel.objects.count() == 1
        task_model_instance = TaskModel.objects.first()

        signals = list(
            SignalInfoModel.objects.order_by('create_dt').values_list('task_id', 'signal_name', 'exception_line')
        )
        self.assertEqual(
            signals,
            [
                (task_model_instance.pk, 'enqueued', ''),
                (task_model_instance.pk, 'executing', ''),
                (task_model_instance.pk, 'complete', ''),
            ],
        )

        assert task_model_instance.state.signal_name == 'complete'
        url = f'/admin/huey_monitor/taskmodel/{task_model_instance.pk}/change/'
        assert task_model_instance.admin_link() == url

        self.client.force_login(self.superuser)
        response = self.client.get(url)
        assert response.status_code == 200
        self.assertTemplateUsed(response, 'admin/change_form.html')

        title = 'View Task | Django site admin'
        if DJANGO_VERSION >= (3, 2):
            title = f'delay_task: finished (Main task) | {title}'

        self.assert_html_parts(
            response,
            parts=(
                f'<title>{title}</title>',
                '<div class="readonly">delay_task</div>',
                '<td>complete</td>',
                '<td>executing</td>',
            ),
        )

    def test_raise_error_task(self):
        assert TaskModel.objects.count() == 0
        assert SignalInfoModel.objects.count() == 0

        raise_error_task(error_class_name='AssertionError', msg='This is a test exception')

        assert TaskModel.objects.count() == 1

        signals = list(SignalInfoModel.objects.order_by('create_dt').values_list('signal_name', 'exception_line'))
        self.assertEqual(
            signals,
            [
                ('enqueued', ''),
                ('executing', ''),
                ('error', 'This is a test exception'),
            ],
        )

        error_signal = SignalInfoModel.objects.get(signal_name='error')
        url = f'/admin/huey_monitor/signalinfomodel/{error_signal.pk}/change/'
        assert error_signal.admin_link() == url

        self.client.force_login(self.superuser)
        response = self.client.get(url)
        assert response.status_code == 200
        self.assertTemplateUsed(response, 'admin/change_form.html')

        title = 'View Task Signal | Django site admin'
        if DJANGO_VERSION >= (3, 2):
            title = f'error - This is a test exception | {title}'

        self.assert_html_parts(
            response,
            parts=(
                f'<title>{title}</title>',
                '<div class="readonly">error</div>',
                '<div class="readonly">This is a test exception</div>',
                'Traceback (most recent call last):',
                'AssertionError: This is a test exception',
            ),
        )

    def test_admin_flush_locks_view(self):
        flush_locks_url = '/admin/huey_monitor/taskmodel/flush_locks/'
        response = self.client.get(flush_locks_url)
        self.assertRedirects(response, expected_url='/admin/login/?next=/admin/huey_monitor/taskmodel/flush_locks/')
        self.assert_messages(response, expected_messages=[])

        self.client.force_login(self.superuser)
        response = self.client.get(flush_locks_url)
        self.assertRedirects(response, expected_url='/admin/huey_monitor/taskmodel/')
        self.assert_messages(response, expected_messages=['No tasks locks exists, nothing to flush, ok.'])

    def test_signalinfo_model_list_filter_overwrite(self):
        self.client.force_login(self.superuser)

        if DJANGO_VERSION < (4, 0):
            # Django 3.2 used other html for the filter
            START_TAG, END_TAG = ('<h3>', '</h3>')
        else:
            START_TAG, END_TAG = ('<summary>', '</summary>')

        FILTER_BY_HOSTNAME_HTML = f'{START_TAG}By Hostname{END_TAG}'

        # Default TaskModelAdmin.list_filter should be used:
        with override_settings(HUEY_MONITOR_SIGNAL_INFO_MODEL_LIST_FILTER=None):
            response = self.client.get('/admin/huey_monitor/signalinfomodel/')
        self.assert_html_parts(
            response,
            parts=(
                '<h1>Select Task Signal to view</h1>',
                f'{START_TAG}By Task name{END_TAG}',
                f'{START_TAG}By Signal Name{END_TAG}',
                FILTER_BY_HOSTNAME_HTML,  # filter by hostname exists
            ),
        )

        # Override TaskModelAdmin.list_filter and don't include hostname filter:
        with override_settings(HUEY_MONITOR_SIGNAL_INFO_MODEL_LIST_FILTER=('task__name', 'signal_name')):
            response = self.client.get('/admin/huey_monitor/signalinfomodel/')
        self.assert_html_parts(
            response,
            parts=(
                '<h1>Select Task Signal to view</h1>',
                f'{START_TAG}By Task name{END_TAG}',
                f'{START_TAG}By Signal Name{END_TAG}',
            ),
        )
        self.assert_parts_not_in_html(response, parts=(FILTER_BY_HOSTNAME_HTML,))

    def test_task_model_list_filter_overwrite(self):
        self.client.force_login(self.superuser)

        if DJANGO_VERSION < (4, 0):
            # Django 3.2 used other html for the filter
            START_TAG, END_TAG = ('<h3>', '</h3>')
        else:
            START_TAG, END_TAG = ('<summary>', '</summary>')

        FILTER_BY_HOSTNAME_HTML = f'{START_TAG}By Hostname{END_TAG}'

        # Default TaskModelAdmin.list_filter should be used:
        with override_settings(HUEY_MONITOR_TASK_MODEL_LIST_FILTER=None):
            response = self.client.get('/admin/huey_monitor/taskmodel/')
        self.assert_html_parts(
            response,
            parts=(
                '<h1>Select Task to view</h1>',
                f'{START_TAG}By Task name{END_TAG}',
                f'{START_TAG}By Signal Name{END_TAG}',
                FILTER_BY_HOSTNAME_HTML,  # filter by hostname exists
            ),
        )

        # Override TaskModelAdmin.list_filter and don't include hostname filter:
        with override_settings(HUEY_MONITOR_TASK_MODEL_LIST_FILTER=('name', 'state__signal_name')):
            response = self.client.get('/admin/huey_monitor/taskmodel/')
        self.assert_html_parts(
            response,
            parts=(
                '<h1>Select Task to view</h1>',
                f'{START_TAG}By Task name{END_TAG}',
                f'{START_TAG}By Signal Name{END_TAG}',
            ),
        )
        self.assert_parts_not_in_html(response, parts=(FILTER_BY_HOSTNAME_HTML,))

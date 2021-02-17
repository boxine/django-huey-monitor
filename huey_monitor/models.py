import logging
import uuid

from bx_py_utils.models.timetracking import TimetrackingBaseModel
from django.db import models
from django.urls import reverse
from django.utils.translation import gettext_lazy as _


logger = logging.getLogger(__name__)


class TaskManager(models.Manager):
    def set_parent_task(self, main_task_id, sub_task_id):
        """
        Save relationship between a task that calls another task.
        """
        logger.info('Set %s as sub task of %s', sub_task_id, main_task_id)
        instance = self.get(task_id=sub_task_id)
        instance.parent_task_id = main_task_id
        instance.save(update_fields=('parent_task',))


class TaskModel(TimetrackingBaseModel):
    objects = TaskManager()

    task_id = models.UUIDField(
        primary_key=True,
        verbose_name=_('Task UUID'),
        help_text=_('The UUID of the Huey-Task'),
    )
    parent_task = models.ForeignKey(
        to='self',
        null=True, blank=True,
        editable=False,
        related_name='+',
        on_delete=models.CASCADE,
        verbose_name=_('Parent Task'),
        help_text=_('Only set if this task is a sub task started from his parent.'),
    )
    name = models.CharField(
        max_length=128,
        verbose_name=_('Task name'),
    )
    state = models.ForeignKey(
        'huey_monitor.SignalInfoModel',
        null=True, blank=True,
        related_name='+',
        on_delete=models.CASCADE,
        verbose_name=_('State'),
        help_text=_('Last Signal information'),
    )

    def admin_link(self):
        url = reverse('admin:huey_monitor_taskmodel_change', args=[self.pk])
        return url

    def __str__(self):
        if self.parent_task_id:
            return f'{self.task_id} - {self.name} (Sub task of {self.parent_task_id})'
        else:
            return f'{self.task_id} - {self.name} (Main task)'

    class Meta:
        verbose_name = _('Task')
        verbose_name_plural = _('Tasks')


class SignalInfoModel(models.Model):
    id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False,
    )

    hostname = models.CharField(
        max_length=128,
        verbose_name=_('Hostname'),
        help_text=_('Hostname of the machine that creates this Signal'),
    )
    pid = models.PositiveIntegerField(
        verbose_name=_('PID'),
        help_text=_('Process ID that creates this Signal'),
    )
    thread = models.CharField(
        max_length=128,
        verbose_name=_('Thread Name'),
        help_text=_('Name of the thread that creates this Signal'),
    )

    task = models.ForeignKey(
        'huey_monitor.TaskModel',
        on_delete=models.CASCADE,
        related_name='signals',
        verbose_name=_('Task'),
        help_text=_('The Task instance for this Signal Info entry.'),
    )
    signal_name = models.CharField(
        max_length=128,
        verbose_name=_('Signal Name'),
        help_text=_('Name of the signal'),
    )
    exception_line = models.TextField(
        max_length=128,
        verbose_name=_('Exception Line'),
    )
    exception = models.TextField(
        null=True, blank=True,
        verbose_name=_('Exception'),
        help_text=_('Full information of a exception'),
    )
    create_dt = models.DateTimeField(
        auto_now_add=True,
        verbose_name=_('Create date'),
        help_text=_('(will be set automatically)')
    )

    def admin_link(self):
        url = reverse('admin:huey_monitor_signalinfomodel_change', args=[self.pk])
        return url

    def __str__(self):
        if self.exception_line:
            return f'{self.signal_name} - {self.exception_line}'
        return self.signal_name

    class Meta:
        verbose_name = _('Task Signal')
        verbose_name_plural = _('Task Signals')

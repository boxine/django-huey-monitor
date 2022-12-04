import logging
import uuid

from bx_django_utils.models.timetracking import TimetrackingBaseModel
from django.db import models
from django.urls import reverse
from django.utils.translation import gettext
from django.utils.translation import gettext_lazy as _
from huey.signals import SIGNAL_EXECUTING

from huey_monitor.constants import TASK_MODEL_DESC_MAX_LENGTH
from huey_monitor.humanize import format_sizeof, percentage, throughput


try:
    from functools import cached_property  # new in Python 3.8
except ImportError:
    from django.utils.functional import cached_property


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
        related_name='sub_tasks',
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
    finished = models.BooleanField(
        default=False,
        verbose_name=_('Finished'),
        help_text=_(
            'Indicates that this Task no longer waits or run.'
            ' (It does not mean that execution was successfully completed.)'
        ),
    )

    desc = models.CharField(
        max_length=TASK_MODEL_DESC_MAX_LENGTH,
        default='',
        blank=True,
        verbose_name=_('Description'),
        help_text=_('Prefix for progress information'),
    )
    total = models.PositiveIntegerField(
        null=True, blank=True,
        help_text=_('The number of expected iterations')
    )
    progress_count = models.PositiveIntegerField(
        null=True,
        blank=True,
        verbose_name=_('Progress Count'),
        help_text=_('Number of units processed (If provided)'),
    )
    cumulate_progress = models.BooleanField(
        default=True,
        verbose_name=_('Cumulate Progress?'),
        help_text=_(
            'Should the progress of the sub tasks be added up and saved in the parent task?'
            ' (Will be done after the task has ended)'
        ),
    )
    unit = models.CharField(
        max_length=64,
        default='it',
        help_text=_('String that will be used to define the unit of each iteration'),
    )
    unit_divisor = models.PositiveIntegerField(
        default=1000,
        help_text=_('Used to convert the units.'),
    )

    @cached_property
    def executing_dt(self):
        executing_signal = SignalInfoModel.objects.filter(
            task_id=self.task_id,
            signal_name=SIGNAL_EXECUTING
        ).only('create_dt').first()
        if executing_signal:
            return executing_signal.create_dt

    @cached_property
    def elapsed_sec(self):
        if self.progress_count is not None:  # tqdm is used
            dt_diff = self.update_dt - self.executing_dt
            return dt_diff.total_seconds()

    def human_percentage(self):
        if self.progress_count is not None and self.total is not None:
            return percentage(num=self.progress_count, total=self.total)
    human_percentage.short_description = _('percentage')

    def human_progress(self):
        if self.progress_count is not None:  # tqdm is used
            return format_sizeof(
                num=self.progress_count, suffix=self.unit, divisor=self.unit_divisor
            )
    human_progress.short_description = _('progress')

    def human_throughput(self):
        if self.progress_count is not None:  # tqdm is used
            return throughput(
                num=self.progress_count,
                elapsed_sec=self.elapsed_sec,
                suffix=self.unit,
                divisor=self.unit_divisor
            )
    human_throughput.short_description = _('throughput')

    def human_progress_string(self):
        parts = []
        if self.progress_count is None:  # tqdm is not used
            pass
        elif self.total:
            parts.append(f'{self.progress_count}/{self.total}{self.unit}')
            parts.append(self.human_percentage())
            parts.append(self.human_throughput())
        else:
            # Progress info without total number
            parts.append(f'{self.progress_count}{self.unit}')
            parts.append(self.human_throughput())

        if self.finished:
            parts.append(gettext('finished'))

        return ' '.join(parts)
    human_progress_string.short_description = _('Progress')

    def human_unit(self):
        """
        Used in admin: Display the unit only if process info used.
        """
        if self.progress_count is not None:  # tqdm is used
            return self.unit
    human_unit.short_description = _('Unit')

    def admin_link(self):
        url = reverse('admin:huey_monitor_taskmodel_change', args=[self.pk])
        return url

    def __str__(self):
        parts = []
        if self.desc:
            parts.append(f'{self.desc}:')
        else:
            # Fallback and use the task name:
            parts.append(f'{self.name}:')

        progress_string = self.human_progress_string()
        if progress_string:
            parts.append(progress_string)
        else:
            # wait for execution or a task without progress information
            parts.append(str(self.state))

        if self.parent_task_id:
            parts.append(f'(Sub task of {self.parent_task.name})')
        else:
            parts.append('(Main task)')

        return ' '.join(parts)

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
        blank=True,
        verbose_name=_('Exception Line'),
    )
    exception = models.TextField(
        null=True, blank=True,
        verbose_name=_('Exception'),
        help_text=_('Full information of a exception'),
    )
    progress_count = models.PositiveIntegerField(
        null=True,
        blank=True,
        verbose_name=_('Progress Count'),
        help_text=_('Progress (if any) at the time of creation.'),
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

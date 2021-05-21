import logging
import uuid

from bx_django_utils.models.timetracking import TimetrackingBaseModel
from django.db import models
from django.db.models import Sum
from django.urls import reverse
from django.utils.translation import gettext_lazy as _
from huey.signals import SIGNAL_EXECUTING

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

    desc = models.CharField(
        max_length=64, default='',
        verbose_name=_('Description'),
        help_text=_('Prefix for progress information'),
    )
    total = models.PositiveIntegerField(
        null=True, blank=True,
        help_text=_('The number of expected iterations')
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
    def progress_info(self):
        progress_count = TaskProgressModel.objects.get_progress_info(task_id=self.task_id)
        if progress_count and self.executing_dt:
            dt_diff = self.update_dt - self.executing_dt
            elapsed_sec = dt_diff.total_seconds()
        else:
            elapsed_sec = None
        return progress_count, elapsed_sec

    def human_percentage(self):
        progress_count, elapsed_sec = self.progress_info
        if progress_count and self.total is not None:
            return percentage(num=progress_count, total=self.total)
    human_percentage.short_description = _('percentage')

    def human_progress(self):
        progress_count, elapsed_sec = self.progress_info
        if progress_count:
            return format_sizeof(
                num=progress_count,
                suffix=self.unit,
                divisor=self.unit_divisor
            )
    human_progress.short_description = _('progress')

    def human_throughput(self):
        progress_count, elapsed_sec = self.progress_info
        if progress_count and elapsed_sec:
            return throughput(
                num=progress_count,
                elapsed_sec=elapsed_sec,
                suffix=self.unit,
                divisor=self.unit_divisor
            )
    human_throughput.short_description = _('throughput')

    def human_progress_string(self):
        progress_count, elapsed_sec = self.progress_info

        parts = []
        if progress_count is None or elapsed_sec is None:
            return ''
        elif self.total:
            parts.append(f'{progress_count}/{self.total}{self.unit}')
            parts.append(self.human_percentage())
            parts.append(self.human_throughput())
        else:
            # Progress info without total number
            parts.append(f'{progress_count}{self.unit}')
            parts.append(self.human_throughput())

        return ' '.join(parts)
    human_progress_string.short_description = _('Progress')

    def human_unit(self):
        """
        Used in admin: Display the unit only if process info used.
        """
        progress_count, elapsed_sec = self.progress_info
        if progress_count or elapsed_sec:
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


class TaskProgressManager(models.Manager):
    def get_progress_info(self, task_id):
        qs = self.all().filter(
            task_id=task_id
        ).aggregate(
            Sum('progress_count'),
        )
        progress_count = qs['progress_count__sum'] or 0
        return progress_count


class TaskProgressModel(models.Model):
    objects = TaskProgressManager()

    id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False,
    )

    task = models.ForeignKey(
        'huey_monitor.TaskModel',
        on_delete=models.CASCADE,
        related_name='progress',
        verbose_name=_('Task'),
        help_text=_('The Task instance for this processed info entry.'),
    )
    progress_count = models.PositiveIntegerField(
        null=True, blank=True,
        verbose_name=_('Progress Count'),
        help_text=_('Number of units processed in current update.'),
    )
    create_dt = models.DateTimeField(
        auto_now_add=True,
        verbose_name=_('Create date'),
        help_text=_('(will be set automatically)')
    )

    def human_progress_count(self):
        if self.progress_count:
            return format_sizeof(
                num=self.progress_count,
                suffix=self.task.unit,
                divisor=self.task.unit_divisor
            )

    def admin_link(self):
        url = reverse('admin:huey_monitor_taskprogressmodel_change', args=[self.pk])
        return url

    def __str__(self):
        return f'{self.task.name} {self.human_progress_count()}'

    class Meta:
        verbose_name = _('Task Progress')
        verbose_name_plural = _('Task Progress')

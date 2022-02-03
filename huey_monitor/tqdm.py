import logging
import warnings

from django.core.exceptions import ValidationError
from huey.api import Task

from huey_monitor.models import TaskModel
from huey_monitor.progress_cache import inc_task_progress


logger = logging.getLogger(__name__)


class ProcessInfo:
    """
    Simple helper inspired by tqdm ;)
    """

    def __init__(
        self,
        task,
        *,
        desc=None,
        total=None,
        unit='it',
        unit_divisor=1000,
        parent_task_id=None,
        cumulate2parents=None,  # deprecated see #57
    ):
        """
        Parameters
        ----------
        task: Huey task instance for this progress information
        desc: str, optional: Prefix for the progressbar.
        total: int, optional: The number of expected iterations.
        unit: str, optional: String that will be used to define the unit of each iteration
        unit_divisor: int, optional
        parent_task_id: int, optional: Huey Task ID if a parent Tasks exists.
        """
        assert isinstance(task, Task), f'No task given: {task!r} (Hint: use "context=True")'
        self.task = task
        self.desc = desc or ''
        self.total = total
        self.unit = unit
        self.unit_divisor = unit_divisor
        self.parent_task_id = parent_task_id

        if cumulate2parents is not None:
            warnings.warn(
                '"cumulate2parents" argument will be remove in the future!',
                PendingDeprecationWarning,
            )

        if len(self.desc) > 64:
            # We call .update() that will not validate the data, so a overlong
            # description will raise a database error and maybe a user doesn't know
            # what's happen ;)
            raise ValidationError(
                'Process info description overlong: %(desc)r',
                params={'desc': self.desc},
            )

        TaskModel.objects.filter(task_id=task.id).update(
            desc=self.desc,
            total=self.total,
            unit=self.unit,
            unit_divisor=self.unit_divisor,
        )

        self.total_progress = 0

        logger.info('Init TaskModel %s', self)

    def update(self, n=1):
        """
        Store the progress information
        """
        self.total_progress = inc_task_progress(
            task_id=self.task.id, progress_count=n, cumulate2parents=self.cumulate2parents
        )

    def __str__(self):
        return (
            f'{self.task.name} - {self.desc} {self.total_progress}/{self.total}{self.unit}'
            f' (divisor: {self.unit_divisor})'
        )

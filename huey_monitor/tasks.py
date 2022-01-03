import logging
import os
import socket
import sys
import threading
import traceback
import uuid
from functools import lru_cache

from django.db import transaction
from django.db.models import Sum
from huey.contrib.djhuey import on_startup, signal

from huey_monitor.constants import ENDED_HUEY_SIGNALS
from huey_monitor.models import SignalInfoModel, TaskModel
from huey_monitor.progress_cache import cleanup_cache, get_progress_count, get_total_progress_count


logger = logging.getLogger(__name__)


@lru_cache(maxsize=None)
def get_hostname():
    return socket.gethostname()


@signal()
def store_signals(signal, task, exc=None):
    """
    Store all Huey signals.
    """
    task_id = uuid.UUID(task.id)

    # Task no longer waits or run?
    task_finished = signal in ENDED_HUEY_SIGNALS

    logger.info('Store Task %s signal %r (finished: %s)', task_id, signal, task_finished)

    signal_kwargs = {
        # TODO: move parts into huey_monitor.models.SignalInfoManager
        'hostname': get_hostname(),
        'pid': os.getpid(),
        'thread': threading.current_thread().name,
        'signal_name': signal,
    }

    if exc is not None:
        signal_kwargs['exception_line'] = str(exc)
        signal_kwargs['exception'] = ''.join(
            traceback.format_exception(*sys.exc_info())
        )

    with transaction.atomic():
        task_model_instance, created = TaskModel.objects.get_or_create(
            task_id=task_id,
            defaults={'name': task.name}
        )

        signal_kwargs['task'] = task_model_instance

        # Store current task progress count to SignalInfoModel instance:
        signal_kwargs['progress_count'] = get_progress_count(task_id=task_id)

        last_signal = SignalInfoModel.objects.create(**signal_kwargs)

        update_fields = ['state_id']

        if task_finished:
            # Task has been ended -> Store progress information from cache into database
            task_model_instance.finished = True
            update_fields.append('finished')

            # Store progress_count, if available
            progress_count = get_progress_count(task_id)
            if progress_count is None and task_model_instance.parent_task_id is None:
                # Maybe sub tasks has process count?
                qs = TaskModel.objects.filter(
                    parent_task_id=task_id
                ).aggregate(Sum('progress_count'))
                progress_count = qs['progress_count__sum']

            if progress_count is not None:
                task_model_instance.progress_count = progress_count
                update_fields.append('progress_count')
                logger.debug('Store collected progress count: %s', progress_count)

        task_model_instance.state_id = last_signal.pk
        task_model_instance.save(update_fields=update_fields)

    if task_finished:
        # Remove information from cache:
        cleanup_cache(task_id=task_id)


@on_startup()
def startup_handler():
    """
    "Change" task state to "unknown" on startup for every "executing" tasks.

    The problem:
    We get no signal if the Huey worker died (e.g.: memory error)
    To remove the "executing" state of tasks: Just add a pseudo signal entry to it.

    Note: This will add a "unknown" state to other task, that are not affected from
    the died worker :(

    See also: https://github.com/coleifer/huey/issues/569
    """
    logger.debug('startup handler called')

    with transaction.atomic():
        qs = TaskModel.objects.filter(state__signal_name='executing')
        for task_model_instance in qs:
            logger.warning('Mark "executing" task %s to "unknown"', task_model_instance.pk)
            last_signal = SignalInfoModel.objects.create(
                # TODO: move parts into huey_monitor.models.SignalInfoManager
                hostname=get_hostname(),
                pid=os.getpid(),
                thread=threading.current_thread().name,
                task_id=task_model_instance.pk,
                signal_name='unknown',
            )
            task_model_instance.state_id = last_signal.pk
            task_model_instance.finished = True
            task_model_instance.save(update_fields=('state_id', 'finished'))

            # Remove information from cache:
            cleanup_cache(task_id=task_model_instance.task_id)

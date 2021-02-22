import logging
import os
import socket
import sys
import threading
import traceback
import uuid
from functools import lru_cache

from django.db import transaction
from huey.contrib.djhuey import on_startup, signal

from huey_monitor.models import SignalInfoModel, TaskModel


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
    logger.info('Store Task %s signal %r', task_id, signal)

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

        last_signal = SignalInfoModel.objects.create(**signal_kwargs)

        task_model_instance.state_id = last_signal.pk
        task_model_instance.save(update_fields=('state_id',))


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
            task_model_instance.save(update_fields=('state_id',))

import sys
import traceback
import uuid

from huey.contrib.djhuey import signal

from huey_monitor.models import SignalInfoModel, TaskModel


@signal()
def store_signals(signal, task, exc=None):
    """
    Store all Huey signals.
    """
    task_id = uuid.UUID(task.id)

    task_model_instance, created = TaskModel.objects.get_or_create(
        task_id=task_id,
        defaults={'name': task.name}
    )

    signal_kwargs = {
        'task': task_model_instance,
        'signal_name': signal,
    }

    if exc is not None:
        signal_kwargs['exception_line'] = str(exc)
        signal_kwargs['exception'] = ''.join(
            traceback.format_exception(*sys.exc_info())
        )

    last_signal = SignalInfoModel.objects.create(**signal_kwargs)

    task_model_instance.state_id = last_signal.pk
    task_model_instance.save(update_fields=('state_id',))

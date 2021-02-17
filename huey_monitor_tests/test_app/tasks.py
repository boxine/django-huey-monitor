import logging
import sys
import time

from huey import crontab
from huey.contrib.djhuey import lock_task, periodic_task, task

from huey_monitor.models import TaskModel


logger = logging.getLogger(__name__)


@task()
def raise_error_task(error_class_name, msg):
    logger.info('Raise %r with msg=%r', error_class_name, msg)
    ErrorClass = __builtins__[error_class_name]
    raise ErrorClass(msg)


@task()
def delay_task(name='<no-name>', sleep=3):
    logger.info('delay called from %r sleep %r sec...', name, sleep)
    time.sleep(sleep)
    logger.info('delay %r sleep ended.', name)


@periodic_task(crontab(minute='1'), context=True)
def one_minute_test_task(task):
    logger.info('one_minute_test_task UUID: %s', task.id)


@task(retries=2)  # Retry the task up to 2 times.
@lock_task('retry_and_lock_task')  # no multiple invocations from running concurrently
def retry_and_lock_task(info='<no-info>', sleep=3):
    logger.info('Start "retry_and_lock_task" - %r - sleep %s Sec.', info, sleep)
    time.sleep(sleep)
    raise RuntimeError(f'{info!r} error after {sleep} sec. sleep')


@task(retries=1)  # Retry the task one time
def out_of_memory_task():
    logger.warning('Start out of memory task !')
    obj = ['X']
    while True:
        obj = obj * 2
        size = sys.getsizeof(obj)
        logger.warning('OOM size: %s', size)


@task(context=True, retries=1)
def sub_task(task, parent_task_id, raise_error=False):
    logger.info('Sub task started from main task: %s', parent_task_id)
    TaskModel.objects.set_parent_task(
        main_task_id=parent_task_id,
        sub_task_id=task.id,
    )
    if raise_error:
        raise RuntimeError('This sub task should be raise an error ;)')


@task(context=True)
def main_task(task):
    logger.info('Main task %s starts three sub tasks', task.id)
    sub_task(parent_task_id=task.id)
    sub_task(parent_task_id=task.id, raise_error=True)
    sub_task(parent_task_id=task.id)

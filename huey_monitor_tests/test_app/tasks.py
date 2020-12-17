import logging
import sys
import time

from huey import crontab
from huey.contrib.djhuey import lock_task, periodic_task, task


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

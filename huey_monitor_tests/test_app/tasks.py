import logging
import math
import sys
import time

from bx_py_utils.iteration import chunk_iterable
from huey import crontab
from huey.contrib.djhuey import lock_task, periodic_task, task

from huey_monitor.models import TaskModel
from huey_monitor.tqdm import ProcessInfo


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


@task(context=True)
def linear_processing_task(task, desc=None, total=2000, no_total=False):
    if no_total:
        process_info = ProcessInfo(task, desc=desc)
    else:
        process_info = ProcessInfo(task, desc=desc, total=total)

    for i in range(total):
        time.sleep(0.1)
        process_info.update(n=1)


@task(context=True)
def parallel_sub_task(task, parent_task_id, item_chunk, **info_kwargs):
    """
    Useless example: Just calculate the SHA256 hash from all files
    """
    # Save relationship between the main and sub tasks:
    TaskModel.objects.set_parent_task(
        main_task_id=parent_task_id,
        sub_task_id=task.id
    )

    total_items = len(item_chunk)

    # Init progress information of this sub task:
    process_info = ProcessInfo(
        task, total=total_items, parent_task_id=parent_task_id, **info_kwargs
    )

    for entry in item_chunk:
        # ...do something with >entry< ...
        logger.info('process %s', entry)
        time.sleep(1)

        # Update sub and main task progress:
        process_info.update(n=1)

    logger.info('Chunk finish: %s', process_info)


@task(context=True)
def parallel_task(task, total=2000, task_num=3, **info_kwargs):
    """
    Example of a parallel processing task.
    """
    # Fill main task instance:
    ProcessInfo(task, total=total, **info_kwargs)

    # Generate some "data" to "process" in parallel Huey tasks
    process_data = list(range(total))

    # Split the file list into chunks and fire Huey tasks for every chunk:
    chunk_size = math.ceil(total / task_num)
    for no, chunk in enumerate(chunk_iterable(process_data, chunk_size), 1):
        # Start sub tasks
        logger.info('Start sub task no. %i', no)
        time.sleep(5)
        parallel_sub_task(parent_task_id=task.id, item_chunk=chunk, **info_kwargs)

import logging

from django.conf import settings
from django.core.cache import cache
from django.utils import timezone


CACHE_PREFIX = 'HueyMonitor'
CACHE_TIMEOUT = getattr(settings, 'HUEY_MONITOR_CACHE_TIMEOUT', 7 * 24 * 60 * 60)

logger = logging.getLogger(__name__)


def _make_progress_cache_key(task_id):
    return f'{CACHE_PREFIX}-progress-{task_id}'


def _make_timestamp_cache_key(task_id):
    return f'{CACHE_PREFIX}-timestamp-{task_id}'


def _set_update_dt(task_id):
    cache_key = _make_timestamp_cache_key(task_id)
    cache.set(key=cache_key, value=timezone.now(), timeout=CACHE_TIMEOUT)


def inc_task_progress(task_id, progress_count):
    """
    Store tqdm progress count and timestamp for one task
    """
    cache_key = _make_progress_cache_key(task_id)
    try:
        new_value = cache.incr(key=cache_key, delta=progress_count)
    except ValueError:
        cache.set(key=cache_key, value=progress_count, timeout=CACHE_TIMEOUT)
        new_value = progress_count

    _set_update_dt(task_id=task_id)

    return new_value


def cleanup_cache(task_id):
    """
    Remove progress count and timestamp of given task.
    Should be called after task completed and information stored into database.
    """
    cache.delete_many([_make_timestamp_cache_key(task_id), _make_progress_cache_key(task_id)])


def get_progress_count(task_id):
    """
    Get the current tqdm progress count of given task
    """
    cache_key = _make_progress_cache_key(task_id)
    progress_count = cache.get(key=cache_key, default=0)
    logger.debug('Get process count %s for %s from cache', progress_count, cache_key)
    return progress_count


def get_total_progress_count(task_ids):
    """
    Accumulate the tqdm progress count of all given tasks.
    Useful to get the current total count of a main task.
    """
    total_progress_count = sum(get_progress_count(task_id) for task_id in task_ids)
    return total_progress_count


def get_update_dt(task_id):
    """
    Return the last update datetime for the given task.
    """
    update_dt = cache.get(key=_make_timestamp_cache_key(task_id))
    return update_dt


def get_last_update_dt(task_ids):
    """
    Returns the last update datetime for all given tasks.
    Useful for main tasks.
    """
    last_update_dt = None
    for task_id in task_ids:
        update_dt = get_update_dt(task_id)
        if update_dt is None:
            continue
        elif last_update_dt is None or update_dt > last_update_dt:
            last_update_dt = update_dt

    return last_update_dt

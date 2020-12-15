import os

from huey import PriorityRedisExpireHuey
from redis import ConnectionPool


pool = ConnectionPool(
    host=os.environ.get('REDIS_HOST', 'redis'),
    port=int(os.environ.get('REDIS_PORT', 6379)),
    max_connections=20
)
HUEY = PriorityRedisExpireHuey(
    name='huey_monitor_tests',  # Just the name for this task queue.
    connection_pool=pool,  # Use a connection pool to redis.
    results=True,  # Store return values of tasks.
    store_none=False,  # If a task returns None, do not save to results.
    utc=True,  # Use UTC for all times internally.
    expire_time=24 * 60 * 60,  # cleaned-up unread task results from Redis after 24h
)

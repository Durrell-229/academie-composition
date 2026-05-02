"""
Lightweight Redis-based task queue (no Celery).
Tasks are decorated with @redis_task and pushed to a Redis list.
A worker (management command) pops and executes them.
"""
import json
import logging
import traceback
import uuid
from functools import wraps
from datetime import datetime

import redis
from django.conf import settings

logger = logging.getLogger(__name__)


def get_redis_connection():
    """Get Redis connection from Django settings."""
    redis_url = getattr(settings, 'REDIS_URL', 'redis://localhost:6379/0')
    return redis.from_url(redis_url)


class RedisTaskRegistry:
    """Registry that maps task names to their functions."""
    _tasks = {}

    @classmethod
    def register(cls, name, func):
        cls._tasks[name] = func

    @classmethod
    def get(cls, name):
        return cls._tasks.get(name)


def redis_task(name):
    """Decorator to mark a function as a Redis background task."""
    def decorator(func):
        @wraps(func)
        def delay(*args, **kwargs):
            """Push task to Redis queue."""
            task_id = str(uuid.uuid4())
            payload = {
                'task_id': task_id,
                'task_name': name,
                'args': args,
                'kwargs': kwargs,
                'created_at': datetime.utcnow().isoformat(),
            }
            try:
                r = get_redis_connection()
                r.lpush('task_queue', json.dumps(payload))
                logger.info(f"Task queued: {name} [{task_id}]")
                return task_id
            except redis.ConnectionError:
                logger.warning(f"Redis unavailable, running task synchronously: {name}")
                return func(*args, **kwargs)

        func.delay = delay
        RedisTaskRegistry.register(name, func)
        return func
    return decorator


def process_task_queue(max_tasks=None, shutdown_event=None):
    """
    Worker loop: pop tasks from Redis and execute them.
    Run via: python manage.py run_worker
    """
    r = get_redis_connection()
    count = 0

    logger.info("Worker started, waiting for tasks...")

    while True:
        if shutdown_event and shutdown_event.is_set():
            logger.info("Worker shutting down...")
            break

        if max_tasks and count >= max_tasks:
            logger.info(f"Processed {max_tasks} tasks, stopping.")
            break

        # Blocking pop with 5s timeout
        result = r.brpop('task_queue', timeout=5)
        if not result:
            continue

        _, raw_payload = result
        count += 1

        try:
            payload = json.loads(raw_payload)
            task_name = payload['task_name']
            task_id = payload['task_id']
            args = payload.get('args', [])
            kwargs = payload.get('kwargs', {})

            func = RedisTaskRegistry.get(task_name)
            if not func:
                logger.error(f"Unknown task: {task_name}")
                continue

            logger.info(f"Executing: {task_name} [{task_id}]")
            result = func(*args, **kwargs)
            logger.info(f"Done: {task_name} [{task_id}] -> {result}")

            # Store result for 1 hour
            r.setex(
                f'task_result:{task_id}',
                3600,
                json.dumps({'status': 'success', 'result': str(result)})
            )

        except Exception as e:
            logger.error(f"Task failed: {traceback.format_exc()}")
            # Store error result
            if 'payload' in dir():
                r.setex(
                    f'task_result:{payload.get("task_id", "unknown")}',
                    3600,
                    json.dumps({'status': 'error', 'error': str(e)})
                )


def get_task_result(task_id):
    """Check the result of a queued task."""
    r = get_redis_connection()
    raw = r.get(f'task_result:{task_id}')
    if raw:
        return json.loads(raw)
    return None

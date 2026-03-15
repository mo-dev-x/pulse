"""Background job queue helpers with graceful fallback."""

from dataclasses import dataclass
from importlib import import_module

from flask import current_app

try:  # pragma: no cover - optional dependency in local/test environments
    from redis import Redis
    from rq import Queue
except ImportError:  # pragma: no cover
    Redis = None
    Queue = None


@dataclass
class JobDispatchResult:
    """Lightweight return object for queued or inline jobs."""

    queued: bool
    mode: str
    job_id: str | None = None
    result: object = None


def _resolve_callable(func_ref):
    if callable(func_ref):
        return func_ref

    module_name, function_name = func_ref.rsplit('.', 1)
    module = import_module(module_name)
    return getattr(module, function_name)


def _serialize_callable(func_ref):
    if isinstance(func_ref, str):
        return func_ref
    return f'{func_ref.__module__}.{func_ref.__name__}'


def _get_queue(queue_name):
    if not current_app.config.get('BACKGROUND_JOBS_ENABLED', False):
        return None

    redis_url = current_app.config.get('REDIS_URL')
    if not redis_url or Redis is None or Queue is None:
        current_app.logger.info(
            'Background jobs requested but Redis/RQ is unavailable; falling back to inline execution.'
        )
        return None

    connection = Redis.from_url(redis_url)
    return Queue(
        queue_name,
        connection=connection,
        default_timeout=current_app.config.get('BACKGROUND_JOB_TIMEOUT', 300),
    )


def enqueue_task(func_ref, *args, queue_name='default', **kwargs):
    """
    Queue a task with RQ when configured, otherwise execute inline.

    Testing uses eager execution by default to keep behavior deterministic.
    """
    func = _resolve_callable(func_ref)
    if current_app.config.get('BACKGROUND_JOBS_EAGER', False):
        return JobDispatchResult(
            queued=False,
            mode='eager',
            result=func(*args, **kwargs),
        )

    queue = _get_queue(queue_name)
    if queue is not None:
        job = queue.enqueue(_serialize_callable(func_ref), *args, **kwargs)
        return JobDispatchResult(queued=True, mode='rq', job_id=job.id)

    return JobDispatchResult(
        queued=False,
        mode='inline',
        result=func(*args, **kwargs),
    )

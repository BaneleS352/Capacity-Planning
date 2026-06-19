from celery import Celery  # type: ignore[import-untyped]

from app.core.config import get_settings

settings = get_settings()
celery_app = Celery(
    "capacity_planning",
    broker=settings.celery_broker_url,
    backend=settings.celery_result_backend,
    include=["app.workers.tasks"],
)
celery_app.conf.update(
    task_serializer="json",
    result_serializer="json",
    accept_content=["json"],
    task_acks_late=True,
    task_reject_on_worker_lost=True,
    worker_prefetch_multiplier=1,
    task_default_retry_delay=30,
    task_routes={
        "capacity.recalculate": {"queue": "planning"},
        "outbox.publish": {"queue": "integration"},
    },
    beat_schedule={
        "publish-outbox-every-10-seconds": {
            "task": "outbox.publish",
            "schedule": 10.0,
        }
    },
)

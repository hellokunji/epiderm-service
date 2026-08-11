from celery import Celery

from app.core.config import settings

celery_app = Celery(
    "epiderm",
    broker=settings.CELERY_BROKER_URL,
    backend=settings.CELERY_RESULT_BACKEND,
    include=[
        "app.tasks.diagnosis",
        "app.tasks.general",
    ],
)

celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
    task_track_started=True,
    result_expires=settings.CELERY_RESULT_EXPIRES,
    task_default_queue="default",
    task_routes={
        "app.tasks.diagnosis.*": {"queue": "diagnosis"},
        "app.tasks.general.*": {"queue": "default"},
    },
    worker_prefetch_multiplier=1,
    task_acks_late=True,
    task_reject_on_worker_lost=True,
)

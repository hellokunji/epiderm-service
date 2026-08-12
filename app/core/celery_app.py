from celery import Celery
from celery.signals import worker_process_init, worker_process_shutdown

from app.core.config import settings

celery_app = Celery(
    "epiderm",
    broker=settings.CELERY_BROKER_URL,
    backend=settings.CELERY_RESULT_BACKEND,
    include=[
        "app.tasks.diagnosis",
        "app.tasks.general",
        "app.tasks.questionnaire",
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
    task_default_queue="questionnaire_submitted",
    task_routes={
        "app.tasks.diagnosis.*": {"queue": "diagnosis_ready"},
        "app.tasks.general.*": {"queue": "questionnaire_submitted"},
        "app.tasks.questionnaire.*": {"queue": "questionnaire_submitted"},
    },
    worker_prefetch_multiplier=1,
    task_acks_late=True,
    task_reject_on_worker_lost=True,
    # Avoid prefork+psycopg2 SIGSEGV on macOS local workers; override in prod if needed.
    worker_pool="solo",
)


@worker_process_init.connect
def _init_worker_process(**_kwargs) -> None:
    # Prefork children must not reuse DB connections opened in the parent
    # (psycopg2 + fork causes SIGSEGV on macOS).
    from app.core.database import engine
    from app.core.mongodb import connect_to_mongo

    engine.dispose(close=False)
    connect_to_mongo()


@worker_process_shutdown.connect
def _shutdown_worker_process(**_kwargs) -> None:
    from app.core.database import engine
    from app.core.mongodb import close_mongo_connection

    close_mongo_connection()
    engine.dispose()


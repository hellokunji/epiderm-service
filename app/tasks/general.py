import logging

from app.core.celery_app import celery_app

logger = logging.getLogger(__name__)


@celery_app.task(name="app.tasks.general.ping")
def ping() -> dict:
    logger.info("Background ping task executed")
    return {"status": "ok"}


@celery_app.task(name="app.tasks.general.log_message")
def log_message(message: str) -> dict:
    logger.info("Background task received message: %s", message)
    return {"logged": message}

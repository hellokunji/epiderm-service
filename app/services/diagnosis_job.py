import logging
from typing import Any, Optional

from celery.result import AsyncResult

from app.core.celery_app import celery_app
from app.core.flow_log import flow_log
from app.schemas.jobs import DiagnosisJobCreated, DiagnosisJobStatus, JobStatus
from app.services.health import get_redis_client
from app.tasks.diagnosis import (
    run_multimodal_diagnosis,
    run_text_diagnosis,
    run_vision_diagnosis,
)

logger = logging.getLogger(__name__)

DIAGNOSIS_READY_QUEUE = "diagnosis_ready"
JOB_KEY_PREFIX = "diagnosis:job:"
CONSULT_JOB_KEY_PREFIX = "diagnosis:consult:"


def _job_cache_key(job_id: str) -> str:
    return f"{JOB_KEY_PREFIX}{job_id}"


def _consult_job_key(consult_id: str) -> str:
    return f"{CONSULT_JOB_KEY_PREFIX}{consult_id}"


def _register_job(job_id: str, consult_id: Optional[str] = None) -> None:
    client = get_redis_client()
    client.setex(_job_cache_key(job_id), celery_app.conf.result_expires, "1")
    if consult_id:
        client.setex(
            _consult_job_key(consult_id),
            celery_app.conf.result_expires,
            job_id,
        )
    flow_log(
        "08c",
        "redis",
        "Registered diagnosis job keys",
        consult_id=consult_id,
        job_id=job_id,
    )


def job_exists(job_id: str) -> bool:
    return bool(get_redis_client().exists(_job_cache_key(job_id)))


def get_job_id_for_consult(consult_id: str) -> Optional[str]:
    return get_redis_client().get(_consult_job_key(consult_id))


def _map_celery_state(state: str) -> JobStatus:
    mapping = {
        "PENDING": JobStatus.PENDING,
        "STARTED": JobStatus.STARTED,
        "SUCCESS": JobStatus.SUCCESS,
        "FAILURE": JobStatus.FAILURE,
        "RETRY": JobStatus.RETRY,
        "REVOKED": JobStatus.REVOKED,
    }
    return mapping.get(state, JobStatus.PENDING)


def enqueue_text_diagnosis(payload: dict) -> DiagnosisJobCreated:
    task = run_text_diagnosis.apply_async(args=[payload], queue=DIAGNOSIS_READY_QUEUE)
    _register_job(task.id, consult_id=payload.get("consult_id"))
    flow_log(
        "08",
        "redis",
        "Published text diagnosis task",
        consult_id=payload.get("consult_id"),
        queue=DIAGNOSIS_READY_QUEUE,
        mode="text",
        task_id=task.id,
        task_name="app.tasks.diagnosis.run_text_diagnosis",
    )
    return DiagnosisJobCreated(job_id=task.id, queue=DIAGNOSIS_READY_QUEUE)


def enqueue_vision_diagnosis(payload: dict) -> DiagnosisJobCreated:
    task = run_vision_diagnosis.apply_async(args=[payload], queue=DIAGNOSIS_READY_QUEUE)
    _register_job(task.id, consult_id=payload.get("consult_id"))
    flow_log(
        "08",
        "redis",
        "Published vision diagnosis task",
        consult_id=payload.get("consult_id"),
        queue=DIAGNOSIS_READY_QUEUE,
        mode="vision",
        task_id=task.id,
        task_name="app.tasks.diagnosis.run_vision_diagnosis",
    )
    return DiagnosisJobCreated(job_id=task.id, queue=DIAGNOSIS_READY_QUEUE)


def enqueue_multimodal_diagnosis(payload: dict) -> DiagnosisJobCreated:
    task = run_multimodal_diagnosis.apply_async(
        args=[payload], queue=DIAGNOSIS_READY_QUEUE
    )
    _register_job(task.id, consult_id=payload.get("consult_id"))
    flow_log(
        "08",
        "redis",
        "Published multimodal diagnosis task",
        consult_id=payload.get("consult_id"),
        queue=DIAGNOSIS_READY_QUEUE,
        mode="multimodal",
        task_id=task.id,
        task_name="app.tasks.diagnosis.run_multimodal_diagnosis",
    )
    return DiagnosisJobCreated(job_id=task.id, queue=DIAGNOSIS_READY_QUEUE)


def enqueue_diagnosis_for_response(
    *,
    consult_id: str,
    response_id: str,
    patient_id: str,
    questionnaire: Optional[dict[str, Any]],
    images: Optional[list[str]],
) -> Optional[DiagnosisJobCreated]:
    """Route a stored questionnaire response to the correct AI diagnosis worker task."""
    cleaned_images = [
        image for image in (images or []) if isinstance(image, str) and image.strip()
    ] or None

    context = {
        "consult_id": consult_id,
        "response_id": response_id,
        "patient_id": patient_id,
    }

    if questionnaire is not None and cleaned_images is not None:
        mode = "multimodal"
    elif questionnaire is not None:
        mode = "text"
    elif cleaned_images is not None:
        mode = "vision"
    else:
        mode = None

    flow_log(
        "08a",
        "consumer",
        "Routing diagnosis mode",
        consult_id=consult_id,
        response_id=response_id,
        mode=mode or "none",
        has_questionnaire=questionnaire is not None,
        image_count=len(cleaned_images or []),
    )

    if mode == "multimodal":
        return enqueue_multimodal_diagnosis(
            {**context, "questionnaire": questionnaire, "images": cleaned_images}
        )
    if mode == "text":
        return enqueue_text_diagnosis({**context, "questionnaire": questionnaire})
    if mode == "vision":
        return enqueue_vision_diagnosis({**context, "images": cleaned_images})
    return None


def get_diagnosis_job(job_id: str) -> DiagnosisJobStatus:
    result = AsyncResult(job_id, app=celery_app)
    status = _map_celery_state(result.state)

    if status == JobStatus.SUCCESS:
        return DiagnosisJobStatus(
            job_id=job_id,
            status=status,
            result=result.result,
        )

    if status == JobStatus.FAILURE:
        return DiagnosisJobStatus(
            job_id=job_id,
            status=status,
            error=str(result.result),
        )

    progress = result.info if isinstance(result.info, dict) else None
    return DiagnosisJobStatus(
        job_id=job_id,
        status=status,
        progress=progress,
    )

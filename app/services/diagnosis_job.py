from celery.result import AsyncResult

from app.core.celery_app import celery_app
from app.schemas.jobs import DiagnosisJobCreated, DiagnosisJobStatus, JobStatus
from app.services.health import get_redis_client
from app.tasks.diagnosis import (
    run_multimodal_diagnosis,
    run_text_diagnosis,
    run_vision_diagnosis,
)

DIAGNOSIS_QUEUE = "diagnosis"
JOB_KEY_PREFIX = "diagnosis:job:"


def _job_cache_key(job_id: str) -> str:
    return f"{JOB_KEY_PREFIX}{job_id}"


def _register_job(job_id: str) -> None:
    client = get_redis_client()
    client.setex(_job_cache_key(job_id), celery_app.conf.result_expires, "1")


def job_exists(job_id: str) -> bool:
    return bool(get_redis_client().exists(_job_cache_key(job_id)))


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
    task = run_text_diagnosis.apply_async(args=[payload], queue=DIAGNOSIS_QUEUE)
    _register_job(task.id)
    return DiagnosisJobCreated(job_id=task.id, queue=DIAGNOSIS_QUEUE)


def enqueue_vision_diagnosis(payload: dict) -> DiagnosisJobCreated:
    task = run_vision_diagnosis.apply_async(args=[payload], queue=DIAGNOSIS_QUEUE)
    _register_job(task.id)
    return DiagnosisJobCreated(job_id=task.id, queue=DIAGNOSIS_QUEUE)


def enqueue_multimodal_diagnosis(payload: dict) -> DiagnosisJobCreated:
    task = run_multimodal_diagnosis.apply_async(args=[payload], queue=DIAGNOSIS_QUEUE)
    _register_job(task.id)
    return DiagnosisJobCreated(job_id=task.id, queue=DIAGNOSIS_QUEUE)


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

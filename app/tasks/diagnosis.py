import logging

from ollama import RequestError, ResponseError

from app.core.celery_app import celery_app
from app.core.config import settings
from app.core.flow_log import flow_log
from app.schemas.diagnosis import (
    DiagnosisMultimodalRequest,
    DiagnosisTextRequest,
    DiagnosisVisionRequest,
    VisualSymptomAnalysis,
)
from app.schemas.llm import SymptomAnalysis
from app.services.diagnosis_result import save_diagnosis_result
from app.services.llm import call_ollama_structured, diagnose_from_questionnaire
from app.models.consult import ConsultStatus
from app.services.consult import update_consult_status

logger = logging.getLogger(__name__)


def _persist_success(
    *,
    payload: dict,
    job_id: str,
    mode: str,
    result: dict,
) -> None:
    consult_id = payload.get("consult_id")
    if not consult_id:
        return
    save_diagnosis_result(
        consult_id=consult_id,
        response_id=payload.get("response_id"),
        patient_id=payload.get("patient_id"),
        job_id=job_id,
        mode=mode,
        status="success",
        result=result,
    )
    flow_log(
        "14c",
        "diagnosis_worker",
        "Setting consult status to DRAI_DG_DIAGNOSED",
        consult_id=consult_id,
        job_id=job_id,
        mode=mode,
    )
    update_consult_status(consult_id, ConsultStatus.DRAI_DG_DIAGNOSED)


def _persist_failure(*, payload: dict, job_id: str, mode: str, error: str) -> None:
    consult_id = payload.get("consult_id")
    if not consult_id:
        return
    save_diagnosis_result(
        consult_id=consult_id,
        response_id=payload.get("response_id"),
        patient_id=payload.get("patient_id"),
        job_id=job_id,
        mode=mode,
        status="failure",
        error=error,
    )


@celery_app.task(
    bind=True,
    name="app.tasks.diagnosis.run_text_diagnosis",
    autoretry_for=(RequestError, ResponseError, ConnectionError, TimeoutError),
    retry_backoff=True,
    max_retries=2,
    default_retry_delay=30,
)
def run_text_diagnosis(self, payload: dict) -> dict:
    consult_id = payload.get("consult_id")
    flow_log(
        "11",
        "diagnosis_worker",
        "Pulled text diagnosis task from diagnosis_ready",
        consult_id=consult_id,
        queue="diagnosis_ready",
        mode="text",
        task_id=self.request.id,
        retry=self.request.retries,
    )
    body = DiagnosisTextRequest.model_validate(payload)
    try:
        flow_log(
            "12",
            "ollama",
            "Calling LLM for text diagnosis",
            consult_id=consult_id,
            mode="text",
            task_id=self.request.id,
        )
        result = diagnose_from_questionnaire(
            body.questionnaire,
            system_prompt=body.system_prompt,
            response_model=SymptomAnalysis,
        )
        result_dict = result.model_dump()
        flow_log(
            "13",
            "ollama",
            "LLM text diagnosis completed",
            consult_id=consult_id,
            mode="text",
            task_id=self.request.id,
        )
        _persist_success(
            payload=payload,
            job_id=self.request.id,
            mode="text",
            result=result_dict,
        )
        flow_log(
            "15",
            "diagnosis_worker",
            "Text diagnosis task finished successfully",
            consult_id=consult_id,
            task_id=self.request.id,
        )
        return result_dict
    except Exception as exc:
        flow_log(
            "13",
            "ollama",
            "LLM text diagnosis failed",
            consult_id=consult_id,
            mode="text",
            task_id=self.request.id,
            error=type(exc).__name__,
            retry=self.request.retries,
        )
        if self.request.retries >= (self.max_retries or 0):
            _persist_failure(
                payload=payload,
                job_id=self.request.id,
                mode="text",
                error=str(exc),
            )
        raise


@celery_app.task(
    bind=True,
    name="app.tasks.diagnosis.run_vision_diagnosis",
    autoretry_for=(RequestError, ResponseError, ConnectionError, TimeoutError),
    retry_backoff=True,
    max_retries=2,
    default_retry_delay=30,
)
def run_vision_diagnosis(self, payload: dict) -> dict:
    consult_id = payload.get("consult_id")
    flow_log(
        "11",
        "diagnosis_worker",
        "Pulled vision diagnosis task from diagnosis_ready",
        consult_id=consult_id,
        queue="diagnosis_ready",
        mode="vision",
        task_id=self.request.id,
        retry=self.request.retries,
    )
    body = DiagnosisVisionRequest.model_validate(payload)
    try:
        flow_log(
            "12",
            "ollama",
            "Calling LLM for vision diagnosis",
            consult_id=consult_id,
            mode="vision",
            model=settings.OLLAMA_VISION_MODEL,
            image_count=len(body.images),
            task_id=self.request.id,
        )
        result = call_ollama_structured(
            user_content=(
                "Analyze the attached clinical images for visible skin or hair symptoms."
            ),
            images=body.images,
            response_model=VisualSymptomAnalysis,
            system_prompt=body.system_prompt,
            model=settings.OLLAMA_VISION_MODEL,
        )
        result_dict = result.model_dump()
        flow_log(
            "13",
            "ollama",
            "LLM vision diagnosis completed",
            consult_id=consult_id,
            mode="vision",
            task_id=self.request.id,
        )
        _persist_success(
            payload=payload,
            job_id=self.request.id,
            mode="vision",
            result=result_dict,
        )
        flow_log(
            "15",
            "diagnosis_worker",
            "Vision diagnosis task finished successfully",
            consult_id=consult_id,
            task_id=self.request.id,
        )
        return result_dict
    except Exception as exc:
        flow_log(
            "13",
            "ollama",
            "LLM vision diagnosis failed",
            consult_id=consult_id,
            mode="vision",
            task_id=self.request.id,
            error=type(exc).__name__,
            retry=self.request.retries,
        )
        if self.request.retries >= (self.max_retries or 0):
            _persist_failure(
                payload=payload,
                job_id=self.request.id,
                mode="vision",
                error=str(exc),
            )
        raise


@celery_app.task(
    bind=True,
    name="app.tasks.diagnosis.run_multimodal_diagnosis",
    autoretry_for=(RequestError, ResponseError, ConnectionError, TimeoutError),
    retry_backoff=True,
    max_retries=2,
    default_retry_delay=30,
)
def run_multimodal_diagnosis(self, payload: dict) -> dict:
    consult_id = payload.get("consult_id")
    flow_log(
        "11",
        "diagnosis_worker",
        "Pulled multimodal diagnosis task from diagnosis_ready",
        consult_id=consult_id,
        queue="diagnosis_ready",
        mode="multimodal",
        task_id=self.request.id,
        retry=self.request.retries,
    )
    body = DiagnosisMultimodalRequest.model_validate(payload)
    try:
        flow_log(
            "12",
            "ollama",
            "Calling LLM for multimodal diagnosis",
            consult_id=consult_id,
            mode="multimodal",
            image_count=len(body.images),
            task_id=self.request.id,
        )
        result = diagnose_from_questionnaire(
            body.questionnaire,
            images=body.images,
            system_prompt=body.system_prompt,
            response_model=VisualSymptomAnalysis,
        )
        result_dict = result.model_dump()
        flow_log(
            "13",
            "ollama",
            "LLM multimodal diagnosis completed",
            consult_id=consult_id,
            mode="multimodal",
            task_id=self.request.id,
        )
        _persist_success(
            payload=payload,
            job_id=self.request.id,
            mode="multimodal",
            result=result_dict,
        )
        flow_log(
            "15",
            "diagnosis_worker",
            "Multimodal diagnosis task finished successfully",
            consult_id=consult_id,
            task_id=self.request.id,
        )
        return result_dict
    except Exception as exc:
        flow_log(
            "13",
            "ollama",
            "LLM multimodal diagnosis failed",
            consult_id=consult_id,
            mode="multimodal",
            task_id=self.request.id,
            error=type(exc).__name__,
            retry=self.request.retries,
        )
        if self.request.retries >= (self.max_retries or 0):
            _persist_failure(
                payload=payload,
                job_id=self.request.id,
                mode="multimodal",
                error=str(exc),
            )
        raise

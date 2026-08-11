from ollama import RequestError, ResponseError

from app.core.celery_app import celery_app
from app.core.config import settings
from app.schemas.diagnosis import (
    DiagnosisMultimodalRequest,
    DiagnosisTextRequest,
    DiagnosisVisionRequest,
    VisualSymptomAnalysis,
)
from app.schemas.llm import SymptomAnalysis
from app.services.llm import call_ollama_structured, diagnose_from_questionnaire


@celery_app.task(
    bind=True,
    name="app.tasks.diagnosis.run_text_diagnosis",
    autoretry_for=(RequestError, ResponseError, ConnectionError, TimeoutError),
    retry_backoff=True,
    max_retries=2,
    default_retry_delay=30,
)
def run_text_diagnosis(self, payload: dict) -> dict:
    body = DiagnosisTextRequest.model_validate(payload)
    result = diagnose_from_questionnaire(
        body.questionnaire,
        system_prompt=body.system_prompt,
        response_model=SymptomAnalysis,
    )
    return result.model_dump()


@celery_app.task(
    bind=True,
    name="app.tasks.diagnosis.run_vision_diagnosis",
    autoretry_for=(RequestError, ResponseError, ConnectionError, TimeoutError),
    retry_backoff=True,
    max_retries=2,
    default_retry_delay=30,
)
def run_vision_diagnosis(self, payload: dict) -> dict:
    body = DiagnosisVisionRequest.model_validate(payload)
    result = call_ollama_structured(
        user_content=(
            "Analyze the attached clinical images for visible skin or hair symptoms."
        ),
        images=body.images,
        response_model=VisualSymptomAnalysis,
        system_prompt=body.system_prompt,
        model=settings.OLLAMA_VISION_MODEL,
    )
    return result.model_dump()


@celery_app.task(
    bind=True,
    name="app.tasks.diagnosis.run_multimodal_diagnosis",
    autoretry_for=(RequestError, ResponseError, ConnectionError, TimeoutError),
    retry_backoff=True,
    max_retries=2,
    default_retry_delay=30,
)
def run_multimodal_diagnosis(self, payload: dict) -> dict:
    body = DiagnosisMultimodalRequest.model_validate(payload)
    result = diagnose_from_questionnaire(
        body.questionnaire,
        images=body.images,
        system_prompt=body.system_prompt,
        response_model=VisualSymptomAnalysis,
    )
    return result.model_dump()

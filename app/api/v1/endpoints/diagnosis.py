from fastapi import APIRouter, HTTPException, status

from app.core.config import settings
from app.schemas.diagnosis import (
    DiagnosisMultimodalRequest,
    DiagnosisTextRequest,
    DiagnosisVisionRequest,
    VisualSymptomAnalysis,
)
from app.schemas.jobs import DiagnosisJobCreated, DiagnosisJobStatus
from app.schemas.llm import SymptomAnalysis
from app.schemas.response import ok
from app.services.diagnosis_job import (
    enqueue_multimodal_diagnosis,
    enqueue_text_diagnosis,
    enqueue_vision_diagnosis,
    get_diagnosis_job,
    job_exists,
)
from app.services.llm import call_ollama_structured, diagnose_from_questionnaire

api_router = APIRouter()
s2s_router = APIRouter()


@api_router.post("/text", response_model=SymptomAnalysis)
def diagnose_text(body: DiagnosisTextRequest):
    return diagnose_from_questionnaire(
        body.questionnaire,
        system_prompt=body.system_prompt,
        response_model=SymptomAnalysis,
    )


@api_router.post("/vision", response_model=VisualSymptomAnalysis)
def diagnose_vision(body: DiagnosisVisionRequest):
    return call_ollama_structured(
        user_content="Analyze the attached clinical images for visible skin or hair symptoms.",
        images=body.images,
        response_model=VisualSymptomAnalysis,
        system_prompt=body.system_prompt,
        model=settings.OLLAMA_VISION_MODEL,
    )


@api_router.post("/multimodal", response_model=VisualSymptomAnalysis)
def diagnose_multimodal(body: DiagnosisMultimodalRequest):
    return diagnose_from_questionnaire(
        body.questionnaire,
        images=body.images,
        system_prompt=body.system_prompt,
        response_model=VisualSymptomAnalysis,
    )


@api_router.post("/jobs/text", response_model=DiagnosisJobCreated, status_code=status.HTTP_202_ACCEPTED)
def enqueue_text_diagnosis_job(body: DiagnosisTextRequest):
    return enqueue_text_diagnosis(body.model_dump())


@api_router.post(
    "/jobs/vision",
    response_model=DiagnosisJobCreated,
    status_code=status.HTTP_202_ACCEPTED,
)
def enqueue_vision_diagnosis_job(body: DiagnosisVisionRequest):
    return enqueue_vision_diagnosis(body.model_dump())


@api_router.post(
    "/jobs/multimodal",
    response_model=DiagnosisJobCreated,
    status_code=status.HTTP_202_ACCEPTED,
)
def enqueue_multimodal_diagnosis_job(body: DiagnosisMultimodalRequest):
    return enqueue_multimodal_diagnosis(body.model_dump())


@api_router.get("/jobs/{job_id}", response_model=DiagnosisJobStatus)
def get_diagnosis_job_status(job_id: str):
    if not job_exists(job_id):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Diagnosis job not found",
        )
    return get_diagnosis_job(job_id)


@s2s_router.post("/text", response_model=SymptomAnalysis)
def diagnose_text_s2s(body: DiagnosisTextRequest):
    return diagnose_from_questionnaire(
        body.questionnaire,
        system_prompt=body.system_prompt,
        response_model=SymptomAnalysis,
    )


@s2s_router.post("/vision", response_model=VisualSymptomAnalysis)
def diagnose_vision_s2s(body: DiagnosisVisionRequest):
    return call_ollama_structured(
        user_content="Analyze the attached clinical images for visible skin or hair symptoms.",
        images=body.images,
        response_model=VisualSymptomAnalysis,
        system_prompt=body.system_prompt,
        model=settings.OLLAMA_VISION_MODEL,
    )


@s2s_router.post("/multimodal", response_model=VisualSymptomAnalysis)
def diagnose_multimodal_s2s(body: DiagnosisMultimodalRequest):
    return diagnose_from_questionnaire(
        body.questionnaire,
        images=body.images,
        system_prompt=body.system_prompt,
        response_model=VisualSymptomAnalysis,
    )


@s2s_router.post("/jobs/text", status_code=status.HTTP_202_ACCEPTED)
def enqueue_text_diagnosis_job_s2s(body: DiagnosisTextRequest):
    return ok(enqueue_text_diagnosis(body.model_dump()))


@s2s_router.post("/jobs/vision", status_code=status.HTTP_202_ACCEPTED)
def enqueue_vision_diagnosis_job_s2s(body: DiagnosisVisionRequest):
    return ok(enqueue_vision_diagnosis(body.model_dump()))


@s2s_router.post("/jobs/multimodal", status_code=status.HTTP_202_ACCEPTED)
def enqueue_multimodal_diagnosis_job_s2s(body: DiagnosisMultimodalRequest):
    return ok(enqueue_multimodal_diagnosis(body.model_dump()))


@s2s_router.get("/jobs/{job_id}")
def get_diagnosis_job_status_s2s(job_id: str):
    if not job_exists(job_id):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Diagnosis job not found",
        )
    return ok(get_diagnosis_job(job_id))

# app/api/v1/endpoints/diagnosis.py
from fastapi import APIRouter
from app.core.config import settings

from app.schemas.diagnosis import (
    DiagnosisMultimodalRequest,
    DiagnosisTextRequest,
    DiagnosisVisionRequest,
    VisualSymptomAnalysis,
)
from app.schemas.llm import SymptomAnalysis
from app.schemas.response import ok
from app.services.llm import diagnose_from_questionnaire, call_ollama_structured, format_questionnaire_prompt

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


# Mirror same 3 handlers on s2s_router, wrapping with ok(...)
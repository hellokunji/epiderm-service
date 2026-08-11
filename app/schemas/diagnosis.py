# app/schemas/diagnosis.py
from typing import List, Optional, Union

from pydantic import BaseModel, Field, field_validator

from app.schemas.llm import SymptomAnalysis


class QuestionAnswer(BaseModel):
    question_id: str
    question: str
    answer: Union[str, List[str], int, float, bool]


class QuestionnairePayload(BaseModel):
    questionnaire_id: Optional[str] = None
    answers: List[QuestionAnswer] = Field(..., min_length=1)


class DiagnosisTextRequest(BaseModel):
    questionnaire: QuestionnairePayload
    system_prompt: Optional[str] = Field(
        default=(
            "You are an AI clinical assistant for skin and hair diagnosis. "
            "Analyze the patient questionnaire and respond strictly in JSON format."
        )
    )


class DiagnosisVisionRequest(BaseModel):
    images: List[str] = Field(..., min_length=1, description="Base64-encoded images")
    system_prompt: Optional[str] = Field(
        default=(
            "You are an AI clinical assistant. Analyze the clinical images "
            "and respond strictly in JSON format."
        )
    )

    @field_validator("images")
    @classmethod
    def validate_images(cls, images: List[str]) -> List[str]:
        if not all(isinstance(img, str) and img.strip() for img in images):
            raise ValueError("Each image must be a non-empty base64 string")
        return images


class DiagnosisMultimodalRequest(BaseModel):
    questionnaire: QuestionnairePayload
    images: List[str] = Field(..., min_length=1)
    system_prompt: Optional[str] = Field(
        default=(
            "You are an AI clinical assistant. Analyze both the questionnaire "
            "responses and clinical images. Respond strictly in JSON format."
        )
    )


# Optional: richer output for vision endpoints
class VisualSymptomAnalysis(SymptomAnalysis):
    visual_observations: List[str] = Field(
        description="What is visibly observed in the images"
    )
    affected_areas: List[str]
    image_confidence: str = Field(description="Low, Moderate, or High")
from typing import Optional

from pydantic import BaseModel, Field


class LLMPromptRequest(BaseModel):
    prompt: str = Field(..., min_length=1, description="User/patient input for the LLM")
    system_prompt: Optional[str] = Field(
        default="You are an AI clinical assistant. Analyze the patient questionnaire and respond strictly in JSON format."
    )


class SymptomAnalysis(BaseModel):
    primary_concern: str
    observed_symptoms: list[str]
    severity_level: str = Field(description="Low, Moderate, or High")
    recommended_kit_type: str
    doctor_notes_summary: str
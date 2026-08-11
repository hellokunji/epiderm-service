import json
from typing import List, Optional, TypeVar

from ollama import chat
from pydantic import BaseModel

from app.core.config import settings
from app.schemas.diagnosis import QuestionnairePayload

T = TypeVar("T", bound=BaseModel)


def format_questionnaire_prompt(questionnaire: QuestionnairePayload) -> str:
    """Turn Q&A JSON into LLM-readable content."""
    return (
        "Patient questionnaire responses (JSON):\n"
        f"{json.dumps(questionnaire.model_dump(), indent=2)}\n\n"
        "Analyze these responses for clinical symptoms and concerns."
    )


def call_ollama_structured(
    *,
    user_content: str,
    response_model: type[T],
    system_prompt: str,
    model: Optional[str] = None,
    images: Optional[List[str]] = None,
    temperature: float = 0.1,
) -> T:
    user_message = {
        "role": "user",
        "content": user_content,
    }
    if images:
        user_message["images"] = images  # base64, file path, or bytes

    response = chat(
        model=model or settings.OLLAMA_MODEL,
        messages=[
            {"role": "system", "content": system_prompt},
            user_message,
        ],
        format=response_model.model_json_schema(),
        options={"temperature": temperature},
    )

    return response_model.model_validate_json(response.message.content)


def diagnose_from_questionnaire(
    questionnaire: QuestionnairePayload,
    *,
    system_prompt: str,
    response_model: type[T],
    images: Optional[List[str]] = None,
) -> T:
    model = settings.OLLAMA_VISION_MODEL if images else settings.OLLAMA_MODEL
    content = format_questionnaire_prompt(questionnaire)

    if images:
        content += (
            "\n\nClinical images are attached. "
            "Combine visual findings with questionnaire answers."
        )

    return call_ollama_structured(
        user_content=content,
        images=images,
        response_model=response_model,
        system_prompt=system_prompt,
        model=model,
    )
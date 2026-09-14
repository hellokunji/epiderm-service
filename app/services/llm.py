import json
from functools import lru_cache
from typing import List, Optional, TypeVar

from ollama import Client
from pydantic import BaseModel

from app.core.config import settings
from app.core.flow_log import flow_log
from app.schemas.diagnosis import QuestionnairePayload

T = TypeVar("T", bound=BaseModel)


@lru_cache
def get_ollama_client() -> Client:
    return Client(host=settings.OLLAMA_HOST)


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
        user_message["images"] = images

    response = get_ollama_client().chat(
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
    retrieved_context: Optional[str] = None,
    consult_id: Optional[str] = None,
) -> T:
    model = settings.OLLAMA_VISION_MODEL if images else settings.OLLAMA_MODEL
    content = format_questionnaire_prompt(questionnaire)

    if retrieved_context:
        flow_log(
            "11r5",
            "rag",
            "Injecting retrieved guidelines into LLM user prompt",
            consult_id=consult_id,
            context_chars=len(retrieved_context),
            prompt_chars=len(content) + len(retrieved_context) + 2,
        )
        content = f"{retrieved_context}\n\n{content}"
    else:
        flow_log(
            "11r5",
            "rag",
            "Calling LLM without retrieved guidelines",
            consult_id=consult_id,
        )

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

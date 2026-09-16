import json
from functools import lru_cache
from typing import List, Optional, TypeVar, Union
from urllib.parse import urlparse

import httpx
from ollama import Client
from pydantic import BaseModel

from app.core.config import settings
from app.core.flow_log import flow_log
from app.schemas.diagnosis import QuestionnairePayload
from app.services.s3 import download_s3_object, parse_s3_location

T = TypeVar("T", bound=BaseModel)
ImageInput = Union[str, bytes]


def _is_http_url(value: str) -> bool:
    parsed = urlparse(value)
    return parsed.scheme in {"http", "https"} and bool(parsed.netloc)


def _is_remote_image(value: str) -> bool:
    return value.startswith("s3://") or _is_http_url(value)


def resolve_images_for_ollama(images: Optional[List[str]]) -> Optional[List[ImageInput]]:
    """Ollama only accepts local paths, bytes, or base64 — not remote URLs."""
    if not images:
        return images

    resolved: List[ImageInput] = list(images)
    url_indexes = [index for index, image in enumerate(images) if _is_remote_image(image)]
    if not url_indexes:
        return resolved

    http_client: Optional[httpx.Client] = None
    try:
        for index in url_indexes:
            location = parse_s3_location(images[index])
            if location:
                resolved[index] = download_s3_object(*location)
                continue
            if http_client is None:
                http_client = httpx.Client(timeout=30.0, follow_redirects=True)
            response = http_client.get(images[index])
            response.raise_for_status()
            resolved[index] = response.content
    finally:
        if http_client is not None:
            http_client.close()
    return resolved


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
    ollama_images = resolve_images_for_ollama(images)
    if ollama_images:
        user_message["images"] = ollama_images

    flow_log(
        "11r6",
        "ollama",
        "LLM call started",
        model=model,
        user_content=user_content,
        system_prompt=system_prompt,
        # images=images,
        response_model=response_model,
        temperature=temperature,
    )
    response = get_ollama_client().chat(
        model=model or settings.OLLAMA_MODEL,
        messages=[
            {"role": "system", "content": system_prompt},
            user_message,
        ],
        format=response_model.model_json_schema(),
        options={"temperature": temperature},
    )

    flow_log(
        "11r6",
        "ollama",
        "LLM call completed",
        model=model,
        user_content=user_content,
        system_prompt=system_prompt,
        images=images,
        temperature=temperature,
        total_duration_ns=response.total_duration,
        response_content=response.message.content,
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

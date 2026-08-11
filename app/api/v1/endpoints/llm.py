# app/api/v1/endpoints/llm.py
from fastapi import APIRouter

from app.schemas.llm import LLMPromptRequest, SymptomAnalysis
from app.schemas.response import ok
from app.services.llm import call_ollama_structured

api_router = APIRouter()
s2s_router = APIRouter()


def _run_llm(body: LLMPromptRequest) -> SymptomAnalysis:
    return call_ollama_structured(
        prompt=body.prompt,
        system_prompt=body.system_prompt,
        response_model=SymptomAnalysis,
    )


@s2s_router.post("/")
def llm_s2s(body: LLMPromptRequest):
    result = _run_llm(body)
    return ok(result)


@api_router.post("/")
def llm_client(body: LLMPromptRequest):
    # return ok({"message": "LLM client endpoint"})
    result = _run_llm(body)
    return ok(result)
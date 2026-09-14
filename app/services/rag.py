from __future__ import annotations

import logging
from typing import Any, Optional

from sqlalchemy import text

from app.core.config import settings
from app.core.database import engine
from app.core.flow_log import flow_log
from app.schemas.diagnosis import QuestionnairePayload

logger = logging.getLogger(__name__)

_embedder = None


def get_embedder():
    """Load SentenceTransformer once per process. Import is deferred so the API image stays slim."""
    global _embedder
    if _embedder is None:
        from sentence_transformers import SentenceTransformer

        flow_log(
            "11r0",
            "rag",
            "Loading embedding model (cold start)",
            model=settings.RAG_EMBEDDING_MODEL,
        )
        _embedder = SentenceTransformer(settings.RAG_EMBEDDING_MODEL)
        flow_log(
            "11r0",
            "rag",
            "Embedding model ready",
            model=settings.RAG_EMBEDDING_MODEL,
        )
    return _embedder


def warmup_embedder() -> None:
    if not settings.RAG_ENABLED:
        flow_log("11r0", "rag", "RAG warmup skipped — RAG_ENABLED=false")
        return
    try:
        get_embedder()
    except ImportError:
        flow_log(
            "11r0",
            "rag",
            "RAG warmup skipped — sentence-transformers not installed",
        )


def build_query_text(questionnaire: QuestionnairePayload) -> str:
    lines: list[str] = []
    for item in questionnaire.answers:
        answer = item.answer
        if isinstance(answer, list):
            answer = ", ".join(str(part) for part in answer)
        lines.append(f"{item.question}: {answer}")
    return "\n".join(lines)


def _vector_literal(values: list[float]) -> str:
    return "[" + ",".join(str(float(value)) for value in values) + "]"


def retrieve_guidelines(
    query_text: str,
    category: str,
    top_k: Optional[int] = None,
    *,
    consult_id: Optional[str] = None,
) -> list[dict[str, Any]]:
    limit = top_k if top_k is not None else settings.RAG_TOP_K
    flow_log(
        "11r2",
        "rag",
        "Encoding query text",
        consult_id=consult_id,
        category=category,
        query_chars=len(query_text),
        model=settings.RAG_EMBEDDING_MODEL,
    )
    embedding = get_embedder().encode(query_text).tolist()
    flow_log(
        "11r2",
        "rag",
        "Query embedding generated",
        consult_id=consult_id,
        embedding_dims=len(embedding),
    )
    query_vec = _vector_literal(embedding)

    sql = text(
        """
        SELECT condition_name,
               document_text,
               1 - (embedding <=> CAST(:query_vec AS vector)) AS score
        FROM clinical_rag.knowledge_base
        WHERE category = :category
        ORDER BY embedding <=> CAST(:query_vec AS vector)
        LIMIT :top_k
        """
    )
    flow_log(
        "11r3",
        "postgres",
        "Running pgvector cosine search",
        consult_id=consult_id,
        category=category,
        top_k=limit,
        table="clinical_rag.knowledge_base",
    )
    with engine.connect() as connection:
        rows = connection.execute(
            sql,
            {"query_vec": query_vec, "category": category, "top_k": limit},
        )
        hits = [
            {
                "condition_name": row.condition_name,
                "document_text": row.document_text,
                "score": float(row.score) if row.score is not None else None,
            }
            for row in rows
        ]
    flow_log(
        "11r3",
        "postgres",
        "pgvector search returned rows",
        consult_id=consult_id,
        hit_count=len(hits),
        hits=[
            {
                "condition_name": hit["condition_name"],
                "score": round(hit["score"], 4) if hit["score"] is not None else None,
            }
            for hit in hits
        ],
    )
    return hits


def format_retrieved_context(hits: list[dict[str, Any]]) -> Optional[str]:
    if not hits:
        return None
    sections = [
        "Retrieved clinical guidelines. Use them only when they match the patient; "
        "do not invent protocols that are not supported by this context or the questionnaire.",
    ]
    for hit in hits:
        sections.append(f"### {hit['condition_name']}\n{hit['document_text']}")
    return "\n\n".join(sections)


def rag_summary(hits: list[dict[str, Any]]) -> list[dict[str, Any]]:
    return [
        {"condition_name": hit["condition_name"], "score": hit.get("score")}
        for hit in hits
    ]


def try_retrieve_for_diagnosis(
    questionnaire: QuestionnairePayload,
    category: Optional[str],
    *,
    consult_id: Optional[str] = None,
) -> tuple[Optional[str], list[dict[str, Any]]]:
    if not settings.RAG_ENABLED:
        flow_log(
            "11r1",
            "rag",
            "Skipping RAG — RAG_ENABLED=false",
            consult_id=consult_id,
        )
        return None, []
    if not category:
        flow_log(
            "11r1",
            "rag",
            "Skipping RAG — no consult category on payload",
            consult_id=consult_id,
        )
        return None, []

    try:
        query_text = build_query_text(questionnaire)
        query_preview = query_text.replace("\n", " | ")[:300]
        flow_log(
            "11r1",
            "rag",
            "Built RAG query from questionnaire",
            consult_id=consult_id,
            category=category,
            answer_count=len(questionnaire.answers),
            query_preview=query_preview,
        )
        if not query_text.strip():
            flow_log(
                "11r1",
                "rag",
                "Skipping RAG — empty query text",
                consult_id=consult_id,
            )
            return None, []
        hits = retrieve_guidelines(query_text, category, consult_id=consult_id)
        context = format_retrieved_context(hits)
        flow_log(
            "11r4",
            "rag",
            "Formatted guidelines for LLM prompt",
            consult_id=consult_id,
            category=category,
            hit_count=len(hits),
            has_context=context is not None,
            context_chars=len(context) if context else 0,
            conditions=[hit["condition_name"] for hit in hits],
        )
        return context, rag_summary(hits)
    except Exception as exc:
        logger.exception("RAG retrieval failed; continuing without context")
        flow_log(
            "11r4",
            "rag",
            "RAG retrieval FAILED — continuing without context",
            consult_id=consult_id,
            category=category,
            error_type=type(exc).__name__,
            error=str(exc),
        )
        return None, []

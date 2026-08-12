import json
from typing import Optional

from sqlalchemy.orm import Session

from app.models.consult import ConsultCategory
from app.models.questionnaire import QuestionnaireVersion
from app.schemas.questionnaire import QuestionnaireVersionRead
from app.services.health import get_redis_client

QUESTIONNAIRE_CACHE_KEY_PREFIX = "questionnaire:active:"


def _cache_key(category_value: str) -> str:
    return f"{QUESTIONNAIRE_CACHE_KEY_PREFIX}{category_value}"


def get_cached_active_questionnaire(
    category: ConsultCategory,
) -> Optional[QuestionnaireVersionRead]:
    raw = get_redis_client().get(_cache_key(category.value))
    if raw is None:
        return None
    return QuestionnaireVersionRead.model_validate(json.loads(raw))


def get_active_questionnaire_from_db(
    db: Session,
    category: ConsultCategory,
) -> Optional[QuestionnaireVersionRead]:
    version = (
        db.query(QuestionnaireVersion)
        .filter(
            QuestionnaireVersion.category == category,
            QuestionnaireVersion.is_active.is_(True),
        )
        .one_or_none()
    )
    if version is None:
        return None
    return QuestionnaireVersionRead.model_validate(version)


def cache_active_questionnaires(db: Session) -> list[QuestionnaireVersionRead]:
    versions = (
        db.query(QuestionnaireVersion)
        .filter(QuestionnaireVersion.is_active.is_(True))
        .order_by(QuestionnaireVersion.category)
        .all()
    )

    client = get_redis_client()
    cached: list[QuestionnaireVersionRead] = []

    for version in versions:
        payload = QuestionnaireVersionRead.model_validate(version)
        client.set(_cache_key(payload.category.value), payload.model_dump_json())
        cached.append(payload)

    return cached


def invalidate_active_questionnaire_cache(
    category: Optional[ConsultCategory] = None,
) -> list[str]:
    categories = [category] if category is not None else list(ConsultCategory)
    client = get_redis_client()
    deleted_keys: list[str] = []

    for cat in categories:
        key = _cache_key(cat.value)
        if client.delete(key):
            deleted_keys.append(key)

    return deleted_keys

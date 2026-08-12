from typing import Optional

from fastapi import APIRouter, Depends, Header, HTTPException, Query, status
from pymongo.database import Database
from sqlalchemy.orm import Session

from app.api.deps.database import get_db, get_mongo_db
from app.core.flow_log import flow_log
from app.models.consult import ConsultCategory, ConsultStatus
from app.models.questionnaire import QuestionnaireVersion
from app.schemas.questionnaire import (
    QuestionnaireCacheInvalidateResult,
    QuestionnaireCacheRefreshResult,
    QuestionnaireSubmitRequest,
    QuestionnaireSubmitResult,
    QuestionnaireVersionListResult,
    QuestionnaireVersionRead,
)
from app.schemas.response import ok
from app.services.consult import create_consult, update_consult_status
from app.services.questionnaire_cache import (
    cache_active_questionnaires,
    get_active_questionnaire_from_db,
    get_cached_active_questionnaire,
    invalidate_active_questionnaire_cache,
)
from app.services.questionnaire_job import enqueue_questionnaire_submission
from app.services.questionnaire_response import create_questionnaire_response

api_router = APIRouter()
s2s_router = APIRouter()


def _list_all(db: Session) -> QuestionnaireVersionListResult:
    versions = (
        db.query(QuestionnaireVersion)
        .order_by(QuestionnaireVersion.category, QuestionnaireVersion.version)
        .all()
    )
    return QuestionnaireVersionListResult(
        items=[QuestionnaireVersionRead.model_validate(v) for v in versions]
    )


@api_router.get("/", response_model=QuestionnaireVersionRead)
def get_active_questionnaire(
    category: ConsultCategory = Query(...),
    db: Session = Depends(get_db),
):
    questionnaire = get_cached_active_questionnaire(category)
    if questionnaire is None:
        questionnaire = get_active_questionnaire_from_db(db, category)
    if questionnaire is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"No active questionnaire found for category {category.value}",
        )
    return questionnaire


@api_router.post(
    "/",
    response_model=QuestionnaireSubmitResult,
    status_code=status.HTTP_202_ACCEPTED,
)
def submit_questionnaire(
    body: QuestionnaireSubmitRequest,
    db: Session = Depends(get_db),
    mongo_db: Database = Depends(get_mongo_db),
    x_user_id: str = Header(..., alias="X-User-Id"),
):
    flow_log(
        "01",
        "api",
        "Submit questionnaire request received",
        patient_id=x_user_id,
        category=body.category.value,
        has_questionnaire=body.questionnaire is not None,
        image_count=len(body.images or []),
    )

    consult = create_consult(
        db,
        patient_id=x_user_id,
        category=body.category,
    )
    flow_log(
        "02",
        "postgres",
        "Consult created",
        consult_id=consult.id,
        patient_id=x_user_id,
        status=consult.status.value,
    )

    response_doc = create_questionnaire_response(
        mongo_db,
        consult_id=consult.id,
        patient_id=x_user_id,
        category=body.category,
        questionnaire=body.questionnaire,
        images=body.images,
    )
    response_id = str(response_doc["_id"])
    flow_log(
        "03",
        "mongodb",
        "Questionnaire response saved",
        consult_id=consult.id,
        response_id=response_id,
        collection="questionnaire_response",
    )

    update_consult_status(
        consult.id,
        ConsultStatus.QUESTIONNAIRE_SUBMITTED,
        db=db,
    )

    task_id = enqueue_questionnaire_submission(
        consult_id=consult.id,
        response_id=response_id,
        patient_id=x_user_id,
        category=body.category.value,
    )
    consult = update_consult_status(
        consult.id,
        ConsultStatus.DRAI_DG_PENDING,
        db=db,
    )
    assert consult is not None
    flow_log(
        "05",
        "api",
        "Returning 202 Accepted to client",
        consult_id=consult.id,
        task_id=task_id,
        status=consult.status.value,
    )
    return QuestionnaireSubmitResult(
        consult_id=consult.id,
        status=consult.status,
        task_id=task_id,
    )


# TODO: This has to be accessible for ADMIN role only
@s2s_router.get("/all")
def list_s2s_questionnaires(db: Session = Depends(get_db)):
    return ok(_list_all(db))


@s2s_router.post("/cache/refresh")
def refresh_s2s_questionnaire_cache(db: Session = Depends(get_db)):
    cached = cache_active_questionnaires(db)
    return ok(
        QuestionnaireCacheRefreshResult(
            cached_count=len(cached),
            items=cached,
        )
    )


@s2s_router.post("/cache/invalidate")
def invalidate_s2s_questionnaire_cache(
    category: Optional[ConsultCategory] = Query(default=None),
):
    deleted_keys = invalidate_active_questionnaire_cache(category)
    return ok(
        QuestionnaireCacheInvalidateResult(
            deleted_count=len(deleted_keys),
            deleted_keys=deleted_keys,
        )
    )

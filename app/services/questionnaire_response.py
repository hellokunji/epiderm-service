from datetime import datetime, timezone
from typing import Any, Optional

from pymongo.database import Database

from app.models.consult import ConsultCategory
from app.schemas.diagnosis import QuestionnairePayload

COLLECTION_NAME = "questionnaire_response"


def create_questionnaire_response(
    mongo_db: Database,
    *,
    consult_id: str,
    patient_id: str,
    category: ConsultCategory,
    questionnaire: Optional[QuestionnairePayload] = None,
    images: Optional[list[str]] = None,
) -> dict[str, Any]:
    document: dict[str, Any] = {
        "consult_id": consult_id,
        "patient_id": patient_id,
        "category": category.value,
        "questionnaire": (
            questionnaire.model_dump() if questionnaire is not None else None
        ),
        "images": images,
        "created_at": datetime.now(timezone.utc),
    }
    result = mongo_db[COLLECTION_NAME].insert_one(document)
    document["_id"] = result.inserted_id
    return document

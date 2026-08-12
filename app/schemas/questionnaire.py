from datetime import datetime
from typing import Any, List, Optional

from pydantic import BaseModel, ConfigDict, Field, field_validator

from app.models.consult import ConsultCategory, ConsultStatus
from app.schemas.diagnosis import QuestionnairePayload


class QuestionnaireVersionRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    category: ConsultCategory
    version: int
    is_active: bool
    data: dict[str, Any]
    created_by: str
    created_at: Optional[datetime]


class QuestionnaireVersionListResult(BaseModel):
    items: list[QuestionnaireVersionRead]


class QuestionnaireCacheRefreshResult(BaseModel):
    cached_count: int
    items: list[QuestionnaireVersionRead]


class QuestionnaireCacheInvalidateResult(BaseModel):
    deleted_count: int
    deleted_keys: list[str]

# TODO: Questionnaire request body validation to be updated
class QuestionnaireSubmitRequest(BaseModel):
    category: ConsultCategory
    questionnaire: Optional[QuestionnairePayload] = None
    images: Optional[List[str]] = Field(
        default=None,
        description="Optional base64-encoded clinical images",
    )

    @field_validator("images")
    @classmethod
    def validate_images(cls, images: Optional[List[str]]) -> Optional[List[str]]:
        if images is None:
            return images
        if not all(isinstance(img, str) and img.strip() for img in images):
            raise ValueError("Each image must be a non-empty base64 string")
        return images


class QuestionnaireSubmitResult(BaseModel):
    consult_id: str
    status: ConsultStatus
    task_id: str


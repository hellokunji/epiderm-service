from typing import Any, Optional

from pydantic import BaseModel, ConfigDict

from app.models.consult import ConsultCategory, ConsultStatus


class ConsultRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    patient_id: str
    doctor_id: Optional[str]
    category: ConsultCategory
    status: ConsultStatus


class ConsultDetailRead(ConsultRead):
    diagnosis: Optional[dict[str, Any]] = None


class ConsultListResult(BaseModel):
    items: list[ConsultRead]

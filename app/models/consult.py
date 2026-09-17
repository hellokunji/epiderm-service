import enum
from typing import Optional

from sqlalchemy import Enum, String
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base


class ConsultCategory(str, enum.Enum):
    SKIN = "SKIN"
    HAIR = "HAIR"


class ConsultStatus(str, enum.Enum):
    CREATED = "CREATED"
    QUESTIONNAIRE_SUBMITTED = "QUESTIONNAIRE_SUBMITTED"
    DRAI_DG_PENDING = "DRAI_DG_PENDING"
    DRAI_DG_PROCESSING = "DRAI_DG_PROCESSING"
    GUARDRAIL_REJECTED = "GUARDRAIL_REJECTED"
    DRAI_DG_DIAGNOSED = "DRAI_DG_DIAGNOSED"
    DRAI_DG_PAYMENT_PENDING = "DRAI_DG_PAYMENT_PENDING"
    DRAI_DG_PAYMENT_SUCCESS = "DRAI_DG_PAYMENT_SUCCESS"
    DRAI_DG_PAYMENT_FAILED = "DRAI_DG_PAYMENT_FAILED"
    DR_DG_PENDING = "DR_DG_PENDING"
    DR_DG_APPROVED = "DR_DG_APPROVED"
    DR_DG_REJECTED = "DR_DG_REJECTED"
    DRAI_KIT_PROCESSING = "DRAI_KIT_PROCESSING"
    DRAI_KIT_PROCESSED = "DRAI_KIT_PROCESSED"
    DR_KIT_PENDING = "DR_KIT_PENDING"
    DR_KIT_CREATED = "DR_KIT_CREATED"


class Consult(Base):
    __tablename__ = "consult"

    id: Mapped[str] = mapped_column(String(100), primary_key=True)
    patient_id: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    doctor_id: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    category: Mapped[ConsultCategory] = mapped_column(
        Enum(
            ConsultCategory,
            name="consult_category",
            values_callable=lambda enum_cls: [member.value for member in enum_cls],
        ),
        nullable=False,
    )
    status: Mapped[ConsultStatus] = mapped_column(
        Enum(
            ConsultStatus,
            name="consult_status",
            values_callable=lambda enum_cls: [member.value for member in enum_cls],
        ),
        nullable=False,
        default=ConsultStatus.CREATED,
        server_default=ConsultStatus.CREATED.value,
    )

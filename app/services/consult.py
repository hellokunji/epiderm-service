from typing import Optional
from uuid import uuid4

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.core.database import SessionLocal
from app.core.flow_log import flow_log
from app.models.consult import Consult, ConsultCategory, ConsultStatus


def create_consult(
    db: Session,
    *,
    patient_id: str,
    category: ConsultCategory,
    doctor_id: Optional[str] = None,
    consult_status: ConsultStatus = ConsultStatus.CREATED,
) -> Consult:
    existing = db.query(Consult).filter(Consult.patient_id == patient_id).first()
    if existing is not None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Patient already has an existing consult",
        )

    consult = Consult(
        id=str(uuid4()),
        patient_id=patient_id,
        doctor_id=doctor_id,
        category=category,
        status=consult_status,
    )
    db.add(consult)
    db.commit()
    db.refresh(consult)
    return consult


def update_consult_status(
    consult_id: str,
    new_status: ConsultStatus,
    *,
    db: Optional[Session] = None,
) -> Optional[Consult]:
    """Update consult status (API or Celery worker). Owns the session when db is omitted."""
    owns_session = db is None
    session = db if db is not None else SessionLocal()
    try:
        flow_log(
            "status",
            "postgres",
            "Attempting consult status update",
            consult_id=consult_id,
            to_status=new_status.value,
        )
        consult = session.query(Consult).filter(Consult.id == consult_id).first()
        if consult is None:
            flow_log(
                "status",
                "postgres",
                "Consult not found while updating status",
                consult_id=consult_id,
                new_status=new_status.value,
            )
            return None

        previous = consult.status.value if consult.status else None
        consult.status = new_status
        session.commit()
        session.refresh(consult)
        flow_log(
            "status",
            "postgres",
            "Consult status updated",
            consult_id=consult_id,
            from_status=previous,
            to_status=consult.status.value,
        )
        return consult
    except Exception as exc:
        session.rollback()
        flow_log(
            "status",
            "postgres",
            "Consult status update FAILED",
            consult_id=consult_id,
            to_status=new_status.value,
            error_type=type(exc).__name__,
            error=str(exc),
        )
        raise
    finally:
        if owns_session:
            session.close()

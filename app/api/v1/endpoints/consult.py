from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.api.deps.database import get_db
from app.models.consult import Consult
from app.schemas.consult import ConsultDetailRead, ConsultListResult, ConsultRead
from app.schemas.jobs import DiagnosisResultRead
from app.schemas.response import ok
from app.services.diagnosis_result import get_diagnosis_result_by_consult

api_router = APIRouter()
s2s_router = APIRouter()


def _get_consult_detail(db: Session, consult_id: str) -> ConsultDetailRead:
    consult = db.query(Consult).filter(Consult.id == consult_id).one_or_none()
    if consult is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Consult not found",
        )
    document = get_diagnosis_result_by_consult(consult_id)
    diagnosis = (
        DiagnosisResultRead.model_validate(document) if document is not None else None
    )
    return ConsultDetailRead(
        **ConsultRead.model_validate(consult).model_dump(),
        diagnosis=diagnosis,
    )


def _list_by_patient_id(db: Session, patient_id: str) -> ConsultListResult:
    consults = (
        db.query(Consult)
        .filter(Consult.patient_id == patient_id)
        .order_by(Consult.id)
        .all()
    )
    return ConsultListResult(items=[ConsultRead.model_validate(c) for c in consults])


@api_router.get("/patient/{patient_id}", response_model=ConsultListResult)
def list_consults_by_patient(patient_id: str, db: Session = Depends(get_db)):
    return _list_by_patient_id(db, patient_id)


@s2s_router.get("/patient/{patient_id}")
def list_s2s_consults_by_patient(patient_id: str, db: Session = Depends(get_db)):
    return ok(_list_by_patient_id(db, patient_id))


@api_router.get("/")
def list_client_consults(db: Session = Depends(get_db)):
    consults = db.query(Consult).order_by(Consult.id).all()
    return ConsultListResult(items=[ConsultRead.model_validate(c) for c in consults])


@s2s_router.get("/")
def list_s2s_consults(db: Session = Depends(get_db)):
    consults = db.query(Consult).order_by(Consult.id).all()
    return ok(ConsultListResult(items=[ConsultRead.model_validate(c) for c in consults]))


@api_router.get("/{consult_id}", response_model=ConsultDetailRead)
def get_consult(consult_id: str, db: Session = Depends(get_db)):
    return _get_consult_detail(db, consult_id)


@s2s_router.get("/{consult_id}")
def get_s2s_consult(consult_id: str, db: Session = Depends(get_db)):
    return ok(_get_consult_detail(db, consult_id))

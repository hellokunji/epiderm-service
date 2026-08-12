from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.api.deps.database import get_db
from app.models.consult import Consult
from app.schemas.consult import ConsultListResult, ConsultRead
from app.schemas.response import ok

api_router = APIRouter()
s2s_router = APIRouter()


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

import logging
from datetime import datetime, timezone
from typing import Any, Optional

from app.core.flow_log import flow_log
from app.core.mongodb import connect_to_mongo, get_mongo_db

logger = logging.getLogger(__name__)

COLLECTION_NAME = "diagnosis_result"


def save_diagnosis_result(
    *,
    consult_id: str,
    job_id: str,
    mode: str,
    result: Optional[dict[str, Any]] = None,
    status: str = "success",
    error: Optional[str] = None,
    response_id: Optional[str] = None,
    patient_id: Optional[str] = None,
) -> dict[str, Any]:
    """Persist AI diagnosis output so the FastAPI app can serve it by consult_id."""
    connect_to_mongo()
    mongo_db = get_mongo_db()
    now = datetime.now(timezone.utc)
    document: dict[str, Any] = {
        "consult_id": consult_id,
        "response_id": response_id,
        "patient_id": patient_id,
        "job_id": job_id,
        "mode": mode,
        "status": status,
        "result": result,
        "error": error,
        "updated_at": now,
    }
    flow_log(
        "14",
        "mongodb",
        "Persisting diagnosis_result for FastAPI",
        consult_id=consult_id,
        collection=COLLECTION_NAME,
        job_id=job_id,
        mode=mode,
        status=status,
        response_id=response_id,
    )
    mongo_db[COLLECTION_NAME].update_one(
        {"consult_id": consult_id},
        {"$set": document, "$setOnInsert": {"created_at": now}},
        upsert=True,
    )
    document["created_at"] = document.get("created_at", now)
    flow_log(
        "14b",
        "mongodb",
        "diagnosis_result upsert complete",
        consult_id=consult_id,
        job_id=job_id,
        status=status,
    )
    return document


def get_diagnosis_result_by_consult(consult_id: str) -> Optional[dict[str, Any]]:
    connect_to_mongo()
    mongo_db = get_mongo_db()
    document = mongo_db[COLLECTION_NAME].find_one(
        {"consult_id": consult_id},
        {"_id": 0},
    )
    flow_log(
        "16",
        "api",
        "FastAPI read diagnosis_result by consult",
        consult_id=consult_id,
        found=document is not None,
        status=(document or {}).get("status"),
    )
    return document

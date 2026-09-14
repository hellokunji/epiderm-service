from enum import Enum
from typing import Any, Optional

from pydantic import BaseModel, Field


class JobStatus(str, Enum):
    PENDING = "pending"
    STARTED = "started"
    SUCCESS = "success"
    FAILURE = "failure"
    RETRY = "retry"
    REVOKED = "revoked"


class DiagnosisJobCreated(BaseModel):
    job_id: str
    status: JobStatus = JobStatus.PENDING
    queue: str


class DiagnosisJobStatus(BaseModel):
    job_id: str
    status: JobStatus
    queue: Optional[str] = None
    result: Optional[dict[str, Any]] = None
    error: Optional[str] = None
    progress: Optional[dict[str, Any]] = Field(
        default=None,
        description="Celery task metadata while the job is running",
    )


class DiagnosisResultRead(BaseModel):
    consult_id: str
    job_id: str
    mode: str
    status: str
    result: Optional[dict[str, Any]] = None
    error: Optional[str] = None
    response_id: Optional[str] = None
    patient_id: Optional[str] = None
    rag_context: Optional[list[dict[str, Any]]] = None

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

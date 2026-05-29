"""Processing job schemas."""

from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field

from app.models.enums import JobStatus


class JobCreate(BaseModel):
    """Payload to create a processing job."""

    batch_id: int | None = None
    job_type: str = Field(default="summarize", max_length=64)


class JobRead(BaseModel):
    """Representation of a processing job."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    created_by: int | None
    batch_id: int | None
    job_type: str
    status: JobStatus
    attempts: int
    max_attempts: int
    task_id: str | None
    last_error: str | None
    result: dict | None
    created_at: datetime
    updated_at: datetime

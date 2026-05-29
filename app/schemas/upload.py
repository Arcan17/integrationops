"""Upload-related response schemas."""

from datetime import datetime

from pydantic import BaseModel, ConfigDict

from app.models.enums import BatchStatus, FileStatus


class ValidationErrorRead(BaseModel):
    """A single recorded validation error."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    uploaded_file_id: int
    row_number: int | None
    column_name: str | None
    error_code: str
    message: str


class UploadedFileRead(BaseModel):
    """An uploaded file within a batch."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    filename: str
    content_type: str | None
    size_bytes: int
    row_count: int
    status: FileStatus


class UploadBatchRead(BaseModel):
    """Summary view of an upload batch."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    created_by: int | None
    status: BatchStatus
    total_files: int
    created_at: datetime


class UploadBatchDetail(UploadBatchRead):
    """Detailed view including the batch's files."""

    files: list[UploadedFileRead] = []

"""Export job schemas."""

from datetime import datetime

from pydantic import BaseModel, ConfigDict

from app.models.enums import ExportFormat, ExportStatus


class ExportCreate(BaseModel):
    """Payload to request a data export."""

    batch_id: int | None = None
    export_format: ExportFormat = ExportFormat.csv


class ExportRead(BaseModel):
    """Export job representation."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    batch_id: int | None
    requested_by: int | None
    export_format: ExportFormat
    status: ExportStatus
    file_path: str | None
    created_at: datetime

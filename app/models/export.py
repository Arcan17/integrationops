"""Export job model."""

from sqlalchemy import Enum, ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base, TimestampMixin
from app.models.enums import ExportFormat, ExportStatus


class ExportJob(Base, TimestampMixin):
    """A request to export processed data into a downloadable file."""

    __tablename__ = "export_jobs"

    id: Mapped[int] = mapped_column(primary_key=True)
    requested_by: Mapped[int | None] = mapped_column(
        ForeignKey("users.id", ondelete="SET NULL"), index=True
    )
    batch_id: Mapped[int | None] = mapped_column(
        ForeignKey("upload_batches.id", ondelete="SET NULL"), index=True
    )
    export_format: Mapped[ExportFormat] = mapped_column(
        Enum(ExportFormat, name="export_format"), nullable=False
    )
    status: Mapped[ExportStatus] = mapped_column(
        Enum(ExportStatus, name="export_status"), default=ExportStatus.queued, nullable=False
    )
    file_path: Mapped[str | None] = mapped_column(String(1024))

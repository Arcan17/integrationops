"""Upload-related models: batches, files and validation errors."""

from sqlalchemy import BigInteger, Enum, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, TimestampMixin
from app.models.enums import BatchStatus, FileStatus


class UploadBatch(Base, TimestampMixin):
    """A logical grouping of files uploaded together by a user."""

    __tablename__ = "upload_batches"

    id: Mapped[int] = mapped_column(primary_key=True)
    created_by: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="SET NULL"), nullable=True, index=True
    )
    status: Mapped[BatchStatus] = mapped_column(
        Enum(BatchStatus, name="batch_status"), default=BatchStatus.received, nullable=False
    )
    total_files: Mapped[int] = mapped_column(Integer, default=0, nullable=False)

    files: Mapped[list["UploadedFile"]] = relationship(
        back_populates="batch", cascade="all, delete-orphan"
    )


class UploadedFile(Base, TimestampMixin):
    """A single uploaded file belonging to a batch."""

    __tablename__ = "uploaded_files"

    id: Mapped[int] = mapped_column(primary_key=True)
    batch_id: Mapped[int] = mapped_column(
        ForeignKey("upload_batches.id", ondelete="CASCADE"), nullable=False, index=True
    )
    filename: Mapped[str] = mapped_column(String(255), nullable=False)
    content_type: Mapped[str | None] = mapped_column(String(127))
    size_bytes: Mapped[int] = mapped_column(BigInteger, default=0, nullable=False)
    row_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    storage_path: Mapped[str | None] = mapped_column(String(1024))
    status: Mapped[FileStatus] = mapped_column(
        Enum(FileStatus, name="file_status"), default=FileStatus.pending, nullable=False
    )

    batch: Mapped["UploadBatch"] = relationship(back_populates="files")
    validation_errors: Mapped[list["ValidationError"]] = relationship(
        back_populates="uploaded_file", cascade="all, delete-orphan"
    )


class ValidationError(Base, TimestampMixin):
    """A single validation failure recorded for a row/column of a file."""

    __tablename__ = "validation_errors"

    id: Mapped[int] = mapped_column(primary_key=True)
    uploaded_file_id: Mapped[int] = mapped_column(
        ForeignKey("uploaded_files.id", ondelete="CASCADE"), nullable=False, index=True
    )
    row_number: Mapped[int | None] = mapped_column(Integer)
    column_name: Mapped[str | None] = mapped_column(String(255))
    error_code: Mapped[str] = mapped_column(String(64), nullable=False)
    message: Mapped[str] = mapped_column(Text, nullable=False)

    uploaded_file: Mapped["UploadedFile"] = relationship(back_populates="validation_errors")

"""Ingestion orchestration: parse, validate, persist clean records and errors."""

from sqlalchemy.orm import Session

from app.models.enums import BatchStatus, FileStatus
from app.models.record import DataRecord
from app.models.upload import UploadBatch, UploadedFile, ValidationError
from app.services.audit import record_event
from app.services.parsing import parse_file
from app.services.validation import validate_row


def ingest_file(
    db: Session,
    *,
    user_id: int,
    filename: str,
    content_type: str | None,
    content: bytes,
) -> UploadBatch:
    """Parse and validate an uploaded file, persisting clean rows and errors.

    Raises :class:`app.services.parsing.ParsingError` on unparseable input.
    """
    rows = parse_file(filename, content)

    batch = UploadBatch(created_by=user_id, status=BatchStatus.validating, total_files=1)
    db.add(batch)
    db.flush()  # assign batch.id

    uploaded_file = UploadedFile(
        batch_id=batch.id,
        filename=filename,
        content_type=content_type,
        size_bytes=len(content),
        row_count=len(rows),
        status=FileStatus.pending,
    )
    db.add(uploaded_file)
    db.flush()  # assign uploaded_file.id

    error_count = 0
    for index, row in enumerate(rows, start=1):
        result = validate_row(row, row_number=index)
        if result.is_valid:
            db.add(
                DataRecord(
                    batch_id=batch.id,
                    uploaded_file_id=uploaded_file.id,
                    row_number=index,
                    data=result.cleaned,
                )
            )
        else:
            error_count += len(result.errors)
            for err in result.errors:
                db.add(ValidationError(uploaded_file_id=uploaded_file.id, **err))

    uploaded_file.status = FileStatus.invalid if error_count else FileStatus.valid
    batch.status = BatchStatus.failed if error_count else BatchStatus.validated

    record_event(
        db,
        actor_id=user_id,
        action="upload.ingested",
        entity_type="upload_batch",
        entity_id=batch.id,
        details={
            "filename": filename,
            "rows": len(rows),
            "errors": error_count,
            "status": batch.status.value,
        },
    )

    db.commit()
    db.refresh(batch)

    from app.services.webhooks import emit_event

    emit_event(
        db,
        "upload.ingested",
        {"batch_id": batch.id, "rows": len(rows), "errors": error_count},
    )
    return batch

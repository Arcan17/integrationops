"""Upload ingestion and inspection endpoints."""

from fastapi import APIRouter, Depends, HTTPException, UploadFile, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api.v1.deps import get_current_user, require_roles
from app.db.session import get_db
from app.models.enums import UserRole
from app.models.upload import UploadBatch, UploadedFile, ValidationError
from app.models.user import User
from app.schemas.upload import (
    UploadBatchDetail,
    UploadBatchRead,
    ValidationErrorRead,
)
from app.services.ingestion import ingest_file
from app.services.parsing import ParsingError

router = APIRouter(prefix="/uploads", tags=["uploads"])


def _get_owned_batch(db: Session, batch_id: int, user: User) -> UploadBatch:
    """Fetch a batch, enforcing ownership unless the user is an admin."""
    batch = db.get(UploadBatch, batch_id)
    if batch is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Batch not found")
    if user.role is not UserRole.admin and batch.created_by != user.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not your batch")
    return batch


@router.post(
    "",
    response_model=UploadBatchDetail,
    status_code=status.HTTP_201_CREATED,
    summary="Upload and ingest a CSV/XLSX file",
    description="Parses, validates and stores a data file. Requires operator role.",
)
async def create_upload(
    file: UploadFile,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles(UserRole.operator)),
) -> UploadBatch:
    """Ingest an uploaded data file and return the resulting batch."""
    content = await file.read()
    try:
        return ingest_file(
            db,
            user_id=current_user.id,
            filename=file.filename or "upload",
            content_type=file.content_type,
            content=content,
        )
    except ParsingError as exc:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(exc)
        ) from exc


@router.get(
    "",
    response_model=list[UploadBatchRead],
    summary="List upload batches",
    description="Lists the caller's batches; admins see all batches.",
)
def list_uploads(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> list[UploadBatch]:
    """List upload batches visible to the current user."""
    stmt = select(UploadBatch).order_by(UploadBatch.created_at.desc())
    if current_user.role is not UserRole.admin:
        stmt = stmt.where(UploadBatch.created_by == current_user.id)
    return list(db.scalars(stmt))


@router.get(
    "/{upload_id}",
    response_model=UploadBatchDetail,
    summary="Get an upload batch",
)
def get_upload(
    upload_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> UploadBatch:
    """Return a single batch with its files."""
    return _get_owned_batch(db, upload_id, current_user)


@router.get(
    "/{upload_id}/errors",
    response_model=list[ValidationErrorRead],
    summary="List validation errors for a batch",
)
def get_upload_errors(
    upload_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> list[ValidationError]:
    """Return validation errors recorded for the batch's files."""
    _get_owned_batch(db, upload_id, current_user)
    stmt = (
        select(ValidationError)
        .join(UploadedFile, ValidationError.uploaded_file_id == UploadedFile.id)
        .where(UploadedFile.batch_id == upload_id)
        .order_by(ValidationError.row_number)
    )
    return list(db.scalars(stmt))

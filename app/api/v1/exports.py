"""Export job endpoints."""

from pathlib import Path

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session

from app.api.v1.deps import require_roles
from app.db.session import get_db
from app.models.enums import ExportStatus, UserRole
from app.models.export import ExportJob
from app.models.upload import UploadBatch
from app.models.user import User
from app.schemas.export import ExportCreate, ExportRead
from app.services.export import create_export
from app.workers.tasks import dispatch_export

router = APIRouter(prefix="/exports", tags=["exports"])


def _get_owned_export(db: Session, export_id: int, user: User) -> ExportJob:
    export = db.get(ExportJob, export_id)
    if export is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Export not found")
    if user.role is not UserRole.admin and export.requested_by != user.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not your export")
    return export


@router.post(
    "",
    response_model=ExportRead,
    status_code=status.HTTP_201_CREATED,
    summary="Create and enqueue an export job",
    description="Creates a CSV/XLSX export job and dispatches it. Requires operator role.",
)
def create_export_job(
    payload: ExportCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles(UserRole.operator)),
) -> ExportJob:
    """Create an export job and enqueue file generation."""
    if payload.batch_id is not None and db.get(UploadBatch, payload.batch_id) is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Batch not found")
    export = create_export(
        db,
        user_id=current_user.id,
        batch_id=payload.batch_id,
        export_format=payload.export_format,
    )
    dispatch_export(export.id)
    return export


@router.get("/{export_id}", response_model=ExportRead, summary="Get an export job")
def get_export(
    export_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles(UserRole.viewer)),
) -> ExportJob:
    """Return an export job's status and metadata."""
    return _get_owned_export(db, export_id, current_user)


@router.get(
    "/{export_id}/download",
    summary="Download a completed export file",
    response_class=FileResponse,
)
def download_export(
    export_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles(UserRole.viewer)),
) -> FileResponse:
    """Stream the generated export file when the job has completed."""
    export = _get_owned_export(db, export_id, current_user)
    if export.status is not ExportStatus.completed or not export.file_path:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT, detail="Export is not ready for download"
        )
    path = Path(export.file_path)
    if not path.is_file():
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Export file is missing"
        )
    return FileResponse(path, filename=path.name)

"""Processing job endpoints."""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api.v1.deps import get_current_user, require_roles
from app.db.session import get_db
from app.models.enums import JobStatus, UserRole
from app.models.job import ProcessingJob
from app.models.upload import UploadBatch
from app.models.user import User
from app.schemas.job import JobCreate, JobRead
from app.services.audit import record_event
from app.services.job import create_job
from app.workers.tasks import dispatch_job

router = APIRouter(prefix="/jobs", tags=["jobs"])


def _get_visible_job(db: Session, job_id: int, user: User) -> ProcessingJob:
    """Fetch a job, enforcing ownership via its batch unless the user is admin."""
    job = db.get(ProcessingJob, job_id)
    if job is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Job not found")
    if user.role is not UserRole.admin and job.created_by != user.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not your job")
    return job


@router.post(
    "",
    response_model=JobRead,
    status_code=status.HTTP_201_CREATED,
    summary="Create and enqueue a processing job",
    description="Creates a job and dispatches it to the Celery worker. Requires operator role.",
)
def create_processing_job(
    payload: JobCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles(UserRole.operator)),
) -> ProcessingJob:
    """Create a job and enqueue it for async processing."""
    if payload.batch_id is not None and db.get(UploadBatch, payload.batch_id) is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Batch not found")

    job = create_job(
        db, user_id=current_user.id, batch_id=payload.batch_id, job_type=payload.job_type
    )
    job.task_id = dispatch_job(job.id)
    db.commit()
    db.refresh(job)
    return job


@router.get("", response_model=list[JobRead], summary="List processing jobs")
def list_jobs(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> list[ProcessingJob]:
    """List jobs visible to the current user (admins see all)."""
    stmt = select(ProcessingJob).order_by(ProcessingJob.created_at.desc())
    if current_user.role is not UserRole.admin:
        stmt = stmt.where(ProcessingJob.created_by == current_user.id)
    return list(db.scalars(stmt))


@router.get("/{job_id}", response_model=JobRead, summary="Get a processing job")
def get_job(
    job_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> ProcessingJob:
    """Return a single job's status and result."""
    return _get_visible_job(db, job_id, current_user)


@router.post(
    "/{job_id}/retry",
    response_model=JobRead,
    summary="Retry a failed job",
    description="Re-enqueues a failed job for processing. Requires operator role.",
)
def retry_job(
    job_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles(UserRole.operator)),
) -> ProcessingJob:
    """Reset a failed job to queued and dispatch it again."""
    job = _get_visible_job(db, job_id, current_user)
    if job.status is not JobStatus.failed:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Only failed jobs can be retried",
        )
    job.status = JobStatus.queued
    job.last_error = None
    job.task_id = dispatch_job(job.id)
    record_event(
        db,
        actor_id=current_user.id,
        action="job.retried",
        entity_type="processing_job",
        entity_id=job.id,
    )
    db.commit()
    db.refresh(job)
    return job

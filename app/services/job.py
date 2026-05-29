"""Processing job business logic and execution."""

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.enums import JobStatus
from app.models.job import ProcessingJob
from app.models.record import DataRecord
from app.services.audit import record_event

# Job type used to deterministically trigger a failure (useful for retry demos/tests).
FAILING_JOB_TYPE = "always_fail"
DEFAULT_JOB_TYPE = "summarize"


def create_job(
    db: Session,
    *,
    user_id: int,
    batch_id: int | None,
    job_type: str = DEFAULT_JOB_TYPE,
    max_attempts: int = 3,
) -> ProcessingJob:
    """Create a queued processing job (caller dispatches it to the worker)."""
    job = ProcessingJob(
        created_by=user_id,
        batch_id=batch_id,
        job_type=job_type,
        status=JobStatus.queued,
        attempts=0,
        max_attempts=max_attempts,
    )
    db.add(job)
    record_event(
        db,
        actor_id=user_id,
        action="job.created",
        entity_type="processing_job",
        details={"job_type": job_type, "batch_id": batch_id},
    )
    db.commit()
    db.refresh(job)
    return job


def _summarize_batch(db: Session, batch_id: int | None) -> dict:
    """Compute a simple aggregate over the batch's clean records."""
    if batch_id is None:
        return {"record_count": 0, "total_amount": 0.0}
    records = list(db.scalars(select(DataRecord).where(DataRecord.batch_id == batch_id)))
    total = sum(float(r.data.get("amount", 0) or 0) for r in records)
    return {"record_count": len(records), "total_amount": total}


def execute_job(db: Session, job_id: int) -> ProcessingJob:
    """Run a job's work. Marks it running, then succeeded; raises on failure.

    Retry/failure bookkeeping is handled by the Celery task wrapper.
    """
    job = db.get(ProcessingJob, job_id)
    if job is None:
        raise ValueError(f"ProcessingJob {job_id} not found")

    job.status = JobStatus.running
    job.attempts += 1
    db.commit()

    if job.job_type == FAILING_JOB_TYPE:
        raise RuntimeError("Simulated job failure")

    result = _summarize_batch(db, job.batch_id)
    job.status = JobStatus.succeeded
    job.result = result
    job.last_error = None
    db.commit()
    db.refresh(job)

    from app.services.webhooks import emit_event

    emit_event(
        db,
        "job.succeeded",
        {"job_id": job.id, "batch_id": job.batch_id, "result": result},
    )
    return job

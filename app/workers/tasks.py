"""Celery tasks for asynchronous job processing."""

from app.core.config import get_settings
from app.db.session import SessionLocal
from app.models.enums import JobStatus
from app.models.job import ProcessingJob
from app.services.job import execute_job
from app.workers.celery_app import celery_app

settings = get_settings()


@celery_app.task(bind=True, name="process_job")
def process_job(self, job_id: int) -> dict:
    """Process a job, retrying on failure up to the job's ``max_attempts``."""
    db = SessionLocal()
    try:
        job = execute_job(db, job_id)
        return {"job_id": job.id, "status": job.status.value, "result": job.result}
    except Exception as exc:  # noqa: BLE001 — convert to retry/failed bookkeeping
        job = db.get(ProcessingJob, job_id)
        if job is not None and job.attempts < job.max_attempts:
            job.status = JobStatus.retrying
            job.last_error = str(exc)
            db.commit()
            raise self.retry(
                exc=exc,
                countdown=settings.JOB_RETRY_COUNTDOWN_SECONDS,
                max_retries=job.max_attempts - 1,
            )
        if job is not None:
            job.status = JobStatus.failed
            job.last_error = str(exc)
            db.commit()
        raise
    finally:
        db.close()


def dispatch_job(job_id: int) -> str:
    """Enqueue a job for processing and return the Celery task id."""
    async_result = process_job.delay(job_id)
    return async_result.id


@celery_app.task(name="deliver_webhook")
def deliver_webhook(delivery_id: int) -> None:
    """Send a single webhook delivery over HTTP."""
    from app.services.webhooks import send_delivery

    db = SessionLocal()
    try:
        send_delivery(db, delivery_id)
    finally:
        db.close()


@celery_app.task(name="generate_export")
def generate_export(export_id: int) -> dict:
    """Generate an export file, marking the job failed on error."""
    from app.models.enums import ExportStatus
    from app.models.export import ExportJob
    from app.services.export import run_export

    db = SessionLocal()
    try:
        export = run_export(db, export_id)
        return {"export_id": export.id, "status": export.status.value}
    except Exception as exc:  # noqa: BLE001 — record failure on the job
        export = db.get(ExportJob, export_id)
        if export is not None:
            export.status = ExportStatus.failed
            db.commit()
        raise
    finally:
        db.close()


def dispatch_export(export_id: int) -> str:
    """Enqueue an export job and return the Celery task id."""
    return generate_export.delay(export_id).id

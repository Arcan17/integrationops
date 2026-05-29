"""Export job creation and file generation (CSV via stdlib, XLSX via openpyxl)."""

import csv
import io
from pathlib import Path

from openpyxl import Workbook
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.models.enums import ExportFormat, ExportStatus
from app.models.export import ExportJob
from app.models.record import DataRecord
from app.services.audit import record_event
from app.services.validation import RECORD_SCHEMA

settings = get_settings()

# Stable column order for exported files.
EXPORT_COLUMNS: tuple[str, ...] = tuple(spec.name for spec in RECORD_SCHEMA)


def create_export(
    db: Session,
    *,
    user_id: int,
    batch_id: int | None,
    export_format: ExportFormat,
) -> ExportJob:
    """Create a queued export job (caller dispatches it to the worker)."""
    export = ExportJob(
        requested_by=user_id,
        batch_id=batch_id,
        export_format=export_format,
        status=ExportStatus.queued,
    )
    db.add(export)
    record_event(
        db,
        actor_id=user_id,
        action="export.created",
        entity_type="export_job",
        details={"batch_id": batch_id, "format": export_format.value},
    )
    db.commit()
    db.refresh(export)
    return export


def _fetch_rows(db: Session, batch_id: int | None) -> list[dict]:
    stmt = select(DataRecord)
    if batch_id is not None:
        stmt = stmt.where(DataRecord.batch_id == batch_id)
    stmt = stmt.order_by(DataRecord.row_number)
    return [r.data for r in db.scalars(stmt)]


def _write_csv(rows: list[dict], path: Path) -> None:
    buffer = io.StringIO()
    writer = csv.DictWriter(buffer, fieldnames=list(EXPORT_COLUMNS), extrasaction="ignore")
    writer.writeheader()
    for row in rows:
        writer.writerow(row)
    path.write_text(buffer.getvalue(), encoding="utf-8")


def _write_xlsx(rows: list[dict], path: Path) -> None:
    workbook = Workbook()
    sheet = workbook.active
    sheet.append(list(EXPORT_COLUMNS))
    for row in rows:
        sheet.append([row.get(col, "") for col in EXPORT_COLUMNS])
    workbook.save(path)


def run_export(db: Session, export_id: int) -> ExportJob:
    """Generate the export file for a queued/running export job."""
    export = db.get(ExportJob, export_id)
    if export is None:
        raise ValueError(f"ExportJob {export_id} not found")

    export.status = ExportStatus.running
    db.commit()

    rows = _fetch_rows(db, export.batch_id)
    export_dir = Path(settings.EXPORT_DIR)
    export_dir.mkdir(parents=True, exist_ok=True)
    path = export_dir / f"export_{export.id}.{export.export_format.value}"

    if export.export_format is ExportFormat.csv:
        _write_csv(rows, path)
    else:
        _write_xlsx(rows, path)

    export.file_path = str(path)
    export.status = ExportStatus.completed
    db.commit()
    db.refresh(export)
    return export

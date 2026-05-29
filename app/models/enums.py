"""Enumerations shared across ORM models."""

import enum


class UserRole(str, enum.Enum):
    """Role-based access control roles."""

    admin = "admin"
    operator = "operator"
    viewer = "viewer"


class BatchStatus(str, enum.Enum):
    """Lifecycle status of an upload batch."""

    received = "received"
    validating = "validating"
    validated = "validated"
    failed = "failed"


class FileStatus(str, enum.Enum):
    """Lifecycle status of an individual uploaded file."""

    pending = "pending"
    valid = "valid"
    invalid = "invalid"


class JobStatus(str, enum.Enum):
    """Lifecycle status of an async processing job."""

    queued = "queued"
    running = "running"
    succeeded = "succeeded"
    failed = "failed"
    retrying = "retrying"


class DeliveryStatus(str, enum.Enum):
    """Delivery status of a webhook attempt."""

    pending = "pending"
    delivered = "delivered"
    failed = "failed"


class ExportFormat(str, enum.Enum):
    """Supported export output formats."""

    csv = "csv"
    xlsx = "xlsx"


class ExportStatus(str, enum.Enum):
    """Lifecycle status of an export job."""

    queued = "queued"
    running = "running"
    completed = "completed"
    failed = "failed"

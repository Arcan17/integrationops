"""Integration tests covering the upload → job → export flow.

These require a reachable PostgreSQL database and run Celery eagerly.
"""

from tests.conftest import auth_header, make_user

from app.models.enums import UserRole

GOOD_CSV = b"external_id,email,amount\nC-1,a@b.com,10\nC-2,c@d.com,5\n"
BAD_CSV = b"external_id,email,amount\nC-1,not-email,abc\n"


def test_register_login_and_me(client):
    client.post(
        "/api/v1/auth/register",
        json={"email": "viewer@example.com", "password": "password123"},
    )
    headers = auth_header(client, "viewer@example.com", "password123")
    resp = client.get("/api/v1/users/me", headers=headers)
    assert resp.status_code == 200
    assert resp.json()["role"] == "viewer"


def test_viewer_cannot_upload(client, db):
    make_user(db, "v@example.com", "password123", UserRole.viewer)
    headers = auth_header(client, "v@example.com", "password123")
    resp = client.post(
        "/api/v1/uploads",
        headers=headers,
        files={"file": ("d.csv", GOOD_CSV, "text/csv")},
    )
    assert resp.status_code == 403


def test_upload_validates_and_summarizes(client, db):
    make_user(db, "op@example.com", "password123", UserRole.operator)
    headers = auth_header(client, "op@example.com", "password123")

    upload = client.post(
        "/api/v1/uploads",
        headers=headers,
        files={"file": ("d.csv", GOOD_CSV, "text/csv")},
    )
    assert upload.status_code == 201, upload.text
    batch = upload.json()
    assert batch["status"] == "validated"
    batch_id = batch["id"]

    job = client.post(
        "/api/v1/jobs",
        headers=headers,
        json={"batch_id": batch_id, "job_type": "summarize"},
    )
    assert job.status_code == 201, job.text
    body = job.json()
    # Eager execution means the job has already run.
    assert body["status"] == "succeeded"
    assert body["result"]["record_count"] == 2
    assert body["result"]["total_amount"] == 15.0


def test_invalid_rows_are_reported(client, db):
    make_user(db, "op2@example.com", "password123", UserRole.operator)
    headers = auth_header(client, "op2@example.com", "password123")

    upload = client.post(
        "/api/v1/uploads",
        headers=headers,
        files={"file": ("bad.csv", BAD_CSV, "text/csv")},
    )
    assert upload.status_code == 201
    batch_id = upload.json()["id"]
    assert upload.json()["status"] == "failed"

    errors = client.get(f"/api/v1/uploads/{batch_id}/errors", headers=headers)
    assert errors.status_code == 200
    codes = {e["error_code"] for e in errors.json()}
    assert {"invalid_email", "invalid_number"} <= codes


def test_failing_job_can_be_retried(client, db):
    make_user(db, "op3@example.com", "password123", UserRole.operator)
    headers = auth_header(client, "op3@example.com", "password123")

    job = client.post(
        "/api/v1/jobs", headers=headers, json={"job_type": "always_fail"}
    )
    job_id = job.json()["id"]
    assert job.json()["status"] == "failed"

    retry = client.post(f"/api/v1/jobs/{job_id}/retry", headers=headers)
    # Retried job fails again (deterministically), but the endpoint accepts it.
    assert retry.status_code == 200

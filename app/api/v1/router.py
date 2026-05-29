"""Aggregated API v1 router.

Feature routers (auth, uploads, jobs, webhooks, exports, audit logs) are
registered here as they are implemented in later phases.
"""

from fastapi import APIRouter

from app.api.v1 import audit_logs, auth, exports, health, jobs, uploads, users, webhooks

api_router = APIRouter()
api_router.include_router(health.router)
api_router.include_router(auth.router)
api_router.include_router(users.router)
api_router.include_router(uploads.router)
api_router.include_router(jobs.router)
api_router.include_router(webhooks.router)
api_router.include_router(exports.router)
api_router.include_router(audit_logs.router)

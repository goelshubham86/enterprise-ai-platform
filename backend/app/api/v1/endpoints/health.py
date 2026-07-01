"""Health check endpoint.

Returns HTTP 200 in all cases so Cloud Run's startup probe always passes.
The `status` field conveys the actual readiness state:

    "starting"  — background service init is in progress (probe passes, 503 on upload)
    "healthy"   — all services are initialised and ready for traffic
    "degraded"  — service init failed; probe passes but upload returns 503

This separation lets Cloud Run mark the instance as "started" (probe passes)
while still signalling to operators (via the status field and service entries)
that backend services may be unavailable.
"""

import time
from datetime import datetime, timezone

from fastapi import APIRouter, Request

from app.core.config import settings

router = APIRouter()

START_TIME = time.time()


@router.get("")
async def health_check(request: Request) -> dict:
    services_ready: bool = getattr(request.app.state, "_services_ready", False)
    init_error: str | None = getattr(request.app.state, "_init_error", None)

    if services_ready:
        status = "healthy"
        service_entries = [
            {"name": "FastAPI", "status": "healthy", "latencyMs": None, "details": "Running"},
            {"name": "ChromaDB", "status": "healthy", "latencyMs": None, "details": "Connected"},
            {"name": "Cloud Storage", "status": "healthy", "latencyMs": None, "details": "Connected"},
            {"name": "Vertex AI Embeddings", "status": "healthy", "latencyMs": None, "details": "Connected"},
        ]
    elif init_error:
        status = "degraded"
        service_entries = [
            {"name": "FastAPI", "status": "healthy", "latencyMs": None, "details": "Running"},
            {
                "name": "Backend Services",
                "status": "unhealthy",
                "latencyMs": None,
                "details": f"Initialisation failed: {init_error}",
            },
        ]
    else:
        status = "starting"
        service_entries = [
            {"name": "FastAPI", "status": "healthy", "latencyMs": None, "details": "Running"},
            {
                "name": "Backend Services",
                "status": "starting",
                "latencyMs": None,
                "details": "Initialising in background — upload endpoint returns 503 until ready",
            },
        ]

    return {
        "status": status,
        "version": "0.2.0",
        "environment": settings.app_env,
        "uptime": int(time.time() - START_TIME),
        "services": service_entries,
        "checkedAt": datetime.now(timezone.utc).isoformat(),
    }

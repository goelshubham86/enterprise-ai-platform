"""Health check endpoint — stub for Phase 1."""
import time
from datetime import datetime, timezone
from fastapi import APIRouter

router = APIRouter()

START_TIME = time.time()


@router.get("")
async def health_check() -> dict:
    return {
        "status": "healthy",
        "version": "0.1.0",
        "environment": "development",
        "uptime": int(time.time() - START_TIME),
        "services": [
            {"name": "FastAPI", "status": "healthy", "latencyMs": None, "details": "Running"},
            {"name": "Vertex AI", "status": "healthy", "latencyMs": None, "details": "Not yet connected"},
            {"name": "Cloud Storage", "status": "healthy", "latencyMs": None, "details": "Not yet connected"},
        ],
        "checkedAt": datetime.now(timezone.utc).isoformat(),
    }

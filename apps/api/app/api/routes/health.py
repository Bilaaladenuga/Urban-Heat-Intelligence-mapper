"""Health check endpoints."""

from datetime import UTC, datetime

from fastapi import APIRouter

from app.core import db
from app.core.config import settings

router = APIRouter()


@router.get("/health")
def health() -> dict:
    """Liveness check for the API and its configuration."""
    return {
        "status": "ok",
        "app": settings.app_name,
        "version": "0.1.0",
        "environment": settings.environment,
        "database": "configured" if db.is_configured() else "not_configured",
        "time": datetime.now(UTC).isoformat(),
    }


@router.get("/health/db")
def health_db() -> dict:
    """PostGIS connectivity check (does not fail when the DB is unconfigured)."""
    return {
        "status": "ok",
        "database": "configured" if db.is_configured() else "not_configured",
        "postgis": db.postgis_version() if db.is_configured() else None,
    }

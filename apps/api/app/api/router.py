"""Aggregates all versioned API route modules."""

from fastapi import APIRouter

from app.api.routes import boundaries, health

api_router = APIRouter()
api_router.include_router(health.router, tags=["health"])
api_router.include_router(boundaries.router, tags=["boundaries"])

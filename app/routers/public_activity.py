"""
app/routers/public_activity.py - Public anonymized activity endpoints.
"""

from __future__ import annotations

from fastapi import APIRouter, Query

from app.services.metrics_store import get_public_activity, get_public_stats


router = APIRouter()


@router.get("/public/activity", tags=["Public"])
async def public_activity(
    limit: int = Query(default=100, ge=1, le=100),
):
    return get_public_activity(limit=limit)


@router.get("/public/stats", tags=["Public"])
async def public_stats():
    return get_public_stats()

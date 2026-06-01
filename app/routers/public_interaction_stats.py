"""
app/routers/public_interaction_stats.py

Public aggregate stats for the experimental interaction-stability endpoint.
Only aggregate metrics are exposed; no raw text, request IDs, API key hashes,
input hashes, content fingerprints, or per-user rows are returned.
"""

from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Query

from app.services.interaction_store import get_interaction_stats

router = APIRouter(prefix="/public/interaction", tags=["Public"])


@router.get("/stats")
async def public_interaction_stats(
    days: int = Query(7, ge=1, le=90, description="Aggregation window in days."),
) -> dict[str, Any]:
    return get_interaction_stats(days=days)

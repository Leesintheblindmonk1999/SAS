"""
app/routers/metrics.py - Admin metrics endpoint for SAS API.
"""

from __future__ import annotations

from fastapi import APIRouter, Header, HTTPException, Query

from app.config import settings
from app.services.metrics_store import get_metrics_summary


router = APIRouter()


def require_admin_secret(x_admin_secret: str | None) -> None:
    admin_secret = getattr(settings, "admin_secret", "")

    if not admin_secret:
        raise HTTPException(
            status_code=503,
            detail="Admin metrics unavailable: ADMIN_SECRET is not configured.",
        )

    if x_admin_secret != admin_secret:
        raise HTTPException(status_code=403, detail="Forbidden")


@router.get("/metrics", include_in_schema=False)
async def metrics(
    window: str = Query(
        default="24h",
        description="Metrics window. Allowed values: 24h, 7d, 30d.",
    ),
    x_admin_secret: str | None = Header(default=None, alias="X-Admin-Secret"),
):
    """
    Admin-only aggregated API metrics.

    Does not expose raw IPs, raw API keys, or API key hashes.
    """
    require_admin_secret(x_admin_secret)

    try:
        return get_metrics_summary(window=window)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

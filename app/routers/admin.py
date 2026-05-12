"""
app/routers/admin.py - SAS Admin endpoints.

Protected by ADMIN_SECRET from Render/.env.
Without ADMIN_SECRET configured, admin endpoints return 503.
"""

from __future__ import annotations

from datetime import datetime, timezone

from fastapi import APIRouter, Header, HTTPException

from app.config import settings
from app.services.auth import create_new_user

router = APIRouter()


def _require_admin_secret(admin_secret: str) -> None:
    if not settings.admin_secret:
        raise HTTPException(status_code=503, detail="ADMIN_SECRET is not configured")

    if admin_secret != settings.admin_secret:
        raise HTTPException(status_code=403, detail="Invalid admin secret")


@router.post("/generate-key", summary="Generate a new API key (admin only)")
async def generate_api_key(
    is_premium: bool = False,
    admin_secret: str = Header(..., alias="X-Admin-Secret"),
):
    """
    Generate a new API key.

    Requires X-Admin-Secret header matching ADMIN_SECRET in Render/.env.
    The raw key is returned ONCE and is never stored in plaintext.
    """
    _require_admin_secret(admin_secret)

    try:
        raw_key = create_new_user(is_premium=is_premium)
        return {
            "api_key": raw_key,
            "is_premium": is_premium,
            "message": "Save this key immediately. It will not be shown again.",
            "rate_limit": "unlimited" if is_premium else f"{settings.free_requests_per_day} requests/day",
        }
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc


@router.get("/metrics", summary="Get API usage metrics (admin only)")
async def get_metrics(
    admin_secret: str = Header(..., alias="X-Admin-Secret"),
):
    """
    Legacy private admin metrics placeholder.

    The newer admin metrics endpoint is /v1/metrics.
    """
    _require_admin_secret(admin_secret)

    return {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "status": "legacy_metrics_placeholder",
        "message": "Use /v1/metrics?window=24h for real admin metrics.",
        "endpoints": {
            "real_metrics": "/v1/metrics?window=24h",
        },
    }

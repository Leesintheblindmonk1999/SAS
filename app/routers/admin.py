"""
app/routers/admin.py — Omni-Scanner API v1.0
Admin endpoint for API key generation and metrics.

SECURITY: protected by ADMIN_SECRET from .env.
Without this, anyone could generate free keys or see usage data.
"""
from fastapi import APIRouter, HTTPException, Header
from datetime import datetime
from app.services.auth import create_new_user
from app.config import settings

router = APIRouter()


@router.post("/generate-key", summary="Generate a new API key (admin only)")
async def generate_api_key(
    is_premium: bool = False,
    admin_secret: str = Header(..., alias="X-Admin-Secret"),
):
    """
    Generate a new API key.

    Requires X-Admin-Secret header matching ADMIN_SECRET in .env.
    The raw key is returned ONCE — it is never stored in plaintext.
    """
    if admin_secret != settings.admin_secret:
        raise HTTPException(status_code=403, detail="Invalid admin secret")

    try:
        raw_key = create_new_user(is_premium=is_premium)
        return {
            "api_key":   raw_key,
            "is_premium": is_premium,
            "message":   "Save this key immediately. It will not be shown again.",
            "rate_limit": "unlimited" if is_premium else f"{settings.free_requests_per_day} requests/day",
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ──────────────────────────────────────────────────────────────────────────────
# METRICS ENDPOINT (Private)
# ──────────────────────────────────────────────────────────────────────────────

@router.get("/metrics", summary="Get API usage metrics (admin only)")
async def get_metrics(
    admin_secret: str = Header(..., alias="X-Admin-Secret"),
):
    """
    Private endpoint for API usage metrics.
    Requires X-Admin-Secret header matching ADMIN_SECRET in .env.

    Returns placeholder data. Full implementation will include:
    - Total requests per endpoint
    - Requests per API key
    - Top IPs
    - Average latency
    """
    if admin_secret != settings.admin_secret:
        raise HTTPException(status_code=403, detail="Invalid admin secret")

    # TODO: Implement real metrics collection from database/cache
    return {
        "timestamp": datetime.utcnow().isoformat() + "Z",
        "status": "metrics_collection_not_yet_implemented",
        "message": "Full metrics coming soon. Currently collecting data from logs.",
        "planned_metrics": [
            "total_requests_per_day",
            "requests_by_endpoint",
            "requests_by_api_key",
            "top_ips",
            "average_latency_per_endpoint",
            "error_rate_by_endpoint",
        ],
        "note": "Use Render logs or your own monitoring for detailed analytics until this endpoint is fully implemented.",
    }

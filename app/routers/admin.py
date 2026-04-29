"""
app/routers/admin.py — Omni-Scanner API v1.0
Admin endpoint for API key generation.

SECURITY: protected by ADMIN_SECRET from .env.
Without this, anyone could generate free keys.
"""
from fastapi import APIRouter, HTTPException, Header
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
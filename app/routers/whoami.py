"""
app/routers/whoami.py - User key identity endpoint.

Mounted with prefix /v1:
GET /v1/whoami
"""

from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Depends, Request

from app.db.auth_store import quota_state, usage_counts
from app.services.auth import get_current_user

router = APIRouter()


@router.get("/whoami", tags=["Auth"])
async def whoami(
    request: Request,
    user: dict[str, Any] = Depends(get_current_user),
) -> dict[str, Any]:
    if user.get("plan") == "legacy":
        return {
            "status": "ok",
            "plan": "legacy",
            "active": True,
            "email": None,
            "email_hash": user.get("email_hash"),
            "daily_limit": None,
            "monthly_limit": None,
            "daily_used": 0,
            "monthly_used": 0,
            "legacy": True,
        }

    counts = usage_counts(int(user["id"]))
    state = quota_state(user)

    # Mask email: show first 2 chars + *** + @domain to avoid enumeration.
    raw_email = user.get("email") or ""
    if raw_email and "@" in raw_email:
        local, domain = raw_email.split("@", 1)
        masked_email = local[:2] + "***@" + domain
    else:
        masked_email = None

    return {
        "status": "ok",
        "plan": user.get("plan"),
        "active": user.get("status") == "active",
        "email": masked_email,
        "email_hash": user.get("email_hash"),
        "daily_limit": user.get("daily_limit"),
        "monthly_limit": user.get("monthly_limit"),
        "daily_used": counts["daily"],
        "monthly_used": counts["monthly"],
        "quota_allowed": state["allowed"],
        "quota_reason": state["reason"],
    }

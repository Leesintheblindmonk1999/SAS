"""
app/routers/whoami.py - User key identity endpoint.

Mounted with prefix /v1:
GET /v1/whoami
"""

from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Depends, Request

from app.config import settings
from app.db.auth_store import quota_state, usage_counts
from app.services.auth import get_current_user

router = APIRouter()


def _mask_email(raw_email: str | None) -> str | None:
    """Mask email: show first 2 chars + *** + @domain to avoid enumeration."""
    if not raw_email or "@" not in raw_email:
        return None

    local, domain = raw_email.split("@", 1)
    return local[:2] + "***@" + domain


@router.get("/whoami", tags=["Auth"])
async def whoami(
    request: Request,
    user: dict[str, Any] = Depends(get_current_user),
) -> dict[str, Any]:
    counts = usage_counts(int(user["id"]))
    state = quota_state(user)

    if user.get("plan") == "legacy":
        return {
            "status": "ok",
            "plan": "legacy",
            "active": user.get("status") == "active",
            "email": None,
            "email_hash": user.get("email_hash"),
            "daily_limit": user.get("daily_limit"),
            "monthly_limit": user.get("monthly_limit"),
            "daily_used": counts["daily"],
            "monthly_used": counts["monthly"],
            "quota_allowed": state["allowed"],
            "quota_reason": state["reason"],
            "legacy": True,
            "message": getattr(
                settings,
                "legacy_deprecation_message",
                "This shared legacy key is limited. Request a personal free API key.",
            ),
        }

    return {
        "status": "ok",
        "plan": user.get("plan"),
        "active": user.get("status") == "active",
        "email": _mask_email(user.get("email")),
        "email_hash": user.get("email_hash"),
        "daily_limit": user.get("daily_limit"),
        "monthly_limit": user.get("monthly_limit"),
        "daily_used": counts["daily"],
        "monthly_used": counts["monthly"],
        "quota_allowed": state["allowed"],
        "quota_reason": state["reason"],
    }

"""
app/services/auth.py - SAS API key authentication.

This file replaces the older simple auth module while preserving compatibility
with existing imports:
- init_auth_db()
- validate_api_key(api_key)
- verify_api_key(api_key)
- create_new_user(is_premium=False)

It also provides:
- api_key_auth_middleware
- get_current_user
"""

from __future__ import annotations

from typing import Any

from fastapi import Header, HTTPException, Request
from fastapi.responses import JSONResponse

from app.db.auth_store import (
    create_admin_key,
    get_user_by_api_key,
    init_auth_db,
    quota_state,
    record_api_usage,
)


PROTECTED_PREFIXES = (
    "/v1/audit",
    "/v1/diff",
    "/v1/chat",
    "/v1/audit_conversation",
    "/v1/whoami",
)


def _is_protected_path(path: str) -> bool:
    return any(path == prefix or path.startswith(prefix + "/") for prefix in PROTECTED_PREFIXES)


def _api_key_from_request(request: Request) -> str | None:
    auth = request.headers.get("Authorization", "").strip()
    bearer = auth.replace("Bearer ", "", 1).strip() if auth.lower().startswith("bearer ") else ""
    return request.headers.get("X-API-Key") or request.headers.get("x-api-key") or bearer or None


def validate_api_key(api_key: str) -> tuple[bool, int | None]:
    """Compatibility function used by existing dependencies.py."""
    user = get_user_by_api_key(api_key)
    if not user:
        return False, None
    if user.get("status") != "active":
        return False, None
    return True, int(user["id"]) if user.get("id") else None


def verify_api_key(api_key: str) -> bool:
    """Compatibility function used by old code."""
    ok, _ = validate_api_key(api_key)
    return ok


def create_new_user(is_premium: bool = False) -> str:
    """Compatibility function used by /admin/generate-key."""
    init_auth_db()
    return create_admin_key(is_premium=is_premium)


def verify_api_key_value(api_key: str | None) -> dict[str, Any]:
    if not api_key:
        raise HTTPException(status_code=401, detail="Missing X-API-Key header")

    user = get_user_by_api_key(api_key)
    if not user:
        raise HTTPException(status_code=401, detail="Invalid API key")

    if user.get("status") != "active":
        raise HTTPException(status_code=403, detail="API key is not active")

    return user


async def get_current_user(
    request: Request,
    x_api_key: str | None = Header(default=None, alias="X-API-Key"),
) -> dict[str, Any]:
    existing = getattr(request.state, "api_user", None)
    if existing:
        return existing
    return verify_api_key_value(x_api_key)


async def api_key_auth_middleware(request: Request, call_next):
    path = request.url.path

    if not _is_protected_path(path):
        return await call_next(request)

    try:
        api_key = _api_key_from_request(request)
        user = verify_api_key_value(api_key)
        state = quota_state(user)

        if not state["allowed"]:
            return JSONResponse(
                status_code=429,
                content={
                    "error": "quota_exceeded",
                    "reason": state["reason"],
                    "plan": user.get("plan"),
                    "daily_used": state["daily_used"],
                    "daily_limit": state["daily_limit"],
                    "monthly_used": state["monthly_used"],
                    "monthly_limit": state["monthly_limit"],
                },
            )

        request.state.api_user = user
        request.state.api_quota = state

    except HTTPException as exc:
        return JSONResponse(status_code=exc.status_code, content={"detail": exc.detail})

    response = await call_next(request)

    try:
        record_api_usage(
            user=user,
            method=request.method,
            path=path,
            status_code=response.status_code,
            request_id=getattr(request.state, "request_id", None),
        )
    except Exception:
        # Usage logging must never break the request.
        pass

    return response

"""
app/middleware/rate_limit.py

Rate limit utilities for SAS.

Compatibility:
- Keeps existing in-memory check_rate_limit().
- Keeps existing ip_hash().
- Keeps RateLimitMiddleware placeholder.
- Adds persistent SQLite-backed limiter helpers for E1.
"""

from __future__ import annotations

import hashlib
import time
from threading import Lock
from typing import Any

from fastapi import HTTPException, Request
from starlette.middleware.base import BaseHTTPMiddleware

from app.services.rate_limit_store import check_persistent_rate_limit

# NOTE: _BUCKETS lives in RAM and resets on every server restart.
# Persistent SQLite-backed limits are added below for selected public routes.
_BUCKETS: dict[str, list[float]] = {}
_LOCK = Lock()

_LAST_CLEANUP: float = 0.0
_CLEANUP_INTERVAL: float = 300.0  # every 5 minutes


class RateLimitMiddleware(BaseHTTPMiddleware):
    """Compatibility placeholder. Existing app can still import this class."""

    async def dispatch(self, request: Request, call_next):
        return await call_next(request)


def client_ip(request: Request) -> str:
    return (
        request.headers.get("true-client-ip")
        or request.headers.get("cf-connecting-ip")
        or request.headers.get("x-real-ip")
        or request.headers.get("x-forwarded-for", "").split(",")[0].strip()
        or (request.client.host if request.client else "unknown")
        or "unknown"
    )


def ip_hash(request: Request) -> str:
    ip = client_ip(request)
    return hashlib.sha256(ip.encode("utf-8")).hexdigest()[:16]


def country_from_request(request: Request) -> str:
    return (
        request.headers.get("cf-ipcountry")
        or request.headers.get("x-vercel-ip-country")
        or request.headers.get("x-country")
        or "unknown"
    )


def check_rate_limit(key: str, limit: int, window_seconds: int) -> None:
    """
    Existing in-memory rate limiter.

    Kept for backward compatibility with current routers.
    """
    now = time.time()
    cutoff = now - window_seconds

    global _LAST_CLEANUP

    with _LOCK:
        # Lazy cleanup to avoid unbounded memory growth.
        if now - _LAST_CLEANUP > _CLEANUP_INTERVAL:
            stale = [k for k, v in _BUCKETS.items() if not any(ts >= cutoff for ts in v)]
            for k in stale:
                del _BUCKETS[k]
            _LAST_CLEANUP = now

        bucket = _BUCKETS.get(key, [])
        bucket = [ts for ts in bucket if ts >= cutoff]

        if len(bucket) >= limit:
            raise HTTPException(
                status_code=429,
                detail="Rate limit exceeded. Try again later.",
            )

        bucket.append(now)
        _BUCKETS[key] = bucket


async def check_persistent_limit_or_raise(
    request: Request,
    key: str,
    scope: str,
    limit: int,
    window_seconds: int,
) -> dict[str, Any]:
    """
    Persistent SQLite-backed rate limit check.

    Raises HTTPException 429 if blocked.
    Fails open if the store has an internal problem.
    """
    result = await check_persistent_rate_limit(
        key=key,
        scope=scope,
        limit=limit,
        window_seconds=window_seconds,
        path=request.url.path,
        method=request.method,
        request_id=getattr(request.state, "request_id", "unknown"),
        country=country_from_request(request),
    )

    if not result.get("allowed", True):
        retry_after = int(result.get("retry_after_seconds") or window_seconds)
        raise HTTPException(
            status_code=429,
            detail={
                "error": "Persistent rate limit exceeded",
                "message": "Too many requests for this endpoint. Please wait and retry.",
                "scope": result.get("scope", scope),
                "limit": int(result.get("limit", limit)),
                "window_seconds": int(result.get("window_seconds", window_seconds)),
                "current_count": int(result.get("current_count", limit)),
                "retry_after_seconds": retry_after,
            },
            headers={"Retry-After": str(retry_after)},
        )

    return result


_PUBLIC_LIMITS: dict[tuple[str, str], tuple[str, int, int]] = {
    ("GET", "/public/request-key"): ("public_request_key_get", 20, 60),
    ("POST", "/public/request-key"): ("public_request_key_post", 5, 600),
    ("POST", "/public/demo/audit"): ("public_demo_audit_post", 15, 600),
    ("GET", "/public/stats"): ("public_stats_get", 60, 60),
    ("GET", "/public/activity"): ("public_activity_get", 60, 60),
}


async def persistent_rate_limit_middleware(request: Request, call_next: Any):
    """
    Path/method based persistent limiter for public surfaces.

    Registered inside request_monitoring_middleware so request.state.request_id
    is available, but before endpoint logic runs.
    """
    path = request.url.path.rstrip("/") or "/"
    method = request.method.upper()

    rule = _PUBLIC_LIMITS.get((method, path))
    if rule:
        scope, limit, window_seconds = rule
        key = f"ip:{ip_hash(request)}"
        await check_persistent_limit_or_raise(
            request=request,
            key=key,
            scope=scope,
            limit=limit,
            window_seconds=window_seconds,
        )

    return await call_next(request)

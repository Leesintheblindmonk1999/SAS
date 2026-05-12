"""
app/middleware/rate_limit.py - Simple in-memory rate limiter.

Good enough for first production version.
For multiple Render instances, replace later with Redis or DB-backed limits.
"""

from __future__ import annotations

import hashlib
import time
from threading import Lock

from fastapi import HTTPException, Request, Response
from starlette.middleware.base import BaseHTTPMiddleware

# NOTE: _BUCKETS lives in RAM and resets on every server restart.
# On Render Free tier this means a user could bypass the rate limit
# across restarts. Acceptable for v1. Migrate to SQLite-backed
# rate limit when scaling to multiple instances.
_BUCKETS: dict[str, list[float]] = {}
_LOCK = Lock()

# Periodically clean up old buckets to prevent unbounded memory growth.
# Called lazily inside check_rate_limit.
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
        or request.headers.get("x-forwarded-for", "").split(",")[0].strip()
        or (request.client.host if request.client else "unknown")
    )


def ip_hash(request: Request) -> str:
    ip = client_ip(request)
    return hashlib.sha256(ip.encode("utf-8")).hexdigest()[:16]


def check_rate_limit(key: str, limit: int, window_seconds: int) -> None:
    now = time.time()
    cutoff = now - window_seconds

    global _LAST_CLEANUP

    with _LOCK:
        # Lazy cleanup to avoid unbounded memory growth
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

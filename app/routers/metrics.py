"""
app/routers/metrics.py - Admin metrics endpoint for SAS API.
"""

from __future__ import annotations

import hashlib

from fastapi import APIRouter, BackgroundTasks, Header, HTTPException, Query, Request

from app.config import settings
from app.services.email_alerts import alert_invalid_admin_access
from app.services.metrics_store import get_metrics_summary


router = APIRouter()


def _client_ip(request: Request) -> str:
    return (
        request.headers.get("true-client-ip")
        or request.headers.get("cf-connecting-ip")
        or request.headers.get("x-forwarded-for", "").split(",")[0].strip()
        or (request.client.host if request.client else "unknown")
    )


def _hash_ip(ip: str) -> str:
    return hashlib.sha256(ip.encode("utf-8")).hexdigest()[:12]


def _country(request: Request) -> str:
    return request.headers.get("cf-ipcountry", "unknown")


def require_admin_secret(
    *,
    request: Request,
    background_tasks: BackgroundTasks,
    x_admin_secret: str | None,
) -> None:
    admin_secret = getattr(settings, "admin_secret", "")

    if not admin_secret:
        background_tasks.add_task(
            alert_invalid_admin_access,
            endpoint=str(request.url.path),
            method=request.method,
            ip_hash=_hash_ip(_client_ip(request)),
            country=_country(request),
            reason="admin_secret_not_configured",
        )
        raise HTTPException(
            status_code=503,
            detail="Admin metrics unavailable: ADMIN_SECRET is not configured.",
        )

    if x_admin_secret != admin_secret:
        background_tasks.add_task(
            alert_invalid_admin_access,
            endpoint=str(request.url.path),
            method=request.method,
            ip_hash=_hash_ip(_client_ip(request)),
            country=_country(request),
            reason="invalid_admin_secret",
        )
        raise HTTPException(status_code=403, detail="Forbidden")


@router.get("/metrics", include_in_schema=False)
async def metrics(
    request: Request,
    background_tasks: BackgroundTasks,
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
    require_admin_secret(
        request=request,
        background_tasks=background_tasks,
        x_admin_secret=x_admin_secret,
    )

    try:
        return get_metrics_summary(window=window)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

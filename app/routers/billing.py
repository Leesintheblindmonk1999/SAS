"""
app/routers/billing.py - Polar billing endpoints.

POST /billing/polar/checkout
POST /billing/polar/webhook
"""

from __future__ import annotations

import hashlib
import json
import time
from typing import Any

from fastapi import APIRouter, HTTPException, Request
from pydantic import BaseModel, EmailStr, Field

from app.services.polar import (
    PolarError,
    create_checkout_session,
    process_polar_webhook,
    verify_standard_webhook,
)

router = APIRouter()

_RATE: dict[str, list[float]] = {}


def _client_ip(request: Request) -> str:
    return (
        request.headers.get("true-client-ip")
        or request.headers.get("cf-connecting-ip")
        or request.headers.get("x-forwarded-for", "").split(",")[0].strip()
        or (request.client.host if request.client else "unknown")
    )


def _ip_hash(request: Request) -> str:
    ip = _client_ip(request)
    return hashlib.sha256(ip.encode("utf-8")).hexdigest()[:12]


def _check_rate(key: str, limit: int, window_seconds: int) -> None:
    now = time.time()
    events = _RATE.get(key, [])
    events = [t for t in events if now - t <= window_seconds]

    if len(events) >= limit:
        raise HTTPException(status_code=429, detail="Too many requests")

    events.append(now)
    _RATE[key] = events


class PolarCheckoutPayload(BaseModel):
    email: EmailStr
    name: str | None = Field(default=None, max_length=120)


def _extract_checkout_url(checkout: dict[str, Any]) -> str | None:
    """
    Polar may return different URL fields depending on API version.
    Normalize them here so the frontend always receives checkout_url.
    """
    candidates = [
        checkout.get("checkout_url"),
        checkout.get("url"),
        checkout.get("hosted_checkout_url"),
        checkout.get("payment_url"),
    ]

    for item in candidates:
        if isinstance(item, str) and item.startswith("http"):
            return item

    return None


@router.post("/billing/polar/checkout", tags=["Billing"])
async def polar_checkout(
    payload: PolarCheckoutPayload,
    request: Request,
) -> dict[str, Any]:
    hashed_ip = _ip_hash(request)

    _check_rate(
        key=f"polar-checkout:{hashed_ip}",
        limit=10,
        window_seconds=60 * 10,
    )

    try:
        checkout = create_checkout_session(
            email=str(payload.email),
            name=payload.name,
        )
    except PolarError as exc:
        raise HTTPException(status_code=500, detail=str(exc))

    if not isinstance(checkout, dict):
        raise HTTPException(
            status_code=500,
            detail="Polar checkout response was not a JSON object.",
        )

    checkout_url = _extract_checkout_url(checkout)

    if not checkout_url:
        raise HTTPException(
            status_code=500,
            detail={
                "error": "Missing checkout URL in Polar response",
                "polar_keys": sorted(list(checkout.keys())),
            },
        )

    return {
        "status": "ok",
        "provider": "polar",
        "checkout_id": checkout.get("id"),
        "checkout_url": checkout_url,
    }


@router.post("/billing/polar/webhook", tags=["Billing"])
async def polar_webhook(request: Request) -> dict[str, Any]:
    raw_body = await request.body()
    headers = dict(request.headers)

    if not verify_standard_webhook(raw_body, headers):
        raise HTTPException(status_code=403, detail="Invalid Polar webhook signature")

    try:
        event = json.loads(raw_body.decode("utf-8")) if raw_body else {}
    except json.JSONDecodeError:
        raise HTTPException(status_code=400, detail="Invalid JSON payload")

    try:
        return process_polar_webhook(event)
    except PolarError as exc:
        raise HTTPException(status_code=500, detail=str(exc))


@router.get("/billing/polar/webhook", tags=["Billing"])
async def polar_webhook_get() -> dict[str, Any]:
    return {
        "status": "ok",
        "provider": "polar",
        "message": "Webhook endpoint is alive. Use POST for notifications.",
    }

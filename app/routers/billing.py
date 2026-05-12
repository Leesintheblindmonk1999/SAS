"""
app/routers/billing.py - Polar billing endpoints.

POST /billing/polar/checkout
POST /billing/polar/webhook
"""

from __future__ import annotations

import json
from typing import Any

from fastapi import APIRouter, HTTPException, Request
from pydantic import BaseModel, EmailStr, Field

from app.db.auth_store import ensure_user
from app.middleware.rate_limit import check_rate_limit, client_ip, ip_hash
from app.services.polar import (
    PolarError,
    create_checkout_session,
    process_polar_webhook,
    verify_standard_webhook,
)

router = APIRouter()


class CheckoutPayload(BaseModel):
    email: EmailStr
    name: str | None = Field(default=None, max_length=120)


@router.post("/billing/polar/checkout", tags=["Billing"])
async def create_polar_checkout(payload: CheckoutPayload, request: Request) -> dict[str, Any]:
    hashed_ip = ip_hash(request)

    check_rate_limit(
        key=f"polar-checkout:{hashed_ip}",
        limit=10,
        window_seconds=60 * 10,
    )

    user = ensure_user(email=str(payload.email), name=payload.name)

    try:
        checkout = create_checkout_session(
            email=user["email"],
            name=user.get("name"),
            customer_ip_address=client_ip(request),
        )
    except PolarError as exc:
        raise HTTPException(status_code=500, detail=str(exc))

    checkout_url = checkout.get("url")
    if not checkout_url:
        raise HTTPException(status_code=500, detail="Polar checkout URL missing")

    return {
        "status": "ok",
        "provider": "polar",
        "checkout_url": checkout_url,
        "checkout_id": checkout.get("id"),
    }


@router.post("/billing/polar/webhook", tags=["Billing"])
async def polar_webhook(request: Request) -> dict[str, Any]:
    raw_body = await request.body()
    headers = dict(request.headers)

    if not verify_standard_webhook(raw_body=raw_body, headers=headers):
        raise HTTPException(status_code=403, detail="Invalid webhook signature")

    try:
        event = json.loads(raw_body.decode("utf-8"))
    except json.JSONDecodeError:
        raise HTTPException(status_code=400, detail="Invalid JSON payload")

    return process_polar_webhook(event)

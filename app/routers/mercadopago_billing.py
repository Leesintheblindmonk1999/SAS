"""
app/routers/mercadopago_billing.py - Mercado Pago billing endpoints.

POST /billing/mercadopago/checkout
POST /billing/mercadopago/webhook
"""

from __future__ import annotations

import json
from typing import Any, Literal

from fastapi import APIRouter, HTTPException, Request
from pydantic import BaseModel, EmailStr, Field

from app.middleware.rate_limit import check_rate_limit, ip_hash
from app.services.mercadopago import MercadoPagoError, create_preference, process_webhook

router = APIRouter()


class MercadoPagoCheckoutPayload(BaseModel):
    email: EmailStr
    name: str | None = Field(default=None, max_length=120)
    plan: Literal["pro", "pilot"] = "pro"


@router.post("/billing/mercadopago/checkout", tags=["Billing"])
async def mercadopago_checkout(
    payload: MercadoPagoCheckoutPayload,
    request: Request,
) -> dict[str, Any]:
    hashed_ip = ip_hash(request)

    check_rate_limit(
        key=f"mercadopago-checkout:{hashed_ip}",
        limit=10,
        window_seconds=60 * 10,
    )

    try:
        pref = create_preference(
            email=str(payload.email),
            name=payload.name,
            plan=payload.plan,
        )
    except MercadoPagoError as exc:
        raise HTTPException(status_code=500, detail=str(exc))

    return {
        "status": "ok",
        "provider": "mercadopago",
        "plan": pref["plan"],
        "amount_ars": pref["amount_ars"],
        "preference_id": pref["preference_id"],
        "checkout_url": pref["checkout_url"],
    }


@router.post("/billing/mercadopago/webhook", tags=["Billing"])
async def mercadopago_webhook(request: Request) -> dict[str, Any]:
    raw_body = await request.body()
    query_params = {k: v for k, v in request.query_params.items()}
    headers = dict(request.headers)

    if raw_body:
        try:
            event = json.loads(raw_body.decode("utf-8"))
        except json.JSONDecodeError:
            event = {}
    else:
        event = {}

    try:
        return process_webhook(
            event=event,
            query_params=query_params,
            headers=headers,
        )
    except MercadoPagoError as exc:
        raise HTTPException(status_code=403, detail=str(exc))


@router.get("/billing/mercadopago/webhook", tags=["Billing"])
async def mercadopago_webhook_get(request: Request) -> dict[str, Any]:
    """
    Some dashboards/tools test webhook URLs with GET.
    Real Mercado Pago notifications should use POST.
    """
    return {
        "status": "ok",
        "provider": "mercadopago",
        "message": "Webhook endpoint is alive. Use POST for notifications.",
    }

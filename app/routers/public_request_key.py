"""
app/routers/public_request_key.py - Public free API key request endpoint.

POST /public/request-key
"""

from __future__ import annotations

from typing import Any

from fastapi import APIRouter, HTTPException, Request
from pydantic import BaseModel, EmailStr, Field

from app.db.auth_store import RateLimitError, create_or_rotate_key_for_email
from app.middleware.rate_limit import check_rate_limit, ip_hash
from app.services.email import send_api_key_email

router = APIRouter()


class RequestKeyPayload(BaseModel):
    email: EmailStr
    name: str | None = Field(default=None, max_length=120)


class RequestKeyResponse(BaseModel):
    status: str
    message: str
    plan: str
    email_delivery: dict[str, Any]


@router.post(
    "/public/request-key",
    response_model=RequestKeyResponse,
    tags=["Public"],
    summary="Request a free SAS API key",
)
async def request_key(payload: RequestKeyPayload, request: Request) -> RequestKeyResponse:
    hashed_ip = ip_hash(request)

    check_rate_limit(
        key=f"request-key:{hashed_ip}",
        limit=5,
        window_seconds=60 * 10,
    )

    try:
        result = create_or_rotate_key_for_email(
            email=str(payload.email),
            name=payload.name,
            ip_hash=hashed_ip,
        )
    except RateLimitError as exc:
        raise HTTPException(status_code=429, detail=str(exc))

    user = result["user"]
    api_key = result["api_key"]

    email_result = send_api_key_email(
        email=user["email"],
        api_key=api_key,
        plan=user["plan"],
        name=user.get("name"),
    )

    if email_result.get("provider") == "log":
        message = "API key generated. Email provider is not configured; check server logs."
    else:
        message = "API key sent by email."

    return RequestKeyResponse(
        status="ok",
        message=message,
        plan=user["plan"],
        email_delivery={
            "sent": bool(email_result.get("sent")),
            "provider": email_result.get("provider"),
        },
    )

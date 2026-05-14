"""
app/routers/public_request_key.py - Public free API key request endpoint.

GET  /public/request-key  -> onboarding/help
POST /public/request-key  -> request a Free SAS API key
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


class RequestKeyHelpResponse(BaseModel):
    status: str
    message: str
    recommended: dict[str, Any]
    free_plan: dict[str, Any]
    next_steps: list[str]
    docs: dict[str, str]


@router.get(
    "/public/request-key",
    response_model=RequestKeyHelpResponse,
    tags=["Public"],
    summary="How to request a Free SAS API key",
    include_in_schema=False,
)
async def request_key_help() -> RequestKeyHelpResponse:
    """
    Human-friendly help for users/browsers that open /public/request-key with GET.

    The real key issuance endpoint is POST /public/request-key.
    This converts accidental 405s into onboarding instructions.
    """
    return RequestKeyHelpResponse(
        status="info",
        message="Use POST /public/request-key to request a Free SAS API key.",
        recommended={
            "cli": {
                "install": "pip install sas-client",
                "command": 'sas request-key --email you@example.com --name "Your Name"',
            },
            "curl": (
                "curl -X POST https://sas-api.onrender.com/public/request-key "
                "-H 'Content-Type: application/json' "
                "-d '{\"email\":\"you@example.com\",\"name\":\"Your Name\"}'"
            ),
            "powershell": (
                'Invoke-RestMethod -Method Post '
                '-Uri "https://sas-api.onrender.com/public/request-key" '
                '-ContentType "application/json" '
                '-Body \'{"email":"you@example.com","name":"Your Name"}\''
            ),
        },
        free_plan={
            "plan": "free",
            "limit": "50 requests/day",
            "delivery": "API key is sent by email automatically.",
            "rate_limit": "Limited by IP and email to reduce abuse.",
        },
        next_steps=[
            "Install the CLI: pip install sas-client",
            'Request a key: sas request-key --email you@example.com --name "Your Name"',
            "Set SAS_API_KEY or SAS_KEY with the key received by email.",
            "Run: sas whoami",
            'Run: sas diff "source" "response"',
        ],
        docs={
            "api": "https://sas-api.onrender.com/docs",
            "landing": "https://leesintheblindmonk1999.github.io/sas-landing/#access",
            "pypi": "https://pypi.org/project/sas-client/",
            "github": "https://github.com/Leesintheblindmonk1999/SAS",
        },
    )


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
        raise HTTPException(
            status_code=429,
            detail={
                "error": "Rate limit exceeded",
                "message": str(exc),
                "help": {
                    "cli": 'sas request-key --email you@example.com --name "Your Name"',
                    "docs": "https://sas-api.onrender.com/docs",
                },
            },
        )

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

"""
app/middleware/validation_logger.py

Safe validation-error observability for SAS.

Purpose:
- Capture 422 validation failures without storing raw request bodies or emails.
- Record request-key conversion failures for funnel analysis.
- Preserve FastAPI's normal validation response flow when used from the
  RequestValidationError handler.

No raw PII is stored.
"""

from __future__ import annotations

import json
import logging
import re
from typing import Any

from fastapi import Request
from fastapi.exceptions import RequestValidationError

from app.db.auth_store import register_failed_attempt
from app.services.audit_store import hash_ip_daily, save_validation_error

logger = logging.getLogger("sas.validation_logger")

_EMAIL_RE = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")


def _client_ip(request: Request) -> str:
    return (
        request.headers.get("true-client-ip")
        or request.headers.get("cf-connecting-ip")
        or request.headers.get("x-real-ip")
        or request.headers.get("x-forwarded-for", "").split(",")[0].strip()
        or (request.client.host if request.client else "unknown")
    )


def _country(request: Request) -> str:
    return (
        request.headers.get("cf-ipcountry")
        or request.headers.get("x-vercel-ip-country")
        or request.headers.get("x-country")
        or "unknown"
    )


def _validation_error_types(exc: RequestValidationError) -> list[str]:
    types: list[str] = []
    for err in exc.errors():
        err_type = str(err.get("type", "unknown"))
        if err_type not in types:
            types.append(err_type)
    return types


def _reason_from_analysis(
    *,
    json_valid: bool,
    email_present: bool,
    email_valid: bool,
    name_present: bool,
    content_type: str,
) -> str:
    """
    Funnel-friendly reason bucket.

    `name` is optional in the current public request-key API, so missing_name is
    not treated as fatal by default.
    """
    if not json_valid:
        return "invalid_json"

    if "application/json" not in (content_type or "").lower():
        return "wrong_content_type"

    if not email_present:
        return "missing_email"

    if not email_valid:
        return "invalid_email"

    return "validation_error"


async def analyze_request_body_safely(request: Request) -> dict[str, Any]:
    """
    Inspect body shape without storing raw body or raw email.

    Returns only booleans and metadata:
    - json_valid
    - email_present
    - email_valid
    - name_present
    """
    content_type = request.headers.get("content-type", "")
    content_length_raw = request.headers.get("content-length")
    try:
        content_length = int(content_length_raw) if content_length_raw else None
    except ValueError:
        content_length = None

    json_valid = False
    email_present = False
    email_valid = False
    name_present = False

    try:
        raw = await request.body()
    except Exception:
        raw = b""

    if raw:
        try:
            parsed = json.loads(raw.decode("utf-8"))
            if isinstance(parsed, dict):
                json_valid = True

                email_value = parsed.get("email")
                name_value = parsed.get("name")

                email_present = email_value is not None and str(email_value).strip() != ""
                name_present = name_value is not None and str(name_value).strip() != ""

                if email_present:
                    email_valid = bool(_EMAIL_RE.match(str(email_value).strip()))
        except Exception:
            json_valid = False
    else:
        json_valid = False

    return {
        "content_type": content_type,
        "content_length": content_length,
        "json_valid": json_valid,
        "email_present": email_present,
        "email_valid": email_valid,
        "name_present": name_present,
    }


async def log_validation_error(request: Request, exc: RequestValidationError) -> None:
    """
    Call this from main.py's RequestValidationError handler.

    It records safe metadata into audit.db validation_errors.
    For POST /public/request-key it also records a failed conversion attempt
    without storing raw email or body.
    """
    path = request.url.path
    method = request.method.upper()
    request_id = getattr(request.state, "request_id", "unknown")

    try:
        analysis = await analyze_request_body_safely(request)

        error_types = _validation_error_types(exc)
        client_ip = _client_ip(request)
        ip_h = hash_ip_daily(client_ip)
        country = _country(request)

        data = {
            "request_id": request_id,
            "path": path,
            "method": method,
            "status": 422,
            "content_type": analysis["content_type"],
            "content_length": analysis["content_length"],
            "json_valid": analysis["json_valid"],
            "email_present": analysis["email_present"],
            "email_valid": analysis["email_valid"],
            "name_present": analysis["name_present"],
            "validation_error_types": json.dumps(error_types),
            "ip_hash": ip_h,
            "country": country.upper(),
        }

        await save_validation_error(data)

        if path == "/public/request-key" and method == "POST":
            reason = _reason_from_analysis(
                json_valid=bool(analysis["json_valid"]),
                email_present=bool(analysis["email_present"]),
                email_valid=bool(analysis["email_valid"]),
                name_present=bool(analysis["name_present"]),
                content_type=str(analysis["content_type"] or ""),
            )

            register_failed_attempt(
                ip_hash=ip_h,
                reason=reason,
                email_present=bool(analysis["email_present"]),
                name_present=bool(analysis["name_present"]),
            )

    except Exception as err:
        logger.warning(
            "validation_error_logging_failed request_id=%s path=%s error=%s",
            request_id,
            path,
            err,
        )

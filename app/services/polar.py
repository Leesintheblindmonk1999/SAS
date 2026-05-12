"""
app/services/polar.py - Polar checkout + webhook helpers.

Uses stdlib urllib.
No Polar SDK dependency required.

Fix:
- Adds explicit User-Agent to avoid Cloudflare / browser-signature 403 code 1010.
"""

from __future__ import annotations

import base64
import hashlib
import hmac
import json
import logging
import os
import time
import urllib.error
import urllib.request
from typing import Any

from app.db.auth_store import (
    hash_email,
    record_payment_event,
    upsert_paid_user,
)
from app.services.email import send_pro_welcome_email

logger = logging.getLogger("sas.polar")


class PolarError(Exception):
    pass


def polar_base_url() -> str:
    sandbox = os.getenv("POLAR_SANDBOX", "false").lower() == "true"
    return "https://sandbox-api.polar.sh/v1" if sandbox else "https://api.polar.sh/v1"


def _polar_headers(token: str) -> dict[str, str]:
    return {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json",
        "Accept": "application/json",
        "User-Agent": "sas-api/1.0 (+https://github.com/Leesintheblindmonk1999/SAS)",
    }


def create_checkout_session(email: str, name: str | None = None) -> dict[str, Any]:
    token = (os.getenv("POLAR_ACCESS_TOKEN") or "").strip()
    product_id = (os.getenv("POLAR_PRODUCT_ID_PRO") or "").strip()

    if not token:
        raise PolarError("Missing POLAR_ACCESS_TOKEN")

    if not product_id:
        raise PolarError("Missing POLAR_PRODUCT_ID_PRO")

    success_url = os.getenv(
        "POLAR_SUCCESS_URL",
        "https://leesintheblindmonk1999.github.io/sas-landing/?checkout=success",
    ).strip()

    return_url = os.getenv(
        "POLAR_RETURN_URL",
        "https://leesintheblindmonk1999.github.io/sas-landing/?checkout=cancel",
    ).strip()

    email = email.strip().lower()
    customer_name = name.strip() if name else None

    payload = {
        "products": [product_id],
        "customer_email": email,
        "customer_name": customer_name,
        "external_customer_id": hash_email(email),
        "success_url": success_url,
        "return_url": return_url,
        "metadata": {
            "email": email,
            "plan": "pro",
            "source": "sas_landing",
        },
        "customer_metadata": {
            "email_hash": hash_email(email),
            "plan": "pro",
        },
    }

    url = f"{polar_base_url()}/checkouts/"

    req = urllib.request.Request(
        url,
        data=json.dumps(payload).encode("utf-8"),
        headers=_polar_headers(token),
        method="POST",
    )

    try:
        with urllib.request.urlopen(req, timeout=20) as resp:
            body = resp.read().decode("utf-8")
            data = json.loads(body)

            if not isinstance(data, dict):
                raise PolarError("Polar checkout response is not a JSON object")

            return data

    except urllib.error.HTTPError as exc:
        body = exc.read().decode("utf-8", errors="replace")
        logger.error(
            "polar_checkout_failed status=%s url=%s body=%s",
            exc.code,
            url,
            body,
        )
        raise PolarError(f"Polar checkout failed: {exc.code} {body}") from exc

    except Exception as exc:
        logger.exception("polar_checkout_failed error=%s", exc)
        raise PolarError(str(exc)) from exc


def _possible_signature_keys(secret: str) -> list[bytes]:
    """
    Polar follows Standard Webhooks.

    Supports:
    - raw secret bytes
    - whsec_ base64-decoded secret
    - fallback base64 decode for dashboard-provided secrets
    """
    keys: list[bytes] = []

    if not secret:
        return keys

    secret = secret.strip()

    if secret.startswith("whsec_"):
        raw = secret.replace("whsec_", "", 1)
        try:
            keys.append(base64.b64decode(raw))
        except Exception:
            keys.append(raw.encode("utf-8"))
    else:
        keys.append(secret.encode("utf-8"))

        try:
            keys.append(base64.b64decode(secret))
        except Exception:
            pass

    unique: list[bytes] = []
    seen: set[bytes] = set()

    for key in keys:
        if key not in seen:
            seen.add(key)
            unique.append(key)

    return unique


def verify_standard_webhook(raw_body: bytes, headers: dict[str, str]) -> bool:
    """
    Verify Standard Webhooks / Svix-style signature.

    If POLAR_WEBHOOK_SECRET is missing, verification is bypassed only to avoid
    breaking local development. Production must configure POLAR_WEBHOOK_SECRET.
    """
    secret = os.getenv("POLAR_WEBHOOK_SECRET", "").strip()

    if not secret:
        logger.warning("POLAR_WEBHOOK_SECRET missing; webhook signature not verified")
        return True

    lower = {k.lower(): v for k, v in headers.items()}

    webhook_id = lower.get("webhook-id") or lower.get("svix-id")
    webhook_timestamp = lower.get("webhook-timestamp") or lower.get("svix-timestamp")
    webhook_signature = lower.get("webhook-signature") or lower.get("svix-signature")

    if not webhook_id or not webhook_timestamp or not webhook_signature:
        logger.warning("polar_webhook_missing_signature_headers")
        return False

    try:
        timestamp = int(webhook_timestamp)
    except ValueError:
        logger.warning("polar_webhook_invalid_timestamp")
        return False

    # 5-minute replay protection.
    if abs(int(time.time()) - timestamp) > 300:
        logger.warning("polar_webhook_timestamp_outside_window")
        return False

    signed = (
        webhook_id.encode("utf-8")
        + b"."
        + webhook_timestamp.encode("utf-8")
        + b"."
        + raw_body
    )

    signatures: list[str] = []

    for chunk in webhook_signature.split(" "):
        chunk = chunk.strip()
        if not chunk:
            continue

        if "," in chunk:
            version, sig = chunk.split(",", 1)
            if version.strip() == "v1":
                signatures.append(sig.strip())
        else:
            signatures.append(chunk)

    for key in _possible_signature_keys(secret):
        expected = base64.b64encode(
            hmac.new(key, signed, hashlib.sha256).digest()
        ).decode("utf-8")

        for received in signatures:
            if hmac.compare_digest(expected, received):
                return True

    logger.warning("polar_webhook_signature_verification_failed")
    return False


def _nested_get(obj: dict[str, Any], *path: str) -> Any:
    cur: Any = obj

    for key in path:
        if not isinstance(cur, dict):
            return None
        cur = cur.get(key)

    return cur


def extract_email_from_event(event: dict[str, Any]) -> str | None:
    data = event.get("data", {})
    metadata = data.get("metadata", {}) if isinstance(data.get("metadata"), dict) else {}
    customer_metadata = (
        data.get("customer_metadata", {})
        if isinstance(data.get("customer_metadata"), dict)
        else {}
    )

    candidates = [
        _nested_get(data, "customer", "email"),
        data.get("customer_email"),
        data.get("email"),
        metadata.get("email"),
        customer_metadata.get("email"),
        _nested_get(data, "checkout", "customer_email"),
        _nested_get(data, "order", "customer_email"),
        _nested_get(data, "subscription", "customer", "email"),
    ]

    for item in candidates:
        if isinstance(item, str) and "@" in item:
            return item.strip().lower()

    return None


def extract_external_id(event: dict[str, Any]) -> str:
    data = event.get("data", {})

    if isinstance(data, dict) and data.get("id"):
        return str(data.get("id"))

    if event.get("id"):
        return str(event.get("id"))

    return str(event.get("timestamp") or time.time())


def extract_customer_id(event: dict[str, Any]) -> str | None:
    data = event.get("data", {})

    if not isinstance(data, dict):
        return None

    return (
        _nested_get(data, "customer", "id")
        or data.get("customer_id")
        or _nested_get(data, "subscription", "customer_id")
        or None
    )


def extract_subscription_id(event: dict[str, Any]) -> str | None:
    event_type = str(event.get("type", ""))
    data = event.get("data", {})

    if not isinstance(data, dict):
        return None

    if data.get("subscription_id"):
        return str(data.get("subscription_id"))

    if event_type.startswith("subscription.") and data.get("id"):
        return str(data.get("id"))

    if _nested_get(data, "subscription", "id"):
        return str(_nested_get(data, "subscription", "id"))

    return None


def process_polar_webhook(event: dict[str, Any]) -> dict[str, Any]:
    event_type = str(event.get("type", "unknown"))
    external_id = extract_external_id(event)
    email = extract_email_from_event(event)

    paid_events = {
        "order.paid",
        "subscription.active",
        "subscription.created",
    }

    inactive_events = {
        "subscription.revoked",
        "subscription.canceled",
        "subscription.past_due",
    }

    if event_type in paid_events:
        if not email:
            record_payment_event(
                provider="polar",
                event_type=event_type,
                external_id=external_id,
                email=None,
                plan="pro",
                status="ignored_missing_email",
                raw_payload=event,
            )
            return {
                "status": "ignored",
                "reason": "missing_email",
                "event_type": event_type,
            }

        user_result = upsert_paid_user(
            email=email,
            plan="pro",
            polar_customer_id=extract_customer_id(event),
            polar_subscription_id=extract_subscription_id(event),
        )

        user = user_result["user"]
        api_key = user_result["api_key"]

        inserted = record_payment_event(
            provider="polar",
            event_type=event_type,
            external_id=external_id,
            email=email,
            plan="pro",
            status="processed",
            raw_payload=event,
            user_id=user["id"],
        )

        if inserted:
            send_pro_welcome_email(
                email=email,
                api_key=api_key,
                name=user.get("name"),
            )

        return {
            "status": "ok",
            "event_type": event_type,
            "email": email,
            "plan": "pro",
            "idempotent_insert": inserted,
            "new_key_created": bool(api_key),
        }

    if event_type in inactive_events:
        inserted = record_payment_event(
            provider="polar",
            event_type=event_type,
            external_id=external_id,
            email=email,
            plan="pro",
            status="received_inactive_event",
            raw_payload=event,
        )

        return {
            "status": "ok",
            "event_type": event_type,
            "action": "recorded_only",
            "idempotent_insert": inserted,
        }

    inserted = record_payment_event(
        provider="polar",
        event_type=event_type,
        external_id=external_id,
        email=email,
        plan=None,
        status="ignored_event_type",
        raw_payload=event,
    )

    return {
        "status": "ignored",
        "event_type": event_type,
        "idempotent_insert": inserted,
    }

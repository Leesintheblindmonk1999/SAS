"""
app/services/polar.py - Polar checkout + webhook helpers.

Uses stdlib urllib and HMAC verification.
No Polar SDK dependency required.
"""

from __future__ import annotations

import base64
import hashlib
import hmac
import json
import logging
import time
import urllib.error
import urllib.request
from typing import Any

from app.config import settings
from app.db.auth_store import (
    connect,
    get_user_by_email,
    hash_email,
    plan_limits,
    record_payment_event,
    upsert_paid_user,
    utc_now,
)
from app.services.email import send_pro_welcome_email

logger = logging.getLogger("sas.polar")


class PolarError(Exception):
    pass


def polar_base_url() -> str:
    return "https://sandbox-api.polar.sh/v1" if getattr(settings, "polar_sandbox", False) else "https://api.polar.sh/v1"


def create_checkout_session(email: str, name: str | None = None, customer_ip_address: str | None = None) -> dict[str, Any]:
    token = getattr(settings, "polar_access_token", "")
    product_id = getattr(settings, "polar_product_id_pro", "")

    if not token:
        raise PolarError("Missing POLAR_ACCESS_TOKEN")
    if not product_id:
        raise PolarError("Missing POLAR_PRODUCT_ID_PRO")

    payload: dict[str, Any] = {
        "products": [product_id],
        "customer_email": email,
        "customer_name": name,
        "external_customer_id": hash_email(email),
        "success_url": getattr(settings, "polar_success_url", "https://leesintheblindmonk1999.github.io/sas-landing/?checkout=success"),
        "return_url": getattr(settings, "polar_return_url", "https://leesintheblindmonk1999.github.io/sas-landing/?checkout=cancel"),
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

    if customer_ip_address and customer_ip_address != "unknown":
        payload["customer_ip_address"] = customer_ip_address

    req = urllib.request.Request(
        f"{polar_base_url()}/checkouts",
        data=json.dumps(payload).encode("utf-8"),
        headers={
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json",
        },
        method="POST",
    )

    try:
        with urllib.request.urlopen(req, timeout=20) as resp:
            body = resp.read().decode("utf-8")
            return json.loads(body)
    except urllib.error.HTTPError as exc:
        body = exc.read().decode("utf-8", errors="replace")
        logger.error("polar_checkout_failed status=%s body=%s", exc.code, body)
        raise PolarError(f"Polar checkout failed: {exc.code} {body}") from exc
    except Exception as exc:
        logger.exception("polar_checkout_failed error=%s", exc)
        raise PolarError(str(exc)) from exc


def _possible_signature_keys(secret: str) -> list[bytes]:
    keys: list[bytes] = []

    if not secret:
        return keys

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
    seen = set()
    for key in keys:
        if key not in seen:
            seen.add(key)
            unique.append(key)
    return unique


def verify_standard_webhook(raw_body: bytes, headers: dict[str, str]) -> bool:
    secret = getattr(settings, "polar_webhook_secret", "")
    if not secret:
        logger.warning("POLAR_WEBHOOK_SECRET missing; webhook signature not verified")
        return True

    lower = {k.lower(): v for k, v in headers.items()}
    webhook_id = lower.get("webhook-id") or lower.get("svix-id")
    webhook_timestamp = lower.get("webhook-timestamp") or lower.get("svix-timestamp")
    webhook_signature = lower.get("webhook-signature") or lower.get("svix-signature")

    if not webhook_id or not webhook_timestamp or not webhook_signature:
        return False

    try:
        timestamp = int(webhook_timestamp)
    except ValueError:
        return False

    if abs(int(time.time()) - timestamp) > 300:
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
        expected = base64.b64encode(hmac.HMAC(key, signed, hashlib.sha256).digest()).decode("utf-8")
        for received in signatures:
            if hmac.compare_digest(expected, received):
                return True

    return False


def _nested_get(obj: dict[str, Any], *path: str) -> Any:
    cur: Any = obj
    for key in path:
        if not isinstance(cur, dict):
            return None
        cur = cur.get(key)
    return cur


def extract_email_from_event(event: dict[str, Any]) -> str | None:
    data = event.get("data", {}) if isinstance(event.get("data"), dict) else {}
    metadata = data.get("metadata", {}) if isinstance(data.get("metadata"), dict) else {}
    customer = data.get("customer", {}) if isinstance(data.get("customer"), dict) else {}

    candidates = [
        customer.get("email"),
        data.get("customer_email"),
        data.get("email"),
        metadata.get("email"),
        _nested_get(data, "checkout", "customer_email"),
        _nested_get(data, "order", "customer_email"),
    ]

    for item in candidates:
        if isinstance(item, str) and "@" in item:
            return item.strip().lower()

    return None


def extract_external_id(event: dict[str, Any]) -> str:
    data = event.get("data", {}) if isinstance(event.get("data"), dict) else {}
    return str(data.get("id") or event.get("id") or event.get("timestamp") or time.time())


def extract_customer_id(event: dict[str, Any]) -> str | None:
    data = event.get("data", {}) if isinstance(event.get("data"), dict) else {}
    customer = data.get("customer", {}) if isinstance(data.get("customer"), dict) else {}
    return customer.get("id") or data.get("customer_id") or None


def extract_subscription_id(event: dict[str, Any]) -> str | None:
    data = event.get("data", {}) if isinstance(event.get("data"), dict) else {}
    event_type = str(event.get("type", ""))
    if event_type.startswith("subscription."):
        return data.get("id") or data.get("subscription_id")
    return data.get("subscription_id") or None


def process_polar_webhook(event: dict[str, Any]) -> dict[str, Any]:
    event_type = str(event.get("type", "unknown"))
    external_id = extract_external_id(event)
    email = extract_email_from_event(event)

    paid_events = {"order.paid", "subscription.active", "subscription.created"}
    inactive_events = {"subscription.revoked", "subscription.canceled", "subscription.past_due"}

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
            return {"status": "ignored", "reason": "missing_email"}

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
            send_pro_welcome_email(email=email, api_key=api_key, name=user.get("name"))

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

        # Downgrade user to free when subscription is cancelled/revoked.
        # Without this, a cancelled Pro user keeps Pro access indefinitely.
        if email:
            try:
                existing = get_user_by_email(email)
                if existing and existing.get("plan") == "pro":
                    limits = plan_limits("free")
                    with connect() as conn:
                        conn.execute(
                            """
                            UPDATE users
                            SET plan = "free",
                                daily_limit = ?,
                                monthly_limit = ?,
                                updated_at = ?
                            WHERE id = ?
                            """,
                            (limits["daily_limit"], limits["monthly_limit"], utc_now(), existing["id"]),
                        )
                    logger.info("polar_subscription_downgraded event=%s", event_type)
            except Exception as exc:
                logger.error("polar_downgrade_failed event=%s error=%s", event_type, exc)

        return {
            "status": "ok",
            "event_type": event_type,
            "action": "recorded_and_downgraded" if email else "recorded_only",
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

    return {"status": "ignored", "event_type": event_type, "idempotent_insert": inserted}

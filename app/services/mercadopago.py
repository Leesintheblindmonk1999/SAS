"""
app/services/mercadopago.py - Mercado Pago Checkout Pro + webhook helpers.

MVP:
- Creates Checkout Pro preferences.
- Processes payment webhooks.
- Upgrades approved buyers to SAS Pro.
- No Mercado Pago SDK dependency.
"""

from __future__ import annotations

import hashlib
import hmac
import json
import logging
import os
import urllib.error
import urllib.parse
import urllib.request
from typing import Any

from app.db.auth_store import record_payment_event, upsert_paid_user
from app.services.email import send_pro_welcome_email

logger = logging.getLogger("sas.mercadopago")


class MercadoPagoError(Exception):
    pass


def _access_token() -> str:
    return (os.getenv("MERCADOPAGO_ACCESS_TOKEN") or "").strip()


def _public_url() -> str:
    return os.getenv(
        "SAS_PUBLIC_URL",
        "https://leesintheblindmonk1999.github.io/sas-landing/",
    ).strip()


def _success_url() -> str:
    return os.getenv(
        "MERCADOPAGO_SUCCESS_URL",
        f"{_public_url()}?mp=success",
    ).strip()


def _failure_url() -> str:
    return os.getenv(
        "MERCADOPAGO_FAILURE_URL",
        f"{_public_url()}?mp=failure",
    ).strip()


def _pending_url() -> str:
    return os.getenv(
        "MERCADOPAGO_PENDING_URL",
        f"{_public_url()}?mp=pending",
    ).strip()


def _notification_url() -> str:
    return os.getenv(
        "MERCADOPAGO_NOTIFICATION_URL",
        "https://sas-api.onrender.com/billing/mercadopago/webhook",
    ).strip()


def _headers() -> dict[str, str]:
    token = _access_token()

    if not token:
        raise MercadoPagoError("Missing MERCADOPAGO_ACCESS_TOKEN")

    return {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json",
        "Accept": "application/json",
        "User-Agent": "sas-api/1.0 (+https://github.com/Leesintheblindmonk1999/SAS)",
    }


def _post_json(url: str, payload: dict[str, Any]) -> dict[str, Any]:
    req = urllib.request.Request(
        url,
        data=json.dumps(payload, ensure_ascii=False).encode("utf-8"),
        headers=_headers(),
        method="POST",
    )

    try:
        with urllib.request.urlopen(req, timeout=25) as resp:
            body = resp.read().decode("utf-8")
            data = json.loads(body)
            return data if isinstance(data, dict) else {}
    except urllib.error.HTTPError as exc:
        body = exc.read().decode("utf-8", errors="replace")
        logger.error("mercadopago_post_failed status=%s body=%s", exc.code, body)
        raise MercadoPagoError(f"Mercado Pago request failed: {exc.code} {body}") from exc
    except Exception as exc:
        logger.exception("mercadopago_post_failed error=%s", exc)
        raise MercadoPagoError(str(exc)) from exc


def _get_json(url: str) -> dict[str, Any]:
    req = urllib.request.Request(
        url,
        headers=_headers(),
        method="GET",
    )

    try:
        with urllib.request.urlopen(req, timeout=25) as resp:
            body = resp.read().decode("utf-8")
            data = json.loads(body)
            return data if isinstance(data, dict) else {}
    except urllib.error.HTTPError as exc:
        body = exc.read().decode("utf-8", errors="replace")
        logger.error("mercadopago_get_failed status=%s body=%s", exc.code, body)
        raise MercadoPagoError(f"Mercado Pago request failed: {exc.code} {body}") from exc
    except Exception as exc:
        logger.exception("mercadopago_get_failed error=%s", exc)
        raise MercadoPagoError(str(exc)) from exc


def _price_for_plan(plan: str) -> float:
    plan = (plan or "pro").strip().lower()

    if plan == "pilot":
        return float(os.getenv("MERCADOPAGO_PILOT_PRICE_ARS", "1500000"))

    return float(os.getenv("MERCADOPAGO_PRO_PRICE_ARS", "9999"))


def _title_for_plan(plan: str) -> str:
    plan = (plan or "pro").strip().lower()

    if plan == "pilot":
        return "SAS Technical Pilot"

    return "SAS Pro LatAm"


def _description_for_plan(plan: str) -> str:
    plan = (plan or "pro").strip().lower()

    if plan == "pilot":
        return "Technical onboarding, initial audit, integration support and SAS API access."

    return "SAS Pro API access for structural coherence auditing."


def _target_sas_plan(plan: str) -> str:
    """
    For now Mercado Pago activates SAS Pro.
    Pilot can later become team/enterprise/manual if needed.
    """
    return "pro"


def create_preference(email: str, name: str | None = None, plan: str = "pro") -> dict[str, Any]:
    email = email.strip().lower()
    plan = (plan or "pro").strip().lower()

    if plan not in {"pro", "pilot"}:
        plan = "pro"

    title = _title_for_plan(plan)
    description = _description_for_plan(plan)
    unit_price = _price_for_plan(plan)

    reference = {
        "provider": "mercadopago",
        "email": email,
        "name": name or "",
        "plan": plan,
        "target_sas_plan": _target_sas_plan(plan),
    }

    payload = {
        "items": [
            {
                "id": f"sas_{plan}",
                "title": title,
                "description": description,
                "quantity": 1,
                "currency_id": "ARS",
                "unit_price": unit_price,
            }
        ],
        "payer": {
            "email": email,
            "name": name or "",
        },
        "back_urls": {
            "success": _success_url(),
            "failure": _failure_url(),
            "pending": _pending_url(),
        },
        "notification_url": _notification_url(),
        "external_reference": json.dumps(reference, ensure_ascii=False, sort_keys=True),
        "metadata": {
            "email": email,
            "name": name or "",
            "plan": plan,
            "target_sas_plan": _target_sas_plan(plan),
            "product": f"sas_{plan}",
        },
        "auto_return": "approved",
        "binary_mode": False,
    }

    data = _post_json(
        "https://api.mercadopago.com/checkout/preferences",
        payload,
    )

    checkout_url = (
        data.get("init_point")
        or data.get("sandbox_init_point")
        or data.get("url")
    )

    if not checkout_url:
        raise MercadoPagoError(f"Missing checkout URL in Mercado Pago response: {data}")

    return {
        "raw": data,
        "checkout_url": checkout_url,
        "preference_id": data.get("id"),
        "plan": plan,
        "amount_ars": unit_price,
    }


def get_payment(payment_id: str) -> dict[str, Any]:
    payment_id = str(payment_id).strip()

    if not payment_id:
        raise MercadoPagoError("Missing payment id")

    return _get_json(f"https://api.mercadopago.com/v1/payments/{urllib.parse.quote(payment_id)}")


def _parse_signature_header(value: str | None) -> dict[str, str]:
    result: dict[str, str] = {}

    if not value:
        return result

    for part in value.split(","):
        if "=" not in part:
            continue
        key, val = part.split("=", 1)
        result[key.strip()] = val.strip()

    return result


def verify_webhook_signature(
    headers: dict[str, str],
    query_params: dict[str, str],
    event: dict[str, Any],
) -> bool:
    """
    Mercado Pago signs webhook notifications using x-signature.

    MVP behavior:
    - If MERCADOPAGO_ENFORCE_WEBHOOK_SIGNATURE=true, invalid signature rejects.
    - Otherwise invalid/missing signature is logged but does not block testing.
    """
    secret = (os.getenv("MERCADOPAGO_WEBHOOK_SECRET") or "").strip()

    if not secret:
        logger.warning("mercadopago_webhook_secret_missing")
        return False

    lower = {k.lower(): v for k, v in headers.items()}

    x_signature = lower.get("x-signature")
    x_request_id = lower.get("x-request-id")

    parts = _parse_signature_header(x_signature)
    ts = parts.get("ts")
    received_v1 = parts.get("v1")

    data_id = (
        query_params.get("data.id")
        or query_params.get("id")
        or str((event.get("data") or {}).get("id") or "")
    ).strip()

    if not x_request_id or not ts or not received_v1 or not data_id:
        logger.warning(
            "mercadopago_webhook_signature_incomplete data_id=%s has_request_id=%s has_ts=%s has_v1=%s",
            data_id,
            bool(x_request_id),
            bool(ts),
            bool(received_v1),
        )
        return False

    manifest = f"id:{data_id};request-id:{x_request_id};ts:{ts};"
    expected = hmac.new(
        secret.encode("utf-8"),
        manifest.encode("utf-8"),
        hashlib.sha256,
    ).hexdigest()

    return hmac.compare_digest(expected, received_v1)


def _extract_payment_id(event: dict[str, Any], query_params: dict[str, str]) -> str | None:
    candidates = [
        query_params.get("data.id"),
        query_params.get("id"),
        str((event.get("data") or {}).get("id") or ""),
        str(event.get("id") or ""),
    ]

    for item in candidates:
        if item and item.strip():
            return item.strip()

    return None


def _parse_external_reference(value: Any) -> dict[str, Any]:
    if not isinstance(value, str) or not value.strip():
        return {}

    try:
        parsed = json.loads(value)
        return parsed if isinstance(parsed, dict) else {}
    except Exception:
        return {}


def _extract_email_from_payment(payment: dict[str, Any]) -> str | None:
    metadata = payment.get("metadata") if isinstance(payment.get("metadata"), dict) else {}
    payer = payment.get("payer") if isinstance(payment.get("payer"), dict) else {}
    ext = _parse_external_reference(payment.get("external_reference"))

    candidates = [
        metadata.get("email"),
        ext.get("email"),
        payer.get("email"),
    ]

    for item in candidates:
        if isinstance(item, str) and "@" in item:
            return item.strip().lower()

    return None


def _extract_plan_from_payment(payment: dict[str, Any]) -> str:
    metadata = payment.get("metadata") if isinstance(payment.get("metadata"), dict) else {}
    ext = _parse_external_reference(payment.get("external_reference"))

    plan = (
        metadata.get("target_sas_plan")
        or ext.get("target_sas_plan")
        or "pro"
    )

    return str(plan).strip().lower() or "pro"


def process_webhook(
    event: dict[str, Any],
    query_params: dict[str, str],
    headers: dict[str, str],
) -> dict[str, Any]:
    signature_ok = verify_webhook_signature(headers, query_params, event)
    enforce = os.getenv("MERCADOPAGO_ENFORCE_WEBHOOK_SIGNATURE", "false").lower() == "true"

    if enforce and not signature_ok:
        raise MercadoPagoError("Invalid Mercado Pago webhook signature")

    payment_id = _extract_payment_id(event, query_params)

    if not payment_id:
        return {
            "status": "ignored",
            "reason": "missing_payment_id",
            "signature_ok": signature_ok,
        }

    try:
        payment = get_payment(payment_id)
    except MercadoPagoError as exc:
        logger.warning("mercadopago_payment_fetch_failed payment_id=%s error=%s", payment_id, exc)
        return {
            "status": "ignored",
            "reason": "payment_fetch_failed",
            "payment_id": payment_id,
            "signature_ok": signature_ok,
        }

    mp_status = str(payment.get("status") or "").lower()
    event_type = f"payment.{mp_status or 'unknown'}"
    email = _extract_email_from_payment(payment)
    target_plan = _extract_plan_from_payment(payment)

    inserted = record_payment_event(
        provider="mercadopago",
        event_type=event_type,
        external_id=str(payment.get("id") or payment_id),
        email=email,
        plan=target_plan,
        status="received",
        raw_payload={
            "webhook": event,
            "query_params": query_params,
            "payment": payment,
            "signature_ok": signature_ok,
        },
        user_id=None,
    )

    if not inserted:
        return {
            "status": "ok",
            "provider": "mercadopago",
            "idempotent": True,
            "payment_id": payment_id,
            "payment_status": mp_status,
            "signature_ok": signature_ok,
        }

    if mp_status != "approved":
        return {
            "status": "ok",
            "provider": "mercadopago",
            "action": "recorded_only",
            "payment_id": payment_id,
            "payment_status": mp_status,
            "signature_ok": signature_ok,
        }

    if not email:
        return {
            "status": "ignored",
            "provider": "mercadopago",
            "reason": "approved_payment_missing_email",
            "payment_id": payment_id,
            "payment_status": mp_status,
            "signature_ok": signature_ok,
        }

    user_result = upsert_paid_user(
        email=email,
        plan=target_plan,
        name=None,
        polar_customer_id=None,
        polar_subscription_id=None,
    )

    user = user_result["user"]
    api_key = user_result["api_key"]

    send_pro_welcome_email(
        email=email,
        api_key=api_key,
        name=user.get("name"),
    )

    return {
        "status": "ok",
        "provider": "mercadopago",
        "payment_id": payment_id,
        "payment_status": mp_status,
        "email": email,
        "plan": target_plan,
        "new_key_created": bool(api_key),
        "signature_ok": signature_ok,
    }

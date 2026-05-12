"""
app/services/email.py - SAS email delivery.

Supported modes:
1. Resend REST API if RESEND_API_KEY is configured.
2. SMTP fallback if SMTP_HOST / SMTP_USERNAME / SMTP_PASSWORD are configured.
3. Log-only placeholder if no email provider is configured.

No extra email SDK is required.
"""

from __future__ import annotations

import json
import logging
import smtplib
import ssl
import urllib.request
from email.message import EmailMessage
from typing import Any

from app.config import settings

logger = logging.getLogger("sas.email")


def _from_email() -> str:
    return getattr(settings, "email_from", "") or getattr(settings, "smtp_from", "") or "SAS <onboarding@sas.local>"


def _api_url() -> str:
    return getattr(settings, "sas_api_url", "https://sas-api.onrender.com")


def _public_url() -> str:
    return getattr(settings, "sas_public_url", "https://leesintheblindmonk1999.github.io/sas-landing/")


def _send_resend(to: str, subject: str, html: str, text: str) -> dict[str, Any]:
    api_key = getattr(settings, "resend_api_key", "")
    if not api_key:
        return {"sent": False, "provider": "resend", "reason": "missing_resend_api_key"}

    payload = {
        "from": _from_email(),
        "to": [to],
        "subject": subject,
        "html": html,
        "text": text,
    }

    req = urllib.request.Request(
        "https://api.resend.com/emails",
        data=json.dumps(payload).encode("utf-8"),
        headers={
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
        },
        method="POST",
    )

    try:
        with urllib.request.urlopen(req, timeout=15) as resp:
            body = resp.read().decode("utf-8")
            return {
                "sent": 200 <= resp.status < 300,
                "provider": "resend",
                "status": resp.status,
                "body": body,
            }
    except Exception as exc:
        logger.exception("resend_email_failed to=%s error=%s", to, exc)
        return {"sent": False, "provider": "resend", "reason": str(exc)}


def _send_smtp(to: str, subject: str, html: str, text: str) -> dict[str, Any]:
    host = getattr(settings, "smtp_host", "")
    username = getattr(settings, "smtp_username", "")
    password = getattr(settings, "smtp_password", "")
    port = int(getattr(settings, "smtp_port", 587))
    use_tls = bool(getattr(settings, "smtp_use_tls", True))

    if not host or not username or not password:
        return {"sent": False, "provider": "smtp", "reason": "missing_smtp_config"}

    msg = EmailMessage()
    msg["From"] = getattr(settings, "smtp_from", "") or username
    msg["To"] = to
    msg["Subject"] = subject
    msg.set_content(text)
    msg.add_alternative(html, subtype="html")

    try:
        if use_tls:
            context = ssl.create_default_context()
            with smtplib.SMTP(host, port, timeout=15) as server:
                server.starttls(context=context)
                server.login(username, password)
                server.send_message(msg)
        else:
            with smtplib.SMTP(host, port, timeout=15) as server:
                server.login(username, password)
                server.send_message(msg)

        return {"sent": True, "provider": "smtp"}
    except Exception as exc:
        logger.exception("smtp_email_failed to=%s error=%s", to, exc)
        return {"sent": False, "provider": "smtp", "reason": str(exc)}


def send_email(to: str, subject: str, html: str, text: str) -> dict[str, Any]:
    if getattr(settings, "resend_api_key", ""):
        result = _send_resend(to, subject, html, text)
        if result.get("sent"):
            return result

    if getattr(settings, "smtp_host", ""):
        result = _send_smtp(to, subject, html, text)
        if result.get("sent"):
            return result

    logger.warning(
        "EMAIL_PROVIDER_NOT_CONFIGURED to=%s subject=%s text=%s",
        to,
        subject,
        text,
    )
    return {"sent": False, "provider": "log", "reason": "email_provider_not_configured"}


def send_api_key_email(email: str, api_key: str, plan: str = "free", name: str | None = None) -> dict[str, Any]:
    greeting = f"Hi {name}," if name else "Hi,"
    api_url = _api_url()
    public_url = _public_url()

    subject = f"Your SAS API key ({plan})"

    text = f"""{greeting}

Your SAS API key is:

{api_key}

Plan: {plan}
API: {api_url}
Docs: {api_url}/docs
Landing: {public_url}

PowerShell example:
$env:SAS_API_KEY="{api_key}"
sas --api-key "{api_key}" diff "Python is a programming language." "A python is a snake."

Do not share this key publicly.

— SAS
"""

    html = f"""
    <div style="font-family:Arial,sans-serif;line-height:1.5">
      <p>{greeting}</p>
      <p>Your SAS API key is:</p>
      <pre style="background:#111;color:#00ffd5;padding:14px;border-radius:8px;white-space:pre-wrap">{api_key}</pre>
      <p><b>Plan:</b> {plan}</p>
      <p><b>API:</b> <a href="{api_url}">{api_url}</a></p>
      <p><b>Docs:</b> <a href="{api_url}/docs">{api_url}/docs</a></p>
      <p><b>Landing:</b> <a href="{public_url}">{public_url}</a></p>
      <p>Do not share this key publicly.</p>
      <p>— SAS</p>
    </div>
    """

    return send_email(email, subject, html, text)


def send_pro_welcome_email(email: str, api_key: str | None = None, name: str | None = None) -> dict[str, Any]:
    greeting = f"Hi {name}," if name else "Hi,"
    api_url = _api_url()

    if api_key:
        key_text = f"\nYour new SAS Pro API key:\n\n{api_key}\n"
        key_html = f"""
        <p>Your new SAS Pro API key:</p>
        <pre style="background:#111;color:#00ffd5;padding:14px;border-radius:8px;white-space:pre-wrap">{api_key}</pre>
        """
    else:
        key_text = "\nYour existing SAS API key has been upgraded to Pro.\n"
        key_html = "<p>Your existing SAS API key has been upgraded to <b>Pro</b>.</p>"

    subject = "SAS Pro activated"

    text = f"""{greeting}

SAS Pro is active.
{key_text}
Plan: Pro
Limit: 10,000 requests/month
API: {api_url}
Docs: {api_url}/docs

— SAS
"""

    html = f"""
    <div style="font-family:Arial,sans-serif;line-height:1.5">
      <p>{greeting}</p>
      <p><b>SAS Pro is active.</b></p>
      {key_html}
      <p><b>Limit:</b> 10,000 requests/month</p>
      <p><b>API:</b> <a href="{api_url}">{api_url}</a></p>
      <p><b>Docs:</b> <a href="{api_url}/docs">{api_url}/docs</a></p>
      <p>— SAS</p>
    </div>
    """

    return send_email(email, subject, html, text)

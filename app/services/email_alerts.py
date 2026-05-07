"""
app/services/email_alerts.py - Email alerting for SAS admin events.

SMTP-based alert system.
No external paid dependency required.
"""

from __future__ import annotations

import asyncio
import smtplib
from datetime import datetime, timezone
from email.message import EmailMessage

from app.config import settings


def _email_configured() -> bool:
    return (
        bool(getattr(settings, "email_alerts_enabled", False))
        and bool(getattr(settings, "smtp_host", "").strip())
        and bool(getattr(settings, "smtp_username", "").strip())
        and bool(getattr(settings, "smtp_password", "").strip())
        and bool(getattr(settings, "alert_email_to", "").strip())
    )


def _send_email_sync(*, subject: str, body: str) -> None:
    """
    Send an email using SMTP.

    Called through asyncio.to_thread() so it does not block the FastAPI event loop.
    """
    if not _email_configured():
        return

    smtp_host = settings.smtp_host.strip()
    smtp_port = int(settings.smtp_port)
    smtp_username = settings.smtp_username.strip()
    smtp_password = settings.smtp_password.strip()
    smtp_from = (settings.smtp_from or smtp_username).strip()
    smtp_to = settings.alert_email_to.strip()

    msg = EmailMessage()
    msg["Subject"] = subject
    msg["From"] = smtp_from
    msg["To"] = smtp_to
    msg.set_content(body)

    with smtplib.SMTP(smtp_host, smtp_port, timeout=10) as server:
        if bool(settings.smtp_use_tls):
            server.starttls()

        server.login(smtp_username, smtp_password)
        server.send_message(msg)


async def send_email_alert(*, subject: str, body: str) -> None:
    """
    Async wrapper.

    Alerting must never break API responses.
    """
    try:
        await asyncio.to_thread(_send_email_sync, subject=subject, body=body)
    except Exception:
        return


async def alert_invalid_admin_access(
    *,
    endpoint: str,
    method: str,
    ip_hash: str,
    country: str,
    reason: str,
) -> None:
    timestamp = datetime.now(timezone.utc).isoformat(timespec="seconds")

    subject = f"SAS admin access alert: {reason}"

    body = (
        "SAS admin access alert\n\n"
        f"time_utc: {timestamp}\n"
        f"endpoint: {method} {endpoint}\n"
        f"country: {country}\n"
        f"ip_hash: {ip_hash}\n"
        f"reason: {reason}\n\n"
        "No raw IP address or API key is included in this alert.\n"
    )

    await send_email_alert(subject=subject, body=body)

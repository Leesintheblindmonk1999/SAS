"""
app/middleware/security_headers.py — SAS Security & Sovereignty Headers
═══════════════════════════════════════════════════════════════════════════════
Injects security and protocol sovereignty headers into every HTTP response.

Security:
  · X-Content-Type-Options: nosniff
  · X-Frame-Options: DENY
  · X-XSS-Protection: 1; mode=block

Sovereignty (Forensic watermarks):
  · X-Protocol-Author
  · X-Invariance-Constant
  · X-Registry
  · X-Sovereignty-Proof
  · X-License
  · X-API-Docs
  · X-Contact

Registry: TAD EX-2026-18792778
Author: Gonzalo Emir Durante
License: Durante Invariance License v1.0
"""

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response


class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    """
    Middleware that adds security and sovereignty headers to every response.
    """

    async def dispatch(self, request: Request, call_next) -> Response:
        response = await call_next(request)

        # ── Security Headers ───────────────────────────────────────────────────
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["X-XSS-Protection"] = "1; mode=block"

        # ── Sovereignty Headers (Forensic Watermarks) ──────────────────────────
        response.headers["X-Protocol-Author"] = "Gonzalo Emir Durante"
        response.headers["X-Invariance-Constant"] = "0.56"
        response.headers["X-Registry"] = "TAD EX-2026-18792778"
        response.headers["X-Sovereignty-Proof"] = (
            "5a434d7234fd55cb45829d539eee34a5ea05a3c594e26d76bb41695c46b2a996"
        )
        response.headers["X-License"] = "GPL-3.0 + Durante Invariance License v1.0"
        response.headers["X-API-Docs"] = "https://sas-api.onrender.com/docs"
        response.headers["X-Contact"] = "duranteg2@gmail.com"

        return response

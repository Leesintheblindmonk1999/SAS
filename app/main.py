"""
app/main.py - SAS - Symbiotic Autoprotection System v1.1.0
FastAPI application entry point.

kappa_D = 0.56 - Durante Constant - TAD EX-2026-18792778

Production improvements:
- Centralized metadata
- Updated SAS DOI
- Professional structured logging
- Hashed IP logging
- Request ID tracing via request.state
- Protected debug endpoint
- No full header exposure
- /readyz readiness endpoint
- Configurable CORS (HEAD included)
- Strong root and integrity endpoints
- Admin-only /v1/metrics endpoint
- Public anonymized activity endpoints
- Public demo endpoint
- Self-service Free API keys
- Plan-aware API key authentication
- Polar checkout/webhook
- Mercado Pago Checkout Pro + webhook
- robots.txt with Cache-Control
- HEAD / for uptime monitors
- RequestValidationError handler (422 with examples)
- /app/data directory auto-creation for Render
"""

from __future__ import annotations

import hashlib
import logging
import sqlite3
import time
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from fastapi import FastAPI, Header, HTTPException, Request, Response
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware

from app.config import settings
from app.db.auth_store import init_auth_db
from app.services.auth import api_key_auth_middleware
from app.services.metrics_store import (
    init_metrics_db,
    purge_old_metrics,
    record_request_metric,
)

# ==============================================================================
# CENTRALIZED METADATA
# ==============================================================================

SAS_VERSION = settings.sas_version
SAS_NAME = settings.sas_name
SAS_DOI = settings.sas_doi
OMNI_VERSION = settings.omni_version
OMNI_DOI = settings.omni_scanner_doi
REGISTRY = settings.registry
KAPPA_D = settings.kappa_d
LEDGER_HASH = settings.ledger_hash
REPO_URL = settings.repo_url
HOSTED_API = settings.hosted_api
OTS_DATE = settings.ots_date
OTS_CHAIN = settings.ots_chain

# ==============================================================================
# LOGGING
# ==============================================================================

logging.basicConfig(level=getattr(logging, settings.log_level.upper(), logging.INFO))
logger = logging.getLogger(__name__)

# ==============================================================================
# OPTIONAL MIDDLEWARES
# ==============================================================================

try:
    from app.middleware.security_headers import SecurityHeadersMiddleware
    HAS_SECURITY = True
except ImportError:
    HAS_SECURITY = False
    SecurityHeadersMiddleware = None
    logger.info("Security headers middleware not found. Continuing without it.")

# ==============================================================================
# CORE ROUTERS
# ==============================================================================

from app.routers import admin, audit, diff, health

# ==============================================================================
# OPTIONAL SAS ROUTERS
# ==============================================================================

try:
    try:
        from app.routers.chat import router as chat_router
    except ImportError:
        from app.routers.chat_router import router as chat_router
    HAS_CHAT = True
except ImportError:
    HAS_CHAT = False
    chat_router = None
    logger.warning("Chat router not found.")

try:
    try:
        from app.routers.audit_conversation import router as audit_conversation_router
    except ImportError:
        from app.routers.audit_conversation_router import router as audit_conversation_router
    HAS_AUDIT_CONVERSATION = True
except ImportError:
    HAS_AUDIT_CONVERSATION = False
    audit_conversation_router = None
    logger.warning("Audit conversation router not found.")

try:
    from app.routers.status import router as status_router
    HAS_STATUS = True
except ImportError:
    HAS_STATUS = False
    status_router = None
    logger.warning("Status router not found.")

try:
    from app.routers.metrics import router as metrics_router
    HAS_METRICS = True
except ImportError:
    HAS_METRICS = False
    metrics_router = None
    logger.info("Metrics router not found. Optional admin metrics disabled.")

try:
    from app.routers.public_activity import router as public_activity_router
    HAS_PUBLIC_ACTIVITY = True
except ImportError:
    HAS_PUBLIC_ACTIVITY = False
    public_activity_router = None
    logger.info("Public activity router not found.")

try:
    from app.routers.public_demo import router as public_demo_router
    HAS_PUBLIC_DEMO = True
except ImportError:
    HAS_PUBLIC_DEMO = False
    public_demo_router = None
    logger.info("Public demo router not found.")

try:
    from app.routers.public_request_key import router as public_request_key_router
    HAS_PUBLIC_REQUEST_KEY = True
except ImportError:
    HAS_PUBLIC_REQUEST_KEY = False
    public_request_key_router = None
    logger.info("Public request-key router not found.")

try:
    from app.routers.whoami import router as whoami_router
    HAS_WHOAMI = True
except ImportError:
    HAS_WHOAMI = False
    whoami_router = None
    logger.info("Whoami router not found.")

try:
    from app.routers.billing import router as billing_router
    HAS_BILLING = True
except ImportError:
    HAS_BILLING = False
    billing_router = None
    logger.info("Billing router not found. Polar billing disabled.")

try:
    from app.routers.mercadopago_billing import router as mercadopago_billing_router
    HAS_MERCADOPAGO_BILLING = True
except ImportError:
    HAS_MERCADOPAGO_BILLING = False
    mercadopago_billing_router = None
    logger.info("Mercado Pago billing router not found.")

# ==============================================================================
# OPTIONAL EXTERNAL AUDIT + NOTARIZATION ROUTERS
# ==============================================================================

if settings.enable_external_audit:
    try:
        from app.routers.external_audit_router import router as external_audit_router
        HAS_EXTERNAL_AUDIT = True
    except ImportError:
        HAS_EXTERNAL_AUDIT = False
        external_audit_router = None
        logger.info("External audit router not found.")
else:
    HAS_EXTERNAL_AUDIT = False
    external_audit_router = None

try:
    from app.routers.notarization_router import router as notarization_router
    HAS_NOTARIZATION = True
except ImportError:
    HAS_NOTARIZATION = False
    notarization_router = None
    logger.info("Notarization router not found.")

# ==============================================================================
# MONITORING HELPERS
# ==============================================================================


def _client_ip(request: Request) -> str:
    """Extract the real client IP from common proxy headers."""
    return (
        request.headers.get("true-client-ip")
        or request.headers.get("cf-connecting-ip")
        or request.headers.get("x-forwarded-for", "").split(",")[0].strip()
        or (request.client.host if request.client else "unknown")
    )


def _hash_ip(ip: str) -> str:
    """Hash IPs before logging to avoid storing raw IP addresses."""
    return hashlib.sha256(ip.encode("utf-8")).hexdigest()[:12]


def _safe_header_snapshot(request: Request) -> dict[str, str]:
    """Return only non-sensitive diagnostic headers."""
    allowed = {"user-agent", "x-forwarded-for", "cf-ipcountry", "cf-ray", "host"}
    return {k: v for k, v in request.headers.items() if k.lower() in allowed}



def _check_sqlite_db(path: str | None, required_table: str | None = None) -> bool:
    """
    Minimal SQLite readiness check.

    Returns True only if:
    - the path is configured;
    - the parent directory exists or can be created;
    - SQLite can open the database;
    - SELECT 1 succeeds;
    - required_table exists, when provided.

    This does not expose DB paths or internal errors to clients.
    """
    if not path:
        return False

    try:
        db_path = Path(path)
        db_path.parent.mkdir(parents=True, exist_ok=True)

        conn = sqlite3.connect(str(db_path), timeout=2)
        try:
            conn.execute("SELECT 1")

            if required_table:
                row = conn.execute(
                    "SELECT name FROM sqlite_master WHERE type='table' AND name=?",
                    (required_table,),
                ).fetchone()
                if row is None:
                    logger.warning("sqlite_readiness_missing_table table=%s", required_table)
                    return False

            return True
        finally:
            conn.close()

    except Exception as exc:
        logger.warning(
            "sqlite_readiness_check_failed table=%s error=%s",
            required_table or "none",
            str(exc),
        )
        return False



# ==============================================================================
# PAYLOAD SIZE LIMIT MIDDLEWARE
# ==============================================================================


class PayloadSizeLimitMiddleware(BaseHTTPMiddleware):
    """
    Reject oversized request bodies before they reach routers or detector logic.

    This is a first-line application-layer defense against accidental or abusive
    large payloads. It relies on Content-Length, which is not a complete DDoS
    solution, but it blocks the common case early and cheaply.

    Limits are intentionally conservative for public endpoints.
    """

    LIMITS_BY_PREFIX: dict[str, int] = {
        "/public/request-key": 2 * 1024,          # 2 KB: email + name only
        "/public/demo/audit": 8 * 1024,           # 8 KB: public demo
        "/v1/chat": 25 * 1024,                    # 25 KB
        "/v1/audit": 50 * 1024,                   # 50 KB
        "/v1/diff": 100 * 1024,                   # 100 KB general cap
        "/admin": 10 * 1024,                      # 10 KB
        "/billing": 100 * 1024,                   # 100 KB provider webhooks
    }

    async def dispatch(self, request: Request, call_next):
        path = request.url.path
        method = request.method.upper()

        # GET/HEAD/OPTIONS normally have no meaningful request body.
        if method in {"GET", "HEAD", "OPTIONS"}:
            return await call_next(request)

        limit = self._limit_for_path(path)
        if limit is None:
            return await call_next(request)

        content_length = request.headers.get("content-length")

        if content_length:
            try:
                size = int(content_length)
            except ValueError:
                size = 0

            if size > limit:
                request_id = getattr(request.state, "request_id", "unknown")

                logger.warning(
                    "payload_too_large request_id=%s method=%s path=%s size=%s limit=%s",
                    request_id,
                    method,
                    path,
                    size,
                    limit,
                )

                return JSONResponse(
                    status_code=413,
                    content={
                        "error": "Payload too large",
                        "message": "Request body exceeds the allowed size for this endpoint.",
                        "path": path,
                        "limit_bytes": limit,
                        "received_bytes": size,
                        "request_id": request_id,
                    },
                )

        return await call_next(request)

    @classmethod
    def _limit_for_path(cls, path: str) -> int | None:
        for prefix, limit in cls.LIMITS_BY_PREFIX.items():
            if path.startswith(prefix):
                return limit
        return None

# ==============================================================================
# REQUEST MONITORING MIDDLEWARE
# ==============================================================================


async def request_monitoring_middleware(request: Request, call_next):
    """
    Professional request observability middleware.

    Adds X-Request-ID, X-Process-Time, X-Trace-Timestamp, X-Monitoring-Node.
    Records aggregate metrics without storing raw IPs or raw API keys.

    Registered FIRST so request_id is always available when auth middleware runs.
    """
    start_time = time.time()
    request_id = str(uuid.uuid4())
    request.state.request_id = request_id

    client_ip = _client_ip(request)
    ip_hash = _hash_ip(client_ip)
    country = request.headers.get("cf-ipcountry", "unknown")
    method = request.method
    path = request.url.path

    try:
        response = await call_next(request)
    except Exception as exc:
        logger.error(
            "request_failed request_id=%s country=%s ip_hash=%s method=%s path=%s error=%s",
            request_id, country, ip_hash, method, path, str(exc),
            exc_info=True,
        )
        raise

    process_time = time.time() - start_time

    logger.info(
        "request request_id=%s country=%s ip_hash=%s method=%s path=%s status=%s time=%.4f",
        request_id, country, ip_hash, method, path, response.status_code, process_time,
    )

    try:
        api_key = request.headers.get("X-API-Key")
        record_request_metric(
            method=method,
            path=path,
            status_code=response.status_code,
            ip_hash=ip_hash,
            api_key=api_key,
            latency_ms=process_time * 1000,
            request_id=request_id,
            country=country,
        )
    except Exception as metrics_error:
        logger.warning(
            "metrics_record_failed request_id=%s error=%s",
            request_id, str(metrics_error),
        )

    response.headers["X-Request-ID"] = request_id
    response.headers["X-Process-Time"] = str(round(process_time, 4))
    response.headers["X-Trace-Timestamp"] = datetime.now(timezone.utc).isoformat()
    response.headers["X-Monitoring-Node"] = "sas-origin"

    return response


# ==============================================================================
# FASTAPI APP
# ==============================================================================

app = FastAPI(
    title=SAS_NAME,
    version=SAS_VERSION,
    description=(
        f"Structural hallucination detection API using kappa_D={KAPPA_D}. "
        f"Registry: {REGISTRY} | SAS DOI: {SAS_DOI}"
    ),
    contact={
        "name": "Gonzalo Emir Durante",
        "url": REPO_URL,
        "email": "duranteg2@gmail.com",
    },
    license_info={
        "name": "GPL-3.0 + Durante Invariance License v1.0",
        "url": f"{REPO_URL}/blob/main/LICENSE.md",
    },
)


# ==============================================================================
# STARTUP
# ==============================================================================

@app.on_event("startup")
async def startup_databases():
    # Ensure /app/data exists on Render and any containerized deployment.
    # SQLite will fail silently if the directory doesn't exist.
    auth_db_path = str(getattr(settings, "auth_db_path", "/app/data/auth.db"))
    metrics_db_path = str(getattr(settings, "metrics_db_path", "/app/data/metrics.db"))

    data_dir = Path(auth_db_path).parent
    data_dir.mkdir(parents=True, exist_ok=True)

    metrics_dir = Path(metrics_db_path).parent
    metrics_dir.mkdir(parents=True, exist_ok=True)

    init_metrics_db()
    init_auth_db()

    deleted = purge_old_metrics()
    if deleted:
        logger.info("metrics_retention deleted_rows=%s", deleted)

    logger.info("startup_complete service=%s version=%s", SAS_NAME, SAS_VERSION)


# ==============================================================================
# MIDDLEWARE REGISTRATION
# FastAPI/Starlette execute the LAST registered HTTP middleware FIRST (outermost).
# Register api_key_auth first and request_monitoring last.
# → request_monitoring executes first (outermost) → sets request_id
# → api_key_auth executes second → request_id is always available if auth fails
# ==============================================================================

app.middleware("http")(api_key_auth_middleware)
app.middleware("http")(request_monitoring_middleware)

app.add_middleware(PayloadSizeLimitMiddleware)

if HAS_SECURITY and SecurityHeadersMiddleware:
    app.add_middleware(SecurityHeadersMiddleware)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    # HEAD included for uptime monitors and crawlers.
    allow_methods=["POST", "GET", "HEAD", "OPTIONS"],
    allow_headers=["*"],
)

# ==============================================================================
# ROUTER REGISTRATION
# ==============================================================================

app.include_router(health.router, tags=["System"])
app.include_router(audit.router, prefix="/v1", tags=["Detection"])
app.include_router(diff.router, prefix="/v1", tags=["Forensic Diff"])
app.include_router(admin.router, prefix="/admin", tags=["Admin"])

if HAS_METRICS and metrics_router:
    app.include_router(metrics_router, prefix="/v1", tags=["Admin"])

if HAS_PUBLIC_ACTIVITY and public_activity_router:
    app.include_router(public_activity_router, tags=["Public"])

if HAS_PUBLIC_DEMO and public_demo_router:
    app.include_router(public_demo_router, tags=["Public"])

if HAS_PUBLIC_REQUEST_KEY and public_request_key_router:
    app.include_router(public_request_key_router, tags=["Public"])

if HAS_WHOAMI and whoami_router:
    app.include_router(whoami_router, prefix="/v1", tags=["Auth"])

if HAS_BILLING and billing_router:
    app.include_router(billing_router, tags=["Billing"])

if HAS_MERCADOPAGO_BILLING and mercadopago_billing_router:
    app.include_router(mercadopago_billing_router, tags=["Billing"])

if HAS_CHAT and chat_router:
    app.include_router(chat_router, tags=["Honest Chat"])

if HAS_AUDIT_CONVERSATION and audit_conversation_router:
    app.include_router(audit_conversation_router, tags=["Conversation Audit"])

if HAS_STATUS and status_router:
    app.include_router(status_router, tags=["SAS Status"])

if HAS_EXTERNAL_AUDIT and external_audit_router:
    app.include_router(external_audit_router, tags=["External Audit"])

if HAS_NOTARIZATION and notarization_router:
    app.include_router(notarization_router, tags=["Notarization"])


# ==============================================================================
# PUBLIC SYSTEM ENDPOINTS
# ==============================================================================


@app.get("/robots.txt", tags=["System"], include_in_schema=False)
async def robots_txt() -> Response:
    """
    Crawler guidance.
    /admin and /billing are excluded from indexing.
    /v1 endpoints are API-only and excluded from web crawlers.
    /public/request-key is excluded — it triggers email/key generation flows
    and has no value for indexing. Rate-limited server-side regardless.
    This is not a security measure — it is crawler etiquette.
    """
    content = (
        "User-agent: *\n"
        "Allow: /\n"
        "Disallow: /admin\n"
        "Disallow: /v1\n"
        "Disallow: /billing\n"
        "Disallow: /public/request-key\n"
    )
    return Response(
        content=content,
        media_type="text/plain",
        # Cache for 1 hour — reduces repeated hits from crawlers.
        headers={"Cache-Control": "public, max-age=3600"},
    )


@app.head("/", tags=["System"], include_in_schema=False)
async def head_root() -> Response:
    """
    HEAD / for uptime monitors (UptimeRobot, Render health checks, etc.).
    Returns 200 with no body. Avoids false 405 errors in logs.
    """
    return Response(status_code=200)


@app.get("/", tags=["System"])
async def root() -> dict[str, Any]:
    """Root endpoint with public metadata and provenance."""
    return {
        "service": SAS_NAME,
        "version": SAS_VERSION,
        "status": "operational",
        "hosted_api": HOSTED_API,
        "docs": "/docs",
        "kappa_d": KAPPA_D,
        "author": "Gonzalo Emir Durante",
        "registry": REGISTRY,
        "sas_doi": SAS_DOI,
        "omni_scanner_doi": OMNI_DOI,
        "ledger_hash": LEDGER_HASH,
        # Benchmark note: conservative presentation for external audiences.
        # Full methodology, dataset and replication details: see DOI and README.
        "benchmark": {
            "pairs": 2000,
            "status": "documented",
            "note": "See repository and DOI for methodology and replication details.",
            "doi": SAS_DOI,
        },
        "message": "Structural coherence audit API for generative AI outputs.",
        "endpoints": {
            "health": "/health",
            "readiness": "/readyz",
            "integrity": "/integrity",
            "audit": "/v1/audit",
            "diff": "/v1/diff",
            "chat": "/v1/chat",
            "whoami": "/v1/whoami",
            "public_stats": "/public/stats",
            "public_activity": "/public/activity",
            "public_demo": "/public/demo/audit",
            "request_key": "/public/request-key",
            "polar_checkout": "/billing/polar/checkout",
            "polar_webhook": "/billing/polar/webhook",
            "mercadopago_checkout": "/billing/mercadopago/checkout",
            "mercadopago_webhook": "/billing/mercadopago/webhook",
            "docs": "/docs",
        },
    }


@app.get("/integrity", tags=["System"])
async def integrity() -> dict[str, Any]:
    """Technical and legal provenance certificate."""
    return {
        "status": "operational",
        "kappa_d": KAPPA_D,
        "author": "Gonzalo Emir Durante",
        "protocol": f"SAS v{SAS_VERSION} - Omni-Scanner v{OMNI_VERSION}",
        "registry": f"{REGISTRY} (Argentina)",
        "zenodo_doi": OMNI_DOI,
        "sas_doi": SAS_DOI,
        "ledger_hash": LEDGER_HASH,
        "ots_date": OTS_DATE,
        "ots_chain": OTS_CHAIN,
        "license": "GPL-3.0 + Durante Invariance License v1.0",
    }


@app.get("/readyz", tags=["System"])
async def readyz() -> dict[str, Any]:
    """
    Granular readiness endpoint for Render and orchestrators.

    Checks:
    - routers imported correctly;
    - auth SQLite database can be opened and contains the users table;
    - metrics SQLite database can be opened and contains api_request_metrics.

    The endpoint does not expose DB paths, table contents, raw errors, or secrets.
    """
    routers = {
        "health": True,
        "audit": True,
        "diff": True,
        "admin": True,
        "metrics": HAS_METRICS,
        "public_activity": HAS_PUBLIC_ACTIVITY,
        "public_demo": HAS_PUBLIC_DEMO,
        "public_request_key": HAS_PUBLIC_REQUEST_KEY,
        "whoami": HAS_WHOAMI,
        "billing_polar": HAS_BILLING,
        "billing_mercadopago": HAS_MERCADOPAGO_BILLING,
        "chat": HAS_CHAT,
        "audit_conversation": HAS_AUDIT_CONVERSATION,
        "status": HAS_STATUS,
        "external_audit": HAS_EXTERNAL_AUDIT,
        "notarization": HAS_NOTARIZATION,
    }

    databases = {
        "auth_db": _check_sqlite_db(
            str(getattr(settings, "auth_db_path", "/app/data/auth.db")),
            required_table="users",
        ),
        "metrics_db": _check_sqlite_db(
            str(getattr(settings, "metrics_db_path", "/app/data/metrics.db")),
            required_table="api_request_metrics",
        ),
    }

    ready = all(databases.values())

    return {
        "status": "ready" if ready else "degraded",
        "service": SAS_NAME,
        "version": SAS_VERSION,
        "kappa_d": KAPPA_D,
        "routers": routers,
        "databases": databases,
    }


# ==============================================================================
# PROTECTED DEBUG ENDPOINTS
# ==============================================================================


@app.get("/v1/debug/whoami", tags=["Debug"], include_in_schema=False)
async def debug_whoami(
    request: Request,
    x_admin_secret: str | None = Header(default=None, alias="X-Admin-Secret"),
) -> dict[str, Any]:
    """Protected diagnostics. Requires enable_debug_endpoints=True + valid admin secret."""
    if not settings.enable_debug_endpoints:
        raise HTTPException(status_code=404, detail="Not found")
    if not settings.admin_secret or x_admin_secret != settings.admin_secret:
        raise HTTPException(status_code=403, detail="Forbidden")

    client_ip = _client_ip(request)
    return {
        "your_ip": client_ip,
        "your_ip_hash": _hash_ip(client_ip),
        "cf_country": request.headers.get("cf-ipcountry", "unknown"),
        "headers": _safe_header_snapshot(request),
        "request_id": getattr(request.state, "request_id", "unknown"),
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }


# ==============================================================================
# ERROR HANDLERS
# ==============================================================================


def _safe_validation_errors(exc: RequestValidationError) -> list[dict[str, Any]]:
    """
    Sanitize validation errors before returning to client.
    Strips raw input values that could expose sensitive data (emails, payloads, etc.)
    Only returns: location, message type, and human-readable message.
    """
    return [
        {
            "loc": err.get("loc"),
            "msg": err.get("msg"),
            "type": err.get("type"),
        }
        for err in exc.errors()
    ]


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(
    request: Request,
    exc: RequestValidationError,
) -> JSONResponse:
    """
    422 Validation errors with helpful examples for public endpoints.
    Makes /public/request-key and /public/demo/audit errors actionable.
    """
    request_id = getattr(request.state, "request_id", "unknown")
    safe_errors = _safe_validation_errors(exc)

    logger.info(
        "validation_error request_id=%s path=%s errors=%s",
        request_id,
        request.url.path,
        safe_errors,
    )

    return JSONResponse(
        status_code=422,
        content={
            "error": "Validation error",
            "message": "Invalid request body or parameters.",
            "details": safe_errors,
            "request_id": request_id,
            "examples": {
                "request_key": {
                    "method": "POST",
                    "path": "/public/request-key",
                    "json": {
                        "email": "you@example.com",
                        "name": "Your Name",
                    },
                },
                "demo_audit": {
                    "method": "POST",
                    "path": "/public/demo/audit",
                    "json": {
                        "source": "The Eiffel Tower is located in Paris, France.",
                        "response": "The Eiffel Tower is located in Berlin, Germany.",
                    },
                },
                "diff": {
                    "method": "POST",
                    "path": "/v1/diff",
                    "headers": {"X-API-Key": "sas_your_key_here"},
                    "json": {
                        "text_a": "The Eiffel Tower is in Paris.",
                        "text_b": "The Eiffel Tower is in Berlin.",
                        "experimental": True,
                    },
                },
            },
        },
    )


@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    """Global exception handler — avoids exposing internals."""
    request_id = getattr(request.state, "request_id", "unknown")

    logger.error(
        "unhandled_exception request_id=%s path=%s error=%s",
        request_id,
        request.url.path,
        str(exc),
        exc_info=True,
    )

    return JSONResponse(
        status_code=500,
        content={
            "error": "Internal server error",
            "message": "The SAS API encountered an unexpected error.",
            "kappa_d": KAPPA_D,
            "registry": REGISTRY,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "request_id": request_id,
        },
    )

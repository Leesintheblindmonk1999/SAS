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
- Configurable CORS
- Strong root and integrity endpoints
"""

from __future__ import annotations

import hashlib
import logging
import time
import uuid
from datetime import datetime, timezone
from typing import Any

from fastapi import FastAPI, Header, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.config import settings

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
    logger.warning("Chat router not found. Expected app/routers/chat.py or app/routers/chat_router.py")

try:
    try:
        from app.routers.audit_conversation import router as audit_conversation_router
    except ImportError:
        from app.routers.audit_conversation_router import router as audit_conversation_router

    HAS_AUDIT_CONVERSATION = True
except ImportError:
    HAS_AUDIT_CONVERSATION = False
    audit_conversation_router = None
    logger.warning("Audit conversation router not found")

try:
    from app.routers.status import router as status_router

    HAS_STATUS = True
except ImportError:
    HAS_STATUS = False
    status_router = None
    logger.warning("Status router not found")

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
        logger.info("External audit router not found. Optional module disabled.")
else:
    HAS_EXTERNAL_AUDIT = False
    external_audit_router = None

try:
    from app.routers.notarization_router import router as notarization_router

    HAS_NOTARIZATION = True
except ImportError:
    HAS_NOTARIZATION = False
    notarization_router = None
    logger.info("Notarization router not found. Optional module disabled.")

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
    allowed = {
        "user-agent",
        "x-forwarded-for",
        "cf-ipcountry",
        "cf-ray",
        "host",
    }
    return {
        key: value
        for key, value in request.headers.items()
        if key.lower() in allowed
    }


# ==============================================================================
# REQUEST MONITORING MIDDLEWARE
# ==============================================================================


async def request_monitoring_middleware(request: Request, call_next):
    """
    Professional request observability middleware.

    Adds:
    - X-Request-ID
    - X-Process-Time
    - X-Trace-Timestamp
    - X-Monitoring-Node
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
            request_id,
            country,
            ip_hash,
            method,
            path,
            str(exc),
            exc_info=True,
        )
        raise

    process_time = time.time() - start_time

    logger.info(
        "request request_id=%s country=%s ip_hash=%s method=%s path=%s status=%s time=%.4f",
        request_id,
        country,
        ip_hash,
        method,
        path,
        response.status_code,
        process_time,
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

app.middleware("http")(request_monitoring_middleware)

if HAS_SECURITY and SecurityHeadersMiddleware:
    app.add_middleware(SecurityHeadersMiddleware)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_methods=["POST", "GET", "OPTIONS"],
    allow_headers=["*"],
)

# ==============================================================================
# ROUTER REGISTRATION
# ==============================================================================

app.include_router(health.router, tags=["System"])
app.include_router(audit.router, prefix="/v1", tags=["Detection"])
app.include_router(diff.router, prefix="/v1", tags=["Forensic Diff"])
app.include_router(admin.router, prefix="/admin", tags=["Admin"])

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
        "benchmark": {
            "pairs": 2000,
            "accuracy": "98.80%",
            "precision": "100.00%",
            "recall": "97.60%",
            "f1_score": "98.79%",
            "false_positives": 0,
        },
        "message": "Structural coherence audit API for generative AI outputs.",
        "endpoints": {
            "health": "/health",
            "readiness": "/readyz",
            "audit": "/v1/audit",
            "diff": "/v1/diff",
            "chat": "/v1/chat",
            "status": "/v1/status",
            "integrity": "/integrity",
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
    """Granular readiness endpoint for Render and orchestrators."""
    return {
        "status": "ready",
        "service": SAS_NAME,
        "version": SAS_VERSION,
        "kappa_d": KAPPA_D,
        "routers": {
            "health": True,
            "audit": True,
            "diff": True,
            "admin": True,
            "chat": HAS_CHAT,
            "audit_conversation": HAS_AUDIT_CONVERSATION,
            "status": HAS_STATUS,
            "external_audit": HAS_EXTERNAL_AUDIT,
            "notarization": HAS_NOTARIZATION,
        },
    }


# ==============================================================================
# PROTECTED DEBUG ENDPOINTS
# ==============================================================================


@app.get("/v1/debug/whoami", tags=["Debug"], include_in_schema=False)
async def whoami(
    request: Request,
    x_admin_secret: str | None = Header(default=None, alias="X-Admin-Secret"),
) -> dict[str, Any]:
    """
    Protected diagnostics endpoint.

    Requirements:
    - settings.enable_debug_endpoints = True
    - valid X-Admin-Secret header

    This endpoint intentionally does not return all request headers.
    """
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
# GLOBAL ERROR HANDLER
# ==============================================================================


@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    """Global exception handler that avoids exposing internals."""
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

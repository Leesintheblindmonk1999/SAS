"""
app/main.py — Omni-Scanner API v1.0 + SAS v1.0
═══════════════════════════════════════════════════════════════════════════════
FastAPI application entry point.

κD = 0.56 — Durante Constant — TAD EX-2026-18792778

Endpoints:
  Existing:
    GET  /health
    GET  /integrity
    POST /v1/audit
    POST /v1/diff
    POST /admin/generate-key

  SAS v1.0:
    POST /v1/chat                — honest chat with resonance + κD filter
    POST /v1/audit_conversation  — notarial conversation certificate
    GET  /v1/status              — system and module status

  New (external audit + notarization):
    POST /v1/audit_external_model  — structural comparison for external models
    POST /v1/notarize              — generates Merkle + Root Hash certificate
"""

from __future__ import annotations

import logging
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.config import settings

# ── Middlewares (con fallback seguro) ─────────────────────────────────────────
try:
    from app.middleware.security_headers import SecurityHeadersMiddleware
    HAS_SECURITY = True
except ImportError:
    HAS_SECURITY = False
    SecurityHeadersMiddleware = None

# ── Existing routers ──────────────────────────────────────────────────────────
from app.routers import audit, diff, admin, health

# ── SAS routers ───────────────────────────────────────────────────────────────
# Chat router (tolerates both naming conventions)
try:
    try:
        from app.routers.chat import router as chat_router
    except ImportError:
        from app.routers.chat_router import router as chat_router
    HAS_CHAT = True
except ImportError:
    HAS_CHAT = False
    chat_router = None
    print("⚠️  Chat router not found. Expected: app/routers/chat.py")

# Audit conversation router
try:
    try:
        from app.routers.audit_conversation import router as audit_conversation_router
    except ImportError:
        from app.routers.audit_conversation_router import router as audit_conversation_router
    HAS_AUDIT = True
except ImportError:
    HAS_AUDIT = False
    audit_conversation_router = None
    print("⚠️  Audit conversation router not found. Expected: app/routers/audit_conversation.py")

# Status router
try:
    from app.routers.status import router as status_router
    HAS_STATUS = True
except ImportError:
    HAS_STATUS = False
    status_router = None
    print("⚠️  Status router not found. Expected: app/routers/status.py")

# ── NEW routers (external audit + notarization) ───────────────────────────────
if settings.enable_external_audit:
    try:
        from app.routers.external_audit_router import router as external_audit_router
        HAS_EXTERNAL_AUDIT = True
    except ImportError:
        HAS_EXTERNAL_AUDIT = False
        external_audit_router = None
        print("ℹ️  External audit router not found. To enable, create app/routers/external_audit_router.py")
else:
    HAS_EXTERNAL_AUDIT = False
    external_audit_router = None
try:
    from app.routers.notarization_router import router as notarization_router
    HAS_NOTARIZATION = True
except ImportError:
    HAS_NOTARIZATION = False
    notarization_router = None
    print("ℹ️  Notarization router not found. To enable, create app/routers/notarization_router.py")

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(
    title="Omni-Scanner API + SAS",
    description=(
        "Structural hallucination detection for LLM outputs using the Durante Constant κD=0.56. "
        "Now extended with the Symbiotic Autoprotection System (SAS) standard. "
        "Validated on 156,215 real HALOGEN pairs — 97.63% precision. "
        "Registry: TAD EX-2026-18792778 | SAS DOI: 10.5281/zenodo.19689077"
    ),
    version="1.1.0",
    contact={
        "name": "Gonzalo Emir Durante",
        "url": "https://github.com/Leesintheblindmonk1999/Omni_Scanner",
        "email": "duranteg2@gmail.com",
    },
    license_info={
        "name": "GPL-3.0 + Durante Invariance License v1.0",
        "url": "https://github.com/Leesintheblindmonk1999/Omni_Scanner",
    },
)

# ── Security Headers (si existen) ────────────────────────────────────────────
if HAS_SECURITY and SecurityHeadersMiddleware:
    app.add_middleware(SecurityHeadersMiddleware)

# ── CORS ─────────────────────────────────────────────────────────────────────
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_methods=["POST", "GET"],
    allow_headers=["*"],
)

# ==============================================================================
# REGISTER ROUTERS
# ==============================================================================

# Existing core routers
app.include_router(health.router, tags=["System"])
app.include_router(audit.router, prefix="/v1", tags=["Detection"])
app.include_router(diff.router, prefix="/v1", tags=["Forensic Diff"])
app.include_router(admin.router, prefix="/admin", tags=["Admin"])

# SAS routers (these routers define prefix="/v1" internally)
if HAS_CHAT and chat_router:
    app.include_router(chat_router, tags=["Honest Chat"])

if HAS_AUDIT and audit_conversation_router:
    app.include_router(audit_conversation_router, tags=["Conversation Audit"])

if HAS_STATUS and status_router:
    app.include_router(status_router, tags=["SAS Status"])

# NEW routers
if HAS_EXTERNAL_AUDIT and external_audit_router:
    app.include_router(external_audit_router, tags=["External Audit"])

if HAS_NOTARIZATION and notarization_router:
    app.include_router(notarization_router, tags=["Notarization"])


# ==============================================================================
# ROOT AND INTEGRITY ENDPOINTS
# ==============================================================================

@app.get("/", tags=["System"])
async def root():
    return {
        "name": "Omni-Scanner API + SAS",
        "version": "1.1.0",
        "kappa_d": 0.56,
        "docs": "/docs",
        "integrity": "/integrity",
        "author": "Gonzalo Emir Durante",
        "registry": "TAD EX-2026-18792778",
        "sas_doi": "10.5281/zenodo.19689077",
    }


@app.get("/integrity", tags=["System"])
async def integrity():
    """Technical and legal provenance certificate."""
    return {
        "status": "operational",
        "kappa_d": 0.56,
        "author": "Gonzalo Emir Durante",
        "protocol": "Omni-Scanner v10.5 — SAS v1.0",
        "registry": "TAD EX-2026-18792778 (Argentina)",
        "zenodo_doi": "10.5281/zenodo.19543972",
        "sas_doi": "10.5281/zenodo.19689077",
        "ledger_hash": "5a434d7234fd55cb45829d539eee34a5ea05a3c594e26d76bb41695c46b2a996",
        "ots_date": "2026-04-11",
        "ots_chain": "Bitcoin (OpenTimestamps)",
        "license": "GPL-3.0 + Durante Invariance License v1.0",
    }
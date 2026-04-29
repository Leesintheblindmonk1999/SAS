"""
app/routers/health.py — Omni-Scanner API v1.0
System health and integrity endpoints.
"""
from fastapi import APIRouter
import platform
import sys

router = APIRouter()


@router.get("/health", summary="Health check")
async def health():
    return {"status": "ok", "kappa_d": 0.56}


@router.get("/integrity", summary="Technical and legal provenance certificate")
async def integrity():
    """
    Returns the cryptographic and legal provenance certificate for this API.

    The ledger_hash is anchored in the Bitcoin blockchain via OpenTimestamps
    (April 11, 2026) and registered under Argentine TAD EX-2026-18792778.
    This endpoint is included in every audit response — clients can verify
    independently that the results are produced by the original Omni-Scanner.
    """
    return {
        "status":       "operational",
        "kappa_d":      0.56,
        "author":       "Gonzalo Emir Durante",
        "protocol":     "Omni-Scanner v10.1 — Project Manifold 0.56",
        "registry":     "TAD EX-2026-18792778 (Argentina)",
        "zenodo_doi":   "10.5281/zenodo.19543972",
        "ledger_hash":  "5a434d7234fd55cb45829d539eee34a5ea05a3c594e26d76bb41695c46b2a996",
        "ots_date":     "2026-04-11",
        "ots_chain":    "Bitcoin (OpenTimestamps)",
        "license":      "GPL-3.0 + Durante Invariance License v1.0",
        "statement": (
            "This API implements the Durante Constant κD=0.56 for structural "
            "hallucination detection. Results are reproducible without GPU, "
            "external APIs, or internet connection."
        ),
        "runtime": {
            "python": sys.version,
            "platform": platform.system(),
        },
    }

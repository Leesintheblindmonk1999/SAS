"""
app/routers/public_demo.py — SAS Public Demo Endpoint
═══════════════════════════════════════════════════════
POST /public/demo/audit — no API key required.

Usa run_diff(text_a, text_b) — el mismo motor forense de /v1/diff.
Source = text_a (referencia ground truth)
Response = text_b (texto sospechoso a auditar)

Seguridad:
- Sin API key en frontend
- Texto completo nunca almacenado (solo len() en logs)
- IP hasheada antes de loggear
- Rate limit en memoria por IP hash (sin dependencias extra)
- Sin stack traces en respuesta
- Max 2000 chars por campo

Registry: TAD EX-2026-18792778
Author: Gonzalo Emir Durante
"""

from __future__ import annotations

import hashlib
import logging
import time
from datetime import datetime, timezone
from typing import Any

from fastapi import APIRouter, HTTPException, Request
from pydantic import BaseModel, Field

from app.config import settings

logger = logging.getLogger("sas.public_demo")

router = APIRouter()

# ==============================================================================
# CONFIG CON FALLBACKS SEGUROS
# ==============================================================================

PUBLIC_DEMO_ENABLED: bool = bool(getattr(settings, "public_demo_enabled", True))
PUBLIC_DEMO_MAX_CHARS: int = int(getattr(settings, "public_demo_max_chars", 2000))
PUBLIC_DEMO_LIMIT_PER_DAY: int = int(getattr(settings, "public_demo_limit_per_day", 25))

# Rate limit en memoria: { ip_hash: {"count": int, "date": "YYYY-MM-DD"} }
_RATE: dict[str, dict[str, Any]] = {}


# ==============================================================================
# HELPERS
# ==============================================================================


def _utc_day() -> str:
    return datetime.now(timezone.utc).date().isoformat()


def _hash_ip(ip: str) -> str:
    return hashlib.sha256(ip.encode("utf-8")).hexdigest()[:12]


def _client_ip(request: Request) -> str:
    return (
        request.headers.get("true-client-ip")
        or request.headers.get("cf-connecting-ip")
        or request.headers.get("x-forwarded-for", "").split(",")[0].strip()
        or (request.client.host if request.client else "unknown")
    )


def _check_rate(ip_hash: str) -> None:
    today = _utc_day()
    entry = _RATE.get(ip_hash)
    if entry and entry.get("date") == today:
        if int(entry.get("count", 0)) >= PUBLIC_DEMO_LIMIT_PER_DAY:
            raise HTTPException(
                status_code=429,
                detail=(
                    f"Demo limit reached ({PUBLIC_DEMO_LIMIT_PER_DAY} requests/day per IP). "
                    "Get a Free API key to continue."
                ),
            )
        entry["count"] = int(entry.get("count", 0)) + 1
    else:
        _RATE[ip_hash] = {"count": 1, "date": today}


def _to_dict(value: Any) -> dict[str, Any]:
    """
    Normaliza el resultado de run_diff a dict.
    Protege contra el caso en que el motor devuelva un objeto Pydantic
    en vez de un diccionario plano.
    """
    if isinstance(value, dict):
        return value
    if hasattr(value, "model_dump"):
        dumped = value.model_dump()
        return dumped if isinstance(dumped, dict) else {}
    if hasattr(value, "dict"):
        dumped = value.dict()
        return dumped if isinstance(dumped, dict) else {}
    return {}


def _extract_isi(raw: dict[str, Any]) -> float:
    """
    Extrae ISI del resultado de run_diff.
    run_diff devuelve manifold_score e isi (ambos = isi_final del module_state).
    """
    evidence = raw.get("evidence") if isinstance(raw.get("evidence"), dict) else {}
    candidates = [
        raw.get("isi"),
        raw.get("manifold_score"),
        evidence.get("isi_final"),
        evidence.get("isi_hard"),
        evidence.get("isi_tda"),
    ]
    for item in candidates:
        if item is not None:
            try:
                return float(item)
            except (TypeError, ValueError):
                continue
    return 0.0


def _extract_verdict(raw: dict[str, Any], isi: float) -> str:
    verdict = raw.get("verdict")
    if isinstance(verdict, str) and verdict.strip():
        return verdict.strip()
    kappa = float(getattr(settings, "kappa_d", 0.56))
    return "MANIFOLD_RUPTURE" if isi < kappa else "COHERENT"


def _extract_fired_modules(raw: dict[str, Any]) -> list[str]:
    """
    Return only modules that actually fired.

    Internal evidence fields may include diagnostic strings such as:
    '[E10] skipped: local knowledge base not configured; no penalty applied'.

    Those are useful for internal debugging, but the public demo should expose
    only modules that actually triggered.
    """
    evidence = raw.get("evidence") if isinstance(raw.get("evidence"), dict) else {}

    candidates = [
        evidence.get("fired_modules"),
        raw.get("fired_modules"),
        evidence.get("extended_modules"),
        raw.get("extended_modules"),
        evidence.get("module_notes"),
        raw.get("module_notes"),
    ]

    fired: list[str] = []

    for item in candidates:
        if not isinstance(item, list):
            continue

        for module in item:
            if isinstance(module, str):
                text = module.strip()
                lower = text.lower()

                if not text:
                    continue

                skip_markers = [
                    "skipped",
                    "not configured",
                    "no penalty applied",
                    "triggered=false",
                    '"triggered": false',
                    "'triggered': false",
                    "enabled=false",
                    '"enabled": false',
                    "'enabled': false",
                ]

                if any(marker in lower for marker in skip_markers):
                    continue

                fired.append(text)
                continue

            if isinstance(module, dict):
                if "triggered" in module and not bool(module.get("triggered")):
                    continue

                if "penalty" in module:
                    try:
                        if float(module.get("penalty", 1.0)) >= 1.0 and not bool(module.get("triggered", False)):
                            continue
                    except (TypeError, ValueError):
                        pass

                code = module.get("code")
                name = module.get("name")

                if code and name:
                    fired.append(f"{code} {name}")
                elif code:
                    fired.append(str(code))
                elif name:
                    fired.append(str(name))
                else:
                    fired.append(str(module))

    seen = set()
    clean = []

    for item in fired:
        if item not in seen:
            seen.add(item)
            clean.append(item)

    return clean


# ==============================================================================
# SCHEMAS
# ==============================================================================


class DemoRequest(BaseModel):
    source: str = Field(
        ...,
        min_length=10,
        max_length=PUBLIC_DEMO_MAX_CHARS,
        description="Source text / texto fuente (ground truth)",
    )
    response: str = Field(
        ...,
        min_length=10,
        max_length=PUBLIC_DEMO_MAX_CHARS,
        description="AI response to audit / respuesta a auditar",
    )


class DemoResponse(BaseModel):
    status: str
    isi: float
    kappa_d: float
    verdict: str
    fired_modules: list[str]
    manipulation_alert: dict[str, Any]
    latency_ms: float
    demo: bool = True


# ==============================================================================
# ENDPOINT
# ==============================================================================


@router.post(
    "/public/demo/audit",
    response_model=DemoResponse,
    tags=["Public"],
    summary="Public SAS demo audit — no API key required",
    description=(
        "Demo pública del motor forense SAS. Usa el mismo pipeline que /v1/diff: "
        "TDA H0+H1 + NIG + E9-E12 con κD=0.56. "
        "Source = texto de referencia. Response = texto a auditar. "
        "No requiere API key. Texto completo no almacenado. "
        f"Máx. {PUBLIC_DEMO_MAX_CHARS} chars por campo. "
        f"Límite: {PUBLIC_DEMO_LIMIT_PER_DAY} requests/día por IP."
    ),
)
async def public_demo_audit(payload: DemoRequest, request: Request) -> DemoResponse:
    if not PUBLIC_DEMO_ENABLED:
        raise HTTPException(status_code=404, detail="Not found")

    source = payload.source.strip()
    response = payload.response.strip()

    if len(source) < 10 or len(response) < 10:
        raise HTTPException(
            status_code=422,
            detail="Both source and response must contain at least 10 non-empty characters.",
        )

    if len(source) > PUBLIC_DEMO_MAX_CHARS or len(response) > PUBLIC_DEMO_MAX_CHARS:
        raise HTTPException(
            status_code=413,
            detail=f"Maximum length exceeded. Limit: {PUBLIC_DEMO_MAX_CHARS} characters per field.",
        )

    client_ip = _client_ip(request)
    ip_hash = _hash_ip(client_ip)
    _check_rate(ip_hash)

    t0 = time.perf_counter()

    try:
        from app.services.detector import run_diff

        raw = _to_dict(
            run_diff(
                text_a=source,       # ground truth / referencia
                text_b=response,     # texto sospechoso
                experimental=True,   # activa E9-E12
                domain="generic",
                enable_modules=None, # usa todos los configurados en settings
            )
        )

    except Exception as exc:
        logger.error(
            "public_demo_audit_failed ip_hash=%s src_len=%d res_len=%d error=%s",
            ip_hash,
            len(source),
            len(response),
            str(exc),
            exc_info=True,
        )
        raise HTTPException(
            status_code=500,
            detail="Internal analysis error. No text was stored.",
        )

    latency_ms = round((time.perf_counter() - t0) * 1000, 2)

    isi = _extract_isi(raw)
    verdict = _extract_verdict(raw, isi)
    fired_modules = _extract_fired_modules(raw)
    manipulation_alert = _extract_manipulation_alert(raw)

    logger.info(
        "public_demo ip_hash=%s src_len=%d res_len=%d isi=%.6f verdict=%s modules=%d latency_ms=%.2f",
        ip_hash,
        len(source),
        len(response),
        isi,
        verdict,
        len(fired_modules),
        latency_ms,
    )

    return DemoResponse(
        status="ok",
        isi=round(isi, 6),
        kappa_d=float(getattr(settings, "kappa_d", 0.56)),
        verdict=verdict,
        fired_modules=fired_modules,
        manipulation_alert=manipulation_alert,
        latency_ms=latency_ms,
        demo=True,
    )

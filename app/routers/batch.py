"""
app/routers/batch.py — SAS /v1/batch endpoint

Audits multiple source/response pairs in a single authenticated request.
Uses the same run_diff engine as /v1/diff internally.

Design rules:
- Requires API key explicitly via Depends(get_api_key).
- Never log source or response text.
- One item failing does not abort the rest.
- Pydantic models enforce field limits at parse time.
- All helpers are defensive — run_diff may return dict, model, or object.

Registry: TAD EX-2026-18792778
Author: Gonzalo Emir Durante
"""

from __future__ import annotations

import logging
import time
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Request
from pydantic import BaseModel, Field, field_validator

from app.config import settings
from app.dependencies import get_api_key

logger = logging.getLogger("sas.batch")

# ── Limits (configurable via settings, with safe defaults) ────────────────────

MAX_BATCH_ITEMS: int = int(getattr(settings, "batch_max_items", 20))
MAX_TEXT_CHARS: int = int(getattr(settings, "batch_max_text_chars", 5000))
KAPPA_D: float = float(getattr(settings, "kappa_d", 0.56))

# ── Router ────────────────────────────────────────────────────────────────────

router = APIRouter()

# ── Request / Response models ─────────────────────────────────────────────────


class BatchPair(BaseModel):
    source: str = Field(..., min_length=1, max_length=MAX_TEXT_CHARS)
    response: str = Field(..., min_length=1, max_length=MAX_TEXT_CHARS)


class BatchRequest(BaseModel):
    pairs: list[BatchPair] = Field(..., min_length=1)
    experimental: bool = True
    domain: str = "generic"

    @field_validator("pairs")
    @classmethod
    def validate_pairs_count(cls, v: list[BatchPair]) -> list[BatchPair]:
        if len(v) > MAX_BATCH_ITEMS:
            raise ValueError(
                f"Batch item limit exceeded. Maximum allowed: {MAX_BATCH_ITEMS}. "
                f"Received: {len(v)}."
            )
        return v


class BatchItemResult(BaseModel):
    index: int
    status: str  # "ok" | "error"
    isi: float | None = None
    kappa_d: float | None = None
    verdict: str | None = None
    fired_modules: list[str] = []
    manipulation_alert: dict[str, Any] = {}
    error: str | None = None


class BatchResponse(BaseModel):
    status: str  # "ok" | "partial_error" | "error"
    count: int
    results: list[BatchItemResult]
    batch: bool = True
    latency_ms: float


# ── Helpers ───────────────────────────────────────────────────────────────────


def _to_dict(result: Any) -> dict[str, Any]:
    """Normalize run_diff output: dict, Pydantic model, or object with .dict()/.model_dump()."""
    if isinstance(result, dict):
        return result
    if hasattr(result, "model_dump"):
        return result.model_dump()
    if hasattr(result, "dict"):
        return result.dict()
    if hasattr(result, "__dict__"):
        return vars(result)
    return {}


def _extract_isi(d: dict[str, Any]) -> float | None:
    val = d.get("isi")
    try:
        return float(val) if val is not None else None
    except (TypeError, ValueError):
        return None


def _extract_verdict(d: dict[str, Any]) -> str | None:
    val = d.get("verdict")
    return str(val) if val is not None else None


def _extract_fired_modules(d: dict[str, Any]) -> list[str]:
    raw = d.get("fired_modules") or d.get("evidence", {}).get("fired_modules", [])
    if not isinstance(raw, list):
        return []
    return [str(m) for m in raw if m is not None]


def _extract_manipulation_alert(d: dict[str, Any]) -> dict[str, Any]:
    raw = d.get("manipulation_alert")
    if not isinstance(raw, dict):
        return {"triggered": False, "sources": []}
    return {
        "triggered": bool(raw.get("triggered", False)),
        "sources": list(raw.get("sources", [])),
    }


# ── Endpoint ──────────────────────────────────────────────────────────────────


@router.post(
    "/batch",
    response_model=BatchResponse,
    summary="Batch structural audit",
    description=(
        "Audit multiple source/response pairs in a single request. "
        f"Maximum {MAX_BATCH_ITEMS} pairs per request. "
        f"Maximum {MAX_TEXT_CHARS} characters per field. "
        "Requires API key. One item failing does not abort the batch."
    ),
)
async def batch_audit(
    payload: BatchRequest,
    request: Request,
    _api_key: str = Depends(get_api_key),
) -> BatchResponse:
    request_id = getattr(request.state, "request_id", "unknown")
    pair_count = len(payload.pairs)
    total_chars = sum(len(p.source) + len(p.response) for p in payload.pairs)

    logger.info(
        "batch_start request_id=%s count=%d total_chars=%d experimental=%s domain=%s",
        request_id,
        pair_count,
        total_chars,
        payload.experimental,
        payload.domain,
    )

    # Import run_diff here to avoid startup failure if detector has a transient import issue.
    # The endpoint returns a clean 503 instead of breaking app startup.
    try:
        from app.services.detector import run_diff
    except ImportError as exc:
        logger.error("batch_detector_import_failed request_id=%s error=%s", request_id, exc)
        raise HTTPException(
            status_code=503,
            detail={
                "error": "Detector unavailable",
                "message": "The SAS detector module could not be loaded.",
                "request_id": request_id,
            },
        )

    start_time = time.time()
    results: list[BatchItemResult] = []
    error_count = 0

    for i, pair in enumerate(payload.pairs):
        try:
            raw = run_diff(
                text_a=pair.source,
                text_b=pair.response,
                experimental=payload.experimental,
                domain=payload.domain,
                enable_modules=None,
            )
            d = _to_dict(raw)

            results.append(
                BatchItemResult(
                    index=i,
                    status="ok",
                    isi=_extract_isi(d),
                    kappa_d=KAPPA_D,
                    verdict=_extract_verdict(d),
                    fired_modules=_extract_fired_modules(d),
                    manipulation_alert=_extract_manipulation_alert(d),
                )
            )

        except Exception as exc:
            error_count += 1
            logger.warning(
                "batch_item_failed request_id=%s index=%d error=%s",
                request_id,
                i,
                str(exc),
            )
            results.append(
                BatchItemResult(
                    index=i,
                    status="error",
                    error="Internal item analysis error",
                )
            )

    latency_ms = round((time.time() - start_time) * 1000, 2)

    if error_count == pair_count:
        overall_status = "error"
    elif error_count > 0:
        overall_status = "partial_error"
    else:
        overall_status = "ok"

    logger.info(
        "batch_complete request_id=%s count=%d errors=%d status=%s latency_ms=%.2f",
        request_id,
        pair_count,
        error_count,
        overall_status,
        latency_ms,
    )

    return BatchResponse(
        status=overall_status,
        count=pair_count,
        results=results,
        batch=True,
        latency_ms=latency_ms,
    )

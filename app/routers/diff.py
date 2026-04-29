"""
app/routers/diff.py — Omni-Scanner API v1.0
Two-document semantic diff endpoint — the primary forensic endpoint.
"""
from fastapi import APIRouter, Depends
from app.models.request import DiffRequest
from app.models.response import DiffResponse, EvidenceBlock
from app.services.detector import run_diff
from app.dependencies import get_api_key

router = APIRouter()


def _to_diff_response(raw: dict) -> DiffResponse:
    ev = raw.get("evidence", {})
    return DiffResponse(
        isi=raw.get("isi", 0.0),
        verdict=raw.get("verdict", "ERROR"),
        manipulation_alert=raw.get("manipulation_alert", False),
        confidence=raw.get("confidence", 0.0),
        evidence=EvidenceBlock(**ev),
        latency_ms=raw.get("latency_ms"),
    )


@router.post("/diff", response_model=DiffResponse, summary="Compare two documents")
async def diff_endpoint(
    request: DiffRequest,
    api_key: str = Depends(get_api_key),
):
    """
    Compare two documents using the TDA+NIG+v10.1 pipeline.

    text_a = reference (ground truth)
    text_b = suspect (potentially hallucinated)

    Returns ISI, verdict, and evidence block with fired modules.
    This is the primary forensic endpoint — use when you have a reference document.
    """
    raw = run_diff(
        text_a=request.text_a,
        text_b=request.text_b,
        experimental=request.experimental,
        domain=request.domain,
        enable_modules=request.enable_modules,
    )
    return _to_diff_response(raw)
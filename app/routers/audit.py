"""
app/routers/audit.py — Omni-Scanner API v1.0
Single-document structural audit endpoint.
"""
from fastapi import APIRouter, Depends
from app.models.request import AuditRequest
from app.models.response import AuditResponse, EvidenceBlock
from app.services.detector import run_audit
from app.dependencies import get_api_key

router = APIRouter()


def _to_audit_response(raw: dict) -> AuditResponse:
    ev = raw.get("evidence", {})
    return AuditResponse(
        manifold_score=raw.get("manifold_score", 0.0),
        verdict=raw.get("verdict", "ERROR"),
        confidence=raw.get("confidence", 0.0),
        manipulation_alert=raw.get("manipulation_alert", False),
        evidence=EvidenceBlock(**ev),
        latency_ms=raw.get("latency_ms"),
    )


@router.post("/audit", response_model=AuditResponse, summary="Audit a single document")
async def audit_endpoint(
    request: AuditRequest,
    api_key: str = Depends(get_api_key),
):
    """
    Audit a single text for structural integrity using the Durante Constant κD=0.56.

    Returns ISI score, verdict, and a full evidence block explaining
    which modules fired and why. Manifold score below 0.56 = structural rupture.
    """
    raw = run_audit(
        text=request.text,
        input_type=request.input_type,
        experimental=request.experimental,
        enable_modules=request.enable_modules,
    )
    return _to_audit_response(raw)
"""
app/routers/diff.py — Omni-Scanner API v1.0
Two-document semantic diff endpoint — the primary forensic endpoint.
"""
from fastapi import APIRouter, Depends, HTTPException
from app.models.request import DiffRequest
from app.models.response import DiffResponse, EvidenceBlock
from app.services.detector import run_diff
from app.dependencies import get_api_key

router = APIRouter()


def _to_diff_response(raw: dict) -> DiffResponse:
    ev = raw.get("evidence", {})
    return DiffResponse(
        manifold_score=raw.get("manifold_score", raw.get("isi", 0.0)),
        isi=raw.get("isi", raw.get("manifold_score", 0.0)),
        verdict=raw.get("verdict", "ERROR"),
        manipulation_alert=raw.get("manipulation_alert", {"triggered": False, "sources": [], "details": {}}),
        confidence=raw.get("confidence", 0.0),
        evidence=EvidenceBlock(**ev) if isinstance(ev, dict) else EvidenceBlock(),
        latency_ms=raw.get("latency_ms", 0.0),
    )


@router.post("/diff", response_model=DiffResponse, summary="Compare two documents")
async def diff_endpoint(
    request: DiffRequest,
    api_key: str = Depends(get_api_key),
):
    """
    Compare two texts and detect structural hallucinations.
    """
    result = run_diff(
        text_a=request.text_a,
        text_b=request.text_b,
        experimental=request.experimental,
        domain=request.domain
    )
    
    if result.get("verdict") == "ERROR":
        raise HTTPException(
            status_code=400, 
            detail=result.get("evidence", {}).get("error", "Unknown error")
        )
    
    return _to_diff_response(result)

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
    """Convert raw detection result to DiffResponse model."""
    ev = raw.get("evidence", {})
    if not isinstance(ev, dict):
        ev = {}
    
    # 🔧 FIX: Asegurar que manifold_score está presente
    manifold_score = raw.get("manifold_score", raw.get("isi", 0.0))
    isi = raw.get("isi", manifold_score)
    
    # 🔧 FIX: Manejar manipulation_alert correctamente
    manipulation_alert = raw.get("manipulation_alert", {})
    if not isinstance(manipulation_alert, dict):
        manipulation_alert = {"triggered": False, "sources": [], "details": {}}
    
    # Convertir manipulation_alert a un objeto ManipulationAlert si es necesario
    from app.models.response import ManipulationAlert
    if isinstance(manipulation_alert, dict):
        manipulation_alert = ManipulationAlert.from_dict(manipulation_alert)
    
    return DiffResponse(
        manifold_score=manifold_score,
        isi=isi,
        verdict=raw.get("verdict", "ERROR"),
        manipulation_alert=manipulation_alert,
        confidence=raw.get("confidence", 0.0),
        evidence=EvidenceBlock(**ev) if isinstance(ev, dict) else EvidenceBlock(),
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
    # Validar que los textos no estén vacíos
    if not request.text_a or not request.text_b:
        raise HTTPException(
            status_code=400,
            detail="Both text_a and text_b are required"
        )
    
    # 🔧 FIX: Si los textos son exactamente iguales, retornar IDENTICAL rápidamente
    if request.text_a.strip() == request.text_b.strip():
        return DiffResponse(
            manifold_score=1.0,
            isi=1.0,
            verdict="IDENTICAL",
            manipulation_alert=ManipulationAlert.from_dict({"triggered": False, "sources": [], "details": {}}),
            confidence=1.0,
            evidence=EvidenceBlock(
                isi_final=1.0,
                kappa_d=0.56,
                note="Texts are exactly identical"
            ),
            latency_ms=0.0,
        )
    
    raw = run_diff(
        text_a=request.text_a,
        text_b=request.text_b,
        experimental=request.experimental,
        domain=request.domain,
        enable_modules=request.enable_modules,
    )
    
    # 🔧 FIX: Forzar veredicto basado en manifold_score si es necesario
    KAPPA_D = 0.56
    manifold_score = raw.get("manifold_score", raw.get("isi", 1.0))
    
    if manifold_score < KAPPA_D and raw.get("verdict") != "MANIFOLD_RUPTURE":
        raw["verdict"] = "MANIFOLD_RUPTURE"
        raw["confidence"] = max(raw.get("confidence", 0.0), 0.95)
    
    return _to_diff_response(raw)

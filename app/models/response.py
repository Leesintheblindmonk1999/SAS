"""
app/models/response.py — Omni-Scanner API v1.0 + SAS v1.0
═══════════════════════════════════════════════════════════════════════════════
Response models. Existing models (EvidenceBlock, ManipulationAlert,
AuditResponse, DiffResponse) preserved. New SAS models appended.

Registry: EX-2026-18792778
Author: Gonzalo Emir Durante — Project Manifold 0.56
License: Durante Invariance License v1.0
"""

from __future__ import annotations

from typing import Any, List, Optional
from pydantic import BaseModel, Field


# ════════════════════════════════════════════════════════════════════════════
# Existing models (unchanged)
# ════════════════════════════════════════════════════════════════════════════

class EvidenceBlock(BaseModel):
    isi_final:       float
    kappa_d:         float = 0.56
    isi_tda:         float | None = None
    isi_nig:         float | None = None
    isi_hard:        float | None = None
    isi_soft:        float | None = None
    wasserstein_h1:  float | None = None
    bottleneck_h1:   float | None = None
    detected_domain: str | None = None
    effective_kappa: float | None = None
    lexical_overlap: float | None = None
    fired_modules:   list[str] = Field(default_factory=list)
    module_notes:    list[str] = Field(default_factory=list)
    extended_modules: list[dict] = Field(default_factory=list)
    module_penalty:  float | None = None
    isi_pre_modules: float | None = None
    author:          str = "Gonzalo Emir Durante"
    registry:        str = "TAD EX-2026-18792778"
    ledger_hash:     str = "5a434d7234fd55cb45829d539eee34a5ea05a3c594e26d76bb41695c46b2a996"
    zenodo_doi:      str = "10.5281/zenodo.19543972"
    error:           str | None = None
    note:            str | None = Field(None, description="Additional note (e.g., identical texts)")


class ManipulationAlertDetails(BaseModel):
    negation_probe:      dict = Field(default_factory=lambda: {"triggered": False, "not_run": True})
    arithmetic_detector: dict = Field(default_factory=lambda: {"triggered": False, "not_run": True})
    reference_check:     dict = Field(default_factory=lambda: {"triggered": False, "not_run": True})


class ManipulationAlert(BaseModel):
    triggered: bool
    sources:   list[str] = Field(default_factory=list)
    details:   ManipulationAlertDetails = Field(default_factory=ManipulationAlertDetails)

    @classmethod
    def from_dict(cls, d: dict) -> "ManipulationAlert":
        if not d:
            return cls(triggered=False, sources=[], details=ManipulationAlertDetails())
        det = d.get("details", {})
        return cls(
            triggered=d.get("triggered", False),
            sources=d.get("sources", []),
            details=ManipulationAlertDetails(
                negation_probe=det.get("negation_probe", {"triggered": False, "not_run": True}),
                arithmetic_detector=det.get("arithmetic_detector", {"triggered": False, "not_run": True}),
                reference_check=det.get("reference_check", {"triggered": False, "not_run": True}),
            ),
        )


class AuditResponse(BaseModel):
    manifold_score:     float
    verdict:            str
    confidence:         float
    manipulation_alert: ManipulationAlert
    evidence:           EvidenceBlock
    latency_ms:         float | None = None


# 🔧 FIX: DiffResponse AHORA INCLUYE manifold_score
class DiffResponse(BaseModel):
    manifold_score:     float  # ← CLAVE: añadido para que coincida con run_diff
    isi:                float
    verdict:            str
    manipulation_alert: ManipulationAlert
    confidence:         float
    evidence:           EvidenceBlock
    latency_ms:         float | None = None


# ════════════════════════════════════════════════════════════════════════════
# SAS Chat response
# ════════════════════════════════════════════════════════════════════════════

class ChatResponse(BaseModel):
    """Response from /v1/chat — includes ISI guarantee and resonance state."""
    response:           str   = Field(..., description="LLM-generated text")
    isi:                float = Field(..., description="ISI of this response [0–1]")
    verdict:            str   = Field(..., description="EQUILIBRIUM | MANIFOLD_RUPTURE | ...")
    manipulation_alert: dict  = Field(..., description="Structured manipulation alert")
    resonance:          float = Field(..., description="Session coherence state E(t)")
    filter_applied:     bool  = Field(..., description="True if response was regenerated")
    model:              str   = Field(..., description="Ollama model used")
    session_id:         str   = Field(..., description="Session identifier")
    latency_ms:         float = Field(..., description="Total latency in milliseconds")
    evidence:           dict  = Field(default_factory=dict)
    warning:            Optional[str] = Field(None, description="Non-fatal warning (e.g. filter interrupted)")
    error:              Optional[str] = Field(None, description="Error message if verdict=ERROR")


# ════════════════════════════════════════════════════════════════════════════
# SAS Conversation Audit response
# ════════════════════════════════════════════════════════════════════════════

class MessageEvidence(BaseModel):
    """Per-message audit result within a conversation."""
    index:              int
    role:               str
    isi:                Optional[float] = None
    verdict:            str
    manipulation_alert: Optional[dict]  = None
    fired_modules:      List[str]       = Field(default_factory=list)


class ConversationAuditResponse(BaseModel):
    """Notarial coherence certificate for a full conversation."""
    conversation_id:      str
    total_messages:       int
    audited_messages:     int
    isi_promedio:         float = Field(..., description="Average ISI of audited messages")
    veredicto_final:      str   = Field(..., description="ESTABLE | INESTABLE")
    mensajes_ruptura:     List[int] = Field(default_factory=list,
                              description="Indices of messages where ISI < κD")
    evidencia_por_mensaje: List[dict] = Field(default_factory=list)
    kappa_d:              float = 0.56
    author:               str   = "Gonzalo Emir Durante"
    registry:             str   = "TAD EX-2026-18792778"
    blockchain_anchor:    str   = "OpenTimestamps SHA-256"
    zenodo_doi:           str   = "10.5281/zenodo.19543972"
    certificado_sha256:   str   = Field(..., description="SHA-256 of the full audit output")


class ExternalAuditResponse(BaseModel):
    model: str
    isi: float
    sigma: float
    structural_similarity_risk: str
    disclaimer: str
    response_preview: str

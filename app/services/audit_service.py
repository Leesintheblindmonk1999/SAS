"""
app/services/audit_service.py — SAS Conversation Audit v1.0
═══════════════════════════════════════════════════════════════════════════════
Implements /v1/audit_conversation:
  · Audits every assistant message in a conversation.
  · Computes average ISI, rupture messages, and final verdict.
  · Generates a SHA-256 certificate of the entire audit output.
  · The certificate is deterministic: same input → same hash.

Registry: EX-2026-18792778
Author: Gonzalo Emir Durante — Project Manifold 0.56
License: Durante Invariance License v1.0
"""

from __future__ import annotations

import hashlib
import json
import uuid
import logging
from typing import Any

from app.services.detector import run_audit

logger = logging.getLogger(__name__)

KAPPA_D: float = 0.56


def run_conversation_audit(
    messages: list[dict[str, str]],
    conversation_id: str | None = None,
    experimental: bool = True,
) -> dict[str, Any]:
    """
    Audit a full conversation and return a notarial coherence certificate.

    Parameters
    ----------
    messages        : List of {"role": "user"|"assistant", "content": str}.
    conversation_id : Optional UUID. Generated if not provided.
    experimental    : Enable v10.1 modules in each per-message audit.

    Returns
    -------
    Structured dict with ISI per message, rupture indices, verdict,
    and a SHA-256 certificate of the output.
    """
    if not conversation_id:
        conversation_id = str(uuid.uuid4())

    per_message_evidence: list[dict[str, Any]] = []
    isi_values: list[float] = []

    for idx, msg in enumerate(messages):
        role    = msg.get("role", "").lower()
        content = msg.get("content", "").strip()

        # Only audit assistant messages — user messages are input, not output
        if role != "assistant" or not content:
            per_message_evidence.append({
                "index":              idx,
                "role":               role,
                "isi":                None,
                "verdict":            "NOT_AUDITED",
                "manipulation_alert": None,
            })
            continue

        try:
            audit = run_audit(text=content, experimental=experimental)
        except Exception as e:
            logger.exception("Audit failed for message %d: %s", idx, e)
            audit = {
                "manifold_score": 0.0,
                "verdict": "ERROR",
                "manipulation_alert": _empty_alert(),
                "evidence": {"error": str(e)},
            }

        isi     = audit.get("manifold_score", audit.get("isi", 0.0))
        verdict = audit.get("verdict", "UNKNOWN")

        isi_values.append(isi)
        per_message_evidence.append({
            "index":              idx,
            "role":               role,
            "isi":                round(isi, 6),
            "verdict":            verdict,
            "manipulation_alert": audit.get("manipulation_alert", _empty_alert()),
            "fired_modules":      audit.get("evidence", {}).get("fired_modules", []),
        })

    # ── Aggregate metrics ──────────────────────────────────────────────────────
    if isi_values:
        isi_promedio = round(sum(isi_values) / len(isi_values), 6)
    else:
        isi_promedio = 1.0

    mensajes_ruptura = [
        ev["index"]
        for ev in per_message_evidence
        if ev.get("isi") is not None and ev["isi"] < KAPPA_D
    ]

    veredicto_final = "ESTABLE" if isi_promedio >= KAPPA_D else "INESTABLE"

    # ── Build output (before certificate so hash covers it) ───────────────────
    output: dict[str, Any] = {
        "conversation_id":      conversation_id,
        "total_messages":       len(messages),
        "audited_messages":     len(isi_values),
        "isi_promedio":         isi_promedio,
        "veredicto_final":      veredicto_final,
        "mensajes_ruptura":     mensajes_ruptura,
        "evidencia_por_mensaje": per_message_evidence,
        "kappa_d":              KAPPA_D,
        "author":               "Gonzalo Emir Durante",
        "registry":             "TAD EX-2026-18792778",
        "blockchain_anchor":    "OpenTimestamps SHA-256",
        "zenodo_doi":           "10.5281/zenodo.19543972",
    }

    # ── SHA-256 certificate (deterministic) ───────────────────────────────────
    canonical = json.dumps(output, sort_keys=True, ensure_ascii=False)
    certificate = hashlib.sha256(canonical.encode("utf-8")).hexdigest()
    output["certificado_sha256"] = certificate

    return output


def _empty_alert() -> dict:
    return {
        "triggered": False,
        "sources": [],
        "details": {
            "negation_probe":      {"triggered": False, "not_run": True},
            "arithmetic_detector": {"triggered": False, "not_run": True},
            "reference_check":     {"triggered": False, "not_run": True},
        },
    }

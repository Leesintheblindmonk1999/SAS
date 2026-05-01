"""
app/routers/status.py — SAS System Status v1.0
═══════════════════════════════════════════════════════════════════════════════
GET /v1/status — returns the health state of the SAS system:
  · Whether Ollama is reachable and which models are available.
  · Active resonance sessions and their current E(t) state.
  · SAS version and κD constant.
  · v10.1 module availability (negation, reference, arithmetic, entropy).

This endpoint is read-only. It never modifies state.

Registry: EX-2026-18792778
Author: Gonzalo Emir Durante — Project Manifold 0.56
License: Durante Invariance License v1.0
"""

from __future__ import annotations

import requests
from fastapi import APIRouter

from app.config import settings

from app.services.resonance import list_sessions
from app.services.chat_service import (
    OLLAMA_URL,
    DEFAULT_MODEL,
    SAS_SYSTEM_PROMPT,
    list_sessions as list_chat_sessions,
)

router = APIRouter(prefix="/v1", tags=["SAS Status"])

KAPPA_D       = 0.56
SAS_VERSION   = "1.1.0"
OLLAMA_MODELS_URL = settings.ollama_models_url


def _check_ollama() -> dict:
    """
    Probe Ollama and return status + available models.
    Times out after 3s to keep the status endpoint fast.
    """
    try:
        resp = requests.get(OLLAMA_MODELS_URL, timeout=3)
        resp.raise_for_status()
        data   = resp.json()
        models = [m["name"] for m in data.get("models", [])]
        return {
            "reachable":      True,
            "url":            OLLAMA_URL,
            "default_model":  DEFAULT_MODEL,
            "available_models": models,
            "default_installed": DEFAULT_MODEL in models or any(
                DEFAULT_MODEL in m for m in models
            ),
        }
    except requests.exceptions.ConnectionError:
        return {
            "reachable":      False,
            "url":            OLLAMA_URL,
            "error":          "Ollama not reachable. Run: ollama serve",
        }
    except Exception as e:
        return {
            "reachable":      False,
            "url":            OLLAMA_URL,
            "error":          str(e),
        }


def _check_modules() -> dict:
    """Check which v10.1 detection modules are importable."""
    modules = {}
    for name, import_path in [
        ("negation_probe",      "core.negation_probe"),
        ("arithmetic_detector", "core.arithmetic_detector"),
        ("reference_check",     "core.reference_check"),
        ("entropy_density",     "core.entropy_density"),
        ("code_ast_diff",       "core.code_ast_diff"),
        ("nig_engine",          "core.nig_engine_v1"),
        ("tda_attestation",     "core.tda_attestation"),
    ]:
        try:
            __import__(import_path)
            modules[name] = "ok"
        except ImportError:
            modules[name] = "missing"
    return modules


@router.get("/status")
def get_status() -> dict:
    """
    Return the current health state of the SAS system.

    Checks: Ollama connectivity, available models, active sessions,
    resonance states, and v10.1 module availability.
    """
    ollama_status   = _check_ollama()
    module_status   = _check_modules()
    resonance_state = list_sessions()
    chat_sessions   = list_chat_sessions()

    # 🔧 FIX: El estado general depende del núcleo de detección (TDA), no de Ollama
    core_ok     = module_status.get("tda_attestation") == "ok"
    system_ok   = core_ok  # Ollama es opcional para el núcleo

    return {
        "status":       "ok" if system_ok else "degraded",
        "sas_version":  SAS_VERSION,
        "kappa_d":      KAPPA_D,
        "author":       "Gonzalo Emir Durante",
        "registry":     "TAD EX-2026-18792778",
        "zenodo_doi":   "10.5281/zenodo.19543972",

        "ollama":       ollama_status,
        "modules":      module_status,

        "sessions": {
            "active_resonance_sessions": len(resonance_state),
            "active_chat_sessions":      len(chat_sessions),
            "resonance_states":          resonance_state,
        },

        "identity": {
            "system_prompt_active": True,
            "system_prompt_length": len(SAS_SYSTEM_PROMPT),
            "jailbreak_patterns":   10,
            "isi_feedback_enabled": True,
            "history_cap":          40,
        },
    }


@router.get("/ping", tags=["SAS Status"])
async def ping():
    """
    Ultra-light health check for load balancers and uptime monitoring.
    Returns minimal response with κD constant.
    """
    return {"pong": True, "kappa_d": KAPPA_D}

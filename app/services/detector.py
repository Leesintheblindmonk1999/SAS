"""
app/services/detector.py — Omni-Scanner API v1.0
Core detection service. Wraps core/semantic_diff.py for API use.
"""

from __future__ import annotations

import sys
import time
import logging
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)

# Project root on sys.path
_SERVICES_DIR = Path(__file__).resolve().parent
_APP_DIR = _SERVICES_DIR.parent
_API_DIR = _APP_DIR.parent
_CORE_DIR = _API_DIR / "core"

for _p in [str(_CORE_DIR), str(_API_DIR)]:
    if _p not in sys.path:
        sys.path.insert(0, _p)

# Import core components
from core.semantic_diff import quick_diff
from core.manipulation_alert import build_manipulation_alert_from_report
from app.config import settings

# Import E9-E12 modules from app.services (they are in the same directory)
from app.services.module_result import ModuleResult
from app.services.logical_contradiction import detect as detect_logical_contradiction
from app.services.fact_grounding import detect as detect_fact_grounding
from app.services.temporal_inconsistency import detect as detect_temporal_inconsistency
from app.services.topic_shift import detect as detect_topic_shift

KAPPA_D: float = 0.56
SCAN_TIMEOUT_SECONDS: int = 15
MIN_TEXT_LENGTH: int = 30


class _TimeoutError(Exception):
    pass


def _with_timeout(fn, *args, seconds: int = SCAN_TIMEOUT_SECONDS, **kwargs):
    try:
        import signal
        if hasattr(signal, "SIGALRM"):
            def _handler(signum, frame):
                raise _TimeoutError("Scan exceeded time limit")
            signal.signal(signal.SIGALRM, _handler)
            signal.alarm(seconds)
            try:
                result = fn(*args, **kwargs)
            finally:
                signal.alarm(0)
            return result
        else:
            return fn(*args, **kwargs)
    except _TimeoutError:
        raise


# 🔧 FIX: Función para detectar textos idénticos
def _are_identical(text_a: str, text_b: str) -> bool:
    """Check if two texts are identical, ignoring whitespace and common separators."""
    if not text_a or not text_b:
        return False
    # Normalize: strip, lower, remove extra spaces
    norm_a = ' '.join(text_a.strip().lower().split())
    norm_b = ' '.join(text_b.strip().lower().split())
    return norm_a == norm_b


_MODULE_RUNNERS = {
    "E9": detect_logical_contradiction,
    "E10": detect_fact_grounding,
    "E11": detect_temporal_inconsistency,
    "E12": detect_topic_shift,
}


def _normalize_module_list(enable_modules: list[str] | None) -> list[str]:
    configured = settings.enabled_modules
    requested = [m.strip().upper() for m in enable_modules] if enable_modules else configured
    return [m for m in requested if m in _MODULE_RUNNERS]


def _run_optional_modules(text_b: str, experimental: bool, enable_modules: list[str] | None):
    if not experimental or len(text_b.strip()) < MIN_TEXT_LENGTH:
        return 1.0, [], [], []

    penalty = 1.0
    results = []
    fired = []
    notes = []

    for code in _normalize_module_list(enable_modules):
        runner = _MODULE_RUNNERS[code]
        try:
            result = runner(text_b)
        except Exception as exc:
            result = ModuleResult(
                code=code,
                name=f"{code} optional module",
                enabled=False,
                skipped=True,
                reason=f"module skipped after error: {exc}",
            )
        results.append(result.to_dict())
        if result.triggered:
            penalty *= result.penalty
            fired.append(f"{result.code} {result.name}: {result.reason} (penalty x{result.penalty:.3f})")
        elif result.skipped:
            notes.append(f"[{result.code}] skipped: {result.reason}")
    return round(penalty, 6), results, fired, notes


def _apply_module_penalty(report, text_b: str, experimental: bool, enable_modules: list[str] | None):
    base_isi = float(getattr(report, 'isi_hard', getattr(report, 'invariant_similarity_index', 0.0)))
    module_penalty, module_results, fired, notes = _run_optional_modules(text_b, experimental, enable_modules)
    final_isi = round(max(0.0, min(1.0, base_isi * module_penalty)), 6)
    verdict = report.verdict
    confidence = getattr(report, 'confidence', 0.0)
    if module_penalty < 1.0 and final_isi < KAPPA_D:
        verdict = "MANIFOLD_RUPTURE"
        confidence = max(float(confidence or 0.0), 0.75)
    return {
        "isi_pre_modules": base_isi,
        "isi_final": final_isi,
        "module_penalty": module_penalty,
        "extended_modules": module_results,
        "fired_modules": fired,
        "module_notes": notes,
        "verdict": verdict,
        "confidence": confidence,
    }


def _build_evidence(report, module_state=None):
    module_state = module_state or {}
    fired_modules = []

    if hasattr(report, 'nig_fired') and report.nig_fired:
        fired_modules.append(f"NIG: {report.nig_violations} numerical violation(s) detected")
    if hasattr(report, 'negation_inversions') and report.negation_inversions > 0:
        fired_modules.append(f"NegationProbe: {report.negation_inversions} logical inversion(s) (penalty x{report.negation_penalty:.3f})")
    if hasattr(report, 'reference_fabrications') and report.reference_fabrications > 0:
        fired_modules.append(f"ReferenceCheck: {report.reference_fabrications} fabricated citation(s)")
    if hasattr(report, 'arithmetic_errors') and report.arithmetic_errors > 0:
        fired_modules.append(f"ArithmeticDetector: {report.arithmetic_errors} arithmetic error(s)")
    if hasattr(report, 'entropy_artificial') and report.entropy_artificial:
        fired_modules.append("EntropyDensity: artificial uniformity detected")
    if hasattr(report, 'flow_fired') and report.flow_fired:
        fired_modules.append(f"FlowCoherence: {len(report.flow_spikes)} entropy spike(s)")
    if hasattr(report, 'cre_fired') and report.cre_fired:
        fired_modules.append(f"CRE/Ricci: {report.cre_ricci_singularities} singularity(ies) — {report.cre_classification}")

    return {
        "isi_tda": round(getattr(report, 'isi_tda', getattr(report, 'invariant_similarity_index', 0.0)), 6),
        "isi_nig": round(getattr(report, 'nig_isi', 1.0), 6),
        "isi_hard": round(getattr(report, 'isi_hard', getattr(report, 'invariant_similarity_index', 0.0)), 6),
        "isi_soft": round(getattr(report, 'isi_soft', 1.0), 6),
        "isi_final": round(module_state.get("isi_final", report.invariant_similarity_index), 6),
        "kappa_d": KAPPA_D,
        "wasserstein_h1": round(getattr(report, 'wasserstein_h1', 0.0), 6),
        "bottleneck_h1": round(getattr(report, 'bottleneck_h1', 0.0), 6),
        "detected_domain": getattr(report, 'detected_domain', 'generic'),
        "effective_kappa": getattr(report, 'effective_kappa', KAPPA_D),
        "lexical_overlap": round(getattr(report, 'lexical_overlap', 0.0), 4),
        "fired_modules": fired_modules + module_state.get("fired_modules", []),
        "module_notes": (getattr(report, 'experimental_notes', [])[:5] + module_state.get("module_notes", []))[:10],
        "extended_modules": module_state.get("extended_modules", []),
        "module_penalty": module_state.get("module_penalty", 1.0),
        "isi_pre_modules": module_state.get("isi_pre_modules"),
        "author": "Gonzalo Emir Durante",
        "registry": "TAD EX-2026-18792778",
        "ledger_hash": "5a434d7234fd55cb45829d539eee34a5ea05a3c594e26d76bb41695c46b2a996",
        "zenodo_doi": "10.5281/zenodo.19543972",
    }


def _run_audit_core(text: str, input_type: str, experimental: bool, enable_modules=None):
    text = text.strip()
    if len(text) < MIN_TEXT_LENGTH:
        return _error_response("Text too short for reliable structural analysis.")

    mid = len(text) // 2
    split_at = mid
    for i in range(mid, min(mid + 200, len(text))):
        if text[i] in ".!?" and i + 1 < len(text) and text[i + 1] == " ":
            split_at = i + 1
            break

    text_a = text[:split_at].strip()
    text_b = text[split_at:].strip()

    if len(text_a) < 50 or len(text_b) < 50:
        text_a = text
        text_b = text
    
    # 🔧 FIX: Si los textos son idénticos, retornar ISI = 1.0 inmediatamente
    if _are_identical(text_a, text_b):
        return {
            "manifold_score": 1.0,
            "verdict": "PERFECT_EQUILIBRIUM",
            "confidence": 1.0,
            "manipulation_alert": {"triggered": False, "sources": [], "details": {}},
            "evidence": {
                "isi_final": 1.0,
                "kappa_d": KAPPA_D,
                "note": "Texts are identical - maximum semantic invariance",
                "author": "Gonzalo Emir Durante",
                "registry": "TAD EX-2026-18792778",
                "ledger_hash": "5a434d7234fd55cb45829d539eee34a5ea05a3c594e26d76bb41695c46b2a996",
                "zenodo_doi": "10.5281/zenodo.19543972",
            }
        }

    report = quick_diff(
        text_a=text_a,
        text_b=text_b,
        kappa_d=KAPPA_D,
        experimental=experimental,
        adaptive_kappa=True,
        domain=input_type,
    )

    module_state = _apply_module_penalty(report, text_b, experimental, enable_modules)

    return {
        "manifold_score": module_state["isi_final"],
        "verdict": module_state["verdict"],
        "confidence": module_state["confidence"],
        "manipulation_alert": build_manipulation_alert_from_report(report),
        "evidence": _build_evidence(report, module_state),
    }


def run_audit(text: str, input_type: str = "generic", experimental: bool = False, enable_modules=None):
    t0 = time.perf_counter()

    if len(text.strip()) < MIN_TEXT_LENGTH:
        return _error_response("Text too short for reliable structural analysis.")

    try:
        result = _with_timeout(_run_audit_core, text, input_type, experimental, enable_modules, seconds=SCAN_TIMEOUT_SECONDS)
        result["latency_ms"] = round((time.perf_counter() - t0) * 1000, 1)
        return result
    except _TimeoutError:
        logger.warning("Audit timeout for text of length %d", len(text))
        return _error_response(f"Scan exceeded {SCAN_TIMEOUT_SECONDS}s limit.")
    except Exception as exc:
        logger.exception("Audit error: %s", exc)
        return _error_response(str(exc))


def run_diff(text_a: str, text_b: str, experimental: bool = False, domain: str = None, enable_modules=None):
    t0 = time.perf_counter()
    
    # 🔧 FIX: Si los textos son idénticos, retornar ISI = 1.0 inmediatamente
    if _are_identical(text_a, text_b):
        return {
            "isi": 1.0,
            "verdict": "PERFECT_EQUILIBRIUM",
            "manipulation_alert": {"triggered": False, "sources": [], "details": {}},
            "confidence": 1.0,
            "evidence": {
                "isi_final": 1.0,
                "kappa_d": KAPPA_D,
                "note": "Texts are identical - maximum semantic invariance",
                "author": "Gonzalo Emir Durante",
                "registry": "TAD EX-2026-18792778",
                "ledger_hash": "5a434d7234fd55cb45829d539eee34a5ea05a3c594e26d76bb41695c46b2a996",
                "zenodo_doi": "10.5281/zenodo.19543972",
            },
            "latency_ms": round((time.perf_counter() - t0) * 1000, 1),
        }

    if len(text_a.strip()) < MIN_TEXT_LENGTH or len(text_b.strip()) < MIN_TEXT_LENGTH:
        return _error_response("Both texts must be at least 30 characters.")

    try:
        report = quick_diff(
            text_a=text_a,
            text_b=text_b,
            kappa_d=KAPPA_D,
            experimental=experimental,
            adaptive_kappa=True,
            domain=domain or "generic",
        )
        module_state = _apply_module_penalty(report, text_b, experimental, enable_modules)
        result = {
            "isi": module_state["isi_final"],
            "verdict": module_state["verdict"],
            "manipulation_alert": build_manipulation_alert_from_report(report),
            "confidence": module_state["confidence"],
            "evidence": _build_evidence(report, module_state),
            "latency_ms": round((time.perf_counter() - t0) * 1000, 1),
        }
        return result
    except _TimeoutError:
        return _error_response(f"Scan exceeded {SCAN_TIMEOUT_SECONDS}s limit.")
    except Exception as exc:
        logger.exception("Diff error: %s", exc)
        return _error_response(str(exc))


def _error_response(message: str):
    return {
        "manifold_score": 0.0,
        "verdict": "ERROR",
        "confidence": 0.0,
        "isi": 0.0,
        "manipulation_alert": {"triggered": False, "sources": [], "details": {}},
        "evidence": {"isi_final": 0.0, "kappa_d": KAPPA_D, "error": message},
        "latency_ms": 0.0,
    }
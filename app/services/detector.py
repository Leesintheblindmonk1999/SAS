"""
app/services/detector.py — Omni-Scanner API v1.0
Core detection service. Wraps core/semantic_diff.py for API use.
"""

from __future__ import annotations

import sys
import time
import re
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

# Import E9-E12 modules from app.services
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
    """
    Run a scan with a best-effort timeout.

    SIGALRM only works from the main thread on Unix. TestClient, threadpool
    execution, and some ASGI/container setups may call this function outside the
    main thread. In that case, fall back to a direct call instead of raising
    `ValueError: signal only works in main thread`.
    """
    try:
        import signal
        import threading

        if hasattr(signal, "SIGALRM") and threading.current_thread() is threading.main_thread():
            def _handler(signum, frame):
                raise _TimeoutError("Scan exceeded time limit")

            previous_handler = signal.getsignal(signal.SIGALRM)
            signal.signal(signal.SIGALRM, _handler)
            signal.alarm(seconds)
            try:
                return fn(*args, **kwargs)
            finally:
                signal.alarm(0)
                signal.signal(signal.SIGALRM, previous_handler)

        return fn(*args, **kwargs)

    except _TimeoutError:
        raise


def _are_identical(text_a: str, text_b: str) -> bool:
    """Check if two texts are identical, ignoring whitespace and common separators."""
    if not text_a or not text_b:
        return False

    norm_a = " ".join(text_a.strip().lower().split())
    norm_b = " ".join(text_b.strip().lower().split())
    return norm_a == norm_b


# ==============================================================================
# SOURCE-TARGET INVARIANCE GUARD
# ==============================================================================

_ENTITY_STOPWORDS = {
    "The",
    "A",
    "An",
    "It",
    "This",
    "That",
    "These",
    "Those",
    "In",
    "On",
    "At",
    "For",
    "From",
    "By",
    "Of",
    "And",
    "Or",
    "But",
    "If",
    "Then",
    "When",
    "While",
    "After",
    "Before",
}


def _normalize_entity(entity: str) -> str:
    entity = " ".join(entity.strip().split())

    for prefix in ("The ", "A ", "An "):
        if entity.startswith(prefix):
            entity = entity[len(prefix):]

    return entity.strip()


def _extract_years(text: str) -> set[str]:
    return set(re.findall(r"\b(?:1[0-9]{3}|20[0-9]{2}|21[0-9]{2})\b", text or ""))


def _extract_numbers(text: str) -> set[str]:
    return set(re.findall(r"\b\d+(?:[.,]\d+)?\b", text or ""))


def _extract_capitalized_entities(text: str) -> set[str]:
    """
    Lightweight source-target entity extractor.

    It catches proper names and locations such as:
    - Eiffel Tower
    - Paris
    - France
    - Berlin
    - Germany

    It intentionally avoids storing text and only returns normalized surface spans.
    """
    if not text:
        return set()

    pattern = r"\b(?:[A-Z][a-z]+(?:\s+[A-Z][a-z]+){0,4})\b"
    raw_entities = re.findall(pattern, text)

    entities: set[str] = set()

    for raw in raw_entities:
        ent = _normalize_entity(raw)
        if not ent:
            continue

        first = ent.split()[0]
        if first in _ENTITY_STOPWORDS:
            continue

        if ent in _ENTITY_STOPWORDS:
            continue

        entities.add(ent)

    return entities


def _source_target_invariance_guard(text_a: str, text_b: str) -> dict[str, Any]:
    """
    Detect source-target factual slot mutations.

    This guard is deliberately conservative:
    - It does not claim external truth.
    - It only checks whether critical anchors present in source changed in target.
    - It is useful when topology is similar but factual slots are mutated.
    """
    years_a = _extract_years(text_a)
    years_b = _extract_years(text_b)

    nums_a = _extract_numbers(text_a)
    nums_b = _extract_numbers(text_b)

    ents_a = _extract_capitalized_entities(text_a)
    ents_b = _extract_capitalized_entities(text_b)

    shared_entities = ents_a & ents_b
    removed_entities = ents_a - ents_b
    added_entities = ents_b - ents_a

    year_mismatch = bool(years_a and years_b and years_a != years_b)
    numeric_mismatch = bool(nums_a and nums_b and nums_a != nums_b)

    # Strong case:
    # source and target share an anchor but replace surrounding factual entities.
    # Example:
    # shared = {"Eiffel Tower"}
    # removed = {"Paris", "France"}
    # added = {"Berlin", "Germany"}
    anchored_entity_shift = bool(shared_entities and removed_entities and added_entities)

    reasons: list[str] = []

    if year_mismatch:
        reasons.append(
            "year mismatch: "
            + ", ".join(sorted(years_a))
            + " -> "
            + ", ".join(sorted(years_b))
        )

    if anchored_entity_shift:
        reasons.append(
            "anchored entity/location shift: removed "
            + ", ".join(sorted(removed_entities))
            + "; added "
            + ", ".join(sorted(added_entities))
        )

    elif numeric_mismatch:
        reasons.append(
            "numeric mismatch: "
            + ", ".join(sorted(nums_a))
            + " -> "
            + ", ".join(sorted(nums_b))
        )

    triggered = bool(reasons)

    if year_mismatch and anchored_entity_shift:
        guard_isi = 0.25
        penalty = 0.25
    elif year_mismatch:
        guard_isi = 0.45
        penalty = 0.45
    elif anchored_entity_shift:
        guard_isi = 0.50
        penalty = 0.50
    elif numeric_mismatch:
        guard_isi = 0.50
        penalty = 0.50
    else:
        guard_isi = 1.0
        penalty = 1.0

    return {
        "triggered": triggered,
        "isi": guard_isi,
        "penalty": penalty,
        "reasons": reasons,
        "evidence": {
            "years_source": sorted(years_a),
            "years_target": sorted(years_b),
            "numbers_source": sorted(nums_a),
            "numbers_target": sorted(nums_b),
            "entities_source": sorted(ents_a),
            "entities_target": sorted(ents_b),
            "shared_entities": sorted(shared_entities),
            "removed_entities": sorted(removed_entities),
            "added_entities": sorted(added_entities),
        },
    }


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


def _run_optional_modules(
    text_b: str,
    experimental: bool,
    enable_modules: list[str] | None,
):
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
            fired.append(
                f"{result.code} {result.name}: {result.reason} "
                f"(penalty x{result.penalty:.3f})"
            )
        elif result.skipped:
            notes.append(f"[{result.code}] skipped: {result.reason}")

    return round(penalty, 6), results, fired, notes


def _apply_module_penalty(
    report,
    text_a: str,
    text_b: str,
    experimental: bool,
    enable_modules: list[str] | None,
):
    base_isi = float(
        getattr(
            report,
            "isi_hard",
            getattr(report, "invariant_similarity_index", 0.0),
        )
    )

    module_penalty, module_results, fired, notes = _run_optional_modules(
        text_b,
        experimental,
        enable_modules,
    )

    source_target_guard = _source_target_invariance_guard(text_a, text_b)

    module_isi = round(max(0.0, min(1.0, base_isi * module_penalty)), 6)
    final_isi = module_isi

    if source_target_guard["triggered"]:
        final_isi = min(final_isi, float(source_target_guard["isi"]))
        fired.append(
            "SourceTargetGuard: "
            + "; ".join(source_target_guard["reasons"])
            + f" (guard ISI={source_target_guard['isi']:.3f})"
        )

    final_isi = round(max(0.0, min(1.0, final_isi)), 6)

    verdict = report.verdict
    confidence = getattr(report, "confidence", 0.0)

    if final_isi < KAPPA_D:
        verdict = "MANIFOLD_RUPTURE"
        confidence = max(float(confidence or 0.0), 0.85)

    return {
        "isi_pre_modules": base_isi,
        "isi_final": final_isi,
        "module_penalty": module_penalty,
        "source_target_guard": source_target_guard,
        "extended_modules": module_results,
        "fired_modules": fired,
        "module_notes": notes,
        "verdict": verdict,
        "confidence": confidence,
    }


def _build_evidence(report, module_state=None):
    module_state = module_state or {}
    fired_modules = []

    if hasattr(report, "nig_fired") and report.nig_fired:
        fired_modules.append(f"NIG: {report.nig_violations} numerical violation(s) detected")

    if hasattr(report, "negation_inversions") and report.negation_inversions > 0:
        fired_modules.append(
            f"NegationProbe: {report.negation_inversions} logical inversion(s) "
            f"(penalty x{report.negation_penalty:.3f})"
        )

    if hasattr(report, "reference_fabrications") and report.reference_fabrications > 0:
        fired_modules.append(
            f"ReferenceCheck: {report.reference_fabrications} fabricated citation(s)"
        )

    if hasattr(report, "arithmetic_errors") and report.arithmetic_errors > 0:
        fired_modules.append(
            f"ArithmeticDetector: {report.arithmetic_errors} arithmetic error(s)"
        )

    if hasattr(report, "entropy_artificial") and report.entropy_artificial:
        fired_modules.append("EntropyDensity: artificial uniformity detected")

    if hasattr(report, "flow_fired") and report.flow_fired:
        fired_modules.append(f"FlowCoherence: {len(report.flow_spikes)} entropy spike(s)")

    if hasattr(report, "cre_fired") and report.cre_fired:
        fired_modules.append(
            f"CRE/Ricci: {report.cre_ricci_singularities} singularity(ies) "
            f"— {report.cre_classification}"
        )

    return {
        "isi_tda": round(
            getattr(report, "isi_tda", getattr(report, "invariant_similarity_index", 0.0)),
            6,
        ),
        "isi_nig": round(getattr(report, "nig_isi", 1.0), 6),
        "isi_hard": round(
            getattr(report, "isi_hard", getattr(report, "invariant_similarity_index", 0.0)),
            6,
        ),
        "isi_soft": round(getattr(report, "isi_soft", 1.0), 6),
        "isi_final": round(module_state.get("isi_final", report.invariant_similarity_index), 6),
        "kappa_d": KAPPA_D,
        "wasserstein_h1": round(getattr(report, "wasserstein_h1", 0.0), 6),
        "bottleneck_h1": round(getattr(report, "bottleneck_h1", 0.0), 6),
        "detected_domain": getattr(report, "detected_domain", "generic"),
        "effective_kappa": getattr(report, "effective_kappa", KAPPA_D),
        "lexical_overlap": round(getattr(report, "lexical_overlap", 0.0), 4),
        "fired_modules": fired_modules + module_state.get("fired_modules", []),
        "module_notes": (
            getattr(report, "experimental_notes", [])[:5]
            + module_state.get("module_notes", [])
        )[:10],
        "extended_modules": module_state.get("extended_modules", []),
        "module_penalty": module_state.get("module_penalty", 1.0),
        "isi_pre_modules": module_state.get("isi_pre_modules"),
        "source_target_guard": module_state.get("source_target_guard"),
        "author": "Gonzalo Emir Durante",
        "registry": "TAD EX-2026-18792778",
        "ledger_hash": "5a434d7234fd55cb45829d539eee34a5ea05a3c594e26d76bb41695c46b2a996",
        "zenodo_doi": "10.5281/zenodo.19543972",
    }


def _run_audit_core(
    text: str,
    input_type: str,
    experimental: bool,
    enable_modules=None,
):
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

    if _are_identical(text_a, text_b):
        return {
            "manifold_score": 1.0,
            "verdict": "PERFECT_EQUILIBRIUM",
            "confidence": 1.0,
            "manipulation_alert": {
                "triggered": False,
                "sources": [],
                "details": {},
            },
            "evidence": {
                "isi_final": 1.0,
                "kappa_d": KAPPA_D,
                "note": "Texts are identical - maximum semantic invariance",
                "author": "Gonzalo Emir Durante",
                "registry": "TAD EX-2026-18792778",
                "ledger_hash": "5a434d7234fd55cb45829d539eee34a5ea05a3c594e26d76bb41695c46b2a996",
                "zenodo_doi": "10.5281/zenodo.19543972",
            },
        }

    report = quick_diff(
        text_a=text_a,
        text_b=text_b,
        kappa_d=KAPPA_D,
        experimental=experimental,
        adaptive_kappa=True,
        domain=input_type,
    )

    module_state = _apply_module_penalty(
        report,
        text_a,
        text_b,
        experimental,
        enable_modules,
    )

    return {
        "manifold_score": module_state["isi_final"],
        "verdict": module_state["verdict"],
        "confidence": module_state["confidence"],
        "manipulation_alert": build_manipulation_alert_from_report(report),
        "evidence": _build_evidence(report, module_state),
    }


def run_audit(
    text: str,
    input_type: str = "generic",
    experimental: bool = False,
    enable_modules=None,
):
    t0 = time.perf_counter()

    if len(text.strip()) < MIN_TEXT_LENGTH:
        return _error_response("Text too short for reliable structural analysis.")

    try:
        result = _with_timeout(
            _run_audit_core,
            text,
            input_type,
            experimental,
            enable_modules,
            seconds=SCAN_TIMEOUT_SECONDS,
        )
        result["latency_ms"] = round((time.perf_counter() - t0) * 1000, 1)
        return result

    except _TimeoutError:
        logger.warning("Audit timeout for text of length %d", len(text))
        return _error_response(f"Scan exceeded {SCAN_TIMEOUT_SECONDS}s limit.")

    except Exception as exc:
        logger.exception("Audit error: %s", exc)
        return _error_response(str(exc))


def run_diff(
    text_a: str,
    text_b: str,
    experimental: bool = False,
    domain: str = None,
    enable_modules=None,
):
    t0 = time.perf_counter()

    if _are_identical(text_a, text_b):
        return {
            "manifold_score": 1.0,
            "isi": 1.0,
            "verdict": "PERFECT_EQUILIBRIUM",
            "manipulation_alert": {
                "triggered": False,
                "sources": [],
                "details": {},
            },
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

        module_state = _apply_module_penalty(
            report,
            text_a,
            text_b,
            experimental,
            enable_modules,
        )

        result = {
            "manifold_score": module_state["isi_final"],
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
        "manipulation_alert": {
            "triggered": False,
            "sources": [],
            "details": {},
        },
        "evidence": {
            "isi_final": 0.0,
            "kappa_d": KAPPA_D,
            "error": message,
        },
        "latency_ms": 0.0,
    }

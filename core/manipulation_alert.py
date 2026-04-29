"""
core/manipulation_alert.py — Manipulation Alert Aggregator v1.0
═══════════════════════════════════════════════════════════════════════════════
Builds the structured manipulation_alert object for the SAS API.

This module is a pure aggregation layer. It does not perform any detection.
It consumes result objects already produced by:
  · negation_probe.py   → NegationResult
  · arithmetic_detector.py → ArithmeticResult
  · reference_check.py  → ReferenceResult

Activation thresholds (by design):
  · negation_probe:     inversion_count >= 1
  · arithmetic_detector: error_count >= 1
  · reference_check:    fabricated_count >= 1
                        (anachronistic_count alone does NOT trigger alert —
                         anachronistic years may be typos, not manipulation)

Compatibility:
  · legacy_mode=True returns a plain bool (drop-in for old consumers).
  · Default is legacy_mode=False (structured object).

Registry: EX-2026-18792778
Author: Gonzalo Emir Durante — Project Manifold 0.56
License: Durante Invariance License v1.0
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional, Union

# ── Type aliases ───────────────────────────────────────────────────────────────
# These mirror the real dataclasses without importing them, so this module
# can be used even when the core detectors are not installed.
# When core modules ARE installed, pass their result objects directly —
# duck typing ensures compatibility.

ManipulationAlertDict = Dict[str, Any]


# ── Threshold constants ────────────────────────────────────────────────────────

_NEGATION_THRESHOLD: int   = 1   # inversion_count >= this → triggered
_ARITHMETIC_THRESHOLD: int = 1   # error_count >= this     → triggered
_REFERENCE_THRESHOLD: int  = 1   # fabricated_count >= this → triggered
                                  # anachronistic_count is intentionally ignored


# ── Core builder ───────────────────────────────────────────────────────────────

def build_manipulation_alert(
    negation_result=None,    # NegationResult | None
    arithmetic_result=None,  # ArithmeticResult | None
    reference_result=None,   # ReferenceResult | None
    legacy_mode: bool = False,
) -> Union[ManipulationAlertDict, bool]:
    """
    Build the structured manipulation_alert object.

    Parameters
    ----------
    negation_result : NegationResult or None
        Output of detect_inversions(). If None, this source is treated as
        not run (not as "no inversions found").
    arithmetic_result : ArithmeticResult or None
        Output of detect_arithmetic_errors(). Same None semantics.
    reference_result : ReferenceResult or None
        Output of detect_fabrications(). Same None semantics.
    legacy_mode : bool
        If True, return a plain bool for backward compatibility with code
        that consumed manipulation_alert as a boolean field.

    Returns
    -------
    dict | bool
        Structured alert object, or plain bool if legacy_mode=True.

    Notes
    -----
    A result being None means the module was not executed (e.g. the module
    is not installed, or experimental=False). This is explicitly represented
    in the output as {"triggered": false, "not_run": true} so consumers can
    distinguish "not run" from "ran and found nothing".
    """

    # ── Negation probe ────────────────────────────────────────────────────────
    if negation_result is None:
        neg_block: Dict[str, Any] = {"triggered": False, "not_run": True}
        neg_triggered = False
    else:
        inv_count = getattr(negation_result, "inversion_count", 0)
        neg_triggered = inv_count >= _NEGATION_THRESHOLD
        neg_block = {
            "triggered":               neg_triggered,
            "inversion_count":         inv_count,
            "polarity_inverted":       getattr(negation_result, "polarity_inverted", False),
            "quantifier_changed":      getattr(negation_result, "quantifier_changed", False),
            "weighted_inversion_score": round(
                getattr(negation_result, "weighted_inversion_score", 0.0), 4
            ),
        }

    # ── Arithmetic detector ───────────────────────────────────────────────────
    if arithmetic_result is None:
        arith_block: Dict[str, Any] = {"triggered": False, "not_run": True}
        arith_triggered = False
    else:
        err_count = getattr(arithmetic_result, "error_count", 0)
        arith_triggered = err_count >= _ARITHMETIC_THRESHOLD
        errors_raw = getattr(arithmetic_result, "errors", [])
        arith_block = {
            "triggered":   arith_triggered,
            "error_count": err_count,
            "errors": [
                {
                    "text":        getattr(e, "matched_text", str(e)),
                    "description": getattr(e, "description", ""),
                }
                for e in errors_raw[:5]   # cap at 5 for API response size
            ],
        }

    # ── Reference check ───────────────────────────────────────────────────────
    if reference_result is None:
        ref_block: Dict[str, Any] = {"triggered": False, "not_run": True}
        ref_triggered = False
    else:
        fab_count     = getattr(reference_result, "fabricated_count", 0)
        anachron_count = getattr(reference_result, "anachronistic_count", 0)
        ref_triggered = fab_count >= _REFERENCE_THRESHOLD
        ref_block = {
            "triggered":           ref_triggered,
            "fabricated_count":    fab_count,
            "anachronistic_count": anachron_count,
            # Anachronistic events are reported for transparency but do NOT
            # trigger the alert — they may be typographical errors, not
            # deliberate manipulation.
        }

    # ── Aggregate ─────────────────────────────────────────────────────────────
    triggered_sources: List[str] = []
    if neg_triggered:
        triggered_sources.append("negation_probe")
    if arith_triggered:
        triggered_sources.append("arithmetic_detector")
    if ref_triggered:
        triggered_sources.append("reference_check")

    global_triggered = len(triggered_sources) > 0

    if legacy_mode:
        return global_triggered

    return {
        "triggered": global_triggered,
        "sources":   triggered_sources,
        "details": {
            "negation_probe":      neg_block,
            "arithmetic_detector": arith_block,
            "reference_check":     ref_block,
        },
    }


# ── Convenience builder from SemanticDiffReport ────────────────────────────────

def build_manipulation_alert_from_report(
    report,
    negation_result=None,
    arithmetic_result=None,
    reference_result=None,
    legacy_mode: bool = False,
) -> Union[ManipulationAlertDict, bool]:
    """
    Convenience wrapper for callers that have a SemanticDiffReport but may
    not have stored the individual result objects.

    If result objects are None, falls back to reading scalar fields from the
    report (negation_inversions, arithmetic_errors, reference_fabrications).
    This ensures backward compatibility even without passing full result objects.
    """

    # Reconstruct minimal proxy objects from report scalars if needed
    class _NegProxy:
        def __init__(self, r):
            self.inversion_count          = getattr(r, "negation_inversions", 0)
            self.polarity_inverted        = self.inversion_count > 0
            self.quantifier_changed       = False
            self.weighted_inversion_score = float(self.inversion_count)

    class _ArithProxy:
        def __init__(self, r):
            self.error_count = getattr(r, "arithmetic_errors", 0)
            self.errors      = []

    class _RefProxy:
        def __init__(self, r):
            self.fabricated_count    = getattr(r, "reference_fabrications", 0)
            self.anachronistic_count = 0

    neg  = negation_result   or (_NegProxy(report)  if report is not None else None)
    arith = arithmetic_result or (_ArithProxy(report) if report is not None else None)
    ref  = reference_result  or (_RefProxy(report)  if report is not None else None)

    return build_manipulation_alert(
        negation_result=neg,
        arithmetic_result=arith,
        reference_result=ref,
        legacy_mode=legacy_mode,
    )

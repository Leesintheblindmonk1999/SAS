"""Smoke tests for interaction_stability service — v1.2.1-mvp.

Tests T0/T0.5: service-level validation without FastAPI.
Requires ENABLE_INTERACTION_STABILITY=true (set via autouse fixture below).
"""
from __future__ import annotations

import os
import pytest

from app.services.interaction_stability import (
    analyze_conversation,
    example_conversation,
    classify_user_action,
    UserAction,
    validate_params,
    demand_driven_transition,
    _contains_keyword,
)
import numpy as np


# ── Feature flag fixture ───────────────────────────────────────────────────────

@pytest.fixture(autouse=True)
def enable_interaction_stability():
    """Enable the feature flag for all tests in this module."""
    os.environ["ENABLE_INTERACTION_STABILITY"] = "true"
    yield
    os.environ.pop("ENABLE_INTERACTION_STABILITY", None)


# ── Helpers ───────────────────────────────────────────────────────────────────

def assert_between(value, lo=0.0, hi=1.0):
    assert lo <= value <= hi, f"{value} not in [{lo}, {hi}]"


# ── T0: Core fields and v1.2.1-mvp structure ─────────────────────────────────

def test_example_conversation_status_and_version():
    result = analyze_conversation(example_conversation())
    assert result.status == "completed"
    assert result.model_version == "interaction-stability-v1.2.1-mvp"
    assert result.theory_doi == "10.5281/zenodo.20335612"
    assert result.theory_reference == "stochastic_interaction_v1.2.0"


def test_example_conversation_trajectory_fields():
    result = analyze_conversation(example_conversation())
    assert len(result.trajectory) > 0
    for step in result.trajectory:
        assert "dominant_state" in step
        assert "dominant_probability" in step
        assert "omega_t" in step
        assert "belief_coherence_chi" in step
        assert "interaction_stability_sigma" in step
        assert "effective_window" in step
        assert "alerts" in step
        assert_between(step["omega_t"])
        assert_between(step["belief_coherence_chi"])
        assert_between(step["interaction_stability_sigma"])
        assert step["omega_t"] == step["belief_coherence_chi"]  # alias check


def test_example_conversation_summary_fields():
    result = analyze_conversation(example_conversation())
    summary = result.summary
    assert "threshold_note" in summary
    assert "conjecture_note" in summary
    assert "demand_model" in summary
    assert summary["demand_model"]["normalized"] is True
    assert "phi" in summary["demand_model"]
    assert "omega_note" in summary
    assert "chi_note" in summary
    assert "sigma_note" in summary
    assert "caution" in summary
    assert "interpretation" in summary


def test_example_conversation_traceability_fields():
    """C3: request_id, executed_at, input_hash, content_fingerprint present."""
    result = analyze_conversation(example_conversation())
    assert result.request_id and len(result.request_id) == 36  # UUID4
    assert result.executed_at and "T" in result.executed_at    # ISO 8601
    assert result.input_hash and len(result.input_hash) == 16
    assert result.content_fingerprint and len(result.content_fingerprint) == 16
    assert result.input_hash != result.content_fingerprint


def test_content_fingerprint_is_content_sensitive():
    """C3: Different content → different fingerprint."""
    conv_a = [
        {"role": "user", "content": "urgente ya"},
        {"role": "assistant", "content": "procesado"},
    ]
    conv_b = [
        {"role": "user", "content": "ok gracias"},
        {"role": "assistant", "content": "procesado"},
    ]
    r_a = analyze_conversation(conv_a)
    r_b = analyze_conversation(conv_b)
    assert r_a.content_fingerprint != r_b.content_fingerprint


def test_content_fingerprint_is_deterministic():
    """C3: Same content → same fingerprint across calls."""
    conv = [
        {"role": "user", "content": "urgente ya"},
        {"role": "assistant", "content": "procesado"},
    ]
    r1 = analyze_conversation(conv)
    r2 = analyze_conversation(conv)
    assert r1.content_fingerprint == r2.content_fingerprint


def test_skipped_turns_top_level():
    """D5: skipped_turns is a top-level field, not buried in summary."""
    conv = [
        {"role": "system", "content": "You are helpful."},
        {"role": "user", "content": "ok"},
        {"role": "assistant", "content": "procesado"},
    ]
    result = analyze_conversation(conv)
    assert hasattr(result, "skipped_turns")
    assert len(result.skipped_turns) == 1
    assert result.skipped_turns[0]["role"] == "system"


def test_effective_window_per_step():
    """D4: effective_window reflects actual steps used, not requested window."""
    conv = [
        {"role": "user", "content": "ok"},
        {"role": "assistant", "content": "procesado"},
    ]
    result = analyze_conversation(conv, window=10)
    assert result.trajectory[0]["effective_window"] == 1


# ── T0: C1 — consecutive turn contamination fix ───────────────────────────────

def test_consecutive_assistant_turns_no_action_contamination():
    """C1: Second assistant turn without user turn must get user_action=N."""
    conv = [
        {"role": "user", "content": "urgente, ya"},
        {"role": "assistant", "content": "Entendido."},
        {"role": "assistant", "content": "Lo proceso ahora."},
    ]
    result = analyze_conversation(conv)
    assert len(result.trajectory) == 2
    assert result.trajectory[0]["user_action"] == "Rc"
    assert result.trajectory[1]["user_action"] == "N"


def test_consecutive_user_turns_last_action_used():
    """C1: Two user turns before assistant — last user action applies."""
    conv = [
        {"role": "user", "content": "ok gracias"},
        {"role": "user", "content": "urgente ya"},
        {"role": "assistant", "content": "procesado"},
    ]
    result = analyze_conversation(conv)
    assert result.trajectory[0]["user_action"] == "Rc"


# ── T0: D1 — word-boundary keyword matching ───────────────────────────────────

def test_word_boundary_no_substring_match():
    """D1: 'noturgente' must not match keyword 'urgente'."""
    action = classify_user_action("noturgente")
    assert action != UserAction.Rc


def test_word_boundary_whole_word_matches():
    """D1: 'urgente' as a standalone word must match Rc."""
    assert classify_user_action("urgente") == UserAction.Rc
    assert classify_user_action("esto es urgente") == UserAction.Rc


def test_contains_keyword_boundary():
    assert _contains_keyword("urgente", "urgente") is True
    assert _contains_keyword("noturgente", "urgente") is False
    assert _contains_keyword("urgente ahora", "urgente") is True


# ── T0: D2 — alpha cap ────────────────────────────────────────────────────────

def test_alpha_above_max_raises():
    """D2: alpha > 20.0 must be rejected by validate_params."""
    with pytest.raises(ValueError, match="alpha must be <= 20.0"):
        validate_params(0.85, 4, 0.56, 25.0, example_conversation())


def test_alpha_at_max_accepted():
    """D2: alpha == 20.0 must be accepted."""
    validate_params(0.85, 4, 0.56, 20.0, example_conversation())  # no exception


# ── T0: C2 — transition matrix rows sum to 1.0 ───────────────────────────────

def test_transition_matrix_rows_sum_to_one():
    """C2: All transition matrix rows must sum to 1.0 for any demand value."""
    for demand in [0.0, 0.25, 0.5, 0.75, 1.0]:
        t = demand_driven_transition(demand)
        row_sums = t.sum(axis=1)
        assert np.allclose(row_sums, 1.0, atol=1e-9), (
            f"Row sums not 1.0 at demand={demand}: {row_sums}"
        )


# ── T0: Validation error cases ────────────────────────────────────────────────

def test_empty_conversation_raises():
    with pytest.raises(ValueError):
        analyze_conversation([])


def test_conversation_without_assistant_raises():
    with pytest.raises(ValueError):
        analyze_conversation([{"role": "user", "content": "hello"}])


def test_feature_flag_off_raises_runtime_error():
    """C4: Disabled flag must raise RuntimeError, not silently succeed."""
    os.environ["ENABLE_INTERACTION_STABILITY"] = "false"
    with pytest.raises(RuntimeError, match="disabled"):
        analyze_conversation(example_conversation())
    os.environ["ENABLE_INTERACTION_STABILITY"] = "true"  # restore for fixture


def test_mode_estimate_raises_not_implemented():
    with pytest.raises(NotImplementedError):
        analyze_conversation(example_conversation(), mode="estimate")


def test_mode_invalid_raises_value_error():
    with pytest.raises(ValueError):
        analyze_conversation(example_conversation(), mode="invalid_mode")

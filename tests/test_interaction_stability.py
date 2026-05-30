"""Smoke tests for interaction_stability.py.

Optional service-level tests for the T0/T0.5 MVP.
"""

from __future__ import annotations

import pytest

from app.services.interaction_stability import analyze_conversation, example_conversation


def assert_between(value, lo=0.0, hi=1.0):
    assert lo <= value <= hi, f"{value} not in [{lo}, {hi}]"


def test_example_conversation_analysis_v120_fields():
    result = analyze_conversation(example_conversation())

    assert result.status == "completed"
    assert result.model_version.startswith("interaction-stability-v1.2.0")
    assert result.theory_doi
    assert result.trajectory

    for step in result.trajectory:
        assert "dominant_state" in step
        assert "dominant_probability" in step
        assert "omega_t" in step
        assert "belief_coherence_chi" in step
        assert "interaction_stability_sigma" in step
        assert_between(step["omega_t"])
        assert_between(step["belief_coherence_chi"])
        assert_between(step["interaction_stability_sigma"])

    assert "threshold_note" in result.summary
    assert "conjecture_note" in result.summary
    assert "demand_model" in result.summary
    assert result.summary["demand_model"]["normalized"] is True


def test_empty_conversation_fails():
    with pytest.raises(ValueError):
        analyze_conversation([])


def test_conversation_without_assistant_fails():
    with pytest.raises(ValueError):
        analyze_conversation([{"role": "user", "content": "hello"}])

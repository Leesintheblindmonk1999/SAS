"""
tests/test_interaction_stability.py

Optional smoke coverage for app.services.interaction_stability.

This module is skipped automatically when interaction_stability is not present
in the current checkout, so it does not block the F1 test suite.
"""

from __future__ import annotations

import pytest

interaction_stability = pytest.importorskip("app.services.interaction_stability")

analyze_conversation = interaction_stability.analyze_conversation
example_conversation = interaction_stability.example_conversation


def assert_between(value, lo=0.0, hi=1.0):
    assert lo <= value <= hi, f"{value} not in [{lo}, {hi}]"


def test_example_conversation_analysis_is_bounded():
    result = analyze_conversation(example_conversation())

    assert result.status
    assert result.model_version
    assert result.summary
    assert result.trajectory

    for step in result.trajectory:
        assert "dominant_state" in step
        assert "dominant_probability" in step
        assert_between(step["belief_coherence_chi"])
        assert_between(step["interaction_stability_sigma"])


def test_empty_conversation_fails():
    with pytest.raises(ValueError):
        analyze_conversation([])


def test_conversation_without_assistant_fails():
    with pytest.raises(ValueError):
        analyze_conversation([{"role": "user", "content": "hello"}])

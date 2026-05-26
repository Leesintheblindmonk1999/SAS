"""
tests/test_batch.py — /v1/batch endpoint tests.

Auth strategy:
- Auth-negative tests use client (no key) and accept 401/422 depending on auth layer.
- Tests that expect 200 use monkeypatched auth via authed_client fixture.
- run_diff is always mocked — detector.py is never imported in these tests.

All assertions use stable fields (status_code, batch, count, index, verdict)
rather than exact wording that may change.
"""

from __future__ import annotations

import pytest
from fastapi.testclient import TestClient


# ── Payloads ──────────────────────────────────────────────────────────────────

PAIR_EIFFEL = {
    "source": "The Eiffel Tower is located in Paris, France, and was built in 1889.",
    "response": "The Eiffel Tower is located in Berlin, Germany, and was built in 1950.",
}

PAIR_WATER = {
    "source": "Water boils at 100 degrees Celsius at sea level.",
    "response": "Water boils at 100 degrees Celsius at sea level.",
}

TWO_PAIR_PAYLOAD = {
    "pairs": [PAIR_EIFFEL, PAIR_WATER],
    "experimental": True,
    "domain": "generic",
}


# ── Auth tests ────────────────────────────────────────────────────────────────


def test_batch_without_api_key_returns_401(client: TestClient) -> None:
    """POST /v1/batch without X-API-Key must not execute anonymously."""
    response = client.post("/v1/batch", json=TWO_PAIR_PAYLOAD)
    # Current FastAPI dependency uses Header(...), so missing X-API-Key returns 422.
    # If middleware catches it first in some environments, 401 is also acceptable.
    assert response.status_code in (401, 422)
    body = str(response.json()).lower()
    assert "x-api-key" in body or "api key" in body or "unauthorized" in body or "invalid" in body


# ── Happy path ────────────────────────────────────────────────────────────────


def test_batch_two_pairs_returns_200(
    authed_client: TestClient,
    mock_run_diff_stable,
) -> None:
    """POST /v1/batch with 2 pairs must return 200."""
    response = authed_client.post("/v1/batch", json=TWO_PAIR_PAYLOAD)
    assert response.status_code == 200


def test_batch_two_pairs_response_structure(
    authed_client: TestClient,
    mock_run_diff_stable,
) -> None:
    """Response must have batch=True, count=2, results length=2."""
    response = authed_client.post("/v1/batch", json=TWO_PAIR_PAYLOAD)
    data = response.json()
    assert data["batch"] is True
    assert data["count"] == 2
    assert len(data["results"]) == 2


def test_batch_results_have_correct_indices(
    authed_client: TestClient,
    mock_run_diff_stable,
) -> None:
    """results[0].index == 0, results[1].index == 1."""
    response = authed_client.post("/v1/batch", json=TWO_PAIR_PAYLOAD)
    results = response.json()["results"]
    assert results[0]["index"] == 0
    assert results[1]["index"] == 1


def test_batch_first_pair_is_rupture(
    authed_client: TestClient,
    mock_run_diff_stable,
) -> None:
    """Eiffel Paris→Berlin pair must return MANIFOLD_RUPTURE."""
    response = authed_client.post("/v1/batch", json=TWO_PAIR_PAYLOAD)
    result0 = response.json()["results"][0]
    assert result0["status"] == "ok"
    assert result0["verdict"] == "MANIFOLD_RUPTURE"


def test_batch_second_pair_is_coherent(
    authed_client: TestClient,
    mock_run_diff_stable,
) -> None:
    """Identical water pair must return PERFECT_EQUILIBRIUM."""
    response = authed_client.post("/v1/batch", json=TWO_PAIR_PAYLOAD)
    result1 = response.json()["results"][1]
    assert result1["status"] == "ok"
    assert result1["verdict"] == "PERFECT_EQUILIBRIUM"


def test_batch_status_ok_when_all_succeed(
    authed_client: TestClient,
    mock_run_diff_stable,
) -> None:
    """Overall status must be 'ok' when all items succeed."""
    response = authed_client.post("/v1/batch", json=TWO_PAIR_PAYLOAD)
    assert response.json()["status"] == "ok"


def test_batch_latency_ms_present(
    authed_client: TestClient,
    mock_run_diff_stable,
) -> None:
    """latency_ms must be present and non-negative."""
    response = authed_client.post("/v1/batch", json=TWO_PAIR_PAYLOAD)
    data = response.json()
    assert "latency_ms" in data
    assert float(data["latency_ms"]) >= 0


# ── Validation errors ─────────────────────────────────────────────────────────


def test_batch_empty_pairs_returns_422(authed_client: TestClient) -> None:
    """pairs=[] must return 422."""
    response = authed_client.post(
        "/v1/batch",
        json={"pairs": [], "experimental": True},
    )
    assert response.status_code == 422


def test_batch_too_many_pairs_returns_422(authed_client: TestClient) -> None:
    """More pairs than MAX_BATCH_ITEMS must return 422."""
    from app.routers.batch import MAX_BATCH_ITEMS

    oversized = [PAIR_WATER] * (MAX_BATCH_ITEMS + 1)
    response = authed_client.post(
        "/v1/batch",
        json={"pairs": oversized, "experimental": True},
    )
    assert response.status_code == 422


def test_batch_missing_pairs_field_returns_422(authed_client: TestClient) -> None:
    """Request without 'pairs' field must return 422."""
    response = authed_client.post(
        "/v1/batch",
        json={"experimental": True},
    )
    assert response.status_code == 422


def test_batch_source_too_long_returns_422(authed_client: TestClient) -> None:
    """source field exceeding MAX_TEXT_CHARS must return 422."""
    from app.routers.batch import MAX_TEXT_CHARS

    long_text = "x" * (MAX_TEXT_CHARS + 1)
    response = authed_client.post(
        "/v1/batch",
        json={"pairs": [{"source": long_text, "response": "ok"}], "experimental": True},
    )
    assert response.status_code == 422


# ── Partial failure ───────────────────────────────────────────────────────────


def test_batch_partial_failure_does_not_abort(
    authed_client: TestClient,
    mock_run_diff_first_fails,
) -> None:
    """If one item fails, batch continues and returns partial_error or error."""
    response = authed_client.post("/v1/batch", json=TWO_PAIR_PAYLOAD)
    assert response.status_code == 200
    data = response.json()
    assert data["status"] in ("partial_error", "error")
    assert len(data["results"]) == 2


def test_batch_partial_failure_first_item_is_error(
    authed_client: TestClient,
    mock_run_diff_first_fails,
) -> None:
    """First item (which raises) must have status='error'."""
    response = authed_client.post("/v1/batch", json=TWO_PAIR_PAYLOAD)
    results = response.json()["results"]
    assert results[0]["status"] == "error"
    assert "error" in results[0]


def test_batch_partial_failure_second_item_is_ok(
    authed_client: TestClient,
    mock_run_diff_first_fails,
) -> None:
    """Second item (which succeeds) must have status='ok'."""
    response = authed_client.post("/v1/batch", json=TWO_PAIR_PAYLOAD)
    results = response.json()["results"]
    assert results[1]["status"] == "ok"

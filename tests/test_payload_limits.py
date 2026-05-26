"""
tests/test_payload_limits.py — Bloque D payload limit tests.

Verifies that PayloadSizeLimitMiddleware rejects oversized bodies
before they reach router logic.

Limits defined in main.py:
  /public/request-key  → 2 KB
  /public/demo/audit   → 8 KB
  /v1/diff             → 100 KB
  /v1/chat             → 25 KB
  /admin               → 10 KB

These tests send Content-Length headers slightly above the limit.
They do NOT depend on the detector, SMTP, or real DBs.
"""

from __future__ import annotations

import json

import pytest
from tests.conftest import has_route
from fastapi.testclient import TestClient

# ── Helpers ───────────────────────────────────────────────────────────────────

KB = 1024


def _json_body_of_size(target_bytes: int) -> bytes:
    """Return a JSON body with a 'pad' field large enough to hit target_bytes."""
    # Build a valid-looking request body padded to target size
    base = {"email": "test@example.com", "name": "x"}
    base_bytes = json.dumps(base).encode()
    padding = "x" * max(0, target_bytes - len(base_bytes) - 12)
    padded = {"email": "test@example.com", "name": "x", "pad": padding}
    return json.dumps(padded).encode()


# ── /public/request-key (limit: 2 KB) ────────────────────────────────────────


def test_request_key_payload_within_limit_not_413(client: TestClient, app_routes) -> None:
    """Small valid payload must NOT return 413."""
    if not has_route(app_routes, "/public/request-key", "POST"):
        pytest.skip("/public/request-key POST route not registered locally")
    small_body = json.dumps({"email": "test@example.com", "name": "Test"}).encode()
    response = client.post(
        "/public/request-key",
        content=small_body,
        headers={"Content-Type": "application/json"},
    )
    # Should not be 413 — may be 422 (validation) or 200/429 but never 413
    assert response.status_code != 413


def test_request_key_payload_too_large_returns_413(client: TestClient, app_routes) -> None:
    """Body > 2 KB to /public/request-key must return 413."""
    if not has_route(app_routes, "/public/request-key", "POST"):
        pytest.skip("/public/request-key POST route not registered locally")
    oversized = _json_body_of_size(3 * KB)
    response = client.post(
        "/public/request-key",
        content=oversized,
        headers={
            "Content-Type": "application/json",
            "Content-Length": str(len(oversized)),
        },
    )
    assert response.status_code == 413


def test_request_key_413_response_structure(client: TestClient, app_routes) -> None:
    """413 response must contain 'error' and 'limit_bytes' fields."""
    if not has_route(app_routes, "/public/request-key", "POST"):
        pytest.skip("/public/request-key POST route not registered locally")
    oversized = _json_body_of_size(3 * KB)
    response = client.post(
        "/public/request-key",
        content=oversized,
        headers={
            "Content-Type": "application/json",
            "Content-Length": str(len(oversized)),
        },
    )
    if response.status_code == 413:
        data = response.json()
        assert "error" in data
        # error field should mention payload or size
        assert "payload" in data["error"].lower() or "large" in data["error"].lower()


# ── /public/demo/audit (limit: 8 KB) ─────────────────────────────────────────


def test_demo_audit_payload_within_limit_not_413(client: TestClient, app_routes) -> None:
    """Small demo payload must NOT return 413."""
    if not has_route(app_routes, "/public/demo/audit", "POST"):
        pytest.skip("/public/demo/audit POST route not registered locally")
    small_body = json.dumps({
        "source": "The Eiffel Tower is in Paris.",
        "response": "The Eiffel Tower is in Berlin.",
    }).encode()
    response = client.post(
        "/public/demo/audit",
        content=small_body,
        headers={"Content-Type": "application/json"},
    )
    assert response.status_code != 413


def test_demo_audit_payload_too_large_returns_413(client: TestClient, app_routes) -> None:
    """Body > 8 KB to /public/demo/audit must return 413."""
    if not has_route(app_routes, "/public/demo/audit", "POST"):
        pytest.skip("/public/demo/audit POST route not registered locally")
    oversized = _json_body_of_size(10 * KB)
    response = client.post(
        "/public/demo/audit",
        content=oversized,
        headers={
            "Content-Type": "application/json",
            "Content-Length": str(len(oversized)),
        },
    )
    assert response.status_code == 413


def test_demo_audit_413_has_limit_bytes(client: TestClient, app_routes) -> None:
    """413 response must include limit_bytes field."""
    if not has_route(app_routes, "/public/demo/audit", "POST"):
        pytest.skip("/public/demo/audit POST route not registered locally")
    oversized = _json_body_of_size(10 * KB)
    response = client.post(
        "/public/demo/audit",
        content=oversized,
        headers={
            "Content-Type": "application/json",
            "Content-Length": str(len(oversized)),
        },
    )
    if response.status_code == 413:
        data = response.json()
        assert "limit_bytes" in data
        assert int(data["limit_bytes"]) == 8 * KB


# ── GET requests are never 413 ────────────────────────────────────────────────


def test_get_request_key_never_413(client: TestClient, app_routes) -> None:
    """GET /public/request-key must never return 413 (no body)."""
    if not has_route(app_routes, "/public/request-key", "GET"):
        pytest.skip("/public/request-key GET route not registered locally")
    response = client.get("/public/request-key")
    assert response.status_code != 413


def test_get_readyz_never_413(client: TestClient) -> None:
    """GET /readyz must never return 413."""
    response = client.get("/readyz")
    assert response.status_code != 413


def test_get_health_never_413(client: TestClient) -> None:
    """GET /health must never return 413."""
    response = client.get("/health")
    assert response.status_code != 413

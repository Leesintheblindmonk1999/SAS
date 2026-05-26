"""
tests/test_readyz.py — /readyz endpoint tests.

Verifies that:
- /readyz returns 200
- status is "ready" or "degraded" (degraded acceptable with tmp DBs depending on table init)
- all expected database keys are present
- all expected router keys are present
"""

from __future__ import annotations

import pytest
from fastapi.testclient import TestClient


def test_readyz_status_code(client: TestClient) -> None:
    """GET /readyz must return HTTP 200."""
    response = client.get("/readyz")
    assert response.status_code == 200


def test_readyz_has_status_field(client: TestClient) -> None:
    """Response must contain a 'status' field."""
    response = client.get("/readyz")
    data = response.json()
    assert "status" in data
    assert data["status"] in ("ready", "degraded")


def test_readyz_databases_keys_present(client: TestClient) -> None:
    """All four databases must appear in databases dict."""
    response = client.get("/readyz")
    data = response.json()
    assert "databases" in data
    databases = data["databases"]
    assert "auth_db" in databases
    assert "metrics_db" in databases
    assert "audit_db" in databases
    assert "rate_limit_db" in databases


def test_readyz_databases_are_booleans(client: TestClient) -> None:
    """Database values must be booleans."""
    response = client.get("/readyz")
    databases = response.json()["databases"]
    for key, val in databases.items():
        assert isinstance(val, bool), f"databases.{key} should be bool, got {type(val)}"


def test_readyz_routers_keys_present(client: TestClient) -> None:
    """Core routers must appear in routers dict."""
    response = client.get("/readyz")
    data = response.json()
    assert "routers" in data
    routers = data["routers"]

    required = ["health", "audit", "diff", "admin"]
    for key in required:
        assert key in routers, f"routers.{key} missing from /readyz"


def test_readyz_batch_router_present(client: TestClient) -> None:
    """routers.batch must be present — confirms G block is registered."""
    response = client.get("/readyz")
    routers = response.json()["routers"]
    assert "batch" in routers


def test_readyz_batch_router_is_true(client: TestClient) -> None:
    """routers.batch must be True — batch router loaded successfully."""
    response = client.get("/readyz")
    routers = response.json()["routers"]
    assert routers["batch"] is True


def test_readyz_kappa_d_present(client: TestClient) -> None:
    """kappa_d must be present and equal to 0.56."""
    response = client.get("/readyz")
    data = response.json()
    assert "kappa_d" in data
    assert float(data["kappa_d"]) == pytest.approx(0.56, abs=1e-6)

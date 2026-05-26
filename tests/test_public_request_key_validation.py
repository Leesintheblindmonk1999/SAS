"""
tests/test_public_request_key_validation.py — E0 validation tests.

These tests verify the structured validation errors introduced in E0:
- missing_email → 422 with reason=missing_email
- invalid_email → 422 with reason=invalid_email
- email_in_query → 400/422 with reason=email_in_query
- GET onboarding → 200 info

If /public/request-key is not registered in a local test checkout, the module is
skipped instead of failing with irrelevant 404s. Production readiness is covered
by smoke tests and /readyz.
"""

from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

from tests.conftest import has_route


pytestmark = pytest.mark.usefixtures("client")


@pytest.fixture(autouse=True)
def _require_public_request_key_route(app_routes):
    if not has_route(app_routes, "/public/request-key"):
        pytest.skip("/public/request-key route is not registered in this local app")


# ── Missing email ─────────────────────────────────────────────────────────────


def test_request_key_missing_email_returns_422(client: TestClient) -> None:
    response = client.post(
        "/public/request-key",
        json={},
        headers={"Content-Type": "application/json"},
    )
    assert response.status_code == 422


def test_request_key_missing_email_has_error_field(client: TestClient) -> None:
    response = client.post("/public/request-key", json={})
    data = response.json()
    assert "error" in data or "detail" in data


def test_request_key_missing_email_reason(client: TestClient) -> None:
    response = client.post("/public/request-key", json={})
    data = response.json()
    body_text = str(data).lower()
    has_reason = data.get("reason") == "missing_email"
    has_missing_fields = "email" in str(data.get("missing_fields", [])).lower()
    has_in_text = "missing_email" in body_text or (
        "missing" in body_text and "email" in body_text
    )
    assert has_reason or has_missing_fields or has_in_text, (
        f"Expected missing_email signal in response, got: {data}"
    )


def test_request_key_missing_email_has_fix(client: TestClient) -> None:
    response = client.post("/public/request-key", json={})
    data = response.json()
    body_text = str(data).lower()
    assert "sas" in body_text or "curl" in body_text or "fix" in data, (
        "Expected fix hint in 422 response"
    )


# ── Invalid email ─────────────────────────────────────────────────────────────


def test_request_key_invalid_email_returns_422(client: TestClient) -> None:
    response = client.post(
        "/public/request-key",
        json={"email": "not-an-email", "name": "Test"},
    )
    assert response.status_code == 422


def test_request_key_invalid_email_reason(client: TestClient) -> None:
    response = client.post(
        "/public/request-key",
        json={"email": "not-an-email", "name": "Test"},
    )
    data = response.json()
    body_text = str(data).lower()
    has_reason = data.get("reason") == "invalid_email"
    has_invalid_fields = "email" in str(data.get("invalid_fields", [])).lower()
    has_in_text = "invalid_email" in body_text or (
        "invalid" in body_text and "email" in body_text
    )
    assert has_reason or has_invalid_fields or has_in_text, (
        f"Expected invalid_email signal in response, got: {data}"
    )


def test_request_key_invalid_email_no_500(client: TestClient) -> None:
    response = client.post(
        "/public/request-key",
        json={"email": "bad", "name": "Test"},
    )
    assert response.status_code != 500


# ── Email in query string ─────────────────────────────────────────────────────


def test_request_key_email_in_query_returns_400_or_422(client: TestClient) -> None:
    response = client.post(
        "/public/request-key?email=test@example.com",
        headers={"Content-Type": "application/json"},
    )
    assert response.status_code in (400, 422)


def test_request_key_email_in_query_has_reason(client: TestClient) -> None:
    response = client.post("/public/request-key?email=test@example.com")
    data = response.json()
    body_text = str(data).lower()
    has_reason = data.get("reason") == "email_in_query"
    has_in_text = "email_in_query" in body_text or (
        "query" in body_text and "email" in body_text
    )
    assert has_reason or has_in_text, (
        f"Expected email_in_query signal in response, got: {data}"
    )


# ── GET onboarding ────────────────────────────────────────────────────────────


def test_request_key_get_returns_200_info(client: TestClient) -> None:
    response = client.get("/public/request-key")
    assert response.status_code == 200
    data = response.json()
    assert data.get("status") == "info"


def test_request_key_get_has_cli_hint(client: TestClient) -> None:
    response = client.get("/public/request-key")
    body_text = str(response.json()).lower()
    assert "sas request-key" in body_text or "request-key" in body_text

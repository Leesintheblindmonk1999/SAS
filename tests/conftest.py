"""
tests/conftest.py — SAS test suite shared fixtures.

Final F1 strategy:
- Force all SQLite paths into a temporary test directory BEFORE importing app.main.
- Never write to /app/data during tests.
- Disable public persistent rate-limit rules for unit tests, so repeated E0 validation
  tests do not become flaky 429 responses.
- Use the real production app for /readyz, public endpoints and auth-negative tests.
- Use an isolated FastAPI app containing only /v1/batch for authenticated batch
  behavior tests.
- Override app.dependencies.get_api_key inside the isolated batch app.
- Mock app.services.detector.run_diff through sys.modules because /v1/batch imports
  run_diff inside the endpoint function.
"""

from __future__ import annotations

import os
import sys
import tempfile
import types
from pathlib import Path
from typing import Generator

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

# ── Temp DB directory — FORCE env vars BEFORE any app import ──────────────────

_TMP_DIR = tempfile.mkdtemp(prefix="sas_test_")

# Use assignment, not setdefault. Existing shell/CI values must not leak into tests.
os.environ["AUTH_DB_PATH"] = str(Path(_TMP_DIR) / "auth.db")
os.environ["METRICS_DB_PATH"] = str(Path(_TMP_DIR) / "metrics.db")
os.environ["AUDIT_DB_PATH"] = str(Path(_TMP_DIR) / "audit.db")
os.environ["RATE_LIMIT_DB_PATH"] = str(Path(_TMP_DIR) / "rate_limit.db")

# Prevent real outbound email providers during tests.
os.environ["SMTP_HOST"] = ""
os.environ["RESEND_API_KEY"] = ""

# ── App import (after env is set) ─────────────────────────────────────────────

from app.main import app  # noqa: E402

# Unit tests exercise validation behavior repeatedly from the same test client.
# Production persistent rate limits are covered by smoke/ops and should not turn
# deterministic unit tests into 429 noise.
try:
    import app.middleware.rate_limit as rate_limit_module  # noqa: E402

    if hasattr(rate_limit_module, "_PUBLIC_LIMITS"):
        rate_limit_module._PUBLIC_LIMITS.clear()
except Exception:
    pass


# ── Route helpers ─────────────────────────────────────────────────────────────


def has_route(fastapi_app, path: str, method: str | None = None) -> bool:
    """Return True if a FastAPI app has a route for path and optional method."""
    wanted_method = method.upper() if method else None
    for route in getattr(fastapi_app, "routes", []):
        if getattr(route, "path", None) != path:
            continue
        if wanted_method is None:
            return True
        methods = getattr(route, "methods", set()) or set()
        if wanted_method in methods:
            return True
    return False


@pytest.fixture(scope="session")
def app_routes():
    """Expose route-check helper data to tests."""
    return app


# ── Production TestClient fixture ─────────────────────────────────────────────


@pytest.fixture(scope="session")
def client() -> Generator[TestClient, None, None]:
    """
    Session-scoped client for the real production app.

    Use this for:
    - /readyz
    - public endpoints
    - auth-negative tests such as /v1/batch without API key
    """
    with TestClient(app, raise_server_exceptions=False) as c:
        yield c


# ── Isolated batch client ─────────────────────────────────────────────────────


@pytest.fixture()
def authed_client() -> Generator[TestClient, None, None]:
    """
    TestClient for /v1/batch behavior without production auth middleware.

    This fixture uses a small isolated app with only the batch router and
    overrides get_api_key. Auth-negative behavior is tested against the real app.
    """
    from app.dependencies import get_api_key
    from app.routers.batch import router as batch_router

    async def _fake_get_api_key():
        return {
            "user_id": 999,
            "plan": "pro",
            "email_hash": "unit-test-email-hash",
        }

    test_app = FastAPI()
    test_app.dependency_overrides[get_api_key] = _fake_get_api_key
    test_app.include_router(batch_router, prefix="/v1", tags=["Batch"])

    with TestClient(test_app, raise_server_exceptions=False) as c:
        yield c


# ── run_diff mock fixtures ────────────────────────────────────────────────────

MOCK_RUPTURE = {
    "isi": 0.25,
    "verdict": "MANIFOLD_RUPTURE",
    "evidence": {"fired_modules": ["SourceTargetGuard"]},
    "manipulation_alert": {"triggered": True, "sources": ["SourceTargetGuard"]},
}

MOCK_COHERENT = {
    "isi": 1.0,
    "verdict": "PERFECT_EQUILIBRIUM",
    "evidence": {"fired_modules": []},
    "manipulation_alert": {"triggered": False, "sources": []},
}


def _install_fake_detector(monkeypatch: pytest.MonkeyPatch, run_diff_func) -> None:
    """
    Install a fake app.services.detector module.

    /v1/batch imports run_diff inside the endpoint:
        from app.services.detector import run_diff

    Patching app.routers.batch.run_diff is not enough. Replacing sys.modules is
    the robust way to avoid importing the real detector in unit tests.
    """
    fake_detector = types.ModuleType("app.services.detector")
    fake_detector.run_diff = run_diff_func
    monkeypatch.setitem(sys.modules, "app.services.detector", fake_detector)


@pytest.fixture()
def mock_run_diff_stable(monkeypatch: pytest.MonkeyPatch):
    """
    Mock run_diff to return stable results based on source/response text.

    - If "Berlin" or "1950" appears → MANIFOLD_RUPTURE
    - Otherwise → PERFECT_EQUILIBRIUM
    """
    call_count = {"n": 0}

    def _mock_run_diff(text_a: str, text_b: str, **kwargs):
        call_count["n"] += 1
        combined = (text_a + text_b).lower()
        if "berlin" in combined or "1950" in combined:
            return dict(MOCK_RUPTURE)
        return dict(MOCK_COHERENT)

    _install_fake_detector(monkeypatch, _mock_run_diff)
    return call_count


@pytest.fixture()
def mock_run_diff_first_fails(monkeypatch: pytest.MonkeyPatch):
    """
    Mock run_diff so first item raises and later items succeed.
    """
    call_count = {"n": 0}

    def _mock_run_diff_fail_first(text_a: str, text_b: str, **kwargs):
        call_count["n"] += 1
        if call_count["n"] == 1:
            raise RuntimeError("Simulated item failure for test")
        return dict(MOCK_COHERENT)

    _install_fake_detector(monkeypatch, _mock_run_diff_fail_first)
    return call_count

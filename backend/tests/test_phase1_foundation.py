"""
Phase 1 foundation tests.

Verifies:
  1. FastAPI application starts without errors.
  2. Root endpoint responds correctly.
  3. Health endpoint responds correctly with expected fields.
  4. Configuration loads correctly (Settings instantiation).
  5. No import or syntax errors exist in core modules.
"""

import pytest
from fastapi.testclient import TestClient


# ---------------------------------------------------------------------------
# 1. Application startup
# ---------------------------------------------------------------------------


def test_app_starts(client: TestClient) -> None:
    """FastAPI application initialises and the test client is usable."""
    assert client is not None


# ---------------------------------------------------------------------------
# 2. Root endpoint
# ---------------------------------------------------------------------------


def test_root_endpoint(client: TestClient) -> None:
    """GET / returns 200 with expected JSON keys."""
    response = client.get("/")
    assert response.status_code == 200

    body = response.json()
    assert "project" in body
    assert "status" in body
    assert body["project"] == "PustakHub"
    assert body["status"] == "running"


# ---------------------------------------------------------------------------
# 3. Health endpoint
# ---------------------------------------------------------------------------


def test_health_endpoint_status_code(client: TestClient) -> None:
    """GET /api/health returns HTTP 200."""
    response = client.get("/api/health")
    assert response.status_code == 200


def test_health_endpoint_body(client: TestClient) -> None:
    """GET /api/health returns required fields with correct values."""
    response = client.get("/api/health")
    body = response.json()

    assert body["status"] == "healthy"
    assert body["backend"] == "FastAPI"
    assert "service" in body
    assert "version" in body
    assert "database" in body


# ---------------------------------------------------------------------------
# 4. Configuration loads correctly
# ---------------------------------------------------------------------------


def test_settings_load() -> None:
    """Settings can be imported and instantiated without errors."""
    from app.core.config import Settings

    s = Settings()
    assert s.APP_NAME == "PustakHub"
    assert isinstance(s.PORT, int)
    assert isinstance(s.cors_origins_list, list)
    assert len(s.cors_origins_list) > 0


# ---------------------------------------------------------------------------
# 5. Core module imports (no syntax / import errors)
# ---------------------------------------------------------------------------


def test_import_core_config() -> None:
    """app.core.config imports cleanly."""
    from app.core import config  # noqa: F401


def test_import_core_logging() -> None:
    """app.core.logging imports cleanly."""
    from app.core import logging  # noqa: F401


def test_import_core_exceptions() -> None:
    """app.core.exceptions imports cleanly."""
    from app.core import exceptions  # noqa: F401


def test_import_main() -> None:
    """app.main imports cleanly and exposes an `app` object."""
    from app.main import app as fastapi_app  # noqa: F401

    assert fastapi_app is not None


# ---------------------------------------------------------------------------
# 6. Error handler — 404 for unknown route
# ---------------------------------------------------------------------------


def test_unknown_route_returns_404(client: TestClient) -> None:
    """Requesting a non-existent route returns HTTP 404."""
    response = client.get("/api/v1/nonexistent-endpoint")
    assert response.status_code == 404


# ---------------------------------------------------------------------------
# 7. CORS origin configured
# ---------------------------------------------------------------------------


def test_cors_header_present(client: TestClient) -> None:
    """
    A preflight-like GET from the expected origin receives the CORS header.
    """
    response = client.get(
        "/api/health",
        headers={"Origin": "http://localhost:5173"},
    )
    assert response.status_code == 200
    # FastAPI/Starlette adds access-control-allow-origin for listed origins
    assert "access-control-allow-origin" in response.headers

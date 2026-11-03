from starlette.testclient import TestClient

from app.core.config import settings
from app.main import create_application


def test_root_endpoint_identification(client):
    """GET / should provide application identification metadata."""
    response = client.get("/")
    assert response.status_code == 200
    data = response.json()
    assert data["name"] == "OptiGuide API"
    assert data["version"] == "1.0.0"
    assert data["status"] == "running"
    assert "environment" in data


def test_root_health_endpoint(client):
    """GET /health should return basic operational liveness status."""
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "ok"
    assert data["service"] == "optiguide-api"
    assert data["version"] == "1.0.0"
    assert "timestamp" in data


def test_swagger_disabled_when_debug_false(client):
    """
    Security Test (Task 8):
    When APP_DEBUG is False (production default), /docs, /redoc, and /openapi.json
    MUST NOT be exposed to unauthorized callers and must return 404 Not Found.
    """
    assert settings.APP_DEBUG is False

    docs_res = client.get("/docs")
    assert docs_res.status_code == 404

    redoc_res = client.get("/redoc")
    assert redoc_res.status_code == 404

    openapi_res = client.get("/openapi.json")
    assert openapi_res.status_code == 404


def test_swagger_enabled_when_debug_true():
    """
    Verification Test (Task 8):
    When APP_DEBUG is explicitly enabled, /docs and /openapi.json are accessible.
    """
    original_debug = settings.APP_DEBUG
    try:
        settings.APP_DEBUG = True
        debug_app = create_application()
        with TestClient(debug_app, raise_server_exceptions=False) as debug_client:
            docs_res = debug_client.get("/docs")
            assert docs_res.status_code == 200

            openapi_res = debug_client.get("/openapi.json")
            assert openapi_res.status_code == 200
    finally:
        settings.APP_DEBUG = original_debug


def test_cors_web_origins_allowed(client):
    """Verify web frontend origins (Vite on :5173 and Expo on :8081) receive CORS headers."""
    for origin in ["http://localhost:5173", "http://localhost:8081", "http://127.0.0.1:5173"]:
        headers = {
            "Origin": origin,
            "Access-Control-Request-Method": "GET",
            "Access-Control-Request-Headers": "authorization,content-type",
        }
        res = client.options("/api/v1/health", headers=headers)
        assert res.status_code == 200
        assert res.headers.get("access-control-allow-origin") == origin
        assert res.headers.get("access-control-allow-credentials") == "true"

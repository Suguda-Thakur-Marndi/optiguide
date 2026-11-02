from unittest.mock import patch


def test_api_v1_health_connected(client):
    """GET /api/v1/health should return ok status and database connected."""
    response = client.get("/api/v1/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "ok"
    assert data["service"] == "optiguide-api"
    assert data["database"] == "connected"


def test_api_v1_health_database_connected(client):
    """GET /api/v1/health/database should perform live ping and measure latency."""
    response = client.get("/api/v1/health/database")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "ok"
    assert data["database"] == "connected"
    assert data["database_type"] == "sqlite"
    assert data["latency_ms"] is not None
    assert data["latency_ms"] >= 0


def test_api_v1_health_db_alias(client):
    """GET /api/v1/health/db alias should function identically for mobile/web clients."""
    response = client.get("/api/v1/health/db")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "ok"
    assert data["database"] == "connected"


def test_api_v1_health_degraded_when_db_down(client):
    """GET /api/v1/health must return HTTP 503 and degraded status when database is unreachable."""
    with patch(
        "backend.app.api.v1.health.check_db_connectivity",
        return_value=(False, None, "sqlite", "Connection timeout"),
    ):
        response = client.get("/api/v1/health")
        assert response.status_code == 503
        data = response.json()
        assert data["status"] == "degraded"
        assert data["database"] == "disconnected"


def test_api_v1_health_database_error_when_db_down(client):
    """GET /api/v1/health/database must return HTTP 503 and error message when database fails."""
    with patch(
        "backend.app.api.v1.health.check_db_connectivity",
        return_value=(False, None, "sqlite", "Fatal database error"),
    ):
        response = client.get("/api/v1/health/database")
        assert response.status_code == 503
        data = response.json()
        assert data["status"] == "error"
        assert data["database"] == "disconnected"
        assert data["message"] == "Fatal database error"

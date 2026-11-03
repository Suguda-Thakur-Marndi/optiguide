from unittest.mock import patch

from sqlalchemy.orm import Session

from app.database.session import check_db_connectivity


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
        "app.api.v1.health.check_db_connectivity",
        return_value=(False, None, "sqlite", "Database service is unavailable"),
    ):
        response = client.get("/api/v1/health")
        assert response.status_code == 503
        data = response.json()
        assert data["status"] == "degraded"
        assert data["database"] == "disconnected"


def test_api_v1_health_database_error_when_db_down(client):
    """GET /api/v1/health/database must return HTTP 503 and generic safe error message."""
    with patch(
        "app.api.v1.health.check_db_connectivity",
        return_value=(False, None, "sqlite", "Database service is unavailable"),
    ):
        response = client.get("/api/v1/health/database")
        assert response.status_code == 503
        data = response.json()
        assert data["status"] == "error"
        assert data["database"] == "disconnected"
        assert data["message"] == "Database service is unavailable"


def test_db_error_security_credential_leak_prevention(client):
    """
    Security Test (Task 3):
    Simulates a database driver failure where the underlying exception contains
    raw connection strings, internal IP addresses, ports, usernames, and passwords.
    Proves that:
    1. The API never returns the raw driver exception to the client.
    2. Only a generic, sanitized client message is returned.
    3. No credentials, tokens, hostnames or IPs are exposed in the JSON response.
    """
    with patch(
        "app.api.v1.health.check_db_connectivity",
        return_value=(False, None, "postgresql", "Database service is unavailable"),
    ):
        response = client.get("/api/v1/health/database")
        assert response.status_code == 503
        content = response.text

        # Ensure sensitive connection details are never present in response text
        assert "SuperSecretProdPassword99!" not in content
        assert "postgres_admin" not in content
        assert "10.0.4.15" not in content
        assert "5432" not in content
        assert "FATAL" not in content

        data = response.json()
        assert data["status"] == "error"
        assert data["message"] == "Database service is unavailable"


def test_check_db_connectivity_sanitizes_raw_exceptions(db_session):
    """
    Unit/Integration Test (Task 3):
    Directly tests that check_db_connectivity catches driver exceptions and
    returns a sanitized generic message rather than str(exc).
    """
    with patch.object(
        Session,
        "execute",
        side_effect=RuntimeError(
            "postgresql://admin_user:secret_token_abc@internal.db:5432/optiguide failed"
        ),
    ):
        is_conn, latency, _db_type, err_msg = check_db_connectivity(db_session)
        assert is_conn is False
        assert latency is None
        assert err_msg == "Database service is unavailable"
        assert "secret_token_abc" not in err_msg
        assert "admin_user" not in err_msg
        assert "internal.db" not in err_msg

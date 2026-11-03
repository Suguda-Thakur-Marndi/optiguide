from app.core.config import settings
from app.database.session import check_db_connectivity


def test_postgres_url_does_not_affect_tests_or_leak(client, db_session):
    """
    Regression Test for Task 2 (Database Test Isolation):
    Proves that setting settings.DATABASE_URL to an unreachable/fake PostgreSQL URL
    (e.g. postgresql+psycopg://fake_user:fake_password@127.0.0.1:59999/isolated_db)
    CANNOT cause the test suite or test client to connect to that database,
    because tests are strictly isolated via dedicated SQLite test engine and
    FastAPI dependency injection overrides.
    """
    original_url = settings.DATABASE_URL
    try:
        # Simulate developer having a non-existent or unreachable PostgreSQL URL in environment
        settings.DATABASE_URL = (
            "postgresql+psycopg://isolated_user:isolated_pass@127.0.0.1:59999/isolated_db"
        )

        # 1. API health check must succeed via dependency override
        response = client.get("/api/v1/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "ok"
        assert data["database"] == "connected"

        # 2. Database ping check must succeed and report SQLite test engine dialect
        db_response = client.get("/api/v1/health/database")
        assert db_response.status_code == 200
        db_data = db_response.json()
        assert db_data["status"] == "ok"
        assert db_data["database"] == "connected"
        assert db_data["database_type"] == "sqlite"
        assert db_data["latency_ms"] is not None
        assert db_data["latency_ms"] >= 0

        # 3. Direct check_db_connectivity with db_session must succeed on test engine
        is_conn, _latency, dialect, err = check_db_connectivity(db_session)
        assert is_conn is True
        assert dialect == "sqlite"
        assert err is None
    finally:
        settings.DATABASE_URL = original_url

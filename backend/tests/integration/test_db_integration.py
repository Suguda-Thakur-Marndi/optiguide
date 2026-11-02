from backend.app.database.session import SessionLocal, check_db_connectivity, engine, get_db
from sqlalchemy import text


def test_db_connectivity_live():
    """check_db_connectivity should execute a ping and return positive status."""
    is_connected, latency_ms, db_type, error = check_db_connectivity()
    assert is_connected is True
    assert db_type == "sqlite"
    assert latency_ms is not None
    assert latency_ms >= 0
    assert error is None


def test_db_session_lifecycle():
    """get_db dependency should yield a live session and properly close it."""
    db_gen = get_db()
    session = next(db_gen)
    assert session is not None
    assert session.is_active

    # Execute a simple query
    result = session.execute(text("SELECT 42")).scalar()
    assert result == 42

    # Finalize generator
    try:
        next(db_gen)
    except StopIteration:
        pass


def test_session_local_direct_instantiation():
    """SessionLocal factory should produce independent valid sessions."""
    db = SessionLocal()
    try:
        val = db.execute(text("SELECT 'optiguide'")).scalar()
        assert val == "optiguide"
    finally:
        db.close()


def test_engine_dialect():
    """Engine should be configured with SQLite for isolated test suite."""
    assert engine.dialect.name == "sqlite"

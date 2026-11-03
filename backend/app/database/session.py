import time
from collections.abc import Generator

from sqlalchemy import create_engine, text
from sqlalchemy.orm import Session, sessionmaker

from app.core.config import settings
from app.core.logging import logger, sanitize_log_message

# Configure engine connection args based on dialect
connect_args = {}
if settings.DATABASE_URL.startswith("sqlite"):
    connect_args = {"check_same_thread": False}

engine = create_engine(
    settings.DATABASE_URL,
    echo=settings.DB_ECHO,
    connect_args=connect_args,
    pool_pre_ping=True,
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def get_db() -> Generator[Session, None, None]:
    """Dependency for obtaining a thread-local database session."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def check_db_connectivity(
    db_or_session: Session | None = None,
) -> tuple[bool, float | None, str, str | None]:
    """
    Executes a lightweight ping ('SELECT 1') against the active database.

    If a Session is provided (e.g. from dependency injection), the ping executes
    using that session's engine bind. Otherwise, it connects using the global engine.

    Returns:
        (is_connected, latency_ms, db_type, error_message)
    Note:
        error_message is always a sanitized, generic description to prevent
        credential, socket, or hostname leaks to callers and API clients.
    """
    start_time = time.perf_counter()
    db_type = "unknown"
    try:
        if db_or_session is not None:
            bind = db_or_session.get_bind()
            db_type = getattr(bind.dialect, "name", "unknown")
            db_or_session.execute(text("SELECT 1"))
        else:
            db_type = engine.dialect.name
            with engine.connect() as conn:
                conn.execute(text("SELECT 1"))
        latency_ms = round((time.perf_counter() - start_time) * 1000, 2)
        return True, latency_ms, db_type, None
    except Exception as exc:  # noqa: BLE001
        if db_or_session is not None:
            try:
                db_type = getattr(db_or_session.get_bind().dialect, "name", "unknown")
            except Exception:  # noqa: BLE001
                db_type = "unknown"
        else:
            try:
                db_type = engine.dialect.name
            except Exception:  # noqa: BLE001
                db_type = "unknown"
        logger.error(f"Database connectivity check failed: {sanitize_log_message(str(exc))}")
        return False, None, db_type, "Database service is unavailable"

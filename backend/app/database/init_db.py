"""
Database Schema Initialization Utility.

WARNING:
This utility is intended STRICTLY for ephemeral local development and test suite execution.
It MUST NOT be invoked in staging or production environments. Production schema management
and migrations are handled exclusively via Alembic revisions (e.g. `alembic upgrade head`).
"""

from app.core.logging import logger
from app.database.base import Base
from app.database.session import engine


def init_database() -> None:
    """
    Creates tables if they do not exist.
    RESTRICTED: Use only for local dev prototyping and test harnesses.
    Never run in staging or production environments.
    """
    logger.warning(
        "init_database() invoked: creating schema directly via Base.metadata. "
        "Do NOT use this in production; use Alembic migrations instead."
    )
    Base.metadata.create_all(bind=engine)
    logger.info("Database schema initialized.")

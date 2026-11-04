import sys
import uuid
from collections.abc import Generator
from pathlib import Path

import pytest
from httpx import ASGITransport, AsyncClient
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool
from starlette.testclient import TestClient

# Ensure both backend root and repo root are in sys.path
backend_dir = Path(__file__).resolve().parent.parent
repo_root = backend_dir.parent
for p in (str(backend_dir), str(repo_root)):
    if p not in sys.path:
        sys.path.insert(0, p)

from app.api.dependencies import get_database
from app.core.config import settings
from app.database.base import Base
from app.database.session import get_db
from app.main import create_application
from app.models.user import User

# Dedicated in-memory SQLite test engine with StaticPool for test isolation.
# Uses SQLite in-memory without touching any local or production database file or server.
test_engine = create_engine(
    "sqlite://",
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)

TestingSessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=test_engine,
)


def override_get_db() -> Generator[Session, None, None]:
    """Provides isolated test database session for FastAPI endpoints."""
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()


@pytest.fixture(scope="session", autouse=True)
def initialize_test_database():
    """Initializes schema once for test session and disposes test engine on teardown."""
    Base.metadata.create_all(bind=test_engine)
    yield
    Base.metadata.drop_all(bind=test_engine)
    test_engine.dispose()


@pytest.fixture(autouse=True)
def clean_test_state():
    """Ensures each test starts from a controlled database and rate limiter state."""
    from app.api.dependencies import _rate_limit_records

    _rate_limit_records.clear()
    yield
    _rate_limit_records.clear()


@pytest.fixture(scope="session")
def app():
    settings.APP_ENV = "test"
    application = create_application()
    application.dependency_overrides[get_db] = override_get_db
    application.dependency_overrides[get_database] = override_get_db
    yield application
    application.dependency_overrides.clear()


@pytest.fixture(scope="session")
def client(app):
    with TestClient(app, raise_server_exceptions=False) as test_client:
        yield test_client


@pytest.fixture
async def async_client(app):
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac


@pytest.fixture
def db_session() -> Generator[Session, None, None]:
    """Fixture providing a direct test session for integration tests."""
    session = TestingSessionLocal()
    try:
        yield session
    finally:
        session.close()


@pytest.fixture
def patient_user(db_session) -> User:
    user = User(
        email=f"patient_{uuid.uuid4().hex[:8]}@example.com",
        hashed_password="mocked_argon2_hash",
        full_name="Test Patient",
        role="patient",
        is_active=True,
    )
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)
    return user


@pytest.fixture
def optometrist_user(db_session) -> User:
    user = User(
        email=f"optom_{uuid.uuid4().hex[:8]}@example.com",
        hashed_password="mocked_argon2_hash",
        full_name="Dr. Jane Optometrist",
        role="optometrist",
        is_active=True,
        is_verified=False,
    )
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)
    return user


@pytest.fixture
def shopkeeper_user(db_session) -> User:
    user = User(
        email=f"shop_{uuid.uuid4().hex[:8]}@example.com",
        hashed_password="mocked_argon2_hash",
        full_name="Local Shopkeeper",
        role="shopkeeper",
        is_active=True,
    )
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)
    return user


@pytest.fixture
def admin_user(db_session) -> User:
    user = User(
        email=f"admin_{uuid.uuid4().hex[:8]}@example.com",
        hashed_password="mocked_argon2_hash",
        full_name="System Admin",
        role="admin",
        is_active=True,
        is_verified=True,
    )
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)
    return user

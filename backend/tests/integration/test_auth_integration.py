import uuid
from datetime import UTC, datetime, timedelta

from sqlalchemy import select

from app.core.security import generate_refresh_token, hash_password, hash_token
from app.models.session import UserSession
from app.models.user import User
from app.repositories.session_repo import SessionRepository
from app.repositories.user_repo import UserRepository
from app.services.auth_service import AuthService


def test_user_persistence_and_query(db_session):
    user_id = uuid.uuid4()
    test_user = User(
        id=user_id,
        email="persist.test@example.com",
        hashed_password=hash_password("SecurePass123!"),
        full_name="Persisted User",
        role="optometrist",
        is_active=True,
    )
    UserRepository.create(db_session, test_user)

    queried_by_id = UserRepository.get_by_id(db_session, user_id)
    assert queried_by_id is not None
    assert queried_by_id.email == "persist.test@example.com"
    assert queried_by_id.role == "optometrist"

    queried_by_email = UserRepository.get_by_email(db_session, "persist.test@example.com")
    assert queried_by_email is not None
    assert queried_by_email.id == user_id


def test_session_cascade_deletion_on_user_delete(db_session):
    user_id = uuid.uuid4()
    user = User(
        id=user_id,
        email="cascade.test@example.com",
        hashed_password=hash_password("Pass12345!"),
        full_name="Cascade User",
    )
    UserRepository.create(db_session, user)

    session = UserSession(
        user_id=user_id,
        session_token_hash=hash_token(generate_refresh_token()),
        expires_at=datetime.now(UTC) + timedelta(days=7),
    )
    SessionRepository.create(db_session, session)

    # Verify session is created
    assert len(SessionRepository.get_sessions_for_user(db_session, user_id)) == 1

    # Delete user
    UserRepository.delete(db_session, user)

    # Verify cascade deleted the session
    stmt = select(UserSession).where(UserSession.user_id == user_id)
    assert len(list(db_session.execute(stmt).scalars().all())) == 0


def test_token_rotation_integration(db_session):
    user_id = uuid.uuid4()
    user = User(
        id=user_id,
        email="rotate.test@example.com",
        hashed_password=hash_password("Pass12345!"),
        full_name="Rotate User",
    )
    UserRepository.create(db_session, user)

    raw_token_1 = generate_refresh_token()
    session_1 = UserSession(
        user_id=user_id,
        session_token_hash=hash_token(raw_token_1),
        expires_at=datetime.now(UTC) + timedelta(days=7),
    )
    SessionRepository.create(db_session, session_1)

    # Perform refresh rotation through service
    res = AuthService.refresh(db_session, raw_token_1)
    assert res.refresh_token != raw_token_1

    # Verify old session is marked revoked in DB
    refreshed_old_session = SessionRepository.get_by_token_hash(db_session, hash_token(raw_token_1))
    assert refreshed_old_session.is_revoked is True
    assert refreshed_old_session.revoked_at is not None

    # Verify new session is active in DB
    new_session = SessionRepository.get_by_token_hash(db_session, hash_token(res.refresh_token))
    assert new_session is not None
    assert new_session.is_revoked is False

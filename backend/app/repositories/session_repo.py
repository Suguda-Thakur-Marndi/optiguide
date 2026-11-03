import uuid
from datetime import UTC, datetime

from sqlalchemy import select, update
from sqlalchemy.orm import Session

from app.models.session import UserSession


class SessionRepository:
    """Data access repository for UserSession entities with concurrency-safe operations."""

    @staticmethod
    def create(db: Session, session: UserSession) -> UserSession:
        db.add(session)
        db.commit()
        db.refresh(session)
        return session

    @staticmethod
    def get_by_token_hash(
        db: Session,
        token_hash: str,
        for_update: bool = False,
    ) -> UserSession | None:
        stmt = select(UserSession).where(UserSession.session_token_hash == token_hash)
        if for_update and db.bind and db.bind.dialect.name == "postgresql":
            stmt = stmt.with_for_update()
        return db.execute(stmt).scalar_one_or_none()

    @staticmethod
    def get_by_id(
        db: Session,
        session_id: uuid.UUID,
        for_update: bool = False,
    ) -> UserSession | None:
        stmt = select(UserSession).where(UserSession.id == session_id)
        if for_update and db.bind and db.bind.dialect.name == "postgresql":
            stmt = stmt.with_for_update()
        return db.execute(stmt).scalar_one_or_none()

    @staticmethod
    def rotate_session_atomic(db: Session, session_id: uuid.UUID) -> bool:
        """
        Atomically conditional update marking a session as revoked.
        Returns True if this operation revoked the session, False if already revoked by a concurrent transaction.
        """
        now = datetime.now(UTC)
        stmt = (
            update(UserSession)
            .where(
                UserSession.id == session_id,
                UserSession.is_revoked.is_(False),
            )
            .values(is_revoked=True, revoked_at=now)
        )
        result = db.execute(stmt)
        db.commit()
        return result.rowcount > 0

    @staticmethod
    def rotate_and_create(
        db: Session,
        old_session_id: uuid.UUID,
        new_session: UserSession,
    ) -> bool:
        """
        Atomically revokes the old session and persists the replacement session
        within a single, isolated database transaction.
        Returns True if successful, False if the old session was already revoked.
        """
        now = datetime.now(UTC)
        stmt = (
            update(UserSession)
            .where(
                UserSession.id == old_session_id,
                UserSession.is_revoked.is_(False),
            )
            .values(is_revoked=True, revoked_at=now)
        )
        result = db.execute(stmt)
        if result.rowcount == 0:
            db.rollback()
            return False

        db.add(new_session)
        db.commit()
        db.refresh(new_session)
        return True

    @staticmethod
    def get_sessions_for_user(db: Session, user_id: uuid.UUID) -> list[UserSession]:
        stmt = (
            select(UserSession)
            .where(UserSession.user_id == user_id)
            .order_by(UserSession.created_at.desc())
        )
        return list(db.execute(stmt).scalars().all())

    @staticmethod
    def revoke_session(db: Session, session: UserSession) -> None:
        session.is_revoked = True
        session.revoked_at = datetime.now(UTC)
        db.commit()
        db.refresh(session)

    @staticmethod
    def revoke_all_for_user(db: Session, user_id: uuid.UUID) -> int:
        now = datetime.now(UTC)
        stmt = (
            update(UserSession)
            .where(
                UserSession.user_id == user_id,
                UserSession.is_revoked.is_(False),
            )
            .values(is_revoked=True, revoked_at=now)
        )
        result = db.execute(stmt)
        db.commit()
        return result.rowcount

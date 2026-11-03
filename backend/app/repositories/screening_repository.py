import uuid
from datetime import UTC, datetime

from sqlalchemy import func, select, update
from sqlalchemy.orm import Session

from app.models.screening_audit_event import ScreeningAuditEvent
from app.models.screening_consent import ScreeningConsent
from app.models.screening_session import ScreeningSession
from app.schemas.screening import ScreeningSessionStatus


class ScreeningRepository:
    """Data access repository for consent, screening sessions, and audit events."""

    # -------------------------------------------------------------------------
    # Consent Management
    # -------------------------------------------------------------------------

    @staticmethod
    def get_active_consent(db: Session, user_id: uuid.UUID) -> ScreeningConsent | None:
        """Retrieves the current active consent record for the specified user."""
        stmt = (
            select(ScreeningConsent)
            .where(
                ScreeningConsent.user_id == user_id,
                ScreeningConsent.is_active.is_(True),
            )
            .order_by(ScreeningConsent.accepted_at.desc())
        )
        return db.execute(stmt).scalars().first()

    @staticmethod
    def get_latest_consent(db: Session, user_id: uuid.UUID) -> ScreeningConsent | None:
        """Retrieves the most recent consent record (active or historical) for the user."""
        stmt = (
            select(ScreeningConsent)
            .where(ScreeningConsent.user_id == user_id)
            .order_by(ScreeningConsent.accepted_at.desc())
        )
        return db.execute(stmt).scalars().first()

    @staticmethod
    def create_consent(db: Session, consent: ScreeningConsent) -> ScreeningConsent:
        """Persists a new consent acceptance record."""
        db.add(consent)
        db.commit()
        db.refresh(consent)
        return consent

    @staticmethod
    def withdraw_consent(db: Session, consent: ScreeningConsent) -> None:
        """Marks an active consent record as withdrawn."""
        consent.is_active = False
        consent.withdrawn_at = datetime.now(UTC)
        db.commit()
        db.refresh(consent)

    # -------------------------------------------------------------------------
    # Screening Session Management
    # -------------------------------------------------------------------------

    @staticmethod
    def create_session(db: Session, session: ScreeningSession) -> ScreeningSession:
        """Persists a new screening session."""
        db.add(session)
        db.commit()
        db.refresh(session)
        return session

    @staticmethod
    def get_session_by_id(
        db: Session,
        session_id: uuid.UUID,
        for_update: bool = False,
    ) -> ScreeningSession | None:
        """Retrieves a screening session by its unique ID."""
        stmt = select(ScreeningSession).where(ScreeningSession.id == session_id)
        if for_update and db.bind and db.bind.dialect.name == "postgresql":
            stmt = stmt.with_for_update()
        return db.execute(stmt).scalar_one_or_none()

    @staticmethod
    def get_active_session_for_user(db: Session, user_id: uuid.UUID) -> ScreeningSession | None:
        """Finds any session currently in progress for the specified user."""
        stmt = (
            select(ScreeningSession)
            .where(
                ScreeningSession.user_id == user_id,
                ScreeningSession.status == ScreeningSessionStatus.IN_PROGRESS.value,
            )
            .order_by(ScreeningSession.started_at.desc())
        )
        return db.execute(stmt).scalars().first()

    @staticmethod
    def list_sessions_for_user(
        db: Session,
        user_id: uuid.UUID,
        status: str | None = None,
        limit: int = 20,
        offset: int = 0,
    ) -> tuple[list[ScreeningSession], int]:
        """
        Lists paginated screening sessions belonging exclusively to user_id.
        Optionally filters by lifecycle status.
        """
        base_query = select(ScreeningSession).where(ScreeningSession.user_id == user_id)
        count_query = (
            select(func.count())
            .select_from(ScreeningSession)
            .where(ScreeningSession.user_id == user_id)
        )

        if status:
            base_query = base_query.where(ScreeningSession.status == status)
            count_query = count_query.where(ScreeningSession.status == status)

        total = db.execute(count_query).scalar_one()

        stmt = base_query.order_by(ScreeningSession.started_at.desc()).offset(offset).limit(limit)
        items = list(db.execute(stmt).scalars().all())

        return items, total

    @staticmethod
    def update_session(db: Session, session: ScreeningSession) -> ScreeningSession:
        """Flushes and commits updates to a screening session."""
        db.commit()
        db.refresh(session)
        return session

    @staticmethod
    def cancel_active_sessions_for_user(
        db: Session,
        user_id: uuid.UUID,
        reason: str,
    ) -> int:
        """
        Cancels all in-progress sessions for a user (e.g. upon consent withdrawal).
        Returns the number of affected sessions.
        """
        now = datetime.now(UTC)
        stmt = (
            update(ScreeningSession)
            .where(
                ScreeningSession.user_id == user_id,
                ScreeningSession.status == ScreeningSessionStatus.IN_PROGRESS.value,
            )
            .values(
                status=ScreeningSessionStatus.CANCELLED.value,
                cancelled_at=now,
                cancellation_reason=reason,
            )
        )
        result = db.execute(stmt)
        db.commit()
        return result.rowcount

    # -------------------------------------------------------------------------
    # Privacy-Conscious Audit Telemetry
    # -------------------------------------------------------------------------

    @staticmethod
    def create_audit_event(db: Session, event: ScreeningAuditEvent) -> ScreeningAuditEvent:
        """Persists a screening audit event within the active transaction."""
        db.add(event)
        db.commit()
        db.refresh(event)
        return event

    @staticmethod
    def list_audit_events_for_session(
        db: Session,
        session_id: uuid.UUID,
    ) -> list[ScreeningAuditEvent]:
        """Internal diagnostic query for lifecycle audit verification."""
        stmt = (
            select(ScreeningAuditEvent)
            .where(ScreeningAuditEvent.session_id == session_id)
            .order_by(ScreeningAuditEvent.occurred_at.asc())
        )
        return list(db.execute(stmt).scalars().all())

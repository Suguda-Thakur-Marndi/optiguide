import uuid
from datetime import UTC, datetime
from typing import TYPE_CHECKING

from sqlalchemy import DateTime, ForeignKey, String, Uuid
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database.base import Base

if TYPE_CHECKING:
    from app.models.screening_audit_event import ScreeningAuditEvent
    from app.models.screening_consent import ScreeningConsent
    from app.models.user import User


class ScreeningSession(Base):
    """
    SQLAlchemy model representing a preliminary vision screening session lifecycle.
    Tracks status transitions: in_progress -> completed | cancelled.
    """

    __tablename__ = "screening_sessions"

    id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    consent_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("screening_consents.id", ondelete="RESTRICT"),
        nullable=False,
        index=True,
    )
    status: Mapped[str] = mapped_column(
        String(50),
        default="in_progress",
        nullable=False,
        index=True,
    )
    cancellation_reason: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True,
    )
    started_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(UTC),
        nullable=False,
        index=True,
    )
    completed_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )
    cancelled_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(UTC),
        nullable=False,
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(UTC),
        onupdate=lambda: datetime.now(UTC),
        nullable=False,
    )

    # Relationships
    user: Mapped["User"] = relationship("User", back_populates="screening_sessions")
    consent: Mapped["ScreeningConsent"] = relationship(
        "ScreeningConsent", back_populates="sessions"
    )
    audit_events: Mapped[list["ScreeningAuditEvent"]] = relationship(
        "ScreeningAuditEvent",
        back_populates="session",
    )

    def __repr__(self) -> str:
        return (
            f"<ScreeningSession id={self.id} user_id={self.user_id} "
            f"status={self.status} started_at={self.started_at}>"
        )

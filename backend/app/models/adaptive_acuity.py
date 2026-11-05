import uuid
from datetime import UTC, datetime

from sqlalchemy import (
    Boolean,
    DateTime,
    Float,
    ForeignKey,
    Index,
    Integer,
    String,
    Text,
    UniqueConstraint,
    Uuid,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database.base import Base


class AdaptiveAcuityTest(Base):
    """
    SQLAlchemy model managing an interactive, adaptive visual acuity screening session.
    Controls protocol progression, current challenge state, and clinical scoring server-side.
    """

    __tablename__ = "adaptive_acuity_tests"

    id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )
    session_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("screening_sessions.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    test_type: Mapped[str] = mapped_column(
        String(20),
        default="DISTANCE",
        nullable=False,
        index=True,  # 'DISTANCE' or 'NEAR'
    )
    test_eye: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        index=True,  # 'right', 'left', 'both'
    )
    optotype_type: Mapped[str] = mapped_column(
        String(30),
        default="TUMBLING_E",
        nullable=False,  # 'TUMBLING_E', 'SLOAN'
    )
    protocol_version: Mapped[str] = mapped_column(
        String(50),
        default="ISO8596_ATS_V1",
        nullable=False,
    )
    status: Mapped[str] = mapped_column(
        String(20),
        default="IN_PROGRESS",
        nullable=False,
        index=True,  # 'IN_PROGRESS', 'COMPLETED', 'CANCELLED', 'EXPIRED'
    )
    calibration_status: Mapped[str] = mapped_column(
        String(30),
        default="UNCALIBRATED",
        nullable=False,  # 'UNCALIBRATED', 'CLIENT_REPORTED', 'SERVER_VERIFIED', 'PROFESSIONALLY_VALIDATED'
    )
    calibration_data: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )
    viewing_distance_meters: Mapped[float] = mapped_column(
        Float,
        default=3.0,
        nullable=False,
    )
    user_reported_occlusion: Mapped[bool] = mapped_column(
        Boolean,
        default=True,
        nullable=False,
    )
    current_level: Mapped[int] = mapped_column(
        Integer,
        default=0,
        nullable=False,
    )
    current_attempt_sequence: Mapped[int] = mapped_column(
        Integer,
        default=1,
        nullable=False,
    )
    current_optotype: Mapped[str | None] = mapped_column(
        String(50),
        nullable=True,
    )
    # Stored strictly server-side — never exposed to client in presentation responses
    current_expected_response: Mapped[str | None] = mapped_column(
        String(50),
        nullable=True,
    )
    total_attempts: Mapped[int] = mapped_column(
        Integer,
        default=0,
        nullable=False,
    )
    correct_attempts: Mapped[int] = mapped_column(
        Integer,
        default=0,
        nullable=False,
    )
    incorrect_attempts: Mapped[int] = mapped_column(
        Integer,
        default=0,
        nullable=False,
    )
    smallest_resolved_level: Mapped[int | None] = mapped_column(
        Integer,
        nullable=True,
    )
    final_snellen: Mapped[str | None] = mapped_column(
        String(20),
        nullable=True,
    )
    final_logmar: Mapped[float | None] = mapped_column(
        Float,
        nullable=True,
    )
    final_decimal: Mapped[float | None] = mapped_column(
        Float,
        nullable=True,
    )
    assessment_id: Mapped[uuid.UUID | None] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("visual_acuity_assessments.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    started_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(UTC),
        nullable=False,
    )
    completed_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )
    cancelled_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )
    cancellation_reason: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True,
    )

    # Relationships
    attempts: Mapped[list["AdaptiveAcuityAttempt"]] = relationship(
        "AdaptiveAcuityAttempt",
        back_populates="test",
        cascade="all, delete-orphan",
        order_by="AdaptiveAcuityAttempt.attempt_sequence.asc()",
    )

    __table_args__ = (
        Index("ix_adaptive_test_user_status", "user_id", "status"),
        Index("ix_adaptive_test_session_status", "session_id", "status"),
    )


class AdaptiveAcuityAttempt(Base):
    """
    SQLAlchemy model recording an individual optotype challenge presentation and user response.
    Enforces sequence integrity and prevents duplicate or out-of-order submissions.
    """

    __tablename__ = "adaptive_acuity_attempts"

    id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )
    test_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("adaptive_acuity_tests.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    attempt_sequence: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
    )
    level: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
    )
    optotype_type: Mapped[str] = mapped_column(
        String(30),
        nullable=False,
    )
    presented_symbol: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
    )
    expected_response: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
    )
    user_response: Mapped[str | None] = mapped_column(
        String(50),
        nullable=True,
    )
    is_correct: Mapped[bool | None] = mapped_column(
        Boolean,
        nullable=True,
    )
    response_duration_ms: Mapped[int | None] = mapped_column(
        Integer,
        nullable=True,
    )
    target_size_arcmin: Mapped[float] = mapped_column(
        Float,
        nullable=False,
    )
    target_height_mm: Mapped[float | None] = mapped_column(
        Float,
        nullable=True,
    )
    target_height_px: Mapped[float | None] = mapped_column(
        Float,
        nullable=True,
    )
    # Voice modality and STT telemetry
    input_modality: Mapped[str] = mapped_column(
        String(20),
        default="MANUAL",
        server_default="MANUAL",
        nullable=False,
    )
    transcription_confidence: Mapped[float | None] = mapped_column(
        Float,
        nullable=True,
    )
    stt_provider: Mapped[str | None] = mapped_column(
        String(50),
        nullable=True,
    )
    raw_transcript: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True,
    )
    recognition_status: Mapped[str | None] = mapped_column(
        String(30),
        nullable=True,
    )
    presented_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(UTC),
        nullable=False,
    )
    answered_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )

    test: Mapped["AdaptiveAcuityTest"] = relationship(
        "AdaptiveAcuityTest",
        back_populates="attempts",
    )

    __table_args__ = (
        UniqueConstraint("test_id", "attempt_sequence", name="uq_test_attempt_sequence"),
        Index("ix_adaptive_attempt_test_seq", "test_id", "attempt_sequence"),
    )

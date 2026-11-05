"""SQLAlchemy models for the OptiGuide Complete Online Vision Screening Platform.

Supports a multi-test interactive screening workflow (inspired by modern digital
vision screening protocols) with 7 specialized modules:
  1. Visual Acuity (Distance & Near, OD/OS/OU, Tumbling E / Landolt C / Sloan)
  2. Astigmatism Radial Clock Dial Screening
  3. Contrast / Light Sensitivity Discrimination
  4. Near Vision Reading Acuity (Paragraph scales)
  5. Near Vision Duochrome (Red/Green comparison)
  6. Color Vision (Pseudoisochromatic plates)
  7. Central Vision / Amsler Distortion Questionnaire
"""

import uuid
from datetime import UTC, datetime
from typing import TYPE_CHECKING

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

if TYPE_CHECKING:
    from app.models.screening_session import ScreeningSession
    from app.models.user import User


class ScreeningCalibration(Base):
    """Stores physical display calibration and viewing distance metadata for a screening session."""

    __tablename__ = "screening_calibrations"

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
    device_category: Mapped[str] = mapped_column(
        String(50),
        default="DESKTOP",
        nullable=False,  # 'DESKTOP', 'LAPTOP', 'TABLET', 'MOBILE'
    )
    screen_width_px: Mapped[int | None] = mapped_column(Integer, nullable=True)
    screen_height_px: Mapped[int | None] = mapped_column(Integer, nullable=True)
    device_pixel_ratio: Mapped[float | None] = mapped_column(Float, nullable=True)
    calibration_method: Mapped[str] = mapped_column(
        String(50),
        default="STANDARD_CARD",
        nullable=False,  # 'STANDARD_CARD', 'COIN_REFERENCE', 'MANUAL_MEASURE', 'DEFAULT_UNVERIFIED'
    )
    calibration_status: Mapped[str] = mapped_column(
        String(50),
        default="UNCALIBRATED",
        nullable=False,  # 'UNCALIBRATED', 'CLIENT_REPORTED', 'SERVER_VERIFIED'
    )
    computed_ppi: Mapped[float | None] = mapped_column(Float, nullable=True)
    target_viewing_distance_cm: Mapped[float] = mapped_column(
        Float,
        default=40.0,
        nullable=False,
    )
    user_confirmed_distance: Mapped[bool] = mapped_column(
        Boolean,
        default=False,
        nullable=False,
    )
    calibration_notes: Mapped[str | None] = mapped_column(String(255), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(UTC),
        nullable=False,
    )

    # Relationships
    session: Mapped["ScreeningSession"] = relationship("ScreeningSession")
    user: Mapped["User"] = relationship("User")


class ScreeningTestInstance(Base):
    """Represents a specific test module execution within a screening session.

    Enforces finite state transitions: NOT_STARTED -> IN_PROGRESS -> COMPLETED | CANCELLED | SKIPPED.
    """

    __tablename__ = "screening_test_instances"

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
        String(50),
        nullable=False,
        index=True,
        # 'VISUAL_ACUITY', 'ASTIGMATISM', 'CONTRAST_SENSITIVITY',
        # 'NEAR_VISION_READING', 'NEAR_VISION_DUOCHROME', 'COLOR_VISION', 'CENTRAL_VISION_AMSLER'
    )
    status: Mapped[str] = mapped_column(
        String(30),
        default="NOT_STARTED",
        nullable=False,
        index=True,
        # 'NOT_STARTED', 'IN_PROGRESS', 'COMPLETED', 'SKIPPED', 'CANCELLED'
    )
    eye: Mapped[str] = mapped_column(
        String(20),
        default="OU",
        nullable=False,
        index=True,  # 'OD', 'OS', 'OU'
    )
    viewing_condition: Mapped[str] = mapped_column(
        String(30),
        default="WITH_GLASSES",
        nullable=False,  # 'WITH_GLASSES', 'WITHOUT_GLASSES', 'UNASSISTED'
    )
    current_step: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    total_steps: Mapped[int] = mapped_column(Integer, default=1, nullable=False)
    protocol_version: Mapped[str] = mapped_column(
        String(50),
        default="OPTIGUIDE_V1",
        nullable=False,
    )
    result_classification: Mapped[str | None] = mapped_column(
        String(50),
        nullable=True,
        # 'NO_CONCERN_REPORTED', 'OBSERVATION_REQUIRES_FOLLOW_UP', 'INCONCLUSIVE', 'INCOMPLETE', 'UNCALIBRATED'
    )
    result_details: Mapped[str | None] = mapped_column(Text, nullable=True)
    clinical_observation: Mapped[str | None] = mapped_column(String(500), nullable=True)
    started_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    cancelled_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    cancellation_reason: Mapped[str | None] = mapped_column(String(255), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(UTC),
        nullable=False,
    )

    # Relationships
    session: Mapped["ScreeningSession"] = relationship("ScreeningSession")
    user: Mapped["User"] = relationship("User")
    responses: Mapped[list["ScreeningTestResponse"]] = relationship(
        "ScreeningTestResponse",
        back_populates="test_instance",
        cascade="all, delete-orphan",
        order_by="ScreeningTestResponse.step_index.asc()",
    )

    __table_args__ = (
        Index("ix_test_inst_session_type", "session_id", "test_type"),
        Index("ix_test_inst_user_status", "user_id", "status"),
    )


class ScreeningTestResponse(Base):
    """Records an individual stimulus response within a test instance.

    Stores expected answers strictly on the server to prevent client cheating.
    """

    __tablename__ = "screening_test_responses"

    id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )
    test_instance_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("screening_test_instances.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    step_index: Mapped[int] = mapped_column(Integer, nullable=False)
    stimulus_id: Mapped[str] = mapped_column(String(50), nullable=False)
    stimulus_version: Mapped[str] = mapped_column(String(50), default="1.0", nullable=False)
    expected_answer: Mapped[str] = mapped_column(String(100), nullable=False)
    user_response: Mapped[str] = mapped_column(String(100), nullable=False)
    is_correct: Mapped[bool | None] = mapped_column(Boolean, nullable=True)
    response_time_ms: Mapped[int | None] = mapped_column(Integer, nullable=True)
    details: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(UTC),
        nullable=False,
    )

    # Relationships
    test_instance: Mapped["ScreeningTestInstance"] = relationship(
        "ScreeningTestInstance", back_populates="responses"
    )

    __table_args__ = (
        UniqueConstraint("test_instance_id", "step_index", name="uq_test_response_step"),
    )


class ScreeningFinalReport(Base):
    """Consolidated preliminary vision screening report generated upon session completion."""

    __tablename__ = "screening_final_reports"

    id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )
    session_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("screening_sessions.id", ondelete="CASCADE"),
        nullable=False,
        unique=True,
        index=True,
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    report_number: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        unique=True,
        index=True,
    )
    overall_classification: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        # 'NO_CONCERN_REPORTED', 'OBSERVATION_REQUIRES_FOLLOW_UP', 'INCONCLUSIVE', 'INCOMPLETE', 'UNCALIBRATED'
    )
    protocol_version: Mapped[str] = mapped_column(
        String(50), default="OPTIGUIDE_V1", nullable=False
    )
    completed_tests_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    skipped_tests_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    summary_content: Mapped[str] = mapped_column(Text, nullable=False)  # JSON formatted
    follow_up_recommendation: Mapped[str] = mapped_column(String(500), nullable=False)
    professional_referral_indicated: Mapped[bool] = mapped_column(
        Boolean, default=False, nullable=False
    )
    limitations_disclaimer: Mapped[str] = mapped_column(Text, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(UTC),
        nullable=False,
    )

    # Relationships
    session: Mapped["ScreeningSession"] = relationship("ScreeningSession")
    user: Mapped["User"] = relationship("User")

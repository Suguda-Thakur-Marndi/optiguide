import uuid
from datetime import UTC, datetime
from typing import TYPE_CHECKING

from sqlalchemy import Boolean, DateTime, Float, ForeignKey, String, Text, Uuid
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database.base import Base

if TYPE_CHECKING:
    from app.models.screening_session import ScreeningSession
    from app.models.user import User


class PDAssessment(Base):
    """
    Pupillary Distance (PD) measurement record.
    Tracks binocular and monocular millimeter values, estimation method,
    calibration metadata, and verification/confirmation lifecycle.
    """

    __tablename__ = "pd_assessments"

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
    session_id: Mapped[uuid.UUID | None] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("screening_sessions.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    measurement_type: Mapped[str] = mapped_column(
        String(20),
        default="BINOCULAR",
        nullable=False,
    )  # BINOCULAR, MONOCULAR
    binocular_pd_mm: Mapped[float] = mapped_column(
        Float,
        nullable=False,
    )  # Physiological adult range: 45.0 - 80.0 mm
    monocular_left_pd_mm: Mapped[float | None] = mapped_column(
        Float,
        nullable=True,
    )  # Physiological range: 22.0 - 40.0 mm
    monocular_right_pd_mm: Mapped[float | None] = mapped_column(
        Float,
        nullable=True,
    )  # Physiological range: 22.0 - 40.0 mm
    unit: Mapped[str] = mapped_column(
        String(10),
        default="mm",
        nullable=False,
    )
    estimation_method: Mapped[str] = mapped_column(
        String(64),
        default="REFERENCE_CARD",
        nullable=False,
    )  # REFERENCE_CARD, SENSOR_ESTIMATE, MANUAL_CLINICAL
    is_calibrated: Mapped[bool] = mapped_column(
        Boolean,
        default=False,
        nullable=False,
    )
    is_server_verified: Mapped[bool] = mapped_column(
        Boolean,
        default=False,
        nullable=False,
    )
    calibration_metadata: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )  # JSON-serialized camera/screen calibration data
    client_confidence_score: Mapped[float | None] = mapped_column(
        Float,
        nullable=True,
    )
    server_confidence_score: Mapped[float | None] = mapped_column(
        Float,
        nullable=True,
    )
    confidence_score: Mapped[float | None] = mapped_column(
        Float,
        nullable=True,
    )  # Effective server-validated confidence rating (0.0 to 1.0)
    is_pediatric: Mapped[bool] = mapped_column(
        Boolean,
        default=False,
        nullable=False,
    )
    device_info: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )
    status: Mapped[str] = mapped_column(
        String(32),
        default="ESTIMATED",
        nullable=False,
        index=True,
    )  # ESTIMATED, USER_CONFIRMED, REJECTED, REQUIRES_PROFESSIONAL_MEASUREMENT, PROFESSIONALLY_REVIEWED
    rejection_reason: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )
    reviewed_by_professional_id: Mapped[uuid.UUID | None] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
    )
    professional_review_notes: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )
    recorded_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(UTC),
        nullable=False,
    )
    confirmed_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )

    # Relationships
    user: Mapped["User"] = relationship(
        "User",
        foreign_keys=[user_id],
    )
    session: Mapped["ScreeningSession | None"] = relationship(
        "ScreeningSession",
        foreign_keys=[session_id],
    )

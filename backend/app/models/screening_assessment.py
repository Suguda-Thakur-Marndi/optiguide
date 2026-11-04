import uuid
from datetime import UTC, datetime
from typing import TYPE_CHECKING

from sqlalchemy import Boolean, DateTime, Float, ForeignKey, Integer, String, Text, Uuid
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database.base import Base

if TYPE_CHECKING:
    from app.models.screening_session import ScreeningSession
    from app.models.user import User


class VisualAcuityAssessment(Base):
    """
    SQLAlchemy model recording distance and near visual acuity assessments.
    Supports Snellen fractions, logMAR conversions, decimal acuity,
    and physical viewing distance calibration parameters.
    """

    __tablename__ = "visual_acuity_assessments"

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
    test_eye: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        index=True,  # 'right', 'left', 'both'
    )
    snellen_fraction: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
    )
    logmar: Mapped[float] = mapped_column(
        Float,
        nullable=False,
    )
    decimal_acuity: Mapped[float] = mapped_column(
        Float,
        nullable=False,
    )
    tested_distance_meters: Mapped[float] = mapped_column(
        Float,
        default=0.6,
        nullable=False,
    )
    unassisted_or_corrected: Mapped[str] = mapped_column(
        String(30),
        default="unassisted",
        nullable=False,
    )
    near_reading_label: Mapped[str | None] = mapped_column(
        String(20),
        nullable=True,
    )
    near_reading_distance_cm: Mapped[float | None] = mapped_column(
        Float,
        nullable=True,
    )
    is_calibrated: Mapped[bool] = mapped_column(
        Boolean,
        default=False,
        nullable=False,
    )
    calibration_metadata: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )
    observations: Mapped[str | None] = mapped_column(
        String(500),
        nullable=True,
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(UTC),
        nullable=False,
    )

    # Relationships
    session: Mapped["ScreeningSession"] = relationship(
        "ScreeningSession",
        back_populates="acuity_assessments",
    )
    user: Mapped["User"] = relationship("User")

    def __repr__(self) -> str:
        return (
            f"<VisualAcuityAssessment id={self.id} session_id={self.session_id} "
            f"eye={self.test_eye} snellen={self.snellen_fraction} logmar={self.logmar}>"
        )


class AstigmatismAssessment(Base):
    """
    SQLAlchemy model recording astigmatic clock dial / radial fan screening observations.
    Evaluates meridian clarity variance without computing cylinder powers.
    """

    __tablename__ = "astigmatism_assessments"

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
    chart_type: Mapped[str] = mapped_column(
        String(50),
        default="clock_dial",
        nullable=False,
    )
    has_uniform_clarity: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
    )
    indicated_axes: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )
    sharpest_meridian_hour: Mapped[int | None] = mapped_column(
        Integer,
        nullable=True,
    )
    screening_observation: Mapped[str] = mapped_column(
        String(500),
        nullable=False,
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(UTC),
        nullable=False,
    )

    # Relationships
    session: Mapped["ScreeningSession"] = relationship(
        "ScreeningSession",
        back_populates="astigmatism_assessments",
    )
    user: Mapped["User"] = relationship("User")

    def __repr__(self) -> str:
        return (
            f"<AstigmatismAssessment id={self.id} session_id={self.session_id} "
            f"uniform={self.has_uniform_clarity} meridian={self.sharpest_meridian_hour}>"
        )


class ColorVisionAssessment(Base):
    """
    SQLAlchemy model recording pseudoisochromatic plate color vision discrimination.
    Assesses red-green and general color variance according to standard clinical screening protocols.
    """

    __tablename__ = "color_vision_assessments"

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
    test_protocol: Mapped[str] = mapped_column(
        String(50),
        default="pseudoisochromatic_plates",
        nullable=False,
    )
    total_plates_presented: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
    )
    correct_plate_count: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
    )
    deficiency_indicated: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
    )
    deficiency_type: Mapped[str] = mapped_column(
        String(50),
        default="none",
        nullable=False,
    )
    responses_detail: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )
    screening_observation: Mapped[str] = mapped_column(
        String(500),
        nullable=False,
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(UTC),
        nullable=False,
    )

    # Relationships
    session: Mapped["ScreeningSession"] = relationship(
        "ScreeningSession",
        back_populates="color_vision_assessments",
    )
    user: Mapped["User"] = relationship("User")

    def __repr__(self) -> str:
        return (
            f"<ColorVisionAssessment id={self.id} session_id={self.session_id} "
            f"score={self.correct_plate_count}/{self.total_plates_presented} deficiency={self.deficiency_type}>"
        )

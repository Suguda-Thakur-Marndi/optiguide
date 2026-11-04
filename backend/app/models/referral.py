import uuid
from datetime import UTC, datetime
from typing import TYPE_CHECKING

from sqlalchemy import Boolean, DateTime, ForeignKey, Integer, String, Text, Uuid
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database.base import Base

if TYPE_CHECKING:
    from app.models.screening_session import ScreeningSession
    from app.models.user import User


class ProfessionalProfile(Base):
    """
    Tracks optometrist / eye care professional credentials, license details,
    and administrative verification status.
    """

    __tablename__ = "professional_profiles"

    id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        unique=True,
        nullable=False,
        index=True,
    )
    license_number: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
        index=True,
    )
    issuing_authority: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
    )
    registration_year: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
    )
    qualification_title: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
    )
    verification_status: Mapped[str] = mapped_column(
        String(32),
        default="PENDING",
        nullable=False,
        index=True,
    )  # PENDING, VERIFIED, REJECTED, SUSPENDED
    verified_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )
    verified_by_admin_id: Mapped[uuid.UUID | None] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
    )
    rejection_reason: Mapped[str | None] = mapped_column(
        Text,
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
    user: Mapped["User"] = relationship(
        "User",
        foreign_keys=[user_id],
        back_populates="professional_profile",
    )


class PatientReferral(Base):
    """
    Formal referral record generated from screening findings.
    Associates the patient, original screening session, clinical priority, and status.
    """

    __tablename__ = "patient_referrals"

    id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )
    patient_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    session_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("screening_sessions.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    referral_reason: Mapped[str] = mapped_column(
        Text,
        nullable=False,
    )
    clinical_priority: Mapped[str] = mapped_column(
        String(32),
        default="ROUTINE",
        nullable=False,
        index=True,
    )  # ROUTINE, PRIORITY, URGENT
    status: Mapped[str] = mapped_column(
        String(32),
        default="PENDING",
        nullable=False,
        index=True,
    )  # PENDING, SHARED, ACCEPTED, IN_REVIEW, COMPLETED, CANCELLED
    notes: Mapped[str | None] = mapped_column(
        Text,
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
    patient: Mapped["User"] = relationship(
        "User",
        foreign_keys=[patient_id],
        back_populates="referrals",
    )
    session: Mapped["ScreeningSession"] = relationship(
        "ScreeningSession",
        foreign_keys=[session_id],
    )
    shares: Mapped[list["PatientRecordShare"]] = relationship(
        "PatientRecordShare",
        back_populates="referral",
        cascade="all, delete-orphan",
    )
    reviews: Mapped[list["ClinicalReview"]] = relationship(
        "ClinicalReview",
        back_populates="referral",
        cascade="all, delete-orphan",
    )
    audit_events: Mapped[list["ReferralAuditEvent"]] = relationship(
        "ReferralAuditEvent",
        back_populates="referral",
        cascade="all, delete-orphan",
    )


class PatientRecordShare(Base):
    """
    Explicit, patient-controlled delegation of a screening referral record
    to a verified eye care professional.
    """

    __tablename__ = "patient_record_shares"

    id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )
    referral_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("patient_referrals.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    patient_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    professional_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    access_status: Mapped[str] = mapped_column(
        String(32),
        default="ACTIVE",
        nullable=False,
        index=True,
    )  # ACTIVE, REVOKED, EXPIRED
    granted_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(UTC),
        nullable=False,
    )
    expires_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )
    revoked_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )

    # Relationships
    referral: Mapped["PatientReferral"] = relationship(
        "PatientReferral",
        back_populates="shares",
    )
    patient: Mapped["User"] = relationship(
        "User",
        foreign_keys=[patient_id],
    )
    professional: Mapped["User"] = relationship(
        "User",
        foreign_keys=[professional_id],
    )


class ClinicalReview(Base):
    """
    Independent professional observations recorded by an authorized optometrist
    reviewing a shared patient referral.
    """

    __tablename__ = "clinical_reviews"

    id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )
    referral_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("patient_referrals.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    professional_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    review_status: Mapped[str] = mapped_column(
        String(32),
        default="IN_PROGRESS",
        nullable=False,
        index=True,
    )  # IN_PROGRESS, EXAMINATION_RECOMMENDED, COMPLETED
    professional_observations: Mapped[str] = mapped_column(
        Text,
        nullable=False,
    )
    in_person_exam_recommended: Mapped[bool] = mapped_column(
        Boolean,
        default=False,
        nullable=False,
    )
    recommended_exam_timeframe: Mapped[str | None] = mapped_column(
        String(64),
        nullable=True,
    )
    closed_at: Mapped[datetime | None] = mapped_column(
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
    referral: Mapped["PatientReferral"] = relationship(
        "PatientReferral",
        back_populates="reviews",
    )
    professional: Mapped["User"] = relationship(
        "User",
        foreign_keys=[professional_id],
    )


class ReferralAuditEvent(Base):
    """
    Immutable audit ledger for security-sensitive referral lifecycle events,
    delegated record shares, revocations, and clinical review submissions.
    """

    __tablename__ = "referral_audit_events"

    id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )
    referral_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("patient_referrals.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    actor_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    actor_role: Mapped[str] = mapped_column(
        String(32),
        nullable=False,
    )
    action: Mapped[str] = mapped_column(
        String(64),
        nullable=False,
        index=True,
    )
    previous_state: Mapped[str | None] = mapped_column(
        String(32),
        nullable=True,
    )
    new_state: Mapped[str | None] = mapped_column(
        String(32),
        nullable=True,
    )
    occurred_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(UTC),
        nullable=False,
        index=True,
    )
    metadata_json: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )

    # Relationships
    referral: Mapped["PatientReferral"] = relationship(
        "PatientReferral",
        back_populates="audit_events",
    )
    actor: Mapped["User"] = relationship(
        "User",
        foreign_keys=[actor_id],
    )

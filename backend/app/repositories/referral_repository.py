import uuid
from datetime import UTC, datetime

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.models.referral import (
    ClinicalReview,
    PatientRecordShare,
    PatientReferral,
    ProfessionalProfile,
)


class ReferralRepository:
    """Database persistence operations for professional profiles, referrals, and clinical reviews."""

    # -------------------------------------------------------------------------
    # Professional Profiles
    # -------------------------------------------------------------------------
    @staticmethod
    def get_profile_by_user_id(db: Session, user_id: uuid.UUID) -> ProfessionalProfile | None:
        stmt = select(ProfessionalProfile).where(ProfessionalProfile.user_id == user_id)
        return db.execute(stmt).scalar_one_or_none()

    @staticmethod
    def get_profile_by_id(db: Session, profile_id: uuid.UUID) -> ProfessionalProfile | None:
        stmt = select(ProfessionalProfile).where(ProfessionalProfile.id == profile_id)
        return db.execute(stmt).scalar_one_or_none()

    @staticmethod
    def create_profile(db: Session, profile: ProfessionalProfile) -> ProfessionalProfile:
        db.add(profile)
        db.commit()
        db.refresh(profile)
        return profile

    @staticmethod
    def update_profile(db: Session, profile: ProfessionalProfile) -> ProfessionalProfile:
        db.commit()
        db.refresh(profile)
        return profile

    @staticmethod
    def list_profiles(
        db: Session, status: str | None = None, limit: int = 20, offset: int = 0
    ) -> tuple[list[ProfessionalProfile], int]:
        stmt = select(ProfessionalProfile)
        count_stmt = select(func.count()).select_from(ProfessionalProfile)
        if status:
            stmt = stmt.where(ProfessionalProfile.verification_status == status)
            count_stmt = count_stmt.where(ProfessionalProfile.verification_status == status)

        total = db.execute(count_stmt).scalar() or 0
        items = (
            db.execute(
                stmt.order_by(ProfessionalProfile.created_at.desc()).limit(limit).offset(offset)
            )
            .scalars()
            .all()
        )
        return list(items), total

    # -------------------------------------------------------------------------
    # Patient Referrals
    # -------------------------------------------------------------------------
    @staticmethod
    def create_referral(db: Session, referral: PatientReferral) -> PatientReferral:
        db.add(referral)
        db.commit()
        db.refresh(referral)
        return referral

    @staticmethod
    def get_referral_by_id(db: Session, referral_id: uuid.UUID) -> PatientReferral | None:
        stmt = select(PatientReferral).where(PatientReferral.id == referral_id)
        return db.execute(stmt).scalar_one_or_none()

    @staticmethod
    def list_referrals_for_patient(
        db: Session, patient_id: uuid.UUID, limit: int = 20, offset: int = 0
    ) -> tuple[list[PatientReferral], int]:
        stmt = select(PatientReferral).where(PatientReferral.patient_id == patient_id)
        count_stmt = (
            select(func.count())
            .select_from(PatientReferral)
            .where(PatientReferral.patient_id == patient_id)
        )
        total = db.execute(count_stmt).scalar() or 0
        items = (
            db.execute(stmt.order_by(PatientReferral.created_at.desc()).limit(limit).offset(offset))
            .scalars()
            .all()
        )
        return list(items), total

    @staticmethod
    def update_referral(db: Session, referral: PatientReferral) -> PatientReferral:
        db.commit()
        db.refresh(referral)
        return referral

    # -------------------------------------------------------------------------
    # Patient Record Shares
    # -------------------------------------------------------------------------
    @staticmethod
    def create_share(db: Session, share: PatientRecordShare) -> PatientRecordShare:
        db.add(share)
        db.commit()
        db.refresh(share)
        return share

    @staticmethod
    def get_share_by_id(db: Session, share_id: uuid.UUID) -> PatientRecordShare | None:
        stmt = select(PatientRecordShare).where(PatientRecordShare.id == share_id)
        return db.execute(stmt).scalar_one_or_none()

    @staticmethod
    def get_active_share(
        db: Session, referral_id: uuid.UUID, professional_id: uuid.UUID
    ) -> PatientRecordShare | None:
        now = datetime.now(UTC)
        stmt = (
            select(PatientRecordShare)
            .where(
                PatientRecordShare.referral_id == referral_id,
                PatientRecordShare.professional_id == professional_id,
                PatientRecordShare.access_status == "ACTIVE",
            )
            .where(
                (PatientRecordShare.expires_at.is_(None)) | (PatientRecordShare.expires_at > now)
            )
        )
        return db.execute(stmt).scalar_one_or_none()

    @staticmethod
    def list_shares_for_referral(db: Session, referral_id: uuid.UUID) -> list[PatientRecordShare]:
        stmt = select(PatientRecordShare).where(PatientRecordShare.referral_id == referral_id)
        return list(db.execute(stmt.order_by(PatientRecordShare.granted_at.desc())).scalars().all())

    @staticmethod
    def list_active_shares_for_professional(
        db: Session, professional_id: uuid.UUID, limit: int = 20, offset: int = 0
    ) -> tuple[list[PatientRecordShare], int]:
        now = datetime.now(UTC)
        stmt = (
            select(PatientRecordShare)
            .where(
                PatientRecordShare.professional_id == professional_id,
                PatientRecordShare.access_status == "ACTIVE",
            )
            .where(
                (PatientRecordShare.expires_at.is_(None)) | (PatientRecordShare.expires_at > now)
            )
        )
        count_stmt = (
            select(func.count())
            .select_from(PatientRecordShare)
            .where(
                PatientRecordShare.professional_id == professional_id,
                PatientRecordShare.access_status == "ACTIVE",
            )
            .where(
                (PatientRecordShare.expires_at.is_(None)) | (PatientRecordShare.expires_at > now)
            )
        )
        total = db.execute(count_stmt).scalar() or 0
        items = (
            db.execute(
                stmt.order_by(PatientRecordShare.granted_at.desc()).limit(limit).offset(offset)
            )
            .scalars()
            .all()
        )
        return list(items), total

    @staticmethod
    def update_share(db: Session, share: PatientRecordShare) -> PatientRecordShare:
        db.commit()
        db.refresh(share)
        return share

    # -------------------------------------------------------------------------
    # Clinical Reviews
    # -------------------------------------------------------------------------
    @staticmethod
    def create_review(db: Session, review: ClinicalReview) -> ClinicalReview:
        db.add(review)
        db.commit()
        db.refresh(review)
        return review

    @staticmethod
    def get_review_by_id(db: Session, review_id: uuid.UUID) -> ClinicalReview | None:
        stmt = select(ClinicalReview).where(ClinicalReview.id == review_id)
        return db.execute(stmt).scalar_one_or_none()

    @staticmethod
    def list_reviews_for_referral(db: Session, referral_id: uuid.UUID) -> list[ClinicalReview]:
        stmt = select(ClinicalReview).where(ClinicalReview.referral_id == referral_id)
        return list(db.execute(stmt.order_by(ClinicalReview.created_at.asc())).scalars().all())

    @staticmethod
    def update_review(db: Session, review: ClinicalReview) -> ClinicalReview:
        db.commit()
        db.refresh(review)
        return review

import json
import uuid
from datetime import UTC, datetime, timedelta
from typing import ClassVar

from sqlalchemy.orm import Session

from app.core.exceptions import (
    EntityNotFoundException,
    ForbiddenException,
    ValidationException,
)
from app.models.referral import (
    ClinicalReview,
    PatientRecordShare,
    PatientReferral,
    ProfessionalProfile,
    ReferralAuditEvent,
)
from app.models.user import User
from app.repositories.referral_repository import ReferralRepository
from app.repositories.screening_repository import ScreeningRepository
from app.repositories.user_repo import UserRepository
from app.schemas.auth import UserRole
from app.schemas.clinical_assessments import (
    AstigmatismResponse,
    ColorVisionResponse,
    VisualAcuityResponse,
)
from app.schemas.referral import (
    ClinicalReviewCreateRequest,
    ClinicalReviewResponse,
    PatientRecordShareRequest,
    PatientRecordShareResponse,
    PatientReferralCreateRequest,
    PatientReferralResponse,
    ProfessionalApplyRequest,
    ProfessionalProfileResponse,
    SharedScreeningDetailsResponse,
)


class ReferralService:
    """Business logic for eye care professional verification, patient referrals, record sharing, and reviews."""

    VALID_REFERRAL_TRANSITIONS: ClassVar[dict[str, list[str]]] = {
        "PENDING": ["SHARED", "IN_REVIEW", "COMPLETED", "CLOSED", "REJECTED"],
        "SHARED": ["IN_REVIEW", "COMPLETED", "CLOSED", "REJECTED"],
        "IN_REVIEW": ["COMPLETED", "CLOSED", "REJECTED"],
        "COMPLETED": ["CLOSED"],
        "CLOSED": [],
        "REJECTED": [],
    }

    @classmethod
    def compute_derived_clinical_priority(cls, db: Session, session_id: uuid.UUID) -> str:
        """
        Derives trusted clinical referral priority from linked screening session findings.
        Prevents patients from self-assigning arbitrary emergency/urgent priority.
        """
        acuity_list = ScreeningRepository.list_acuity_assessments_for_session(db, session_id)
        astig_list = ScreeningRepository.list_astigmatism_assessments_for_session(db, session_id)
        color_list = ScreeningRepository.list_color_vision_assessments_for_session(db, session_id)

        max_logmar = max((a.logmar for a in acuity_list), default=-1.0)
        logmars = {a.test_eye.lower(): a.logmar for a in acuity_list}
        diff = (
            abs(logmars["right"] - logmars["left"])
            if ("right" in logmars and "left" in logmars)
            else 0.0
        )

        has_astig = any(not a.has_uniform_clarity for a in astig_list)
        has_color_def = any(c.deficiency_indicated for c in color_list)

        if max_logmar >= 0.70 or diff >= 0.40:
            return "URGENT"
        if max_logmar >= 0.40 or diff >= 0.30 or has_astig or has_color_def:
            return "PRIORITY"
        return "ROUTINE"

    @classmethod
    def transition_status(
        cls,
        db: Session,
        referral: PatientReferral,
        new_status: str,
        actor: User,
        reason: str | None = None,
        commit: bool = True,
    ) -> PatientReferral:
        """Enforces canonical referral lifecycle transitions with immutable audit logging."""
        current = referral.status
        if current == new_status:
            return referral

        # Prevent closed referrals from being reopened
        if current == "CLOSED":
            raise ValidationException(
                "Invalid referral status transition: Closed referrals cannot be reopened."
            )

        allowed = cls.VALID_REFERRAL_TRANSITIONS.get(current, [])
        if new_status not in allowed:
            raise ValidationException(
                f"Invalid referral status transition: Cannot transition from '{current}' to '{new_status}'."
            )

        now = datetime.now(UTC)
        referral.status = new_status
        referral.updated_at = now
        db.add(referral)

        audit = ReferralAuditEvent(
            referral_id=referral.id,
            actor_id=actor.id,
            actor_role=actor.role,
            action="STATUS_TRANSITION",
            previous_state=current,
            new_state=new_status,
            occurred_at=now,
            metadata_json=json.dumps({"reason": reason}) if reason else None,
        )
        db.add(audit)
        if commit:
            db.commit()
            db.refresh(referral)
        else:
            db.flush()
        return referral

    # -------------------------------------------------------------------------
    # 1. Professional Verification
    # -------------------------------------------------------------------------
    @staticmethod
    def apply_for_verification(
        db: Session, user: User, payload: ProfessionalApplyRequest
    ) -> ProfessionalProfileResponse:
        allowed_roles = {UserRole.OPTOMETRIST.value, UserRole.EYE_CARE_PROFESSIONAL.value}
        if user.role not in allowed_roles:
            raise ForbiddenException(
                "Only registered Optometrists / Eye Care Professionals can submit professional credentials."
            )

        existing = ReferralRepository.get_profile_by_user_id(db, user.id)
        now = datetime.now(UTC)
        if existing:
            # Update existing profile
            existing.license_number = payload.license_number.strip()
            existing.issuing_authority = payload.issuing_authority.strip()
            existing.registration_year = payload.registration_year
            existing.qualification_title = payload.qualification_title.strip()
            existing.verification_status = "PENDING"
            existing.rejection_reason = None
            existing.verified_at = None
            existing.verified_by_admin_id = None
            existing.updated_at = now
            updated = ReferralRepository.update_profile(db, existing)
            return ProfessionalProfileResponse.model_validate(updated)

        profile = ProfessionalProfile(
            user_id=user.id,
            license_number=payload.license_number.strip(),
            issuing_authority=payload.issuing_authority.strip(),
            registration_year=payload.registration_year,
            qualification_title=payload.qualification_title.strip(),
            verification_status="PENDING",
            created_at=now,
            updated_at=now,
        )
        created = ReferralRepository.create_profile(db, profile)
        return ProfessionalProfileResponse.model_validate(created)

    @staticmethod
    def get_my_profile(db: Session, user: User) -> ProfessionalProfileResponse:
        profile = ReferralRepository.get_profile_by_user_id(db, user.id)
        if not profile:
            raise EntityNotFoundException("ProfessionalProfile", str(user.id))
        return ProfessionalProfileResponse.model_validate(profile)

    @staticmethod
    def admin_verify_professional(
        db: Session,
        admin_user: User,
        profile_id: uuid.UUID,
        action: str,
        rejection_reason: str | None = None,
    ) -> ProfessionalProfileResponse:
        profile = ReferralRepository.get_profile_by_id(db, profile_id)
        if not profile:
            raise EntityNotFoundException("ProfessionalProfile", str(profile_id))

        target_user = UserRepository.get_by_id(db, profile.user_id)
        if not target_user:
            raise EntityNotFoundException("User", str(profile.user_id))

        now = datetime.now(UTC)
        if action == "VERIFY":
            profile.verification_status = "VERIFIED"
            profile.verified_at = now
            profile.verified_by_admin_id = admin_user.id
            profile.rejection_reason = None
            target_user.is_verified = True
        elif action == "REJECT":
            if not rejection_reason:
                raise ValidationException(
                    "Rejection reason is mandatory when rejecting credentials."
                )
            profile.verification_status = "REJECTED"
            profile.rejection_reason = rejection_reason.strip()
            profile.verified_at = None
            target_user.is_verified = False
        elif action == "SUSPEND":
            profile.verification_status = "SUSPENDED"
            profile.rejection_reason = (
                rejection_reason.strip()
                if rejection_reason
                else "Account suspended by administrator."
            )
            target_user.is_verified = False
        elif action == "REACTIVATE":
            profile.verification_status = "VERIFIED"
            profile.rejection_reason = None
            target_user.is_verified = True

        profile.updated_at = now
        ReferralRepository.update_profile(db, profile)
        UserRepository.update(db, target_user)
        return ProfessionalProfileResponse.model_validate(profile)

    @staticmethod
    def list_pending_profiles(
        db: Session, status: str | None = "PENDING", limit: int = 20, offset: int = 0
    ) -> tuple[list[ProfessionalProfileResponse], int]:
        items, total = ReferralRepository.list_profiles(
            db, status=status, limit=limit, offset=offset
        )
        return [ProfessionalProfileResponse.model_validate(i) for i in items], total

    # -------------------------------------------------------------------------
    # 2. Patient Referrals
    # -------------------------------------------------------------------------
    @classmethod
    def create_referral(
        cls, db: Session, patient: User, payload: PatientReferralCreateRequest
    ) -> PatientReferralResponse:
        session = ScreeningRepository.get_session_by_id_for_user(db, payload.session_id, patient.id)
        if not session:
            raise EntityNotFoundException("ScreeningSession", str(payload.session_id))

        derived_priority = cls.compute_derived_clinical_priority(db, session.id)
        # Protect against patient self-assigning priority without clinical findings
        if (
            payload.clinical_priority in ("URGENT", "PRIORITY")
            and payload.clinical_priority != derived_priority
        ):
            raise ValidationException(
                f"Referral priority cannot be self-assigned to '{payload.clinical_priority}' without "
                f"supporting high-risk clinical assessment findings. "
                f"Triage priority is derived server-side from objective clinical screening findings ('{derived_priority}')."
            )

        now = datetime.now(UTC)
        referral = PatientReferral(
            patient_id=patient.id,
            session_id=session.id,
            referral_reason=payload.referral_reason.strip(),
            clinical_priority=derived_priority,
            status="PENDING",
            notes=payload.notes.strip() if payload.notes else None,
            created_at=now,
            updated_at=now,
        )
        try:
            db.add(referral)
            db.flush()

            audit = ReferralAuditEvent(
                referral_id=referral.id,
                actor_id=patient.id,
                actor_role=patient.role,
                action="REFERRAL_CREATED",
                previous_state=None,
                new_state="PENDING",
                occurred_at=now,
                metadata_json=json.dumps(
                    {
                        "clinical_priority": derived_priority,
                        "session_id": str(session.id),
                    }
                ),
            )
            db.add(audit)
            db.commit()
            db.refresh(referral)
        except Exception:
            db.rollback()
            raise

        resp = PatientReferralResponse.model_validate(referral)
        resp.patient_name = patient.full_name
        resp.patient_email = patient.email
        return resp

    @staticmethod
    def list_my_referrals(
        db: Session, patient: User, limit: int = 20, offset: int = 0
    ) -> tuple[list[PatientReferralResponse], int]:
        items, total = ReferralRepository.list_referrals_for_patient(
            db, patient.id, limit=limit, offset=offset
        )
        result = []
        for i in items:
            resp = PatientReferralResponse.model_validate(i)
            resp.patient_name = patient.full_name
            resp.patient_email = patient.email
            result.append(resp)
        return result, total

    @staticmethod
    def get_referral(db: Session, user: User, referral_id: uuid.UUID) -> PatientReferralResponse:
        referral = ReferralRepository.get_referral_by_id(db, referral_id)
        if not referral:
            raise EntityNotFoundException("PatientReferral", str(referral_id))

        # Check access: patient owner, admin, or shared professional
        is_owner = referral.patient_id == user.id
        is_admin = user.role == UserRole.ADMIN.value
        has_share = ReferralRepository.get_active_share(db, referral.id, user.id) is not None

        if not (is_owner or is_admin or has_share):
            raise EntityNotFoundException("PatientReferral", str(referral_id))

        patient = UserRepository.get_by_id(db, referral.patient_id)
        resp = PatientReferralResponse.model_validate(referral)
        if patient:
            resp.patient_name = patient.full_name
            resp.patient_email = patient.email
        return resp

    # -------------------------------------------------------------------------
    # 3. Patient Record Sharing & Delegation
    # -------------------------------------------------------------------------
    @staticmethod
    def share_referral(
        db: Session, patient: User, referral_id: uuid.UUID, payload: PatientRecordShareRequest
    ) -> PatientRecordShareResponse:
        referral = ReferralRepository.get_referral_by_id(db, referral_id)
        if not referral or referral.patient_id != patient.id:
            raise EntityNotFoundException("PatientReferral", str(referral_id))

        # Verify professional exists, is verified, and has clinical role
        professional = UserRepository.get_by_id(db, payload.professional_id)
        if not professional:
            raise EntityNotFoundException("User", str(payload.professional_id))

        allowed_roles = {UserRole.OPTOMETRIST.value, UserRole.EYE_CARE_PROFESSIONAL.value}
        if professional.role not in allowed_roles:
            raise ValidationException("Selected user is not an eye care professional.")

        prof_profile = ReferralRepository.get_profile_by_user_id(db, professional.id)
        if not prof_profile or prof_profile.verification_status != "VERIFIED":
            raise ValidationException(
                "Records can only be shared with verified eye care professionals."
            )

        now = datetime.now(UTC)
        expires_at = now + timedelta(days=payload.expires_in_days)

        try:
            # Check if existing share exists
            existing = ReferralRepository.get_active_share(db, referral.id, professional.id)
            if existing:
                existing.expires_at = expires_at
                existing.access_status = "ACTIVE"
                existing.revoked_at = None
                db.add(existing)
                target_share = existing
            else:
                share = PatientRecordShare(
                    referral_id=referral.id,
                    patient_id=patient.id,
                    professional_id=professional.id,
                    access_status="ACTIVE",
                    granted_at=now,
                    expires_at=expires_at,
                )
                db.add(share)
                target_share = share

            prev_status = referral.status
            # Update referral status to SHARED if currently PENDING
            if referral.status == "PENDING":
                referral.status = "SHARED"
                referral.updated_at = now
                db.add(referral)

            audit = ReferralAuditEvent(
                referral_id=referral.id,
                actor_id=patient.id,
                actor_role=patient.role,
                action="SHARE_GRANTED",
                previous_state=prev_status,
                new_state=referral.status,
                occurred_at=now,
                metadata_json=json.dumps(
                    {
                        "professional_id": str(professional.id),
                        "expires_at": expires_at.isoformat(),
                    }
                ),
            )
            db.add(audit)
            db.commit()
            db.refresh(target_share)
        except Exception:
            db.rollback()
            raise

        resp = PatientRecordShareResponse.model_validate(target_share)
        resp.professional_name = professional.full_name
        resp.professional_license = prof_profile.license_number
        return resp

    @staticmethod
    def revoke_share(
        db: Session, patient: User, referral_id: uuid.UUID, share_id: uuid.UUID
    ) -> PatientRecordShareResponse:
        share = ReferralRepository.get_share_by_id(db, share_id)
        if not share or share.referral_id != referral_id or share.patient_id != patient.id:
            raise EntityNotFoundException("PatientRecordShare", str(share_id))

        try:
            now = datetime.now(UTC)
            share.access_status = "REVOKED"
            share.revoked_at = now
            db.add(share)

            audit = ReferralAuditEvent(
                referral_id=referral_id,
                actor_id=patient.id,
                actor_role=patient.role,
                action="SHARE_REVOKED",
                previous_state="ACTIVE",
                new_state="REVOKED",
                occurred_at=now,
                metadata_json=json.dumps(
                    {
                        "share_id": str(share.id),
                        "professional_id": str(share.professional_id),
                    }
                ),
            )
            db.add(audit)
            db.commit()
            db.refresh(share)
        except Exception:
            db.rollback()
            raise

        return PatientRecordShareResponse.model_validate(share)

    @staticmethod
    def list_shares_for_referral(
        db: Session, patient: User, referral_id: uuid.UUID
    ) -> list[PatientRecordShareResponse]:
        referral = ReferralRepository.get_referral_by_id(db, referral_id)
        if not referral or referral.patient_id != patient.id:
            raise EntityNotFoundException("PatientReferral", str(referral_id))

        shares = ReferralRepository.list_shares_for_referral(db, referral_id)
        results = []
        for s in shares:
            prof = UserRepository.get_by_id(db, s.professional_id)
            prof_profile = ReferralRepository.get_profile_by_user_id(db, s.professional_id)
            resp = PatientRecordShareResponse.model_validate(s)
            if prof:
                resp.professional_name = prof.full_name
            if prof_profile:
                resp.professional_license = prof_profile.license_number
            results.append(resp)
        return results

    @staticmethod
    def list_shared_records_for_professional(
        db: Session, professional: User, limit: int = 20, offset: int = 0
    ) -> tuple[list[PatientRecordShareResponse], int]:
        shares, total = ReferralRepository.list_active_shares_for_professional(
            db, professional.id, limit=limit, offset=offset
        )
        results = []
        for s in shares:
            prof_profile = ReferralRepository.get_profile_by_user_id(db, professional.id)
            resp = PatientRecordShareResponse.model_validate(s)
            resp.professional_name = professional.full_name
            if prof_profile:
                resp.professional_license = prof_profile.license_number
            results.append(resp)
        return results, total

    @classmethod
    def get_shared_screening_details(
        cls, db: Session, professional: User, referral_id: uuid.UUID
    ) -> SharedScreeningDetailsResponse:
        active_share = ReferralRepository.get_active_share(db, referral_id, professional.id)
        if not active_share and professional.role != UserRole.ADMIN.value:
            all_shares = ReferralRepository.list_shares_for_referral(db, referral_id)
            prof_share = next((s for s in all_shares if s.professional_id == professional.id), None)
            if prof_share:
                if prof_share.access_status == "REVOKED":
                    raise ForbiddenException(
                        "Access to this referral record has been revoked by the patient."
                    )
                if prof_share.expires_at and prof_share.expires_at <= datetime.now(UTC):
                    raise ForbiddenException("Access to this referral record has expired.")
            raise EntityNotFoundException("PatientReferral", str(referral_id))

        referral = ReferralRepository.get_referral_by_id(db, referral_id)
        if not referral:
            raise EntityNotFoundException("PatientReferral", str(referral_id))

        if referral.status in ["PENDING", "SHARED"]:
            cls.transition_status(db, referral, "IN_REVIEW", professional)

        session = ScreeningRepository.get_session_by_id(db, referral.session_id)
        if not session:
            raise EntityNotFoundException("ScreeningSession", str(referral.session_id))

        acuity = ScreeningRepository.list_acuity_assessments_for_session(db, session.id)
        astig = ScreeningRepository.list_astigmatism_assessments_for_session(db, session.id)
        color = ScreeningRepository.list_color_vision_assessments_for_session(db, session.id)
        reviews = ReferralRepository.list_reviews_for_referral(db, referral.id)

        patient = UserRepository.get_by_id(db, referral.patient_id)
        ref_resp = PatientReferralResponse.model_validate(referral)
        if patient:
            ref_resp.patient_name = patient.full_name
            ref_resp.patient_email = patient.email

        share_resp = (
            PatientRecordShareResponse.model_validate(active_share)
            if active_share
            else PatientRecordShareResponse(
                id=uuid.uuid4(),
                referral_id=referral.id,
                patient_id=referral.patient_id,
                professional_id=professional.id,
                access_status="ADMIN_ACCESS",
                granted_at=datetime.now(UTC),
            )
        )

        session_dict = {
            "id": str(session.id),
            "status": session.status,
            "started_at": session.started_at.isoformat() if session.started_at else None,
            "completed_at": session.completed_at.isoformat() if session.completed_at else None,
            "notes": session.notes,
            "device_info": session.device_info,
        }

        return SharedScreeningDetailsResponse(
            referral=ref_resp,
            share=share_resp,
            screening_session=session_dict,
            visual_acuity_assessments=[VisualAcuityResponse.model_validate(a) for a in acuity],
            astigmatism_assessments=[AstigmatismResponse.model_validate(a) for a in astig],
            color_vision_assessments=[ColorVisionResponse.model_validate(a) for a in color],
            reviews=[ClinicalReviewResponse.model_validate(r) for r in reviews],
        )

    # -------------------------------------------------------------------------
    # 4. Clinical Reviews
    # -------------------------------------------------------------------------
    @classmethod
    def create_review(
        cls,
        db: Session,
        professional: User,
        referral_id: uuid.UUID,
        payload: ClinicalReviewCreateRequest,
    ) -> ClinicalReviewResponse:
        active_share = ReferralRepository.get_active_share(db, referral_id, professional.id)
        if not active_share and professional.role != UserRole.ADMIN.value:
            all_shares = ReferralRepository.list_shares_for_referral(db, referral_id)
            prof_share = next((s for s in all_shares if s.professional_id == professional.id), None)
            if prof_share:
                if prof_share.access_status == "REVOKED":
                    raise ForbiddenException(
                        "Access to this referral record has been revoked by the patient."
                    )
                if prof_share.expires_at and prof_share.expires_at <= datetime.now(UTC):
                    raise ForbiddenException("Access to this referral record has expired.")
            raise ForbiddenException(
                "Cannot submit clinical review: No active record share exists for this referral."
            )

        referral = ReferralRepository.get_referral_by_id(db, referral_id)
        if not referral:
            raise EntityNotFoundException("PatientReferral", str(referral_id))

        now = datetime.now(UTC)
        review = ClinicalReview(
            referral_id=referral.id,
            professional_id=professional.id,
            review_status="EXAMINATION_RECOMMENDED"
            if payload.in_person_exam_recommended
            else "COMPLETED",
            professional_observations=payload.professional_observations.strip(),
            in_person_exam_recommended=payload.in_person_exam_recommended,
            recommended_exam_timeframe=payload.recommended_exam_timeframe.strip()
            if payload.recommended_exam_timeframe
            else None,
            closed_at=now,
            created_at=now,
            updated_at=now,
        )
        try:
            db.add(review)
            db.flush()
            # Update referral status via state machine atomically
            cls.transition_status(db, referral, "COMPLETED", professional, commit=False)
            db.commit()
            db.refresh(review)
        except Exception:
            db.rollback()
            raise

        return ClinicalReviewResponse.model_validate(review)

    @classmethod
    def close_referral(
        cls, db: Session, user: User, referral_id: uuid.UUID
    ) -> PatientReferralResponse:
        referral = ReferralRepository.get_referral_by_id(db, referral_id)
        if not referral:
            raise EntityNotFoundException("PatientReferral", str(referral_id))

        is_owner = referral.patient_id == user.id
        is_admin = user.role == UserRole.ADMIN.value
        has_share = ReferralRepository.get_active_share(db, referral.id, user.id) is not None

        if not (is_owner or is_admin or has_share):
            raise ForbiddenException("You do not have permission to close this referral.")

        cls.transition_status(db, referral, "CLOSED", user)
        patient = UserRepository.get_by_id(db, referral.patient_id)
        resp = PatientReferralResponse.model_validate(referral)
        if patient:
            resp.patient_name = patient.full_name
            resp.patient_email = patient.email
        return resp

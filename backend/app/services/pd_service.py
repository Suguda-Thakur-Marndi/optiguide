import json
import uuid
from datetime import UTC, datetime

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.exceptions import (
    EntityNotFoundException,
    ForbiddenException,
    ValidationException,
)
from app.models.pd_assessment import PDAssessment
from app.models.referral import PatientRecordShare
from app.models.user import User
from app.repositories.pd_repository import PDRepository
from app.repositories.referral_repository import ReferralRepository
from app.repositories.screening_repository import ScreeningRepository
from app.schemas.auth import UserRole
from app.schemas.pd_assessment import (
    PDAssessmentCreateRequest,
    PDAssessmentResponse,
    PDProfessionalReviewRequest,
)


class PDService:
    """Business logic and physiological validation for Pupillary Distance (PD) measurements."""

    # Physiological human boundaries for adult distance PD (mm)
    MIN_BINOCULAR_PD_MM = 45.0
    MAX_BINOCULAR_PD_MM = 80.0
    MIN_MONOCULAR_PD_MM = 20.0
    MAX_MONOCULAR_PD_MM = 42.0

    # Physiological human boundaries for pediatric distance PD (mm)
    MIN_PEDIATRIC_BINOCULAR_PD_MM = 38.0
    MAX_PEDIATRIC_BINOCULAR_PD_MM = 55.0
    MIN_PEDIATRIC_MONOCULAR_PD_MM = 18.0
    MAX_PEDIATRIC_MONOCULAR_PD_MM = 30.0

    @classmethod
    def validate_measurement(cls, payload: PDAssessmentCreateRequest) -> None:
        is_pedia = getattr(payload, "is_pediatric", False)
        min_b = cls.MIN_PEDIATRIC_BINOCULAR_PD_MM if is_pedia else cls.MIN_BINOCULAR_PD_MM
        max_b = cls.MAX_PEDIATRIC_BINOCULAR_PD_MM if is_pedia else cls.MAX_BINOCULAR_PD_MM
        min_m = cls.MIN_PEDIATRIC_MONOCULAR_PD_MM if is_pedia else cls.MIN_MONOCULAR_PD_MM
        max_m = cls.MAX_PEDIATRIC_MONOCULAR_PD_MM if is_pedia else cls.MAX_MONOCULAR_PD_MM
        pop_label = "pediatric" if is_pedia else "human"

        if not (min_b <= payload.binocular_pd_mm <= max_b):
            raise ValidationException(
                f"Binocular PD measurement ({payload.binocular_pd_mm} mm) falls outside physiological {pop_label} range "
                f"({min_b} - {max_b} mm)."
            )

        if payload.monocular_left_pd_mm is not None and not (
            min_m <= payload.monocular_left_pd_mm <= max_m
        ):
            raise ValidationException(
                f"Left monocular PD ({payload.monocular_left_pd_mm} mm) outside physiological {pop_label} range "
                f"({min_m} - {max_m} mm)."
            )

        if payload.monocular_right_pd_mm is not None and not (
            min_m <= payload.monocular_right_pd_mm <= max_m
        ):
            raise ValidationException(
                f"Right monocular PD ({payload.monocular_right_pd_mm} mm) outside physiological {pop_label} range "
                f"({min_m} - {max_m} mm)."
            )

    @classmethod
    def record_assessment(
        cls, db: Session, user: User, payload: PDAssessmentCreateRequest
    ) -> PDAssessmentResponse:
        cls.validate_measurement(payload)

        # If associated with a screening session, verify ownership
        if payload.session_id:
            session = ScreeningRepository.get_session_by_id_for_user(
                db, payload.session_id, user.id
            )
            if not session:
                raise EntityNotFoundException("ScreeningSession", str(payload.session_id))

        # Server-side validation of calibration evidence & confidence
        # Client-submitted calibration and confidence are strictly untrusted claims
        client_calibrated_claim = payload.is_calibrated
        client_confidence_claim = payload.confidence_score

        server_verified = False
        server_confidence: float | None = None
        status = "ESTIMATED"

        # In the absence of an independent backend image-processing pipeline,
        # the server never establishes verification based on client-submitted metadata.
        # Manual clinical measurements entered directly by verified optometrists are trusted.
        if (
            payload.estimation_method == "MANUAL_CLINICAL"
            and user.role in {UserRole.OPTOMETRIST.value, UserRole.EYE_CARE_PROFESSIONAL.value}
            and user.is_verified
        ):
            server_verified = True
            server_confidence = 1.0
            status = "PROFESSIONALLY_REVIEWED"

        now = datetime.now(UTC)
        calibration_meta = dict(payload.calibration_metadata or {})
        if payload.calibration_metadata:
            calibration_meta["server_verification"] = "UNVERIFIED_CLIENT_CLAIM"

        assessment = PDAssessment(
            user_id=user.id,
            session_id=payload.session_id,
            measurement_type=payload.measurement_type,
            binocular_pd_mm=round(payload.binocular_pd_mm, 1),
            monocular_left_pd_mm=round(payload.monocular_left_pd_mm, 1)
            if payload.monocular_left_pd_mm is not None
            else None,
            monocular_right_pd_mm=round(payload.monocular_right_pd_mm, 1)
            if payload.monocular_right_pd_mm is not None
            else None,
            unit="mm",
            estimation_method=payload.estimation_method,
            is_calibrated=client_calibrated_claim,
            is_server_verified=server_verified,
            client_confidence_score=client_confidence_claim,
            server_confidence_score=server_confidence,
            confidence_score=server_confidence,
            is_pediatric=payload.is_pediatric,
            calibration_metadata=json.dumps(calibration_meta) if calibration_meta else None,
            device_info=json.dumps(payload.device_info) if payload.device_info else None,
            status=status,
            recorded_at=now,
        )
        created = PDRepository.create_assessment(db, assessment)
        return PDAssessmentResponse.model_validate(created)

    @staticmethod
    def get_assessment(db: Session, user: User, assessment_id: uuid.UUID) -> PDAssessmentResponse:
        assessment = PDRepository.get_assessment_by_id(db, assessment_id)
        if not assessment:
            raise EntityNotFoundException("PDAssessment", str(assessment_id))

        # Check access: patient owner, administrator, or verified professional with active share
        is_owner = assessment.user_id == user.id
        is_admin = user.role == UserRole.ADMIN.value
        has_share = False
        allowed_clinical_roles = {UserRole.OPTOMETRIST.value, UserRole.EYE_CARE_PROFESSIONAL.value}
        if user.role in allowed_clinical_roles and user.is_verified:
            shares, _ = ReferralRepository.list_active_shares_for_professional(
                db, user.id, limit=100
            )
            if assessment.session_id:
                has_share = any(
                    s.referral.session_id == assessment.session_id for s in shares if s.referral
                )
            else:
                has_share = any(s.patient_id == assessment.user_id for s in shares)

        if not (is_owner or is_admin or has_share):
            raise EntityNotFoundException("PDAssessment", str(assessment_id))

        return PDAssessmentResponse.model_validate(assessment)

    @staticmethod
    def list_my_assessments(
        db: Session, user: User, limit: int = 20, offset: int = 0
    ) -> tuple[list[PDAssessmentResponse], int]:
        items, total = PDRepository.list_assessments_for_user(
            db, user.id, limit=limit, offset=offset
        )
        return [PDAssessmentResponse.model_validate(i) for i in items], total

    @staticmethod
    def confirm_assessment(
        db: Session, user: User, assessment_id: uuid.UUID
    ) -> PDAssessmentResponse:
        assessment = PDRepository.get_assessment_by_id(db, assessment_id)
        if not assessment or assessment.user_id != user.id:
            raise EntityNotFoundException("PDAssessment", str(assessment_id))

        assessment.status = "USER_CONFIRMED"
        assessment.confirmed_at = datetime.now(UTC)
        updated = PDRepository.update_assessment(db, assessment)
        return PDAssessmentResponse.model_validate(updated)

    @staticmethod
    def reject_assessment(
        db: Session, user: User, assessment_id: uuid.UUID, rejection_reason: str
    ) -> PDAssessmentResponse:
        assessment = PDRepository.get_assessment_by_id(db, assessment_id)
        if not assessment or assessment.user_id != user.id:
            raise EntityNotFoundException("PDAssessment", str(assessment_id))

        assessment.status = "REJECTED"
        assessment.rejection_reason = rejection_reason.strip()
        updated = PDRepository.update_assessment(db, assessment)
        return PDAssessmentResponse.model_validate(updated)

    @staticmethod
    def review_assessment_by_professional(
        db: Session,
        professional: User,
        assessment_id: uuid.UUID,
        payload: PDProfessionalReviewRequest,
    ) -> PDAssessmentResponse:
        """
        Verified eye care professional performs clinical verification of a PD measurement.
        Requires active patient authorization/record share.
        """
        allowed_roles = {UserRole.OPTOMETRIST.value, UserRole.EYE_CARE_PROFESSIONAL.value}
        if professional.role not in allowed_roles or not professional.is_verified:
            raise ForbiddenException(
                "Access denied: Only verified eye care professionals can review PD assessments."
            )

        assessment = PDRepository.get_assessment_by_id(db, assessment_id)
        if not assessment:
            raise EntityNotFoundException("PDAssessment", str(assessment_id))

        # Check access: Must hold an active, unexpired record share for this patient / session
        is_admin = professional.role == UserRole.ADMIN.value
        if not is_admin:
            shares, _ = ReferralRepository.list_active_shares_for_professional(
                db, professional.id, limit=100
            )
            has_active_share = False
            if assessment.session_id:
                has_active_share = any(
                    s.referral.session_id == assessment.session_id for s in shares if s.referral
                )
            else:
                has_active_share = any(s.patient_id == assessment.user_id for s in shares)

            if not has_active_share:
                stmt = select(PatientRecordShare).where(
                    PatientRecordShare.professional_id == professional.id,
                    PatientRecordShare.patient_id == assessment.user_id,
                )
                prior_shares = list(db.execute(stmt).scalars().all())
                if any(s.access_status == "REVOKED" for s in prior_shares):
                    raise ForbiddenException(
                        "Access denied: Patient record share has been revoked."
                    )
                if any(s.expires_at and s.expires_at <= datetime.now(UTC) for s in prior_shares):
                    raise ForbiddenException("Access denied: Patient record share has expired.")
                raise ForbiddenException(
                    "Access denied: No active patient record share found authorizing professional review of this assessment."
                )

        # Distinguish review actions
        if payload.status == "REQUIRES_PROFESSIONAL_MEASUREMENT":
            assessment.status = "REQUIRES_PROFESSIONAL_MEASUREMENT"
            assessment.is_server_verified = False
            assessment.server_confidence_score = None
            assessment.confidence_score = None
        elif payload.status == "REJECTED" or payload.action == "REJECT":
            assessment.status = "REJECTED"
            assessment.is_server_verified = False
            assessment.server_confidence_score = None
            assessment.confidence_score = None
            assessment.rejection_reason = payload.clinical_notes.strip()
        else:
            if payload.action == "MEASURE" and payload.measured_binocular_pd_mm is None:
                raise ValidationException(
                    "Physical measurement confirmation requires submitting measured_binocular_pd_mm."
                )

            if payload.measured_binocular_pd_mm is not None:
                assessment.binocular_pd_mm = payload.measured_binocular_pd_mm
            if payload.measured_left_pd_mm is not None:
                assessment.monocular_left_pd_mm = payload.measured_left_pd_mm
            if payload.measured_right_pd_mm is not None:
                assessment.monocular_right_pd_mm = payload.measured_right_pd_mm

            assessment.status = "PROFESSIONALLY_REVIEWED"
            assessment.is_server_verified = True
            assessment.server_confidence_score = 1.0
            assessment.confidence_score = 1.0

        assessment.reviewed_by_professional_id = professional.id
        assessment.professional_review_notes = payload.clinical_notes.strip()
        updated = PDRepository.update_assessment(db, assessment)
        return PDAssessmentResponse.model_validate(updated)

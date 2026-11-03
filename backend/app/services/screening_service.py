import hashlib
import json
import uuid
from datetime import UTC, datetime

from sqlalchemy.orm import Session

from app.core.exceptions import (
    ConsentRequiredException,
    EntityNotFoundException,
    InvalidConsentVersionException,
    InvalidSessionTransitionException,
    SessionAlreadyActiveException,
    ValidationException,
)
from app.models.screening_assessment import (
    AstigmatismAssessment,
    ColorVisionAssessment,
    VisualAcuityAssessment,
)
from app.models.screening_audit_event import ScreeningAuditEvent
from app.models.screening_consent import ScreeningConsent
from app.models.screening_session import ScreeningSession
from app.models.user import User
from app.repositories.screening_repository import ScreeningRepository
from app.schemas.auth import MessageResponse
from app.schemas.clinical_assessments import (
    AstigmatismCreateRequest,
    AstigmatismResponse,
    ClinicalSessionSummaryResponse,
    ColorVisionCreateRequest,
    ColorVisionResponse,
    VisualAcuityCreateRequest,
    VisualAcuityResponse,
)
from app.schemas.screening import (
    ConsentAcceptRequest,
    ConsentResponse,
    ConsentStatusResponse,
    ScreeningSessionCancelRequest,
    ScreeningSessionCreateRequest,
    ScreeningSessionListResponse,
    ScreeningSessionResponse,
    ScreeningSessionStatus,
)

# -----------------------------------------------------------------------------
# Server-Controlled Official Consent Document (Version 1.0.0)
# -----------------------------------------------------------------------------
CURRENT_CONSENT_VERSION = "1.0.0"
CONSENT_DOCUMENT_TITLE = "OptiGuide Preliminary Vision Screening Consent & Clinical Disclosure"

CONSENT_DOCUMENT_TEXT = """# OptiGuide Preliminary Vision Screening Consent & Clinical Disclosure (v1.0.0)

## 1. Scope & Purpose of OptiGuide
OptiGuide is an assistive digital screening platform designed to facilitate preliminary vision checks (including distance visual acuity, near vision, and color sensitivity assessments) and personalized eyewear guidance.

## 2. Non-Diagnostic Medical Disclaimer
- OptiGuide is NOT a medical diagnostic tool or clinical prescription device.
- OptiGuide does NOT replace a comprehensive examination conducted by a licensed optometrist, ophthalmologist, or medical doctor.
- OptiGuide does NOT autonomously compute, generate, or finalize optical prescriptions or lens power.
- All scores, measurements, and recommendations are strictly preliminary approximations and cannot confirm, treat, or rule out any ocular or refractive condition.

## 3. Data Collection & Privacy Safeguards
- Data Collected: User screening questionnaire responses, test inputs, device screen calibration parameters (distance, scale), and session timestamps.
- Usage: To calculate preliminary screening scores and assist in identifying relevant eyewear configurations.
- Confidentiality: All records are strictly account-isolated, encrypted, and guarded against unauthorized access.
- Commercial Boundary: Unverified third parties and commercial retail shopkeepers cannot inspect your private clinical responses.

## 4. Voluntary Participation & Withdrawal Rights
- Participation is voluntary. You may stop a test or withdraw your screening consent at any time.
- Withdrawing consent immediately terminates any ongoing screening sessions and prevents new sessions from starting until consent is renewed.
"""

CONSENT_DOCUMENT_HASH = hashlib.sha256(CONSENT_DOCUMENT_TEXT.strip().encode("utf-8")).hexdigest()

CLINICAL_DISCLAIMER_TEXT = (
    "OptiGuide is a preliminary vision screening aid and not a diagnostic system. "
    "Results must be confirmed by a licensed eye care professional."
)


class ScreeningService:
    """Domain service managing informed consent, session state transitions, clinical assessments, and audit telemetry."""

    @staticmethod
    def get_current_consent_status(db: Session, user: User) -> ConsentStatusResponse:
        """Returns the current server-controlled consent document along with the user's active state."""
        active_consent = ScreeningRepository.get_active_consent(db, user.id)
        latest_consent = ScreeningRepository.get_latest_consent(db, user.id)

        has_accepted = (
            active_consent is not None and active_consent.consent_version == CURRENT_CONSENT_VERSION
        )
        is_active = active_consent is not None

        return ConsentStatusResponse(
            version=CURRENT_CONSENT_VERSION,
            title=CONSENT_DOCUMENT_TITLE,
            content=CONSENT_DOCUMENT_TEXT,
            hash=CONSENT_DOCUMENT_HASH,
            has_accepted=has_accepted,
            is_active=is_active,
            accepted_at=active_consent.accepted_at if active_consent else None,
            withdrawn_at=latest_consent.withdrawn_at if latest_consent else None,
        )

    @staticmethod
    def accept_consent(
        db: Session,
        user: User,
        payload: ConsentAcceptRequest,
    ) -> ConsentResponse:
        """
        Records the user's explicit acceptance of the server-controlled consent document.
        Validates the requested version against the active server version.
        """
        if payload.version.strip() != CURRENT_CONSENT_VERSION:
            raise InvalidConsentVersionException(
                f"Requested consent version '{payload.version}' is invalid or obsolete. "
                f"Current server version is '{CURRENT_CONSENT_VERSION}'."
            )

        active = ScreeningRepository.get_active_consent(db, user.id)
        if active and active.consent_version == CURRENT_CONSENT_VERSION:
            # Idempotent return of already active consent
            return ConsentResponse.model_validate(active)

        now = datetime.now(UTC)
        new_consent = ScreeningConsent(
            user_id=user.id,
            consent_version=CURRENT_CONSENT_VERSION,
            consent_text_hash=CONSENT_DOCUMENT_HASH,
            accepted_at=now,
            is_active=True,
        )
        saved_consent = ScreeningRepository.create_consent(db, new_consent)

        # Audit Event
        audit = ScreeningAuditEvent(
            user_id=user.id,
            session_id=None,
            event_type="CONSENT_ACCEPTED",
            occurred_at=now,
            metadata_json=json.dumps(
                {"version": CURRENT_CONSENT_VERSION, "hash": CONSENT_DOCUMENT_HASH}
            ),
        )
        ScreeningRepository.create_audit_event(db, audit)

        return ConsentResponse.model_validate(saved_consent)

    @staticmethod
    def withdraw_consent(db: Session, user: User) -> MessageResponse:
        """
        Withdraws active screening consent and automatically cancels any ongoing session.
        Preserves historical consent records for regulatory compliance.
        """
        active_consent = ScreeningRepository.get_active_consent(db, user.id)
        if not active_consent:
            return MessageResponse(
                message="No active screening consent found to withdraw.",
                success=True,
            )

        now = datetime.now(UTC)
        ScreeningRepository.withdraw_consent(db, active_consent)

        # Automatically cancel any in-progress screening sessions
        cancelled_count = ScreeningRepository.cancel_active_sessions_for_user(
            db=db,
            user_id=user.id,
            reason="consent_withdrawn",
        )

        # Audit Event
        audit = ScreeningAuditEvent(
            user_id=user.id,
            session_id=None,
            event_type="CONSENT_WITHDRAWN",
            occurred_at=now,
            metadata_json=json.dumps(
                {
                    "withdrawn_version": active_consent.consent_version,
                    "cancelled_in_progress_sessions": cancelled_count,
                }
            ),
        )
        ScreeningRepository.create_audit_event(db, audit)

        return MessageResponse(
            message=f"Screening consent withdrawn successfully. {cancelled_count} active session(s) cancelled.",
            success=True,
        )

    @staticmethod
    def create_session(
        db: Session,
        user: User,
        payload: ScreeningSessionCreateRequest | None = None,
    ) -> ScreeningSessionResponse:
        """
        Creates a new screening session in IN_PROGRESS status.
        Enforces valid active consent and the single-active-session policy.
        """
        # 1. Enforce active consent
        active_consent = ScreeningRepository.get_active_consent(db, user.id)
        if not active_consent or not active_consent.is_active:
            raise ConsentRequiredException(
                "Active informed consent is required to start a preliminary vision screening session. "
                "Please review and accept the screening consent disclosure."
            )

        # 2. Enforce single active session concurrency policy
        existing_active = ScreeningRepository.get_active_session_for_user(db, user.id)
        if existing_active:
            raise SessionAlreadyActiveException(
                f"An active screening session (ID: {existing_active.id}) is already in progress. "
                f"Please complete or cancel it before initiating a new session."
            )

        # 3. Create session with server-generated timestamps
        now = datetime.now(UTC)
        session = ScreeningSession(
            user_id=user.id,
            consent_id=active_consent.id,
            status=ScreeningSessionStatus.IN_PROGRESS.value,
            started_at=now,
            notes=getattr(payload, "notes", None) if payload else None,
            device_info=json.dumps(getattr(payload, "device_info", None)) if payload and getattr(payload, "device_info", None) else None,
        )
        created_session = ScreeningRepository.create_session(db, session)

        # 4. Record Audit Event
        audit = ScreeningAuditEvent(
            user_id=user.id,
            session_id=created_session.id,
            event_type="SESSION_CREATED",
            occurred_at=now,
            metadata_json=json.dumps({"consent_id": str(active_consent.id)}),
        )
        ScreeningRepository.create_audit_event(db, audit)

        return ScreeningSessionResponse.model_validate(created_session)

    @staticmethod
    def list_sessions(
        db: Session,
        user: User,
        status: str | None = None,
        limit: int = 20,
        offset: int = 0,
    ) -> ScreeningSessionListResponse:
        """Retrieves paginated screening sessions belonging exclusively to the authenticated user."""
        limit = max(1, min(limit, 100))
        offset = max(0, offset)

        if status:
            valid_statuses = {s.value for s in ScreeningSessionStatus}
            if status.lower() not in valid_statuses:
                raise ValidationException(
                    f"Invalid status filter '{status}'. Must be one of: {', '.join(sorted(valid_statuses))}."
                )
            status = status.lower()

        items, total = ScreeningRepository.list_sessions_for_user(
            db=db,
            user_id=user.id,
            status=status,
            limit=limit,
            offset=offset,
        )

        return ScreeningSessionListResponse(
            items=[ScreeningSessionResponse.model_validate(i) for i in items],
            total=total,
            limit=limit,
            offset=offset,
        )

    @staticmethod
    def get_session(
        db: Session,
        user: User,
        session_id: uuid.UUID,
    ) -> ScreeningSessionResponse:
        """Retrieves a single screening session ensuring strict ownership verification (IDOR protection)."""
        session = ScreeningRepository.get_session_by_id(db, session_id)
        if not session or session.user_id != user.id:
            raise EntityNotFoundException("ScreeningSession", session_id)

        return ScreeningSessionResponse.model_validate(session)

    @staticmethod
    def complete_session(
        db: Session,
        user: User,
        session_id: uuid.UUID,
    ) -> ScreeningSessionResponse:
        """
        Transitions an IN_PROGRESS session to COMPLETED.
        Enforces valid state transition and records completion timestamp.
        """
        session = ScreeningRepository.get_session_by_id(db, session_id, for_update=True)
        if not session or session.user_id != user.id:
            raise EntityNotFoundException("ScreeningSession", session_id)

        if session.status == ScreeningSessionStatus.COMPLETED.value:
            raise InvalidSessionTransitionException("Screening session has already been completed.")

        if session.status == ScreeningSessionStatus.CANCELLED.value:
            raise InvalidSessionTransitionException(
                "A cancelled screening session cannot be completed."
            )

        now = datetime.now(UTC)
        session.status = ScreeningSessionStatus.COMPLETED.value
        session.completed_at = now
        updated = ScreeningRepository.update_session(db, session)

        # Audit Event
        audit = ScreeningAuditEvent(
            user_id=user.id,
            session_id=updated.id,
            event_type="SESSION_COMPLETED",
            occurred_at=now,
        )
        ScreeningRepository.create_audit_event(db, audit)

        return ScreeningSessionResponse.model_validate(updated)

    @staticmethod
    def cancel_session(
        db: Session,
        user: User,
        session_id: uuid.UUID,
        payload: ScreeningSessionCancelRequest | None = None,
    ) -> ScreeningSessionResponse:
        """
        Transitions an IN_PROGRESS session to CANCELLED.
        Enforces valid state transition and records cancellation reason.
        """
        session = ScreeningRepository.get_session_by_id(db, session_id, for_update=True)
        if not session or session.user_id != user.id:
            raise EntityNotFoundException("ScreeningSession", session_id)

        if session.status == ScreeningSessionStatus.CANCELLED.value:
            raise InvalidSessionTransitionException("Screening session has already been cancelled.")

        if session.status == ScreeningSessionStatus.COMPLETED.value:
            raise InvalidSessionTransitionException(
                "A completed screening session cannot be cancelled."
            )

        now = datetime.now(UTC)
        reason = payload.reason.strip() if payload and payload.reason else "user_cancelled"

        session.status = ScreeningSessionStatus.CANCELLED.value
        session.cancelled_at = now
        session.cancellation_reason = reason
        updated = ScreeningRepository.update_session(db, session)

        # Audit Event
        audit = ScreeningAuditEvent(
            user_id=user.id,
            session_id=updated.id,
            event_type="SESSION_CANCELLED",
            occurred_at=now,
            metadata_json=json.dumps({"reason": reason}),
        )
        ScreeningRepository.create_audit_event(db, audit)

        return ScreeningSessionResponse.model_validate(updated)

    # -------------------------------------------------------------------------
    # Visual Acuity Assessment (Phase 3.2)
    # -------------------------------------------------------------------------

    @staticmethod
    def record_visual_acuity(
        db: Session,
        user: User,
        session_id: uuid.UUID,
        payload: VisualAcuityCreateRequest,
    ) -> VisualAcuityResponse:
        """
        Records a visual acuity assessment for an in-progress screening session.
        Applies physical calibration validation and Snellen/logMAR mapping.
        """
        session = ScreeningRepository.get_session_by_id(db, session_id)
        if not session or session.user_id != user.id:
            raise EntityNotFoundException("ScreeningSession", session_id)

        if session.status != ScreeningSessionStatus.IN_PROGRESS.value:
            raise InvalidSessionTransitionException(
                f"Cannot record assessment on screening session with status '{session.status}'."
            )

        calib_str = None
        if payload.calibration:
            calib_str = json.dumps(payload.calibration.model_dump())

        assessment = VisualAcuityAssessment(
            session_id=session_id,
            user_id=user.id,
            test_eye=payload.test_eye,
            snellen_fraction=payload.snellen_fraction,
            logmar=payload.logmar,
            decimal_acuity=payload.decimal_acuity,
            tested_distance_meters=payload.tested_distance_meters,
            unassisted_or_corrected=payload.unassisted_or_corrected,
            near_reading_label=payload.near_reading_label,
            near_reading_distance_cm=payload.near_reading_distance_cm,
            is_calibrated=payload.is_calibrated,
            calibration_metadata=calib_str,
            observations=payload.observations,
        )
        saved = ScreeningRepository.create_acuity_assessment(db, assessment)

        # Audit
        audit = ScreeningAuditEvent(
            user_id=user.id,
            session_id=session_id,
            event_type="ACUITY_ASSESSMENT_RECORDED",
            occurred_at=datetime.now(UTC),
            metadata_json=json.dumps(
                {
                    "eye": payload.test_eye,
                    "snellen": payload.snellen_fraction,
                    "logmar": payload.logmar,
                }
            ),
        )
        ScreeningRepository.create_audit_event(db, audit)

        return VisualAcuityResponse.model_validate(saved)

    @staticmethod
    def get_visual_acuity_for_session(
        db: Session,
        user: User,
        session_id: uuid.UUID,
    ) -> list[VisualAcuityResponse]:
        """Retrieves all visual acuity results for the specified session."""
        session = ScreeningRepository.get_session_by_id(db, session_id)
        if not session or session.user_id != user.id:
            raise EntityNotFoundException("ScreeningSession", session_id)

        items = ScreeningRepository.list_acuity_assessments_for_session(db, session_id)
        return [VisualAcuityResponse.model_validate(i) for i in items]

    # -------------------------------------------------------------------------
    # Astigmatism Screening Assessment (Phase 3.3)
    # -------------------------------------------------------------------------

    @staticmethod
    def record_astigmatism(
        db: Session,
        user: User,
        session_id: uuid.UUID,
        payload: AstigmatismCreateRequest,
    ) -> AstigmatismResponse:
        """Records an astigmatism dial/fan screening result."""
        session = ScreeningRepository.get_session_by_id(db, session_id)
        if not session or session.user_id != user.id:
            raise EntityNotFoundException("ScreeningSession", session_id)

        if session.status != ScreeningSessionStatus.IN_PROGRESS.value:
            raise InvalidSessionTransitionException(
                f"Cannot record assessment on screening session with status '{session.status}'."
            )

        obs = payload.screening_observation
        if not obs:
            if payload.has_uniform_clarity:
                obs = "Radial clock chart appeared uniformly clear with no prominent meridian asymmetry observed."
            else:
                axis = f"{payload.sharpest_meridian_hour} o'clock" if payload.sharpest_meridian_hour else "indicated"
                obs = f"Potential meridian clarity variance observed along {axis} axis. Requires professional examination."

        axes_str = json.dumps(payload.indicated_axes) if payload.indicated_axes else None

        assessment = AstigmatismAssessment(
            session_id=session_id,
            user_id=user.id,
            chart_type=payload.chart_type,
            has_uniform_clarity=payload.has_uniform_clarity,
            indicated_axes=axes_str,
            sharpest_meridian_hour=payload.sharpest_meridian_hour,
            screening_observation=obs,
        )
        saved = ScreeningRepository.create_astigmatism_assessment(db, assessment)

        audit = ScreeningAuditEvent(
            user_id=user.id,
            session_id=session_id,
            event_type="ASTIGMATISM_ASSESSMENT_RECORDED",
            occurred_at=datetime.now(UTC),
            metadata_json=json.dumps({"has_uniform_clarity": payload.has_uniform_clarity}),
        )
        ScreeningRepository.create_audit_event(db, audit)

        return AstigmatismResponse.model_validate(saved)

    @staticmethod
    def get_astigmatism_for_session(
        db: Session,
        user: User,
        session_id: uuid.UUID,
    ) -> list[AstigmatismResponse]:
        """Retrieves astigmatism screening results for the specified session."""
        session = ScreeningRepository.get_session_by_id(db, session_id)
        if not session or session.user_id != user.id:
            raise EntityNotFoundException("ScreeningSession", session_id)

        items = ScreeningRepository.list_astigmatism_assessments_for_session(db, session_id)
        return [AstigmatismResponse.model_validate(i) for i in items]

    # -------------------------------------------------------------------------
    # Color Vision Screening Assessment (Phase 3.3)
    # -------------------------------------------------------------------------

    @staticmethod
    def record_color_vision(
        db: Session,
        user: User,
        session_id: uuid.UUID,
        payload: ColorVisionCreateRequest,
    ) -> ColorVisionResponse:
        """Records a pseudoisochromatic color vision plate screening result."""
        session = ScreeningRepository.get_session_by_id(db, session_id)
        if not session or session.user_id != user.id:
            raise EntityNotFoundException("ScreeningSession", session_id)

        if session.status != ScreeningSessionStatus.IN_PROGRESS.value:
            raise InvalidSessionTransitionException(
                f"Cannot record assessment on screening session with status '{session.status}'."
            )

        obs = payload.screening_observation
        if not obs:
            if payload.deficiency_indicated:
                obs = f"Plate score {payload.correct_plate_count}/{payload.total_plates_presented}. Potential color discrimination variance noted."
            else:
                obs = f"Plate score {payload.correct_plate_count}/{payload.total_plates_presented}. Standard chromatic discrimination observed."

        detail_str = json.dumps(payload.responses_detail) if payload.responses_detail else None

        assessment = ColorVisionAssessment(
            session_id=session_id,
            user_id=user.id,
            test_protocol=payload.test_protocol,
            total_plates_presented=payload.total_plates_presented,
            correct_plate_count=payload.correct_plate_count,
            deficiency_indicated=payload.deficiency_indicated,
            deficiency_type=payload.deficiency_type,
            responses_detail=detail_str,
            screening_observation=obs,
        )
        saved = ScreeningRepository.create_color_vision_assessment(db, assessment)

        audit = ScreeningAuditEvent(
            user_id=user.id,
            session_id=session_id,
            event_type="COLOR_VISION_ASSESSMENT_RECORDED",
            occurred_at=datetime.now(UTC),
            metadata_json=json.dumps(
                {
                    "score": f"{payload.correct_plate_count}/{payload.total_plates_presented}",
                    "deficiency_indicated": payload.deficiency_indicated,
                }
            ),
        )
        ScreeningRepository.create_audit_event(db, audit)

        return ColorVisionResponse.model_validate(saved)

    @staticmethod
    def get_color_vision_for_session(
        db: Session,
        user: User,
        session_id: uuid.UUID,
    ) -> list[ColorVisionResponse]:
        """Retrieves color vision plate results for the specified session."""
        session = ScreeningRepository.get_session_by_id(db, session_id)
        if not session or session.user_id != user.id:
            raise EntityNotFoundException("ScreeningSession", session_id)

        items = ScreeningRepository.list_color_vision_assessments_for_session(db, session_id)
        return [ColorVisionResponse.model_validate(i) for i in items]

    # -------------------------------------------------------------------------
    # Comprehensive Clinical Session Summary
    # -------------------------------------------------------------------------

    @staticmethod
    def get_session_summary(
        db: Session,
        user: User,
        session_id: uuid.UUID,
    ) -> ClinicalSessionSummaryResponse:
        """
        Aggregates all assessments for a session and evaluates clinical triage rules:
        - Flags referral if acuity logMAR >= 0.4 (20/50 or worse).
        - Flags referral if interocular difference >= 0.3 logMAR lines.
        - Flags referral if astigmatism dial reports asymmetry.
        - Flags referral if color vision indicates deficiency.
        """
        session = ScreeningRepository.get_session_by_id(db, session_id)
        if not session or session.user_id != user.id:
            raise EntityNotFoundException("ScreeningSession", session_id)

        acuity_list = ScreeningRepository.list_acuity_assessments_for_session(db, session_id)
        astig_list = ScreeningRepository.list_astigmatism_assessments_for_session(db, session_id)
        color_list = ScreeningRepository.list_color_vision_assessments_for_session(db, session_id)

        referral_reasons = []

        # Check Visual Acuity
        logmars = {}
        for a in acuity_list:
            logmars[a.test_eye.lower()] = a.logmar
            if a.logmar >= 0.4:
                referral_reasons.append(
                    f"Reduced distance visual acuity in {a.test_eye} eye (Snellen: {a.snellen_fraction}, logMAR: {a.logmar:.2f})."
                )

        if "right" in logmars and "left" in logmars:
            diff = abs(logmars["right"] - logmars["left"])
            if diff >= 0.3:
                referral_reasons.append(
                    f"Interocular visual acuity asymmetry of {diff:.2f} logMAR between right and left eyes."
                )

        # Check Astigmatism
        for astig in astig_list:
            if not astig.has_uniform_clarity:
                referral_reasons.append(
                    f"Meridian clarity variation noted under {astig.chart_type} screening."
                )

        # Check Color Vision
        for cv in color_list:
            if cv.deficiency_indicated:
                referral_reasons.append(
                    f"Pseudoisochromatic plate screening indicated possible {cv.deficiency_type} color variance."
                )

        referral_recommended = len(referral_reasons) > 0

        return ClinicalSessionSummaryResponse(
            session=ScreeningSessionResponse.model_validate(session),
            acuity_results=[VisualAcuityResponse.model_validate(a) for a in acuity_list],
            astigmatism_results=[AstigmatismResponse.model_validate(a) for a in astig_list],
            color_vision_results=[ColorVisionResponse.model_validate(c) for c in color_list],
            referral_recommended=referral_recommended,
            referral_reasons=referral_reasons,
            clinical_disclaimer=CLINICAL_DISCLAIMER_TEXT,
        )

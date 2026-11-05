import json
import uuid
from datetime import UTC, datetime

from sqlalchemy.orm import Session

from app.core.exceptions import (
    ConsentRequiredException,
    EntityNotFoundException,
    InvalidSessionTransitionException,
    ValidationException,
)
from app.models.adaptive_acuity import (
    AdaptiveAcuityAttempt,
    AdaptiveAcuityTest,
)
from app.models.screening_assessment import VisualAcuityAssessment
from app.models.screening_audit_event import ScreeningAuditEvent
from app.models.user import User
from app.repositories.adaptive_acuity_repository import AdaptiveAcuityRepository
from app.repositories.screening_repository import ScreeningRepository
from app.schemas.adaptive_acuity import (
    AdaptiveAcuityCancelRequest,
    AdaptiveAcuityResponseRequest,
    AdaptiveAcuityResultResponse,
    AdaptiveAcuityStartRequest,
    AdaptiveAcuityStepResponse,
    AdaptiveAcuityVoiceStepResponse,
    OptotypeChallengeResponse,
)
from app.schemas.screening import ScreeningSessionStatus
from app.services.adaptive_acuity_engine import (
    AcuityLevelSpec,
    AdaptiveAcuityEngine,
    CalibrationTier,
)
from app.services.visual_acuity_service import VisualAcuityService
from app.services.voice_acuity_interpreter import VoiceAcuityInterpreter
from app.services.voice_service import VoiceService


class AdaptiveAcuityService:
    """Orchestrates interactive adaptive visual acuity screening tests."""

    @staticmethod
    def start_test(
        db: Session,
        user: User,
        session_id: uuid.UUID,
        payload: AdaptiveAcuityStartRequest,
    ) -> tuple[AdaptiveAcuityTest, OptotypeChallengeResponse]:
        """
        Initiates a new adaptive screening test session.
        Enforces active consent, screening session lifecycle, and prevents concurrent active duplicates.
        """
        # 1. Verify Active Screening Consent
        active_consent = ScreeningRepository.get_active_consent(db, user.id)
        if not active_consent:
            raise ConsentRequiredException(
                "Active informed consent is required to start an adaptive vision screening test."
            )

        # 2. Verify Screening Session
        session = ScreeningRepository.get_session_by_id(db, session_id)
        if not session or session.user_id != user.id:
            raise EntityNotFoundException("ScreeningSession", session_id)

        if session.status != ScreeningSessionStatus.IN_PROGRESS.value:
            raise InvalidSessionTransitionException(
                f"Cannot start adaptive test on screening session with status '{session.status}'."
            )

        # 3. Canonicalize Parameters
        canonical_eye = VisualAcuityService.canonicalize_eye(payload.test_eye)
        canonical_type = VisualAcuityService.canonicalize_assessment_type(payload.test_type)
        optotype_type = payload.optotype_type.upper().strip()

        # 4. Prevent Conflicting Active Tests
        existing_active = AdaptiveAcuityRepository.get_active_test_for_config(
            db=db,
            session_id=session_id,
            test_eye=canonical_eye,
            test_type=canonical_type,
        )
        if existing_active:
            raise ValidationException(
                f"An adaptive visual acuity test for {canonical_eye} eye ({canonical_type}) "
                f"is already in progress (Test ID: {existing_active.id}). "
                "Complete or cancel it before starting a new test."
            )

        # 5. Viewing Distance and Geometry Validation
        if payload.viewing_distance_meters is not None:
            dist = float(payload.viewing_distance_meters)
        else:
            dist = (
                AdaptiveAcuityEngine.DEFAULT_DISTANCE_METERS
                if canonical_type == "DISTANCE"
                else AdaptiveAcuityEngine.DEFAULT_NEAR_METERS
            )

        # 6. Evaluate Physical Calibration Tier
        calib_dict = payload.calibration.model_dump() if payload.calibration else None
        calib_tier, calib_info = AdaptiveAcuityEngine.evaluate_calibration(
            calibration_dict=calib_dict,
            test_type=canonical_type,
        )

        display_dpi = calib_info.get("display_dpi")

        # 7. Sizing & Optotype Generation for Initial Challenge
        starting_level = payload.starting_level
        if starting_level not in AdaptiveAcuityEngine.LEVEL_SPECS:
            starting_level = 6  # 20/40 driving standard default

        spec: AcuityLevelSpec = AdaptiveAcuityEngine.LEVEL_SPECS[starting_level]
        height_mm, height_px = AdaptiveAcuityEngine.calculate_optotype_dimensions(
            arcmin=spec.arcmin,
            viewing_distance_meters=dist,
            display_dpi=display_dpi,
        )

        symbol, expected, choices = AdaptiveAcuityEngine.generate_next_optotype(
            optotype_type=optotype_type,
            previous_optotype=None,
        )

        now = datetime.now(UTC)
        test = AdaptiveAcuityTest(
            session_id=session_id,
            user_id=user.id,
            test_type=canonical_type,
            test_eye=canonical_eye,
            optotype_type=optotype_type,
            protocol_version=payload.protocol_version,
            status="IN_PROGRESS",
            calibration_status=calib_tier.value,
            calibration_data=json.dumps(calib_info),
            viewing_distance_meters=dist,
            user_reported_occlusion=payload.user_reported_occlusion,
            current_level=starting_level,
            current_attempt_sequence=1,
            current_optotype=symbol,
            current_expected_response=expected,
            total_attempts=0,
            correct_attempts=0,
            incorrect_attempts=0,
            started_at=now,
        )
        saved_test = AdaptiveAcuityRepository.create_test(db, test)

        # 8. Create First Attempt Record
        attempt = AdaptiveAcuityAttempt(
            test_id=saved_test.id,
            attempt_sequence=1,
            level=starting_level,
            optotype_type=optotype_type,
            presented_symbol=symbol,
            expected_response=expected,
            target_size_arcmin=spec.arcmin,
            target_height_mm=height_mm,
            target_height_px=height_px,
            presented_at=now,
        )
        AdaptiveAcuityRepository.create_attempt(db, attempt)

        # Audit
        audit = ScreeningAuditEvent(
            user_id=user.id,
            session_id=session_id,
            event_type="ADAPTIVE_TEST_STARTED",
            occurred_at=now,
            metadata_json=json.dumps(
                {
                    "test_id": str(saved_test.id),
                    "eye": canonical_eye,
                    "type": canonical_type,
                    "starting_level": starting_level,
                    "calibration_tier": calib_tier.value,
                }
            ),
        )
        ScreeningRepository.create_audit_event(db, audit)

        # 9. Build Safe Challenge Response (Zero Answer Leakage)
        challenge = OptotypeChallengeResponse(
            test_id=saved_test.id,
            attempt_sequence=1,
            current_level=starting_level,
            level_snellen=spec.snellen,
            level_logmar=spec.logmar,
            optotype_type=optotype_type,
            presented_symbol=symbol,
            choices=choices,
            target_size_arcmin=spec.arcmin,
            target_height_mm=height_mm,
            target_height_px=height_px,
            test_eye=canonical_eye,
            test_type=canonical_type,
            instructions=(
                f"Testing {canonical_eye.upper()} eye at {dist:.1f}m. "
                "Ensure non-tested eye is covered. Select the direction or letter shown."
            ),
        )

        return saved_test, challenge

    @staticmethod
    def get_current_challenge(
        db: Session,
        user: User,
        test_id: uuid.UUID,
    ) -> OptotypeChallengeResponse:
        """Retrieves the active challenge for an in-progress adaptive test."""
        test = AdaptiveAcuityRepository.get_test_by_id(db, test_id)
        if not test or test.user_id != user.id:
            raise EntityNotFoundException("AdaptiveAcuityTest", test_id)

        if test.status != "IN_PROGRESS":
            raise ValidationException(f"Adaptive test is not in progress (Status: {test.status}).")

        attempt = AdaptiveAcuityRepository.get_attempt(db, test.id, test.current_attempt_sequence)
        if not attempt:
            raise EntityNotFoundException("AdaptiveAcuityAttempt", test.current_attempt_sequence)

        spec = AdaptiveAcuityEngine.LEVEL_SPECS[test.current_level]
        if test.optotype_type == "SLOAN":
            choices = AdaptiveAcuityEngine.SLOAN_LETTERS
        elif test.optotype_type == "LANDOLT_C":
            choices = AdaptiveAcuityEngine.LANDOLT_C_DIRECTIONS
        else:
            choices = AdaptiveAcuityEngine.TUMBLING_E_DIRECTIONS

        return OptotypeChallengeResponse(
            test_id=test.id,
            attempt_sequence=attempt.attempt_sequence,
            current_level=test.current_level,
            level_snellen=spec.snellen,
            level_logmar=spec.logmar,
            optotype_type=test.optotype_type,
            presented_symbol=attempt.presented_symbol,
            choices=choices,
            target_size_arcmin=attempt.target_size_arcmin,
            target_height_mm=attempt.target_height_mm,
            target_height_px=attempt.target_height_px,
            test_eye=test.test_eye,
            test_type=test.test_type,
            instructions=(
                f"Testing {test.test_eye.upper()} eye at {test.viewing_distance_meters:.1f}m. "
                "Select the direction or letter shown."
            ),
        )

    @classmethod
    def _advance_or_complete_step(
        cls,
        db: Session,
        test: AdaptiveAcuityTest,
        current_attempt: AdaptiveAcuityAttempt,
        is_correct: bool,
        now: datetime,
    ) -> tuple[bool, OptotypeChallengeResponse | None, AdaptiveAcuityResultResponse | None]:
        """
        Advances the 3-of-4 ATS clinical staircase progression or finalizes preliminary acuity calculation.
        Shared across manual response submission and voice response submission.
        """
        # 1. Update Aggregated Counters
        test.total_attempts += 1
        if is_correct:
            test.correct_attempts += 1
        else:
            test.incorrect_attempts += 1

        # 2. Determine Level Status under Protocol (3-of-4 ATS Rule)
        level_attempts = AdaptiveAcuityRepository.list_attempts_for_level(
            db=db,
            test_id=test.id,
            level=test.current_level,
        )
        level_bools = [a.is_correct for a in level_attempts if a.is_correct is not None]
        level_progress = AdaptiveAcuityEngine.evaluate_level_progress(level_bools)

        # Reconstruct set of previously passed levels for stopping rule evaluation
        all_attempts = AdaptiveAcuityRepository.list_attempts_for_test(db, test.id)
        passed_levels: set[int] = set()
        for lvl_idx in AdaptiveAcuityEngine.LEVEL_SPECS:
            lvl_bools = [
                a.is_correct
                for a in all_attempts
                if a.level == lvl_idx and a.is_correct is not None
            ]
            if AdaptiveAcuityEngine.evaluate_level_progress(lvl_bools) == "PASS":
                passed_levels.add(lvl_idx)

        action, next_level, resolved_acuity_level = AdaptiveAcuityEngine.determine_next_action(
            current_level=test.current_level,
            level_result=level_progress,
            passed_levels=passed_levels,
        )

        # 3. Handle Completion or Next Challenge
        if action == "STOP_COMPLETE":
            test.status = "COMPLETED"
            test.completed_at = now
            test.smallest_resolved_level = resolved_acuity_level

            if resolved_acuity_level is not None:
                spec = AdaptiveAcuityEngine.LEVEL_SPECS[resolved_acuity_level]
                test.final_snellen = spec.snellen
                test.final_logmar = spec.logmar
                test.final_decimal = spec.decimal_acuity
            else:
                # User failed largest optotype (< 20/200)
                test.final_snellen = "> 20/200"
                test.final_logmar = 1.10
                test.final_decimal = 0.08

            # Automatically persist VisualAcuityAssessment for parent screening session
            is_calibrated_bool = test.calibration_status in [
                CalibrationTier.SERVER_VERIFIED.value,
                CalibrationTier.PROFESSIONALLY_VALIDATED.value,
            ]
            assessment = VisualAcuityAssessment(
                session_id=test.session_id,
                user_id=test.user_id,
                test_eye=test.test_eye,
                assessment_type=test.test_type,
                snellen_fraction=test.final_snellen,
                logmar=test.final_logmar or 1.0,
                decimal_acuity=test.final_decimal or 0.1,
                tested_distance_meters=test.viewing_distance_meters,
                unassisted_or_corrected="unassisted",
                is_calibrated=is_calibrated_bool,
                calibration_metadata=test.calibration_data,
                observations=(
                    f"Adaptive screening ({test.protocol_version}) completed. "
                    f"Calibration tier: {test.calibration_status}. "
                    f"Attempts: {test.total_attempts} ({test.correct_attempts} correct)."
                ),
                created_at=now,
                updated_at=now,
            )
            saved_assessment = ScreeningRepository.create_acuity_assessment(db, assessment)
            test.assessment_id = saved_assessment.id
            AdaptiveAcuityRepository.update_test(db, test)

            # Audit
            audit = ScreeningAuditEvent(
                user_id=test.user_id,
                session_id=test.session_id,
                event_type="ADAPTIVE_TEST_COMPLETED",
                occurred_at=now,
                metadata_json=json.dumps(
                    {
                        "test_id": str(test.id),
                        "snellen": test.final_snellen,
                        "logmar": test.final_logmar,
                        "attempts": test.total_attempts,
                    }
                ),
            )
            ScreeningRepository.create_audit_event(db, audit)

            result_summary = AdaptiveAcuityService._build_result_response(test)
            return True, None, result_summary

        # Next Challenge within ongoing test
        if next_level is not None and next_level != test.current_level:
            test.current_level = next_level

        test.current_attempt_sequence += 1

        # Sizing and Optotype Generation
        curr_spec = AdaptiveAcuityEngine.LEVEL_SPECS[test.current_level]
        calib_dict = json.loads(test.calibration_data) if test.calibration_data else {}
        display_dpi = calib_dict.get("display_dpi")

        height_mm, height_px = AdaptiveAcuityEngine.calculate_optotype_dimensions(
            arcmin=curr_spec.arcmin,
            viewing_distance_meters=test.viewing_distance_meters,
            display_dpi=display_dpi,
        )

        symbol, expected, choices = AdaptiveAcuityEngine.generate_next_optotype(
            optotype_type=test.optotype_type,
            previous_optotype=current_attempt.presented_symbol,
        )

        test.current_optotype = symbol
        test.current_expected_response = expected
        AdaptiveAcuityRepository.update_test(db, test)

        # Create next attempt in DB
        next_attempt = AdaptiveAcuityAttempt(
            test_id=test.id,
            attempt_sequence=test.current_attempt_sequence,
            level=test.current_level,
            optotype_type=test.optotype_type,
            presented_symbol=symbol,
            expected_response=expected,
            target_size_arcmin=curr_spec.arcmin,
            target_height_mm=height_mm,
            target_height_px=height_px,
            presented_at=now,
        )
        AdaptiveAcuityRepository.create_attempt(db, next_attempt)

        next_challenge = OptotypeChallengeResponse(
            test_id=test.id,
            attempt_sequence=test.current_attempt_sequence,
            current_level=test.current_level,
            level_snellen=curr_spec.snellen,
            level_logmar=curr_spec.logmar,
            optotype_type=test.optotype_type,
            presented_symbol=symbol,
            choices=choices,
            target_size_arcmin=curr_spec.arcmin,
            target_height_mm=height_mm,
            target_height_px=height_px,
            test_eye=test.test_eye,
            test_type=test.test_type,
            instructions=(
                f"Testing {test.test_eye.upper()} eye at {test.viewing_distance_meters:.1f}m. "
                "Select the direction or letter shown."
            ),
        )

        return False, next_challenge, None

    @classmethod
    def submit_response(
        cls,
        db: Session,
        user: User,
        test_id: uuid.UUID,
        payload: AdaptiveAcuityResponseRequest,
    ) -> AdaptiveAcuityStepResponse:
        """
        Validates citizen's response server-side, updates progression under 3-of-4 ATS rule,
        and generates next challenge or finalizes preliminary acuity calculation.
        """
        test = AdaptiveAcuityRepository.get_test_by_id(db, test_id, for_update=True)
        if not test or test.user_id != user.id:
            raise EntityNotFoundException("AdaptiveAcuityTest", test_id)

        if test.status != "IN_PROGRESS":
            raise ValidationException(
                f"Cannot submit response to test with status '{test.status}'."
            )

        if payload.attempt_sequence != test.current_attempt_sequence:
            raise ValidationException(
                f"Out-of-order or duplicate attempt submitted. Expected attempt #{test.current_attempt_sequence}, "
                f"received #{payload.attempt_sequence}."
            )

        attempt = AdaptiveAcuityRepository.get_attempt(db, test.id, test.current_attempt_sequence)
        if not attempt:
            raise EntityNotFoundException("AdaptiveAcuityAttempt", test.current_attempt_sequence)

        if attempt.is_correct is not None:
            raise ValidationException(
                f"Attempt #{payload.attempt_sequence} has already been evaluated."
            )

        # 1. Independent Server-Side Correctness Evaluation
        canonical_user = payload.user_response.strip().upper()
        canonical_expected = attempt.expected_response.strip().upper()
        is_correct = canonical_user == canonical_expected

        now = datetime.now(UTC)
        attempt.user_response = payload.user_response.strip()
        attempt.is_correct = is_correct
        attempt.response_duration_ms = payload.response_duration_ms
        attempt.answered_at = now
        attempt.input_modality = "MANUAL"
        AdaptiveAcuityRepository.update_attempt(db, attempt)

        is_complete, next_challenge, result_summary = cls._advance_or_complete_step(
            db=db,
            test=test,
            current_attempt=attempt,
            is_correct=is_correct,
            now=now,
        )

        return AdaptiveAcuityStepResponse(
            test_id=test.id,
            attempt_sequence=attempt.attempt_sequence,
            test_status="COMPLETED" if is_complete else "IN_PROGRESS",
            was_correct=is_correct,
            level=test.current_level,
            total_attempts=test.total_attempts,
            correct_attempts=test.correct_attempts,
            is_test_complete=is_complete,
            next_challenge=next_challenge,
            result_summary=result_summary,
        )

    @classmethod
    def submit_voice_response(
        cls,
        db: Session,
        user: User,
        test_id: uuid.UUID,
        attempt_sequence: int,
        audio_bytes: bytes,
        response_duration_ms: int | None = None,
    ) -> AdaptiveAcuityVoiceStepResponse:
        """
        Processes microphone audio input for the active optotype presentation challenge.
        Performs speech recognition, normalizes speech into optotype answers, detects
        visual inability or speech ambiguity, and either prompts for retry without penalty
        or advances the adaptive staircase.
        """
        test = AdaptiveAcuityRepository.get_test_by_id(db, test_id, for_update=True)
        if not test or test.user_id != user.id:
            raise EntityNotFoundException("AdaptiveAcuityTest", test_id)

        if test.status != "IN_PROGRESS":
            raise ValidationException(
                f"Cannot submit response to test with status '{test.status}'."
            )

        if attempt_sequence != test.current_attempt_sequence:
            raise ValidationException(
                f"Out-of-order or duplicate attempt submitted. Expected attempt #{test.current_attempt_sequence}, "
                f"received #{attempt_sequence}."
            )

        attempt = AdaptiveAcuityRepository.get_attempt(db, test.id, test.current_attempt_sequence)
        if not attempt:
            raise EntityNotFoundException("AdaptiveAcuityAttempt", test.current_attempt_sequence)

        if attempt.is_correct is not None:
            raise ValidationException(f"Attempt #{attempt_sequence} has already been evaluated.")

        # 1. Transcribe audio if provided
        raw_transcript = ""
        transcription_confidence = None
        stt_provider = "System.Speech (offline)"

        if not audio_bytes or len(audio_bytes) == 0:
            raw_transcript = ""
            transcription_confidence = 0.0
            stt_provider = "System.Speech (empty_audio)"
        else:
            try:
                transcription = VoiceService.transcribe_audio(audio_bytes)
                raw_transcript = transcription.text
                transcription_confidence = transcription.confidence
                stt_provider = transcription.provider
            except ValidationException as e:
                # If audio is corrupt non-WAV format, re-raise as validation error
                err_msg = str(e).lower()
                if "unsupported audio format" in err_msg or "byte length" in err_msg:
                    raise
                # Empty frames or brief duration treated as silence
                raw_transcript = ""
                transcription_confidence = 0.0
                stt_provider = "System.Speech (silent_audio)"

        # 2. Interpret transcription with clinical acuity rules
        interpretation = VoiceAcuityInterpreter.interpret_voice_response(
            raw_transcript=raw_transcript,
            confidence=transcription_confidence,
            optotype_type=test.optotype_type,
        )

        now = datetime.now(UTC)

        # 3. Handle Retry Required (Ambiguous, Low Confidence, or Unrecognized)
        if interpretation.retry_required:
            attempt.raw_transcript = interpretation.raw_transcript
            attempt.transcription_confidence = interpretation.confidence
            attempt.stt_provider = stt_provider
            attempt.recognition_status = interpretation.status
            attempt.input_modality = "VOICE"
            AdaptiveAcuityRepository.update_attempt(db, attempt)

            spec = AdaptiveAcuityEngine.LEVEL_SPECS[test.current_level]
            if test.optotype_type == "SLOAN":
                choices = AdaptiveAcuityEngine.SLOAN_LETTERS
            elif test.optotype_type == "LANDOLT_C":
                choices = AdaptiveAcuityEngine.LANDOLT_C_DIRECTIONS
            else:
                choices = AdaptiveAcuityEngine.TUMBLING_E_DIRECTIONS

            current_challenge = OptotypeChallengeResponse(
                test_id=test.id,
                attempt_sequence=attempt.attempt_sequence,
                current_level=test.current_level,
                level_snellen=spec.snellen,
                level_logmar=spec.logmar,
                optotype_type=test.optotype_type,
                presented_symbol=attempt.presented_symbol,
                choices=choices,
                target_size_arcmin=attempt.target_size_arcmin,
                target_height_mm=attempt.target_height_mm,
                target_height_px=attempt.target_height_px,
                test_eye=test.test_eye,
                test_type=test.test_type,
                instructions=(
                    f"Testing {test.test_eye.upper()} eye at {test.viewing_distance_meters:.1f}m. "
                    "Speak clearly into the microphone."
                ),
            )

            return AdaptiveAcuityVoiceStepResponse(
                test_id=test.id,
                attempt_sequence=attempt.attempt_sequence,
                test_status=test.status,
                was_correct=None,
                level=test.current_level,
                total_attempts=test.total_attempts,
                correct_attempts=test.correct_attempts,
                is_test_complete=False,
                input_modality="VOICE",
                recognition_status=interpretation.status,
                raw_transcript=interpretation.raw_transcript,
                recognized_symbol=interpretation.normalized_symbol,
                transcription_confidence=interpretation.confidence,
                stt_provider=stt_provider,
                retry_required=True,
                feedback_message=interpretation.feedback_message,
                next_challenge=current_challenge,
                result_summary=None,
            )

        # 4. Speech is recognized or Citizen indicated inability ("CANNOT_SEE")
        if interpretation.status == "CANNOT_SEE":
            user_response_val = "CANNOT_SEE"
            is_correct = False
        else:
            user_response_val = interpretation.normalized_symbol or ""
            canonical_user = user_response_val.strip().upper()
            canonical_expected = attempt.expected_response.strip().upper()
            is_correct = canonical_user == canonical_expected

        attempt.user_response = user_response_val
        attempt.is_correct = is_correct
        attempt.response_duration_ms = response_duration_ms
        attempt.answered_at = now
        attempt.input_modality = "VOICE"
        attempt.transcription_confidence = interpretation.confidence
        attempt.stt_provider = stt_provider
        attempt.raw_transcript = interpretation.raw_transcript
        attempt.recognition_status = interpretation.status
        AdaptiveAcuityRepository.update_attempt(db, attempt)

        # 5. Advance or Complete Test Step
        is_complete, next_challenge, result_summary = cls._advance_or_complete_step(
            db=db,
            test=test,
            current_attempt=attempt,
            is_correct=is_correct,
            now=now,
        )

        return AdaptiveAcuityVoiceStepResponse(
            test_id=test.id,
            attempt_sequence=attempt.attempt_sequence,
            test_status="COMPLETED" if is_complete else "IN_PROGRESS",
            was_correct=is_correct,
            level=test.current_level,
            total_attempts=test.total_attempts,
            correct_attempts=test.correct_attempts,
            is_test_complete=is_complete,
            input_modality="VOICE",
            recognition_status=interpretation.status,
            raw_transcript=interpretation.raw_transcript,
            recognized_symbol=interpretation.normalized_symbol,
            transcription_confidence=interpretation.confidence,
            stt_provider=stt_provider,
            retry_required=False,
            feedback_message=interpretation.feedback_message,
            next_challenge=next_challenge,
            result_summary=result_summary,
        )

    @staticmethod
    def cancel_test(
        db: Session,
        user: User,
        test_id: uuid.UUID,
        payload: AdaptiveAcuityCancelRequest | None = None,
    ) -> AdaptiveAcuityResultResponse:
        """Cancels an active adaptive test."""
        test = AdaptiveAcuityRepository.get_test_by_id(db, test_id, for_update=True)
        if not test or test.user_id != user.id:
            raise EntityNotFoundException("AdaptiveAcuityTest", test_id)

        if test.status != "IN_PROGRESS":
            raise InvalidSessionTransitionException(
                f"Cannot cancel test with status '{test.status}'."
            )

        now = datetime.now(UTC)
        reason = payload.reason if payload and payload.reason else "user_cancelled"
        test.status = "CANCELLED"
        test.cancelled_at = now
        test.cancellation_reason = reason
        updated = AdaptiveAcuityRepository.update_test(db, test)

        # Audit
        audit = ScreeningAuditEvent(
            user_id=user.id,
            session_id=test.session_id,
            event_type="ADAPTIVE_TEST_CANCELLED",
            occurred_at=now,
            metadata_json=json.dumps({"test_id": str(test.id), "reason": reason}),
        )
        ScreeningRepository.create_audit_event(db, audit)

        return AdaptiveAcuityService._build_result_response(updated)

    @staticmethod
    def complete_test(
        db: Session,
        user: User,
        test_id: uuid.UUID,
    ) -> AdaptiveAcuityResultResponse:
        """Allows early finalization of an ongoing adaptive test."""
        test = AdaptiveAcuityRepository.get_test_by_id(db, test_id, for_update=True)
        if not test or test.user_id != user.id:
            raise EntityNotFoundException("AdaptiveAcuityTest", test_id)

        if test.status != "IN_PROGRESS":
            raise InvalidSessionTransitionException(
                f"Cannot finalize test with status '{test.status}'."
            )

        now = datetime.now(UTC)
        test.status = "COMPLETED"
        test.completed_at = now

        # Use highest level passed so far, or None
        all_attempts = AdaptiveAcuityRepository.list_attempts_for_test(db, test.id)
        passed_levels = set()
        for lvl_idx in AdaptiveAcuityEngine.LEVEL_SPECS:
            lvl_bools = [
                a.is_correct
                for a in all_attempts
                if a.level == lvl_idx and a.is_correct is not None
            ]
            if AdaptiveAcuityEngine.evaluate_level_progress(lvl_bools) == "PASS":
                passed_levels.add(lvl_idx)

        resolved_level = max(passed_levels) if passed_levels else None
        test.smallest_resolved_level = resolved_level

        if resolved_level is not None:
            spec = AdaptiveAcuityEngine.LEVEL_SPECS[resolved_level]
            test.final_snellen = spec.snellen
            test.final_logmar = spec.logmar
            test.final_decimal = spec.decimal_acuity
        else:
            test.final_snellen = "INCOMPLETE"
            test.final_logmar = 1.00
            test.final_decimal = 0.10

        is_calibrated_bool = test.calibration_status in [
            CalibrationTier.SERVER_VERIFIED.value,
            CalibrationTier.PROFESSIONALLY_VALIDATED.value,
        ]
        assessment = VisualAcuityAssessment(
            session_id=test.session_id,
            user_id=test.user_id,
            test_eye=test.test_eye,
            assessment_type=test.test_type,
            snellen_fraction=test.final_snellen,
            logmar=test.final_logmar or 1.0,
            decimal_acuity=test.final_decimal or 0.1,
            tested_distance_meters=test.viewing_distance_meters,
            unassisted_or_corrected="unassisted",
            is_calibrated=is_calibrated_bool,
            calibration_metadata=test.calibration_data,
            observations=(
                f"Adaptive test ({test.protocol_version}) completed early by request. "
                f"Attempts: {test.total_attempts} ({test.correct_attempts} correct)."
            ),
            created_at=now,
            updated_at=now,
        )
        saved_assessment = ScreeningRepository.create_acuity_assessment(db, assessment)
        test.assessment_id = saved_assessment.id
        updated = AdaptiveAcuityRepository.update_test(db, test)

        return AdaptiveAcuityService._build_result_response(updated)

    @staticmethod
    def get_test_result(
        db: Session,
        user: User,
        test_id: uuid.UUID,
    ) -> AdaptiveAcuityResultResponse:
        """Retrieves visual acuity result summary enforcing strict ownership."""
        test = AdaptiveAcuityRepository.get_test_by_id(db, test_id)
        if not test or test.user_id != user.id:
            raise EntityNotFoundException("AdaptiveAcuityTest", test_id)

        return AdaptiveAcuityService._build_result_response(test)

    @staticmethod
    def _build_result_response(test: AdaptiveAcuityTest) -> AdaptiveAcuityResultResponse:
        """Constructs standardized result envelope with mandatory clinical disclaimer."""
        is_calibrated_bool = test.calibration_status in [
            CalibrationTier.SERVER_VERIFIED.value,
            CalibrationTier.PROFESSIONALLY_VALIDATED.value,
        ]
        return AdaptiveAcuityResultResponse(
            test_id=test.id,
            session_id=test.session_id,
            user_id=test.user_id,
            test_type=test.test_type,
            test_eye=test.test_eye,
            optotype_type=test.optotype_type,
            protocol_version=test.protocol_version,
            status=test.status,
            calibration_status=test.calibration_status,
            is_calibrated=is_calibrated_bool,
            viewing_distance_meters=test.viewing_distance_meters,
            user_reported_occlusion=test.user_reported_occlusion,
            total_attempts=test.total_attempts,
            correct_attempts=test.correct_attempts,
            incorrect_attempts=test.incorrect_attempts,
            smallest_resolved_level=test.smallest_resolved_level,
            final_snellen=test.final_snellen,
            final_logmar=test.final_logmar,
            final_decimal=test.final_decimal,
            assessment_id=test.assessment_id,
            started_at=test.started_at,
            completed_at=test.completed_at,
            clinical_disclaimer=AdaptiveAcuityEngine.CLINICAL_DISCLAIMER,
            validation_status=AdaptiveAcuityEngine.CLINICAL_VALIDATION_STATUS,
        )

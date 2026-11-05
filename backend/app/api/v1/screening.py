import base64
import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, Query, Request, status
from sqlalchemy.orm import Session

from app.api.dependencies import get_current_active_user, get_db
from app.core.exceptions import ValidationException
from app.models.user import User
from app.schemas.adaptive_acuity import (
    AdaptiveAcuityCancelRequest,
    AdaptiveAcuityResponseRequest,
    AdaptiveAcuityResultResponse,
    AdaptiveAcuityStartRequest,
    AdaptiveAcuityStepResponse,
    AdaptiveAcuityVoiceResponseRequest,
    AdaptiveAcuityVoiceStepResponse,
    OptotypeChallengeResponse,
)
from app.schemas.auth import MessageResponse
from app.schemas.clinical_assessments import (
    AstigmatismCreateRequest,
    AstigmatismResponse,
    ClinicalSessionSummaryResponse,
    ColorVisionCreateRequest,
    ColorVisionResponse,
    VisualAcuityCreateRequest,
    VisualAcuityListResponse,
    VisualAcuityResponse,
    VisualAcuitySummaryResponse,
)
from app.schemas.online_screening import (
    CalibrationResponse,
    CalibrationSubmitRequest,
    FinalScreeningReportResponse,
    ScreeningHistoryResponse,
    ScreeningPlatformConfigResponse,
    TestCancelRequest,
    TestChallengeResponse,
    TestModuleDefinition,
    TestResponseSubmitRequest,
    TestResultResponse,
    TestStartRequest,
    TestStepResponse,
)
from app.schemas.screening import (
    ConsentAcceptRequest,
    ConsentResponse,
    ConsentStatusResponse,
    ScreeningSessionCancelRequest,
    ScreeningSessionCreateRequest,
    ScreeningSessionListResponse,
    ScreeningSessionResponse,
)
from app.services.adaptive_acuity_service import AdaptiveAcuityService
from app.services.online_screening_service import OnlineScreeningService
from app.services.screening_service import ScreeningService

router = APIRouter()


# -----------------------------------------------------------------------------
# Consent Management Endpoints (with /consent alias)
# -----------------------------------------------------------------------------


@router.get(
    "/consent/current",
    response_model=ConsentStatusResponse,
    status_code=status.HTTP_200_OK,
    summary="Get Current Consent Document & State",
    description="Returns the server-controlled screening consent document and the authenticated user's acceptance status.",
)
async def get_current_consent(
    current_user: Annotated[User, Depends(get_current_active_user)],
    db: Annotated[Session, Depends(get_db)],
) -> ConsentStatusResponse:
    return ScreeningService.get_current_consent_status(db=db, user=current_user)


@router.get(
    "/consent",
    response_model=ConsentStatusResponse,
    status_code=status.HTTP_200_OK,
    summary="Get Current Consent (Alias)",
    description="Canonical alias for /screening/consent/current to support unified web and mobile clients.",
    include_in_schema=False,
)
async def get_consent_alias(
    current_user: Annotated[User, Depends(get_current_active_user)],
    db: Annotated[Session, Depends(get_db)],
) -> ConsentStatusResponse:
    return ScreeningService.get_current_consent_status(db=db, user=current_user)


@router.post(
    "/consent/accept",
    response_model=ConsentResponse,
    status_code=status.HTTP_200_OK,
    summary="Accept Screening Consent",
    description="Records informed consent acceptance for the active server-controlled document version.",
)
async def accept_consent(
    payload: ConsentAcceptRequest,
    current_user: Annotated[User, Depends(get_current_active_user)],
    db: Annotated[Session, Depends(get_db)],
) -> ConsentResponse:
    return ScreeningService.accept_consent(db=db, user=current_user, payload=payload)


@router.post(
    "/consent/withdraw",
    response_model=MessageResponse,
    status_code=status.HTTP_200_OK,
    summary="Withdraw Screening Consent",
    description="Withdraws active consent, terminates any in-progress screening sessions, and blocks new sessions.",
)
async def withdraw_consent(
    current_user: Annotated[User, Depends(get_current_active_user)],
    db: Annotated[Session, Depends(get_db)],
) -> MessageResponse:
    return ScreeningService.withdraw_consent(db=db, user=current_user)


# -----------------------------------------------------------------------------
# Screening Session Lifecycle Endpoints
# -----------------------------------------------------------------------------


@router.post(
    "/sessions",
    response_model=ScreeningSessionResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Initiate Screening Session",
    description="Creates a new preliminary vision screening session in IN_PROGRESS status. Requires active consent.",
)
async def create_screening_session(
    current_user: Annotated[User, Depends(get_current_active_user)],
    db: Annotated[Session, Depends(get_db)],
    payload: ScreeningSessionCreateRequest | None = None,
) -> ScreeningSessionResponse:
    return ScreeningService.create_session(db=db, user=current_user, payload=payload)


@router.get(
    "/sessions",
    response_model=ScreeningSessionListResponse,
    status_code=status.HTTP_200_OK,
    summary="List User Screening Sessions",
    description="Retrieves a paginated list of screening sessions belonging exclusively to the authenticated user.",
)
async def list_screening_sessions(
    current_user: Annotated[User, Depends(get_current_active_user)],
    db: Annotated[Session, Depends(get_db)],
    status_filter: str | None = Query(default=None, alias="status", max_length=50),
    limit: int = Query(default=20, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
) -> ScreeningSessionListResponse:
    return ScreeningService.list_sessions(
        db=db,
        user=current_user,
        status=status_filter,
        limit=limit,
        offset=offset,
    )


@router.get(
    "/sessions/{session_id}",
    response_model=ScreeningSessionResponse,
    status_code=status.HTTP_200_OK,
    summary="Get Screening Session Details",
    description="Retrieves a specific screening session by ID. Strictly enforces user ownership.",
)
async def get_screening_session(
    session_id: uuid.UUID,
    current_user: Annotated[User, Depends(get_current_active_user)],
    db: Annotated[Session, Depends(get_db)],
) -> ScreeningSessionResponse:
    return ScreeningService.get_session(db=db, user=current_user, session_id=session_id)


@router.post(
    "/sessions/{session_id}/complete",
    response_model=ScreeningSessionResponse,
    status_code=status.HTTP_200_OK,
    summary="Complete Screening Session",
    description="Transitions an IN_PROGRESS session to COMPLETED. Server records completion timestamp.",
)
async def complete_screening_session(
    session_id: uuid.UUID,
    current_user: Annotated[User, Depends(get_current_active_user)],
    db: Annotated[Session, Depends(get_db)],
) -> ScreeningSessionResponse:
    return ScreeningService.complete_session(db=db, user=current_user, session_id=session_id)


@router.post(
    "/sessions/{session_id}/cancel",
    response_model=ScreeningSessionResponse,
    status_code=status.HTTP_200_OK,
    summary="Cancel Screening Session",
    description="Transitions an IN_PROGRESS session to CANCELLED. Server records cancellation timestamp and reason.",
)
async def cancel_screening_session(
    session_id: uuid.UUID,
    current_user: Annotated[User, Depends(get_current_active_user)],
    db: Annotated[Session, Depends(get_db)],
    payload: ScreeningSessionCancelRequest | None = None,
) -> ScreeningSessionResponse:
    return ScreeningService.cancel_session(
        db=db,
        user=current_user,
        session_id=session_id,
        payload=payload,
    )


# -----------------------------------------------------------------------------
# Clinical Assessment Endpoints (Visual Acuity, Astigmatism, Color Vision)
# -----------------------------------------------------------------------------


@router.post(
    "/sessions/{session_id}/acuity",
    response_model=VisualAcuityResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Record Visual Acuity Assessment",
    description="Records distance or near visual acuity screening findings for an active session.",
)
async def record_acuity_assessment(
    session_id: uuid.UUID,
    payload: VisualAcuityCreateRequest,
    current_user: Annotated[User, Depends(get_current_active_user)],
    db: Annotated[Session, Depends(get_db)],
) -> VisualAcuityResponse:
    return ScreeningService.record_visual_acuity(
        db=db,
        user=current_user,
        session_id=session_id,
        payload=payload,
    )


@router.get(
    "/sessions/{session_id}/acuity",
    response_model=list[VisualAcuityResponse],
    status_code=status.HTTP_200_OK,
    summary="Get Visual Acuity Assessments",
    description="Retrieves all visual acuity results associated with the session.",
)
async def get_acuity_assessments(
    session_id: uuid.UUID,
    current_user: Annotated[User, Depends(get_current_active_user)],
    db: Annotated[Session, Depends(get_db)],
) -> list[VisualAcuityResponse]:
    return ScreeningService.get_visual_acuity_for_session(
        db=db,
        user=current_user,
        session_id=session_id,
    )


@router.get(
    "/sessions/{session_id}/acuity/summary",
    response_model=VisualAcuitySummaryResponse,
    status_code=status.HTTP_200_OK,
    summary="Get Visual Acuity Session Summary",
    description="Returns a deterministic preliminary visual acuity summary (OD, OS, OU) and triage recommendations for the session.",
)
async def get_acuity_session_summary(
    session_id: uuid.UUID,
    current_user: Annotated[User, Depends(get_current_active_user)],
    db: Annotated[Session, Depends(get_db)],
) -> VisualAcuitySummaryResponse:
    return ScreeningService.get_visual_acuity_session_summary(
        db=db,
        user=current_user,
        session_id=session_id,
    )


@router.get(
    "/acuity/history",
    response_model=VisualAcuityListResponse,
    status_code=status.HTTP_200_OK,
    summary="List Visual Acuity History",
    description="Returns paginated historical visual acuity screening records for the authenticated user.",
)
async def list_acuity_history(
    current_user: Annotated[User, Depends(get_current_active_user)],
    db: Annotated[Session, Depends(get_db)],
    limit: Annotated[int, Query(ge=1, le=100)] = 20,
    offset: Annotated[int, Query(ge=0)] = 0,
) -> VisualAcuityListResponse:
    items, total = ScreeningService.list_visual_acuity_history(
        db=db,
        user=current_user,
        limit=limit,
        offset=offset,
    )
    return VisualAcuityListResponse(
        items=items,
        total=total,
        limit=limit,
        offset=offset,
    )


@router.get(
    "/acuity/{assessment_id}",
    response_model=VisualAcuityResponse,
    status_code=status.HTTP_200_OK,
    summary="Get Visual Acuity Assessment by ID",
    description="Retrieves a single visual acuity assessment by ID, strictly verifying ownership (IDOR defense).",
)
async def get_acuity_assessment_by_id(
    assessment_id: uuid.UUID,
    current_user: Annotated[User, Depends(get_current_active_user)],
    db: Annotated[Session, Depends(get_db)],
) -> VisualAcuityResponse:
    return ScreeningService.get_visual_acuity_by_id(
        db=db,
        user=current_user,
        assessment_id=assessment_id,
    )


# -----------------------------------------------------------------------------
# Adaptive Visual Acuity Screening Endpoints (Interactive Optotype Engine)
# -----------------------------------------------------------------------------


@router.post(
    "/sessions/{session_id}/acuity/start",
    response_model=OptotypeChallengeResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Start Interactive Adaptive Visual Acuity Test",
    description="Initiates an interactive optotype test session under server-controlled staircase progression.",
)
async def start_adaptive_acuity_test(
    session_id: uuid.UUID,
    payload: AdaptiveAcuityStartRequest,
    current_user: Annotated[User, Depends(get_current_active_user)],
    db: Annotated[Session, Depends(get_db)],
) -> OptotypeChallengeResponse:
    _test, challenge = AdaptiveAcuityService.start_test(
        db=db,
        user=current_user,
        session_id=session_id,
        payload=payload,
    )
    return challenge


@router.get(
    "/acuity/tests/{test_id}/next",
    response_model=OptotypeChallengeResponse,
    status_code=status.HTTP_200_OK,
    summary="Get Next Optotype Challenge",
    description="Retrieves the active optotype presentation challenge without leaking the expected answer.",
)
async def get_adaptive_test_challenge(
    test_id: uuid.UUID,
    current_user: Annotated[User, Depends(get_current_active_user)],
    db: Annotated[Session, Depends(get_db)],
) -> OptotypeChallengeResponse:
    return AdaptiveAcuityService.get_current_challenge(
        db=db,
        user=current_user,
        test_id=test_id,
    )


@router.post(
    "/acuity/tests/{test_id}/response",
    response_model=AdaptiveAcuityStepResponse,
    status_code=status.HTTP_200_OK,
    summary="Submit Optotype Response",
    description="Evaluates user response correctness server-side and advances difficulty or calculates final visual acuity.",
)
async def submit_adaptive_test_response(
    test_id: uuid.UUID,
    payload: AdaptiveAcuityResponseRequest,
    current_user: Annotated[User, Depends(get_current_active_user)],
    db: Annotated[Session, Depends(get_db)],
) -> AdaptiveAcuityStepResponse:
    return AdaptiveAcuityService.submit_response(
        db=db,
        user=current_user,
        test_id=test_id,
        payload=payload,
    )


@router.post(
    "/acuity/tests/{test_id}/voice-response",
    response_model=AdaptiveAcuityVoiceStepResponse,
    status_code=status.HTTP_200_OK,
    summary="Submit Voice Optotype Response",
    description=(
        "Processes microphone audio recording (PCM WAV) or base64 audio payload, "
        "performs speech-to-text recognition and clinical interpretation, advances test difficulty "
        "staircase under 3-of-4 ATS rule, or requests verbal clarification if speech is ambiguous or unclear."
    ),
)
async def submit_adaptive_voice_response(
    test_id: uuid.UUID,
    request: Request,
    current_user: Annotated[User, Depends(get_current_active_user)],
    db: Annotated[Session, Depends(get_db)],
) -> AdaptiveAcuityVoiceStepResponse:
    content_type = request.headers.get("content-type", "")

    if content_type.startswith("multipart/form-data"):
        form = await request.form()
        attempt_seq_raw = form.get("attempt_sequence")
        if not attempt_seq_raw:
            raise ValidationException("Field 'attempt_sequence' is required.")
        try:
            attempt_seq = int(attempt_seq_raw)
        except (ValueError, TypeError) as exc:
            raise ValidationException("Field 'attempt_sequence' must be a valid integer.") from exc

        duration_raw = form.get("response_duration_ms")
        response_duration_ms = int(duration_raw) if duration_raw is not None else None

        upload = form.get("file") or form.get("audio") or form.get("audio_file")
        if not upload or not hasattr(upload, "read"):
            raise ValidationException("Audio file is required in multipart/form-data submission.")
        audio_bytes = await upload.read()
    else:
        try:
            body_data = await request.json()
        except Exception as exc:
            raise ValidationException("Malformed JSON request body.") from exc

        payload = AdaptiveAcuityVoiceResponseRequest.model_validate(body_data)
        attempt_seq = payload.attempt_sequence
        response_duration_ms = payload.response_duration_ms

        if not payload.audio_base64:
            raise ValidationException(
                "Field 'audio_base64' is required when submitting JSON audio."
            )
        try:
            audio_bytes = base64.b64decode(payload.audio_base64)
        except Exception as exc:
            raise ValidationException("Invalid base64 encoding for audio payload.") from exc

    return AdaptiveAcuityService.submit_voice_response(
        db=db,
        user=current_user,
        test_id=test_id,
        attempt_sequence=attempt_seq,
        audio_bytes=audio_bytes,
        response_duration_ms=response_duration_ms,
    )


@router.post(
    "/acuity/tests/{test_id}/complete",
    response_model=AdaptiveAcuityResultResponse,
    status_code=status.HTTP_200_OK,
    summary="Finalize Adaptive Acuity Test",
    description="Manually completes an active adaptive screening test and calculates preliminary visual acuity from passed levels.",
)
async def complete_adaptive_test(
    test_id: uuid.UUID,
    current_user: Annotated[User, Depends(get_current_active_user)],
    db: Annotated[Session, Depends(get_db)],
) -> AdaptiveAcuityResultResponse:
    return AdaptiveAcuityService.complete_test(
        db=db,
        user=current_user,
        test_id=test_id,
    )


@router.post(
    "/acuity/tests/{test_id}/cancel",
    response_model=AdaptiveAcuityResultResponse,
    status_code=status.HTTP_200_OK,
    summary="Cancel Adaptive Acuity Test",
    description="Cancels an ongoing adaptive screening test session.",
)
async def cancel_adaptive_test(
    test_id: uuid.UUID,
    current_user: Annotated[User, Depends(get_current_active_user)],
    db: Annotated[Session, Depends(get_db)],
    payload: AdaptiveAcuityCancelRequest | None = None,
) -> AdaptiveAcuityResultResponse:
    return AdaptiveAcuityService.cancel_test(
        db=db,
        user=current_user,
        test_id=test_id,
        payload=payload,
    )


@router.get(
    "/acuity/tests/{test_id}/result",
    response_model=AdaptiveAcuityResultResponse,
    status_code=status.HTTP_200_OK,
    summary="Get Adaptive Acuity Test Result",
    description="Retrieves the final visual acuity score, protocol determination, and clinical screening disclaimers.",
)
async def get_adaptive_test_result(
    test_id: uuid.UUID,
    current_user: Annotated[User, Depends(get_current_active_user)],
    db: Annotated[Session, Depends(get_db)],
) -> AdaptiveAcuityResultResponse:
    return AdaptiveAcuityService.get_test_result(
        db=db,
        user=current_user,
        test_id=test_id,
    )


@router.post(
    "/sessions/{session_id}/astigmatism",
    response_model=AstigmatismResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Record Astigmatism Dial Assessment",
    description="Records radial clock dial / fan screening findings for meridian clarity variance.",
)
async def record_astigmatism_assessment(
    session_id: uuid.UUID,
    payload: AstigmatismCreateRequest,
    current_user: Annotated[User, Depends(get_current_active_user)],
    db: Annotated[Session, Depends(get_db)],
) -> AstigmatismResponse:
    return ScreeningService.record_astigmatism(
        db=db,
        user=current_user,
        session_id=session_id,
        payload=payload,
    )


@router.get(
    "/sessions/{session_id}/astigmatism",
    response_model=list[AstigmatismResponse],
    status_code=status.HTTP_200_OK,
    summary="Get Astigmatism Assessments",
    description="Retrieves astigmatism screening records for the session.",
)
async def get_astigmatism_assessments(
    session_id: uuid.UUID,
    current_user: Annotated[User, Depends(get_current_active_user)],
    db: Annotated[Session, Depends(get_db)],
) -> list[AstigmatismResponse]:
    return ScreeningService.get_astigmatism_for_session(
        db=db,
        user=current_user,
        session_id=session_id,
    )


@router.post(
    "/sessions/{session_id}/color-vision",
    response_model=ColorVisionResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Record Color Vision Assessment",
    description="Records pseudoisochromatic plate discrimination findings for color vision screening.",
)
async def record_color_vision_assessment(
    session_id: uuid.UUID,
    payload: ColorVisionCreateRequest,
    current_user: Annotated[User, Depends(get_current_active_user)],
    db: Annotated[Session, Depends(get_db)],
) -> ColorVisionResponse:
    return ScreeningService.record_color_vision(
        db=db,
        user=current_user,
        session_id=session_id,
        payload=payload,
    )


@router.get(
    "/sessions/{session_id}/color-vision",
    response_model=list[ColorVisionResponse],
    status_code=status.HTTP_200_OK,
    summary="Get Color Vision Assessments",
    description="Retrieves color vision plate screening records for the session.",
)
async def get_color_vision_assessments(
    session_id: uuid.UUID,
    current_user: Annotated[User, Depends(get_current_active_user)],
    db: Annotated[Session, Depends(get_db)],
) -> list[ColorVisionResponse]:
    return ScreeningService.get_color_vision_for_session(
        db=db,
        user=current_user,
        session_id=session_id,
    )


@router.get(
    "/sessions/{session_id}/summary",
    response_model=ClinicalSessionSummaryResponse,
    status_code=status.HTTP_200_OK,
    summary="Get Comprehensive Session Clinical Summary",
    description="Compiles an aggregated summary of all acuity, astigmatism, and color vision assessments with referral triage.",
)
async def get_session_summary(
    session_id: uuid.UUID,
    current_user: Annotated[User, Depends(get_current_active_user)],
    db: Annotated[Session, Depends(get_db)],
) -> ClinicalSessionSummaryResponse:
    return ScreeningService.get_session_summary(
        db=db,
        user=current_user,
        session_id=session_id,
    )


# -----------------------------------------------------------------------------
# Online Vision Screening Platform: Modular 7-Test Engine & Final Reports
# -----------------------------------------------------------------------------


@router.get(
    "/configuration",
    response_model=ScreeningPlatformConfigResponse,
    status_code=status.HTTP_200_OK,
    summary="Get Online Screening Platform Configuration & Catalog",
    description="Returns the complete catalog of vision screening modules, protocol metadata, and clinical disclaimers.",
)
async def get_screening_configuration(
    lang: Annotated[str, Query(description="Response language code: 'en', 'hi', or 'or'")] = "en",
) -> ScreeningPlatformConfigResponse:
    return OnlineScreeningService.get_platform_configuration(lang=lang)


@router.get(
    "/tests",
    response_model=list[TestModuleDefinition],
    status_code=status.HTTP_200_OK,
    summary="List All Vision Screening Test Modules",
    description="Enumerates available tests (Visual Acuity, Astigmatism, Contrast, Near Reading, Duochrome, Color, Amsler).",
)
async def list_screening_tests(
    lang: Annotated[str, Query(description="Response language code: 'en', 'hi', or 'or'")] = "en",
) -> list[TestModuleDefinition]:
    config = OnlineScreeningService.get_platform_configuration(lang=lang)
    return config.available_modules


@router.get(
    "/tests/{test_type}",
    response_model=TestModuleDefinition,
    status_code=status.HTTP_200_OK,
    summary="Get Specific Test Module Definition & Instructions",
    description="Retrieves protocol metadata, viewing distance, and instructions for a specified test module.",
)
async def get_screening_test_definition(
    test_type: str,
    lang: Annotated[str, Query(description="Response language code: 'en', 'hi', or 'or'")] = "en",
) -> TestModuleDefinition:
    return OnlineScreeningService.get_module_definition(test_type=test_type, lang=lang)


@router.post(
    "/sessions/{session_id}/start",
    response_model=ScreeningSessionResponse,
    status_code=status.HTTP_200_OK,
    summary="Explicitly Start/Confirm Screening Session",
    description="Validates session state, confirms consent, and transitions status to IN_PROGRESS.",
)
async def start_screening_session(
    session_id: uuid.UUID,
    current_user: Annotated[User, Depends(get_current_active_user)],
    db: Annotated[Session, Depends(get_db)],
) -> ScreeningSessionResponse:
    return OnlineScreeningService.start_session(db=db, user=current_user, session_id=session_id)


@router.post(
    "/sessions/{session_id}/calibration",
    response_model=CalibrationResponse,
    status_code=status.HTTP_200_OK,
    summary="Submit Hardware Display Calibration & Viewing Distance",
    description="Records screen dimensions, target distance, and evaluates physical PPI calibration claims.",
)
async def record_session_calibration(
    session_id: uuid.UUID,
    payload: CalibrationSubmitRequest,
    current_user: Annotated[User, Depends(get_current_active_user)],
    db: Annotated[Session, Depends(get_db)],
) -> CalibrationResponse:
    return OnlineScreeningService.record_calibration(
        db=db, user=current_user, session_id=session_id, payload=payload
    )


@router.get(
    "/sessions/{session_id}/calibration",
    response_model=CalibrationResponse,
    status_code=status.HTTP_200_OK,
    summary="Get Session Display Calibration Status",
    description="Retrieves active display calibration parameters and viewing distance for the session.",
)
async def get_session_calibration(
    session_id: uuid.UUID,
    current_user: Annotated[User, Depends(get_current_active_user)],
    db: Annotated[Session, Depends(get_db)],
) -> CalibrationResponse:
    return OnlineScreeningService.get_calibration(db=db, user=current_user, session_id=session_id)


@router.post(
    "/sessions/{session_id}/tests/{test_type}/start",
    response_model=TestChallengeResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Start Interactive Test Module",
    description="Initializes a modular screening test instance (e.g. VISUAL_ACUITY, ASTIGMATISM, CONTRAST_SENSITIVITY, NEAR_VISION_READING, NEAR_VISION_DUOCHROME, COLOR_VISION, CENTRAL_VISION_AMSLER) and returns the first challenge.",
)
async def start_session_test_module(
    session_id: uuid.UUID,
    test_type: str,
    current_user: Annotated[User, Depends(get_current_active_user)],
    db: Annotated[Session, Depends(get_db)],
    payload: TestStartRequest | None = None,
) -> TestChallengeResponse:
    return OnlineScreeningService.start_test_instance(
        db=db,
        user=current_user,
        session_id=session_id,
        test_type=test_type,
        payload=payload,
    )


@router.get(
    "/tests/{test_id}/next",
    response_model=TestChallengeResponse,
    status_code=status.HTTP_200_OK,
    summary="Get Next Test Challenge / Stimulus",
    description="Returns the active stimulus presentation for the test instance without leaking the server expected answer.",
)
async def get_test_next_challenge(
    test_id: uuid.UUID,
    current_user: Annotated[User, Depends(get_current_active_user)],
    db: Annotated[Session, Depends(get_db)],
) -> TestChallengeResponse:
    return OnlineScreeningService.get_current_challenge(db=db, user=current_user, test_id=test_id)


@router.post(
    "/tests/{test_id}/responses",
    response_model=TestStepResponse,
    status_code=status.HTTP_200_OK,
    summary="Submit Test Step Response",
    description="Evaluates user response server-side, records attempt, and advances to next challenge or completes the module.",
)
async def submit_test_step_response(
    test_id: uuid.UUID,
    payload: TestResponseSubmitRequest,
    current_user: Annotated[User, Depends(get_current_active_user)],
    db: Annotated[Session, Depends(get_db)],
) -> TestStepResponse:
    return OnlineScreeningService.submit_test_response(
        db=db, user=current_user, test_id=test_id, payload=payload
    )


@router.post(
    "/tests/{test_id}/complete",
    response_model=TestResultResponse,
    status_code=status.HTTP_200_OK,
    summary="Finalize Test Module Instance",
    description="Concludes active test module execution and calculates preliminary clinical observations.",
)
async def complete_test_module(
    test_id: uuid.UUID,
    current_user: Annotated[User, Depends(get_current_active_user)],
    db: Annotated[Session, Depends(get_db)],
) -> TestResultResponse:
    return OnlineScreeningService.complete_test_instance(db=db, user=current_user, test_id=test_id)


@router.post(
    "/tests/{test_id}/cancel",
    response_model=TestResultResponse,
    status_code=status.HTTP_200_OK,
    summary="Cancel Test Module Instance",
    description="Cancels an active test instance and marks it as incomplete.",
)
async def cancel_test_module(
    test_id: uuid.UUID,
    current_user: Annotated[User, Depends(get_current_active_user)],
    db: Annotated[Session, Depends(get_db)],
    payload: TestCancelRequest | None = None,
) -> TestResultResponse:
    return OnlineScreeningService.cancel_test_instance(
        db=db, user=current_user, test_id=test_id, payload=payload
    )


@router.get(
    "/tests/{test_id}/result",
    response_model=TestResultResponse,
    status_code=status.HTTP_200_OK,
    summary="Get Test Module Result",
    description="Retrieves evaluated result observations, metrics, and classification for a completed test.",
)
async def get_test_module_result(
    test_id: uuid.UUID,
    current_user: Annotated[User, Depends(get_current_active_user)],
    db: Annotated[Session, Depends(get_db)],
) -> TestResultResponse:
    return OnlineScreeningService.get_test_result(db=db, user=current_user, test_id=test_id)


@router.get(
    "/sessions/{session_id}/report",
    response_model=FinalScreeningReportResponse,
    status_code=status.HTTP_200_OK,
    summary="Generate / Get Consolidated Final Screening Report",
    description="Aggregates results from all completed test modules and produces a comprehensive preliminary vision report.",
)
async def get_session_final_report(
    session_id: uuid.UUID,
    current_user: Annotated[User, Depends(get_current_active_user)],
    db: Annotated[Session, Depends(get_db)],
) -> FinalScreeningReportResponse:
    return OnlineScreeningService.get_report_for_session(
        db=db, user=current_user, session_id=session_id
    )


@router.get(
    "/reports/{report_id}",
    response_model=FinalScreeningReportResponse,
    status_code=status.HTTP_200_OK,
    summary="Get Final Screening Report by Report ID",
    description="Retrieves an authoritative final screening report by its unique report UUID.",
)
async def get_final_report_by_id(
    report_id: uuid.UUID,
    current_user: Annotated[User, Depends(get_current_active_user)],
    db: Annotated[Session, Depends(get_db)],
) -> FinalScreeningReportResponse:
    return OnlineScreeningService.get_report_by_id(db=db, user=current_user, report_id=report_id)


@router.get(
    "/history",
    response_model=ScreeningHistoryResponse,
    status_code=status.HTTP_200_OK,
    summary="List User Screening History & Final Reports",
    description="Retrieves paginated screening sessions, completed modules, and final reports belonging exclusively to the user.",
)
async def get_screening_history(
    current_user: Annotated[User, Depends(get_current_active_user)],
    db: Annotated[Session, Depends(get_db)],
    limit: Annotated[int, Query(ge=1, le=100)] = 20,
    offset: Annotated[int, Query(ge=0)] = 0,
) -> ScreeningHistoryResponse:
    return OnlineScreeningService.list_user_history(
        db=db, user=current_user, limit=limit, offset=offset
    )

import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session

from app.api.dependencies import get_current_active_user, get_db
from app.models.user import User
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
)
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

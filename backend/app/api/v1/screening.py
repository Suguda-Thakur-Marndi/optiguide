import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session

from app.api.dependencies import get_current_active_user, get_db
from app.models.user import User
from app.schemas.auth import MessageResponse
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
# Consent Management Endpoints
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
    _payload: ScreeningSessionCreateRequest,
    current_user: Annotated[User, Depends(get_current_active_user)],
    db: Annotated[Session, Depends(get_db)],
) -> ScreeningSessionResponse:
    return ScreeningService.create_session(db=db, user=current_user)


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

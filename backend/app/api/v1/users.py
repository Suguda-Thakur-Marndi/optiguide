import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from app.api.dependencies import (
    get_current_active_user,
    get_db,
    require_admin,
    require_verified_professional,
)
from app.core.exceptions import EntityNotFoundException
from app.models.user import User
from app.repositories.user_repo import UserRepository
from app.schemas.auth import (
    MessageResponse,
    SessionResponse,
    UserProfileResponse,
    UserStatusUpdateRequest,
    UserUpdateRequest,
)
from app.services.user_service import UserService

router = APIRouter()


@router.get(
    "/me",
    response_model=UserProfileResponse,
    status_code=status.HTTP_200_OK,
    summary="Get Current User Profile",
    description="Retrieves the profile of the current authenticated user.",
)
async def get_current_user_profile(
    current_user: Annotated[User, Depends(get_current_active_user)],
) -> UserProfileResponse:
    return UserProfileResponse.model_validate(current_user)


@router.patch(
    "/me",
    response_model=UserProfileResponse,
    status_code=status.HTTP_200_OK,
    summary="Update Current User Profile",
    description="Updates editable profile fields (full name, phone number, language).",
)
async def update_current_user_profile(
    payload: UserUpdateRequest,
    current_user: Annotated[User, Depends(get_current_active_user)],
    db: Annotated[Session, Depends(get_db)],
) -> UserProfileResponse:
    updated_user = UserService.update_profile(db=db, user=current_user, payload=payload)
    return UserProfileResponse.model_validate(updated_user)


@router.get(
    "/me/sessions",
    response_model=list[SessionResponse],
    status_code=status.HTTP_200_OK,
    summary="List User Sessions",
    description="Retrieves active and historical refresh token sessions for the current user.",
)
async def list_current_user_sessions(
    current_user: Annotated[User, Depends(get_current_active_user)],
    db: Annotated[Session, Depends(get_db)],
) -> list[SessionResponse]:
    sessions = UserService.list_sessions(db=db, user_id=current_user.id)
    return [SessionResponse.model_validate(s) for s in sessions]


@router.patch(
    "/{user_id}/status",
    response_model=UserProfileResponse,
    status_code=status.HTTP_200_OK,
    summary="Admin: Update User Account Status",
    description="Enables system administrators to activate, deactivate, or assign roles to user accounts.",
)
async def admin_update_user_status(
    user_id: uuid.UUID,
    payload: UserStatusUpdateRequest,
    _admin: Annotated[User, Depends(require_admin)],
    db: Annotated[Session, Depends(get_db)],
) -> UserProfileResponse:
    target_user = UserRepository.get_by_id(db, user_id)
    if target_user is None:
        raise EntityNotFoundException("User", user_id)

    updated = UserService.update_user_status(db=db, target_user=target_user, payload=payload)
    return UserProfileResponse.model_validate(updated)


@router.get(
    "/clinical/review-access",
    response_model=MessageResponse,
    status_code=status.HTTP_200_OK,
    summary="Verify Clinical Review Authorization",
    description="Enforces that the user is an authorized, verified Eye Care Professional or Administrator.",
)
async def verify_clinical_review_access(
    current_clinician: Annotated[User, Depends(require_verified_professional)],
) -> MessageResponse:
    return MessageResponse(
        message=f"Access granted for verified clinician: {current_clinician.full_name} ({current_clinician.role})"
    )

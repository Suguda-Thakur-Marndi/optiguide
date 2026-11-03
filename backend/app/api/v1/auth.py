from typing import Annotated

from fastapi import APIRouter, Depends, Request, status
from sqlalchemy.orm import Session

from app.api.dependencies import (
    get_client_ip,
    get_current_active_user,
    get_db,
    rate_limit,
)
from app.core.config import settings
from app.models.user import User
from app.schemas.auth import (
    AuthResponse,
    MessageResponse,
    TokenRefreshRequest,
    TokenRefreshResponse,
    UserLoginRequest,
    UserProfileResponse,
    UserRegisterRequest,
)
from app.services.auth_service import AuthService

router = APIRouter()


@router.post(
    "/register",
    response_model=AuthResponse,
    status_code=status.HTTP_201_CREATED,
    summary="User Registration",
    description="Registers a new user account and returns access/refresh token pair.",
    dependencies=[Depends(rate_limit(max_requests=settings.REGISTER_RATE_LIMIT_PER_MINUTE))],
)
async def register(
    payload: UserRegisterRequest,
    request: Request,
    db: Annotated[Session, Depends(get_db)],
) -> AuthResponse:
    client_ip = get_client_ip(request)
    user_agent = request.headers.get("User-Agent")
    return AuthService.register(
        db=db,
        payload=payload,
        client_ip=client_ip,
        user_agent=user_agent,
    )


@router.post(
    "/login",
    response_model=AuthResponse,
    status_code=status.HTTP_200_OK,
    summary="User Authentication",
    description="Authenticates credentials and returns access/refresh token pair with session metadata.",
    dependencies=[Depends(rate_limit(max_requests=settings.LOGIN_RATE_LIMIT_PER_MINUTE))],
)
async def login(
    payload: UserLoginRequest,
    request: Request,
    db: Annotated[Session, Depends(get_db)],
) -> AuthResponse:
    client_ip = get_client_ip(request)
    user_agent = request.headers.get("User-Agent")
    return AuthService.login(
        db=db,
        payload=payload,
        client_ip=client_ip,
        user_agent=user_agent,
    )


@router.post(
    "/refresh",
    response_model=TokenRefreshResponse,
    status_code=status.HTTP_200_OK,
    summary="Rotate Refresh Token",
    description="Rotates the refresh token and returns a new access/refresh token pair.",
)
async def refresh_tokens(
    payload: TokenRefreshRequest,
    request: Request,
    db: Annotated[Session, Depends(get_db)],
) -> TokenRefreshResponse:
    client_ip = get_client_ip(request)
    user_agent = request.headers.get("User-Agent")
    return AuthService.refresh(
        db=db,
        raw_refresh_token=payload.refresh_token,
        client_ip=client_ip,
        user_agent=user_agent,
    )


@router.post(
    "/logout",
    response_model=MessageResponse,
    status_code=status.HTTP_200_OK,
    summary="User Logout",
    description="Revokes the active refresh token session.",
)
async def logout(
    payload: TokenRefreshRequest,
    db: Annotated[Session, Depends(get_db)],
) -> MessageResponse:
    AuthService.logout(db=db, raw_refresh_token=payload.refresh_token)
    return MessageResponse(message="Logged out successfully.")


@router.post(
    "/logout-all",
    response_model=MessageResponse,
    status_code=status.HTTP_200_OK,
    summary="Revoke All Sessions",
    description="Revokes all active sessions and refresh tokens for the current user.",
)
async def logout_all(
    current_user: Annotated[User, Depends(get_current_active_user)],
    db: Annotated[Session, Depends(get_db)],
) -> MessageResponse:
    count = AuthService.logout_all(db=db, user=current_user)
    return MessageResponse(message=f"Successfully revoked {count} active sessions.")


@router.get(
    "/me",
    response_model=UserProfileResponse,
    status_code=status.HTTP_200_OK,
    summary="Get Authenticated User",
    description="Returns profile information for the currently authenticated user.",
)
async def get_me(
    current_user: Annotated[User, Depends(get_current_active_user)],
) -> UserProfileResponse:
    return UserProfileResponse.model_validate(current_user)

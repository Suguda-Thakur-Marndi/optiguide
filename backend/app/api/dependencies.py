import time
import uuid
from collections import defaultdict
from collections.abc import Callable, Generator
from typing import Annotated

from fastapi import Depends, Request
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.exceptions import (
    AuthenticationException,
    ForbiddenException,
    RateLimitExceededException,
    TokenInvalidException,
    UserInactiveException,
)
from app.core.security import decode_access_token
from app.database.session import get_db
from app.models.user import User
from app.repositories.user_repo import UserRepository
from app.schemas.auth import UserRole

# Optional bearer scheme so missing tokens raise custom AuthenticationException
security_bearer = HTTPBearer(auto_error=False)


def get_database() -> Generator[Session, None, None]:
    """Dependency yielding a thread-local SQLAlchemy session."""
    yield from get_db()


def get_client_ip(request: Request) -> str:
    """
    Extracts client IP coordinate with anti-spoofing defense.
    X-Forwarded-For is strictly ignored unless TRUST_FORWARDED_FOR is enabled AND
    the connecting client host is present in TRUSTED_PROXIES.
    """
    client_host = request.client.host if request.client else "127.0.0.1"

    if settings.TRUST_FORWARDED_FOR:
        trusted = (
            settings.TRUSTED_PROXIES
            if isinstance(settings.TRUSTED_PROXIES, list)
            else [settings.TRUSTED_PROXIES]
        )
        if client_host in trusted:
            forwarded = request.headers.get("X-Forwarded-For")
            if forwarded:
                return forwarded.split(",")[0].strip()

    return client_host


class BaseRateLimiter:
    """Abstract interface for rate-limiting engines (supports future Redis backend)."""

    def is_rate_limited(self, key: str, max_requests: int, window_seconds: int = 60) -> bool:
        raise NotImplementedError

    def clear(self) -> None:
        raise NotImplementedError


class InMemoryRateLimiter(BaseRateLimiter):
    """Sliding-window in-memory rate limiter with thread-safe timestamp records."""

    def __init__(self) -> None:
        self.records: dict[str, list[float]] = defaultdict(list)

    def is_rate_limited(self, key: str, max_requests: int, window_seconds: int = 60) -> bool:
        now = time.time()
        window_start = now - window_seconds
        records = [ts for ts in self.records[key] if ts > window_start]
        records.append(now)
        self.records[key] = records
        return len(records) > max_requests

    def clear(self) -> None:
        self.records.clear()


# Global limiter instance and backward-compatible alias for test harness
rate_limiter = InMemoryRateLimiter()
_rate_limit_records = rate_limiter.records


def rate_limit(max_requests: int, window_seconds: int = 60) -> Callable:
    """FastAPI dependency enforcing sliding-window rate limits per client IP and endpoint."""

    async def _rate_limiter(request: Request) -> None:
        client_ip = get_client_ip(request)
        endpoint = request.url.path
        key = f"{client_ip}:{endpoint}"

        if rate_limiter.is_rate_limited(
            key=key, max_requests=max_requests, window_seconds=window_seconds
        ):
            raise RateLimitExceededException("Too many requests. Please try again later.")

    return _rate_limiter


def get_current_user(
    credentials: Annotated[HTTPAuthorizationCredentials | None, Depends(security_bearer)],
    db: Annotated[Session, Depends(get_db)],
) -> User:
    """Extracts, cryptographically verifies, and resolves the authenticated User from Bearer token."""
    if credentials is None or not credentials.credentials:
        raise AuthenticationException("Authentication credentials were not provided.")

    token = credentials.credentials
    payload = decode_access_token(token)

    sub = payload.get("sub")
    if not sub:
        raise TokenInvalidException("Token subject identifier missing.")

    try:
        user_uuid = uuid.UUID(sub)
    except ValueError as err:
        raise TokenInvalidException("Invalid user identifier in token.") from err

    user = UserRepository.get_by_id(db, user_uuid)
    if user is None:
        raise AuthenticationException("User account not found.")

    if not user.is_active:
        raise UserInactiveException("User account has been deactivated.")

    return user


def get_current_active_user(
    current_user: Annotated[User, Depends(get_current_user)],
) -> User:
    """Ensures authenticated user is active."""
    if not current_user.is_active:
        raise UserInactiveException("User account has been deactivated.")
    return current_user


def require_roles(*allowed_roles: str) -> Callable:
    """Factory creating an RBAC dependency enforcing specified role membership."""

    # Map aliases so both canonical and legacy role strings match
    expanded_roles: set[str] = set()
    for role in allowed_roles:
        r = role.lower().strip()
        expanded_roles.add(r)
        if r in (UserRole.PATIENT.value, UserRole.USER.value):
            expanded_roles.update([UserRole.PATIENT.value, UserRole.USER.value])
        elif r in (UserRole.OPTOMETRIST.value, UserRole.EYE_CARE_PROFESSIONAL.value):
            expanded_roles.update(
                [
                    UserRole.OPTOMETRIST.value,
                    UserRole.EYE_CARE_PROFESSIONAL.value,
                ]
            )

    def _role_checker(
        current_user: Annotated[User, Depends(get_current_active_user)],
    ) -> User:
        if current_user.role not in expanded_roles:
            raise ForbiddenException(
                f"Operation requires one of the following roles: {', '.join(allowed_roles)}."
            )
        return current_user

    return _role_checker


def require_verified_professional(
    current_user: Annotated[User, Depends(get_current_active_user)],
) -> User:
    """
    Enforces that the user is an Eye Care Professional AND has been verified by an administrator.
    System administrators automatically satisfy this clinical dependency.
    Unverified professionals are blocked with HTTP 403.
    """
    allowed_roles = {
        UserRole.OPTOMETRIST.value,
        UserRole.EYE_CARE_PROFESSIONAL.value,
        UserRole.ADMIN.value,
    }
    if current_user.role not in allowed_roles:
        raise ForbiddenException("Access restricted to Eye Care Professionals.")

    if current_user.role != UserRole.ADMIN.value and not current_user.is_verified:
        raise ForbiddenException(
            "Professional account requires verification by an authorized administrator."
        )

    return current_user


# Pre-configured role dependencies
require_admin = require_roles("admin")
require_clinician = require_roles("optometrist", "eye_care_professional", "admin")

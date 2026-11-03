from datetime import UTC, datetime, timedelta

from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.exceptions import (
    AuthenticationException,
    TokenExpiredException,
    TokenInvalidException,
    TokenRevokedException,
    UserAlreadyExistsException,
    UserInactiveException,
    ValidationException,
)
from app.core.logging import logger
from app.core.security import (
    DUMMY_ARGON2_HASH,
    create_access_token,
    generate_refresh_token,
    hash_password,
    hash_token,
    needs_rehash,
    validate_password_strength,
    verify_password,
)
from app.models.session import UserSession
from app.models.user import User
from app.repositories.session_repo import SessionRepository
from app.repositories.user_repo import UserRepository
from app.schemas.auth import (
    AuthResponse,
    TokenRefreshResponse,
    UserLoginRequest,
    UserProfileResponse,
    UserRegisterRequest,
    UserRole,
)


class AuthService:
    """Domain service orchestrating user registration, authentication, and token management."""

    @staticmethod
    def register(
        db: Session,
        payload: UserRegisterRequest,
        client_ip: str | None = None,
        user_agent: str | None = None,
    ) -> AuthResponse:
        normalized_email = payload.email.lower().strip()
        existing_user = UserRepository.get_by_email(db, normalized_email)
        if existing_user is not None:
            raise UserAlreadyExistsException("A user with this email address already exists.")

        # Enforce password strength and max-length DoS boundary
        is_strong, err_msg = validate_password_strength(payload.password)
        if not is_strong:
            raise ValidationException(err_msg or "Password does not meet security criteria.")

        # Public self-registration ALWAYS assigns standard user/patient role
        # Any privileged role in payload is already rejected by UserRegisterRequest validator
        assigned_role = UserRole.PATIENT.value

        hashed_pwd = hash_password(payload.password)
        new_user = User(
            email=normalized_email,
            hashed_password=hashed_pwd,
            full_name=payload.full_name.strip(),
            role=assigned_role,
            phone_number=payload.phone_number,
            preferred_language=payload.preferred_language,
            is_active=True,
            is_verified=False,
            last_login_at=datetime.now(UTC),
        )
        user = UserRepository.create(db, new_user)

        # Generate Access Token
        access_token, expires_in = create_access_token(
            user_id=user.id,
            email=user.email,
            role=user.role,
        )

        # Generate & Persist Refresh Token Session
        raw_refresh = generate_refresh_token()
        refresh_expires = datetime.now(UTC) + timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS)
        session = UserSession(
            user_id=user.id,
            session_token_hash=hash_token(raw_refresh),
            user_agent=user_agent,
            ip_address=client_ip,
            expires_at=refresh_expires,
        )
        SessionRepository.create(db, session)

        logger.info(f"User registered successfully: id={user.id} role={user.role}")
        return AuthResponse(
            access_token=access_token,
            refresh_token=raw_refresh,
            token_type="Bearer",
            expires_in=expires_in,
            user=UserProfileResponse.model_validate(user),
        )

    @staticmethod
    def login(
        db: Session,
        payload: UserLoginRequest,
        client_ip: str | None = None,
        user_agent: str | None = None,
    ) -> AuthResponse:
        normalized_email = payload.email.lower().strip()
        user = UserRepository.get_by_email(db, normalized_email)

        if user is None:
            # Equalize timing via dummy Argon2id hash verification to prevent username enumeration
            verify_password(payload.password, DUMMY_ARGON2_HASH)
            raise AuthenticationException("Invalid email or password.")

        # Always verify password FIRST so invalid passwords never reveal account status
        if not verify_password(payload.password, user.hashed_password):
            raise AuthenticationException("Invalid email or password.")

        # Only check active status after credentials have been verified
        if not user.is_active:
            raise UserInactiveException("User account has been deactivated.")

        # Update last login timestamp & rehash password if hash parameters upgraded
        user.last_login_at = datetime.now(UTC)
        if needs_rehash(user.hashed_password):
            user.hashed_password = hash_password(payload.password)
        UserRepository.update(db, user)

        # Generate Access Token
        access_token, expires_in = create_access_token(
            user_id=user.id,
            email=user.email,
            role=user.role,
        )

        # Generate & Persist Refresh Token Session
        raw_refresh = generate_refresh_token()
        refresh_expires = datetime.now(UTC) + timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS)
        session = UserSession(
            user_id=user.id,
            session_token_hash=hash_token(raw_refresh),
            user_agent=user_agent,
            ip_address=client_ip,
            expires_at=refresh_expires,
        )
        SessionRepository.create(db, session)

        logger.info(f"User authenticated successfully: id={user.id}")
        return AuthResponse(
            access_token=access_token,
            refresh_token=raw_refresh,
            token_type="Bearer",
            expires_in=expires_in,
            user=UserProfileResponse.model_validate(user),
        )

    @staticmethod
    def refresh(
        db: Session,
        raw_refresh_token: str,
        client_ip: str | None = None,
        user_agent: str | None = None,
    ) -> TokenRefreshResponse:
        token_hash = hash_token(raw_refresh_token)
        session = SessionRepository.get_by_token_hash(db, token_hash, for_update=True)
        if session is None:
            raise TokenInvalidException("Refresh token is invalid or does not exist.")

        now = datetime.now(UTC)

        # REUSE DETECTION: If token was already revoked, terminate all active sessions
        if session.is_revoked:
            logger.warning(
                f"SECURITY ALERT: Refresh token reuse detected for user_id={session.user_id}! "
                f"Terminating all active sessions."
            )
            SessionRepository.revoke_all_for_user(db, session.user_id)
            raise TokenRevokedException(
                "Refresh token has already been rotated or revoked. All active sessions terminated."
            )

        # Ensure session.expires_at is timezone-aware
        expires_at = session.expires_at
        if expires_at.tzinfo is None:
            expires_at = expires_at.replace(tzinfo=UTC)

        if expires_at < now:
            SessionRepository.revoke_session(db, session)
            raise TokenExpiredException("Refresh token has expired. Please log in again.")

        user = UserRepository.get_by_id(db, session.user_id)
        if user is None or not user.is_active:
            SessionRepository.revoke_session(db, session)
            raise UserInactiveException("Associated user account is inactive or not found.")

        # Prepare replacement session
        new_raw_refresh = generate_refresh_token()
        new_expires = now + timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS)
        new_session = UserSession(
            user_id=user.id,
            session_token_hash=hash_token(new_raw_refresh),
            user_agent=user_agent or session.user_agent,
            ip_address=client_ip or session.ip_address,
            expires_at=new_expires,
        )

        # ATOMIC ROTATION & REPLACEMENT IN A SINGLE DATABASE TRANSACTION
        rotated_successfully = SessionRepository.rotate_and_create(
            db=db,
            old_session_id=session.id,
            new_session=new_session,
        )
        if not rotated_successfully:
            # A concurrent transaction rotated the token in the same window
            raise TokenRevokedException(
                "Refresh token has already been rotated by a concurrent request."
            )

        new_access_token, expires_in = create_access_token(
            user_id=user.id,
            email=user.email,
            role=user.role,
        )
        return TokenRefreshResponse(
            access_token=new_access_token,
            refresh_token=new_raw_refresh,
            token_type="Bearer",
            expires_in=expires_in,
        )

    @staticmethod
    def logout(db: Session, raw_refresh_token: str) -> None:
        token_hash = hash_token(raw_refresh_token)
        session = SessionRepository.get_by_token_hash(db, token_hash)
        if session is not None and not session.is_revoked:
            SessionRepository.revoke_session(db, session)
            logger.info(f"Session revoked for user_id={session.user_id}")

    @staticmethod
    def logout_all(db: Session, user: User) -> int:
        count = SessionRepository.revoke_all_for_user(db, user.id)
        logger.info(f"All active sessions ({count}) revoked for user_id={user.id}")
        return count

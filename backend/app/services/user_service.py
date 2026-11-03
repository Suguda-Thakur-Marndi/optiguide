import uuid

from sqlalchemy.orm import Session

from app.models.session import UserSession
from app.models.user import User
from app.repositories.session_repo import SessionRepository
from app.repositories.user_repo import UserRepository
from app.schemas.auth import UserRole, UserStatusUpdateRequest, UserUpdateRequest


class UserService:
    """Domain service managing user profiles and session inspections."""

    @staticmethod
    def update_profile(db: Session, user: User, payload: UserUpdateRequest) -> User:
        if payload.full_name is not None:
            user.full_name = payload.full_name.strip()
        if payload.phone_number is not None:
            user.phone_number = payload.phone_number.strip() if payload.phone_number else None
        if payload.preferred_language is not None:
            user.preferred_language = payload.preferred_language.strip()

        return UserRepository.update(db, user)

    @staticmethod
    def list_sessions(db: Session, user_id: uuid.UUID) -> list[UserSession]:
        return SessionRepository.get_sessions_for_user(db, user_id)

    @staticmethod
    def update_user_status(
        db: Session,
        target_user: User,
        payload: UserStatusUpdateRequest,
    ) -> User:
        if payload.is_active is not None:
            target_user.is_active = payload.is_active
            if not payload.is_active:
                # If deactivating user, terminate all active sessions immediately
                SessionRepository.revoke_all_for_user(db, target_user.id)

        if payload.is_verified is not None:
            target_user.is_verified = payload.is_verified

        if payload.role is not None:
            raw_role = payload.role.value if hasattr(payload.role, "value") else str(payload.role)
            target_user.role = UserRole.normalize_role(raw_role)

        return UserRepository.update(db, target_user)

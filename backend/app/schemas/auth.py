import uuid
from datetime import datetime
from enum import Enum

from pydantic import AliasChoices, BaseModel, ConfigDict, EmailStr, Field, field_validator


class UserRole(str, Enum):
    """
    User roles in the OptiGuide platform.
    Canonical application roles: USER, SHOPKEEPER, EYE_CARE_PROFESSIONAL, ADMIN.
    Aliases: PATIENT (maps to USER), OPTOMETRIST (maps to EYE_CARE_PROFESSIONAL).
    """

    USER = "user"
    PATIENT = "patient"  # Documented equivalent / alias for USER
    OPTOMETRIST = "optometrist"  # Clinical alias for EYE_CARE_PROFESSIONAL
    EYE_CARE_PROFESSIONAL = "eye_care_professional"  # Canonical clinical role
    SHOPKEEPER = "shopkeeper"
    ADMIN = "admin"

    @classmethod
    def is_privileged(cls, role: str) -> bool:
        """Determines if a role requires elevated administrative or professional authorization."""
        r = role.lower().strip()
        return r in {
            cls.ADMIN.value,
            cls.SHOPKEEPER.value,
            cls.OPTOMETRIST.value,
            cls.EYE_CARE_PROFESSIONAL.value,
        }

    @classmethod
    def normalize_role(cls, role: str) -> str:
        """Normalizes role aliases to canonical equivalents while preserving DB compatibility."""
        r = role.lower().strip()
        if r == cls.USER.value:
            return cls.PATIENT.value  # Preserve Phase 1 / 2 DB compatibility
        if r == cls.EYE_CARE_PROFESSIONAL.value:
            return cls.OPTOMETRIST.value
        return r


class UserRegisterRequest(BaseModel):
    """
    Payload for user registration.
    Public registration strictly forbids privileged role self-assignment.
    """

    email: EmailStr = Field(..., json_schema_extra={"example": "patient@example.com"})
    password: str = Field(
        ..., min_length=8, max_length=128, json_schema_extra={"example": "SecurePass123!"}
    )
    full_name: str = Field(
        ...,
        min_length=2,
        max_length=255,
        validation_alias=AliasChoices("full_name", "fullName"),
        json_schema_extra={"example": "Jane Doe"},
    )
    role: str | None = Field(
        default=None,
        validation_alias=AliasChoices("role"),
        json_schema_extra={"example": "patient"},
    )
    phone_number: str | None = Field(
        default=None,
        max_length=50,
        validation_alias=AliasChoices("phone_number", "phoneNumber"),
        json_schema_extra={"example": "+15551234567"},
    )
    preferred_language: str = Field(
        default="en",
        max_length=10,
        validation_alias=AliasChoices("preferred_language", "preferredLanguage"),
        json_schema_extra={"example": "en"},
    )

    @field_validator("email")
    @classmethod
    def normalize_email(cls, v: str) -> str:
        return v.lower().strip()

    @field_validator("role")
    @classmethod
    def validate_role_safety(cls, v: str | None) -> str | None:
        if v is not None:
            r = v.lower().strip()
            if UserRole.is_privileged(r):
                raise ValueError(
                    "Self-registration with privileged roles is prohibited. "
                    "Public registration is restricted to standard user accounts."
                )
        return v

    model_config = ConfigDict(
        populate_by_name=True,
        extra="forbid",
    )


class UserLoginRequest(BaseModel):
    """Payload for user authentication."""

    email: EmailStr = Field(..., json_schema_extra={"example": "patient@example.com"})
    password: str = Field(
        ..., min_length=1, max_length=128, json_schema_extra={"example": "SecurePass123!"}
    )

    @field_validator("email")
    @classmethod
    def normalize_email(cls, v: str) -> str:
        return v.lower().strip()

    model_config = ConfigDict(
        populate_by_name=True,
        extra="forbid",
    )


class TokenRefreshRequest(BaseModel):
    """Payload for refresh token exchange or logout."""

    refresh_token: str = Field(
        ...,
        validation_alias=AliasChoices("refresh_token", "refreshToken"),
        json_schema_extra={"example": "raw_refresh_token_string"},
    )

    model_config = ConfigDict(
        populate_by_name=True,
        extra="forbid",
    )


class UserProfileResponse(BaseModel):
    """Public representation of an OptiGuide user profile."""

    id: uuid.UUID
    email: str
    full_name: str
    role: str
    phone_number: str | None = None
    preferred_language: str = "en"
    is_active: bool
    is_verified: bool
    created_at: datetime
    updated_at: datetime
    last_login_at: datetime | None = None

    model_config = ConfigDict(from_attributes=True, populate_by_name=True)


class AuthResponse(BaseModel):
    """OAuth2 / JWT response returned upon successful authentication or registration."""

    access_token: str
    refresh_token: str
    token_type: str = "Bearer"
    expires_in: int
    user: UserProfileResponse


class TokenRefreshResponse(BaseModel):
    """Response returned upon successful token rotation."""

    access_token: str
    refresh_token: str
    token_type: str = "Bearer"
    expires_in: int


class UserUpdateRequest(BaseModel):
    """
    Payload for updating user profile fields.
    Strict allowlist: only non-privileged profile attributes are permitted.
    All privileged fields (role, is_admin, is_verified, etc.) are strictly forbidden.
    """

    full_name: str | None = Field(
        default=None,
        min_length=2,
        max_length=255,
        validation_alias=AliasChoices("full_name", "fullName"),
    )
    phone_number: str | None = Field(
        default=None,
        max_length=50,
        validation_alias=AliasChoices("phone_number", "phoneNumber"),
    )
    preferred_language: str | None = Field(
        default=None,
        max_length=10,
        validation_alias=AliasChoices("preferred_language", "preferredLanguage"),
    )

    model_config = ConfigDict(
        populate_by_name=True,
        extra="forbid",
    )


class UserStatusUpdateRequest(BaseModel):
    """Admin-only payload for updating account status or role."""

    is_active: bool | None = None
    is_verified: bool | None = None
    role: UserRole | str | None = None

    model_config = ConfigDict(
        populate_by_name=True,
        extra="forbid",
    )


class SessionResponse(BaseModel):
    """Diagnostic response representing an active or revoked refresh token session."""

    id: uuid.UUID
    user_agent: str | None = None
    ip_address: str | None = None
    is_revoked: bool
    expires_at: datetime
    created_at: datetime
    revoked_at: datetime | None = None

    model_config = ConfigDict(from_attributes=True)


class MessageResponse(BaseModel):
    """Generic status and message response."""

    message: str
    success: bool = True

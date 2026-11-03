import hashlib
import re
import secrets
import uuid
from datetime import UTC, datetime, timedelta

import argon2
import jwt
from argon2.exceptions import InvalidHashError, VerificationError

from app.core.config import settings
from app.core.exceptions import TokenExpiredException, TokenInvalidException

# Initialize Argon2id password hasher with OWASP-recommended parameters
password_hasher = argon2.PasswordHasher(
    time_cost=3,
    memory_cost=65536,
    parallelism=4,
    hash_len=32,
    salt_len=16,
    type=argon2.Type.ID,
)

# Constant-time dummy hash for nonexistent accounts to mitigate timing attacks on login
DUMMY_ARGON2_HASH = "$argon2id$v=19$m=65536,t=3,p=4$c29tZXNhbHQxMjM0NTY3OA$9vXy54Hh7vKkOQ43b4y9o1uE4uW7w7b9/1234567890"


def hash_password(password: str) -> str:
    """Hashes a plaintext password using Argon2id."""
    return password_hasher.hash(password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verifies a plaintext password against an Argon2id hash."""
    try:
        return password_hasher.verify(hashed_password, plain_password)
    except (VerificationError, InvalidHashError):
        return False
    except Exception:  # noqa: BLE001
        return False


def needs_rehash(hashed_password: str) -> bool:
    """Checks if the stored hash parameters should be updated."""
    try:
        return password_hasher.check_needs_rehash(hashed_password)
    except Exception:  # noqa: BLE001
        return False


def validate_password_strength(password: str) -> tuple[bool, str | None]:
    """
    Validates password strength according to OptiGuide security baseline:
    - Minimum length (default 8 characters)
    - Maximum length (128 characters) to prevent CPU starvation DoS
    - Contains at least one letter and at least one digit
    """
    if not password or len(password) < settings.PASSWORD_MIN_LENGTH:
        return (
            False,
            f"Password must be at least {settings.PASSWORD_MIN_LENGTH} characters long.",
        )
    if len(password) > settings.PASSWORD_MAX_LENGTH:
        return (
            False,
            f"Password must not exceed {settings.PASSWORD_MAX_LENGTH} characters.",
        )
    if not re.search(r"[A-Za-z]", password):
        return False, "Password must contain at least one letter."
    if not re.search(r"\d", password):
        return False, "Password must contain at least one digit."
    return True, None


def generate_refresh_token() -> str:
    """Generates a high-entropy URL-safe base64 string for refresh sessions."""
    return secrets.token_urlsafe(32)


def hash_token(raw_token: str) -> str:
    """Computes SHA-256 hex digest of a token secret for secure database storage."""
    return hashlib.sha256(raw_token.encode("utf-8")).hexdigest()


def create_access_token(
    user_id: uuid.UUID | str,
    email: str,
    role: str,
    expires_delta: timedelta | None = None,
) -> tuple[str, int]:
    """
    Generates an encoded JWT access token with standard RFC 7519 claims.
    Returns:
        (encoded_jwt_str, expires_in_seconds)
    """
    now = datetime.now(UTC)
    if expires_delta:
        expire_at = now + expires_delta
        expires_in = int(expires_delta.total_seconds())
    else:
        expires_delta_default = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
        expire_at = now + expires_delta_default
        expires_in = int(expires_delta_default.total_seconds())

    claims = {
        "sub": str(user_id),
        "email": email.lower().strip(),
        "role": role,
        "type": "access",
        "jti": str(uuid.uuid4()),
        "iss": settings.JWT_ISSUER,
        "aud": settings.JWT_AUDIENCE,
        "iat": int(now.timestamp()),
        "exp": int(expire_at.timestamp()),
    }

    token = jwt.encode(
        claims,
        settings.JWT_SECRET_KEY,
        algorithm=settings.JWT_ALGORITHM,
    )
    return token, expires_in


def decode_access_token(token: str) -> dict:
    """
    Validates and decodes a JWT access token.
    Enforces signature, expiration, type, issuer, audience, and subject format.
    """
    try:
        payload = jwt.decode(
            token,
            settings.JWT_SECRET_KEY,
            algorithms=[settings.JWT_ALGORITHM],
            issuer=settings.JWT_ISSUER,
            audience=settings.JWT_AUDIENCE,
            options={
                "require": ["sub", "exp", "type", "role", "iss", "aud", "iat"],
                "verify_signature": True,
                "verify_exp": True,
                "verify_iss": True,
                "verify_aud": True,
            },
        )
        if payload.get("type") != "access":
            raise TokenInvalidException("Token is not a valid access token.")

        # Strict UUID validation on subject identifier
        sub = payload.get("sub")
        try:
            uuid.UUID(str(sub))
        except (ValueError, TypeError, AttributeError) as err:
            raise TokenInvalidException("Token subject must be a valid UUID.") from err

        return payload
    except jwt.ExpiredSignatureError as err:
        raise TokenExpiredException("Access token has expired.") from err
    except jwt.PyJWTError as err:
        raise TokenInvalidException("Access token signature or format is invalid.") from err

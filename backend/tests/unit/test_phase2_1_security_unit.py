import uuid
from datetime import UTC, datetime, timedelta

import jwt
import pytest
from pydantic import ValidationError

from app.api.dependencies import InMemoryRateLimiter, get_client_ip
from app.core.config import Settings, settings
from app.core.exceptions import TokenInvalidException
from app.core.security import (
    DUMMY_ARGON2_HASH,
    decode_access_token,
    validate_password_strength,
    verify_password,
)
from app.schemas.auth import UserRegisterRequest, UserRole, UserUpdateRequest


class DummyClient:
    def __init__(self, host: str):
        self.host = host


class DummyRequest:
    def __init__(self, headers: dict[str, str], client_host: str = "192.168.1.100"):
        self.headers = headers
        self.client = DummyClient(client_host)


# -------------------------------------------------------------------------
# 1. Password Security & DoS Boundary Tests
# -------------------------------------------------------------------------


def test_password_boundary_validation():
    # Empty
    valid, msg = validate_password_strength("")
    assert not valid
    assert "at least 8" in msg

    # Too short (< 8)
    valid, msg = validate_password_strength("Short1!")
    assert not valid
    assert "at least 8" in msg

    # Overly long (> 128 chars) DoS boundary
    long_pass = "A" * 128 + "1"
    valid, msg = validate_password_strength(long_pass)
    assert not valid
    assert "must not exceed 128" in msg

    # Missing letter
    valid, msg = validate_password_strength("1234567890!")
    assert not valid
    assert "at least one letter" in msg

    # Missing digit
    valid, msg = validate_password_strength("abcdefghijkl!")
    assert not valid
    assert "at least one digit" in msg

    # Exactly 8 characters with letter and digit
    valid, msg = validate_password_strength("Pass1234")
    assert valid
    assert msg is None

    # Exactly 128 characters
    exact_128 = "A" * 126 + "1b"
    valid, msg = validate_password_strength(exact_128)
    assert valid
    assert msg is None


def test_dummy_hash_verification():
    # Verify dummy hash handles constant-time verification without crashing
    assert not verify_password("AnyPassword123!", DUMMY_ARGON2_HASH)
    assert not verify_password("", DUMMY_ARGON2_HASH)


# -------------------------------------------------------------------------
# 2. JWT Cryptographic Claims & Algorithm Rejection Tests
# -------------------------------------------------------------------------


def test_jwt_strict_uuid_validation():
    # Generate token with non-UUID subject identifier
    now = datetime.now(UTC)
    claims = {
        "sub": "not-a-valid-uuid",
        "email": "user@example.com",
        "role": "patient",
        "type": "access",
        "jti": str(uuid.uuid4()),
        "iss": settings.JWT_ISSUER,
        "aud": settings.JWT_AUDIENCE,
        "iat": int(now.timestamp()),
        "exp": int((now + timedelta(minutes=15)).timestamp()),
    }
    raw_token = jwt.encode(claims, settings.JWT_SECRET_KEY, algorithm=settings.JWT_ALGORITHM)

    with pytest.raises(TokenInvalidException) as exc_info:
        decode_access_token(raw_token)
    assert "Token subject must be a valid UUID" in str(exc_info.value)


def test_jwt_algorithm_none_rejection():
    # Attempt "none" algorithm attack
    now = datetime.now(UTC)
    claims = {
        "sub": str(uuid.uuid4()),
        "email": "user@example.com",
        "role": "patient",
        "type": "access",
        "jti": str(uuid.uuid4()),
        "iss": settings.JWT_ISSUER,
        "aud": settings.JWT_AUDIENCE,
        "iat": int(now.timestamp()),
        "exp": int((now + timedelta(minutes=15)).timestamp()),
    }
    raw_token = jwt.encode(claims, "", algorithm="none")

    with pytest.raises(TokenInvalidException):
        decode_access_token(raw_token)


def test_jwt_wrong_algorithm_rejection():
    # Attempt HS384 when HS256 is expected
    now = datetime.now(UTC)
    claims = {
        "sub": str(uuid.uuid4()),
        "email": "user@example.com",
        "role": "patient",
        "type": "access",
        "jti": str(uuid.uuid4()),
        "iss": settings.JWT_ISSUER,
        "aud": settings.JWT_AUDIENCE,
        "iat": int(now.timestamp()),
        "exp": int((now + timedelta(minutes=15)).timestamp()),
    }
    raw_token = jwt.encode(claims, settings.JWT_SECRET_KEY, algorithm="HS384")

    with pytest.raises(TokenInvalidException):
        decode_access_token(raw_token)


def test_jwt_missing_required_claims():
    now = datetime.now(UTC)
    # Missing iat
    claims = {
        "sub": str(uuid.uuid4()),
        "email": "user@example.com",
        "role": "patient",
        "type": "access",
        "jti": str(uuid.uuid4()),
        "iss": settings.JWT_ISSUER,
        "aud": settings.JWT_AUDIENCE,
        "exp": int((now + timedelta(minutes=15)).timestamp()),
    }
    raw_token = jwt.encode(claims, settings.JWT_SECRET_KEY, algorithm=settings.JWT_ALGORITHM)
    with pytest.raises(TokenInvalidException):
        decode_access_token(raw_token)


def test_jwt_wrong_issuer_and_audience():
    now = datetime.now(UTC)
    # Wrong issuer
    claims = {
        "sub": str(uuid.uuid4()),
        "email": "user@example.com",
        "role": "patient",
        "type": "access",
        "jti": str(uuid.uuid4()),
        "iss": "untrusted-issuer",
        "aud": settings.JWT_AUDIENCE,
        "iat": int(now.timestamp()),
        "exp": int((now + timedelta(minutes=15)).timestamp()),
    }
    raw_token = jwt.encode(claims, settings.JWT_SECRET_KEY, algorithm=settings.JWT_ALGORITHM)
    with pytest.raises(TokenInvalidException):
        decode_access_token(raw_token)

    # Wrong audience
    claims["iss"] = settings.JWT_ISSUER
    claims["aud"] = "untrusted-audience"
    raw_token2 = jwt.encode(claims, settings.JWT_SECRET_KEY, algorithm=settings.JWT_ALGORITHM)
    with pytest.raises(TokenInvalidException):
        decode_access_token(raw_token2)


# -------------------------------------------------------------------------
# 3. Production Configuration Security Tests
# -------------------------------------------------------------------------


def test_production_fails_with_insecure_or_short_secret():
    with pytest.raises(ValueError) as exc:
        Settings(
            APP_ENV="production",
            JWT_SECRET_KEY="dev-insecure-secret-key-change-in-production-optiguide-2026",
        )
    assert "CRITICAL SECURITY CONFIGURATION ERROR" in str(exc.value)

    with pytest.raises(ValueError) as exc2:
        Settings(
            APP_ENV="production",
            JWT_SECRET_KEY="short-secret-under-32-chars",
        )
    assert "CRITICAL SECURITY CONFIGURATION ERROR" in str(exc2.value)


# -------------------------------------------------------------------------
# 4. Anti-Spoofing IP Detection & Rate Limiter Unit Tests
# -------------------------------------------------------------------------


def test_client_ip_anti_spoofing():
    # By default, TRUST_FORWARDED_FOR is False -> untrusted X-Forwarded-For ignored
    req = DummyRequest(
        headers={"X-Forwarded-For": "203.0.113.195, 70.41.3.18"}, client_host="10.0.0.1"
    )
    assert get_client_ip(req) == "10.0.0.1"


def test_in_memory_rate_limiter_isolation():
    limiter = InMemoryRateLimiter()
    key = "127.0.0.1:/test"

    # Within limit of 3
    assert not limiter.is_rate_limited(key, max_requests=3, window_seconds=60)
    assert not limiter.is_rate_limited(key, max_requests=3, window_seconds=60)
    assert not limiter.is_rate_limited(key, max_requests=3, window_seconds=60)

    # Exceeds limit
    assert limiter.is_rate_limited(key, max_requests=3, window_seconds=60)

    # Isolated clear
    limiter.clear()
    assert not limiter.is_rate_limited(key, max_requests=3, window_seconds=60)


# -------------------------------------------------------------------------
# 5. Schema Validation & Privilege Guard Tests
# -------------------------------------------------------------------------


def test_user_register_request_forbids_privileged_roles():
    for forbidden_role in ["admin", "optometrist", "eye_care_professional", "shopkeeper"]:
        with pytest.raises(ValidationError) as exc:
            UserRegisterRequest(
                email="test@example.com",
                password="SecurePassword123!",
                full_name="Test User",
                role=forbidden_role,
            )
        assert "Self-registration with privileged roles is prohibited" in str(exc.value)


def test_user_register_request_forbids_extra_fields():
    with pytest.raises(ValidationError) as exc:
        UserRegisterRequest(
            email="test@example.com",
            password="SecurePassword123!",
            full_name="Test User",
            is_admin=True,  # Extra forbidden field
        )
    assert "extra_forbidden" in str(exc.value)


def test_user_update_request_forbids_privileged_fields():
    # Role cannot be modified
    with pytest.raises(ValidationError) as exc:
        UserUpdateRequest(role="admin")
    assert "extra_forbidden" in str(exc.value)

    # is_admin cannot be modified
    with pytest.raises(ValidationError) as exc:
        UserUpdateRequest(is_admin=True)
    assert "extra_forbidden" in str(exc.value)

    # is_verified cannot be modified
    with pytest.raises(ValidationError) as exc:
        UserUpdateRequest(is_verified=True)
    assert "extra_forbidden" in str(exc.value)

    # Safe update allowed
    update_req = UserUpdateRequest(full_name="Updated Name")
    assert update_req.full_name == "Updated Name"


def test_role_enum_canonicalization():
    assert UserRole.is_privileged("admin")
    assert UserRole.is_privileged("shopkeeper")
    assert UserRole.is_privileged("optometrist")
    assert UserRole.is_privileged("eye_care_professional")
    assert not UserRole.is_privileged("patient")
    assert not UserRole.is_privileged("user")

    assert UserRole.normalize_role("user") == "patient"
    assert UserRole.normalize_role("eye_care_professional") == "optometrist"
    assert UserRole.normalize_role("admin") == "admin"

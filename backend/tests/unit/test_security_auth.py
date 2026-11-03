import uuid
from datetime import UTC, datetime, timedelta

import jwt
import pytest

from app.core.config import settings
from app.core.exceptions import TokenExpiredException, TokenInvalidException
from app.core.security import (
    create_access_token,
    decode_access_token,
    generate_refresh_token,
    hash_password,
    hash_token,
    needs_rehash,
    validate_password_strength,
    verify_password,
)


def test_argon2id_password_hashing_and_verification():
    raw_pwd = "SuperClinicalSecretPass123!"
    hashed = hash_password(raw_pwd)

    assert hashed.startswith("$argon2id$")
    assert verify_password(raw_pwd, hashed) is True
    assert verify_password("WrongPassword123!", hashed) is False
    assert needs_rehash(hashed) is False


def test_password_strength_validation():
    # Too short (< 8 chars)
    valid, msg = validate_password_strength("Short1")
    assert valid is False
    assert "8 characters" in (msg or "")

    # Missing letters
    valid, msg = validate_password_strength("1234567890")
    assert valid is False
    assert "letter" in (msg or "")

    # Missing digits
    valid, msg = validate_password_strength("NoDigitsHere!")
    assert valid is False
    assert "digit" in (msg or "")

    # Valid strong password
    valid, msg = validate_password_strength("ValidPassw0rd!")
    assert valid is True
    assert msg is None


def test_refresh_token_generation_and_hashing():
    token_1 = generate_refresh_token()
    token_2 = generate_refresh_token()

    assert token_1 != token_2
    assert len(token_1) >= 40

    hash_1 = hash_token(token_1)
    hash_2 = hash_token(token_1)
    assert hash_1 == hash_2
    assert len(hash_1) == 64  # SHA-256 hex digest length


def test_jwt_creation_and_decoding():
    user_id = uuid.uuid4()
    email = "optometrist@optiguide.test"
    role = "optometrist"

    token, expires_in = create_access_token(user_id=user_id, email=email, role=role)
    assert token is not None
    assert expires_in == settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60

    payload = decode_access_token(token)
    assert payload["sub"] == str(user_id)
    assert payload["email"] == email
    assert payload["role"] == role
    assert payload["type"] == "access"
    assert payload["iss"] == settings.JWT_ISSUER
    assert payload["aud"] == settings.JWT_AUDIENCE
    assert "jti" in payload


def test_jwt_expired_token_rejection():
    user_id = uuid.uuid4()
    # Create token expired 10 seconds ago
    token, _ = create_access_token(
        user_id=user_id,
        email="patient@example.com",
        role="patient",
        expires_delta=timedelta(seconds=-10),
    )

    with pytest.raises(TokenExpiredException):
        decode_access_token(token)


def test_jwt_invalid_signature_rejection():
    user_id = uuid.uuid4()
    # Sign with different secret
    claims = {
        "sub": str(user_id),
        "email": "hacker@evil.com",
        "role": "admin",
        "type": "access",
        "exp": int((datetime.now(UTC) + timedelta(minutes=15)).timestamp()),
    }
    bogus_token = jwt.encode(
        claims,
        "wrong-unauthorized-secret-key-at-least-32-chars-long",
        algorithm="HS256",
    )

    with pytest.raises(TokenInvalidException):
        decode_access_token(bogus_token)


def test_jwt_wrong_type_rejection():
    user_id = uuid.uuid4()
    # Forge token with type 'refresh'
    claims = {
        "sub": str(user_id),
        "email": "test@example.com",
        "role": "patient",
        "type": "refresh",
        "iss": settings.JWT_ISSUER,
        "aud": settings.JWT_AUDIENCE,
        "exp": int((datetime.now(UTC) + timedelta(minutes=15)).timestamp()),
    }
    refresh_as_access = jwt.encode(
        claims, settings.JWT_SECRET_KEY, algorithm=settings.JWT_ALGORITHM
    )

    with pytest.raises(TokenInvalidException):
        decode_access_token(refresh_as_access)


@pytest.mark.asyncio
async def test_rate_limiter_exceeded():
    from unittest.mock import MagicMock

    from app.api.dependencies import rate_limit
    from app.core.exceptions import RateLimitExceededException

    limiter = rate_limit(max_requests=2, window_seconds=60)
    mock_request = MagicMock()
    mock_request.url.path = "/test-rate-limit"
    mock_request.headers.get.return_value = None
    mock_request.client.host = "192.168.1.100"

    # 1st request -> ok
    await limiter(mock_request)
    # 2nd request -> ok
    await limiter(mock_request)
    # 3rd request -> raises RateLimitExceededException
    with pytest.raises(RateLimitExceededException):
        await limiter(mock_request)

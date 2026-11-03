import uuid
from datetime import UTC, datetime, timedelta

from app.core.security import generate_refresh_token, hash_token
from app.models.session import UserSession
from app.repositories.session_repo import SessionRepository


def test_register_success(client):
    payload = {
        "email": "new.patient@example.com",
        "password": "Password123!",
        "full_name": "New Patient",
        "role": "patient",
        "phone_number": "+1234567890",
        "preferred_language": "en",
    }
    response = client.post("/api/v1/auth/register", json=payload)
    assert response.status_code == 201
    data = response.json()
    assert "access_token" in data
    assert "refresh_token" in data
    assert data["token_type"] == "Bearer"
    assert data["user"]["email"] == "new.patient@example.com"
    assert data["user"]["full_name"] == "New Patient"
    assert data["user"]["role"] == "patient"
    assert data["user"]["is_active"] is True


def test_register_duplicate_email(client):
    payload = {
        "email": "duplicate@example.com",
        "password": "Password123!",
        "full_name": "Original User",
    }
    res1 = client.post("/api/v1/auth/register", json=payload)
    assert res1.status_code == 201

    # Second registration with same email (case-insensitive)
    payload_dup = {
        "email": "DUPLICATE@example.com",
        "password": "Password123!",
        "full_name": "Another Name",
    }
    res2 = client.post("/api/v1/auth/register", json=payload_dup)
    assert res2.status_code == 409
    data = res2.json()
    assert "error" in data
    assert data["error"]["code"] == "CONFLICT"


def test_register_weak_password(client):
    payload = {
        "email": "weakpass@example.com",
        "password": "short",
        "full_name": "Weak User",
    }
    response = client.post("/api/v1/auth/register", json=payload)
    assert response.status_code == 422
    data = response.json()
    assert "error" in data
    assert data["error"]["code"] == "VALIDATION_ERROR"


def test_register_invalid_email(client):
    payload = {
        "email": "not-an-email",
        "password": "ValidPassword123!",
        "full_name": "Invalid Email User",
    }
    response = client.post("/api/v1/auth/register", json=payload)
    assert response.status_code == 422
    data = response.json()
    assert "error" in data
    assert data["error"]["code"] == "VALIDATION_ERROR"


def test_login_success(client):
    # Register first
    reg_payload = {
        "email": "login.test@example.com",
        "password": "SecurePassword123!",
        "full_name": "Login Test User",
    }
    client.post("/api/v1/auth/register", json=reg_payload)

    # Login with registered credentials
    login_payload = {
        "email": "login.test@example.com",
        "password": "SecurePassword123!",
    }
    response = client.post("/api/v1/auth/login", json=login_payload)
    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    assert "refresh_token" in data
    assert data["user"]["email"] == "login.test@example.com"


def test_login_incorrect_password(client):
    # Register first
    reg_payload = {
        "email": "wrongpwd@example.com",
        "password": "CorrectPassword123!",
        "full_name": "Wrong Password User",
    }
    client.post("/api/v1/auth/register", json=reg_payload)

    # Login with wrong password
    login_payload = {
        "email": "wrongpwd@example.com",
        "password": "WrongPassword123!",
    }
    response = client.post("/api/v1/auth/login", json=login_payload)
    assert response.status_code == 401
    data = response.json()
    assert "error" in data
    assert data["error"]["code"] == "UNAUTHORIZED"
    # Ensure generic failure message (prevent user enumeration)
    assert "Invalid email or password" in data["error"]["message"]


def test_login_nonexistent_email(client):
    login_payload = {
        "email": "does.not.exist@example.com",
        "password": "AnyPassword123!",
    }
    response = client.post("/api/v1/auth/login", json=login_payload)
    assert response.status_code == 401
    data = response.json()
    assert "error" in data
    assert data["error"]["code"] == "UNAUTHORIZED"
    assert "Invalid email or password" in data["error"]["message"]


def test_refresh_token_lifecycle_and_reuse_detection(client):
    # Register
    reg_payload = {
        "email": "refresh.flow@example.com",
        "password": "ValidPassword123!",
        "full_name": "Refresh User",
    }
    reg_res = client.post("/api/v1/auth/register", json=reg_payload)
    refresh_token_1 = reg_res.json()["refresh_token"]

    # 1. Rotate refresh token successfully
    refresh_res = client.post("/api/v1/auth/refresh", json={"refresh_token": refresh_token_1})
    assert refresh_res.status_code == 200
    refreshed_data = refresh_res.json()
    assert "access_token" in refreshed_data
    assert "refresh_token" in refreshed_data
    refresh_token_2 = refreshed_data["refresh_token"]
    assert refresh_token_2 != refresh_token_1

    # 2. REUSE DETECTION: Present old, rotated token (refresh_token_1) again
    reuse_res = client.post("/api/v1/auth/refresh", json={"refresh_token": refresh_token_1})
    assert reuse_res.status_code == 401
    reuse_data = reuse_res.json()
    assert reuse_data["error"]["code"] == "TOKEN_REVOKED"

    # 3. Prove all sessions were revoked: refresh_token_2 should now also fail!
    followup_res = client.post("/api/v1/auth/refresh", json={"refresh_token": refresh_token_2})
    assert followup_res.status_code == 401


def test_refresh_token_invalid(client):
    response = client.post("/api/v1/auth/refresh", json={"refresh_token": "non_existent_token_xyz"})
    assert response.status_code == 401
    data = response.json()
    assert data["error"]["code"] == "TOKEN_INVALID"


def test_refresh_token_expired(client, db_session):
    # Register user
    reg_payload = {
        "email": "expired.token@example.com",
        "password": "ValidPassword123!",
        "full_name": "Expired User",
    }
    reg_res = client.post("/api/v1/auth/register", json=reg_payload)
    user_id = uuid.UUID(reg_res.json()["user"]["id"])

    # Manually create an expired session in DB
    expired_raw_token = generate_refresh_token()
    past_date = datetime.now(UTC) - timedelta(days=2)
    session = UserSession(
        user_id=user_id,
        session_token_hash=hash_token(expired_raw_token),
        expires_at=past_date,
    )
    SessionRepository.create(db_session, session)

    # Attempt to refresh with expired token
    response = client.post("/api/v1/auth/refresh", json={"refresh_token": expired_raw_token})
    assert response.status_code == 401
    data = response.json()
    assert data["error"]["code"] == "TOKEN_EXPIRED"


def test_logout_single_session(client):
    reg_payload = {
        "email": "logout.test@example.com",
        "password": "ValidPassword123!",
        "full_name": "Logout User",
    }
    reg_res = client.post("/api/v1/auth/register", json=reg_payload)
    refresh_token = reg_res.json()["refresh_token"]

    # Logout
    logout_res = client.post("/api/v1/auth/logout", json={"refresh_token": refresh_token})
    assert logout_res.status_code == 200
    assert logout_res.json()["success"] is True

    # Attempting to refresh should fail
    refresh_res = client.post("/api/v1/auth/refresh", json={"refresh_token": refresh_token})
    assert refresh_res.status_code == 401


def test_logout_all_sessions(client):
    reg_payload = {
        "email": "logoutall@example.com",
        "password": "ValidPassword123!",
        "full_name": "Logout All User",
    }
    reg_res = client.post("/api/v1/auth/register", json=reg_payload)
    access_token = reg_res.json()["access_token"]
    refresh_token_1 = reg_res.json()["refresh_token"]

    # Create second session via login
    login_res = client.post(
        "/api/v1/auth/login",
        json={"email": "logoutall@example.com", "password": "ValidPassword123!"},
    )
    refresh_token_2 = login_res.json()["refresh_token"]

    # Call logout-all with Bearer auth
    headers = {"Authorization": f"Bearer {access_token}"}
    logout_all_res = client.post("/api/v1/auth/logout-all", headers=headers)
    assert logout_all_res.status_code == 200
    assert logout_all_res.json()["success"] is True

    # Both refresh tokens must now be revoked
    assert (
        client.post("/api/v1/auth/refresh", json={"refresh_token": refresh_token_1}).status_code
        == 401
    )
    assert (
        client.post("/api/v1/auth/refresh", json={"refresh_token": refresh_token_2}).status_code
        == 401
    )


def test_get_me_endpoint(client):
    reg_payload = {
        "email": "me.test@example.com",
        "password": "ValidPassword123!",
        "full_name": "Me Test User",
        "role": "patient",
    }
    reg_res = client.post("/api/v1/auth/register", json=reg_payload)
    access_token = reg_res.json()["access_token"]

    # Unauthenticated request -> 401
    unauth_res = client.get("/api/v1/auth/me")
    assert unauth_res.status_code == 401
    assert unauth_res.json()["error"]["code"] == "UNAUTHORIZED"

    # Authenticated request -> 200
    headers = {"Authorization": f"Bearer {access_token}"}
    auth_res = client.get("/api/v1/auth/me", headers=headers)
    assert auth_res.status_code == 200
    data = auth_res.json()
    assert data["email"] == "me.test@example.com"
    assert data["full_name"] == "Me Test User"
    assert data["role"] == "patient"

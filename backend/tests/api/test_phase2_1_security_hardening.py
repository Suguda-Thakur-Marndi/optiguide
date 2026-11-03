import uuid

import pytest

from app.core.security import create_access_token
from app.repositories.user_repo import UserRepository

# -------------------------------------------------------------------------
# 1. Privileged Role Registration Prevention Tests
# -------------------------------------------------------------------------


@pytest.mark.parametrize(
    "privileged_role",
    ["admin", "optometrist", "eye_care_professional", "shopkeeper"],
)
def test_public_registration_blocks_privileged_roles(client, privileged_role):
    payload = {
        "email": f"attacker_{privileged_role}@example.com",
        "password": "SecurePassword123!",
        "full_name": "Attacker Trying Role",
        "role": privileged_role,
    }
    response = client.post("/api/v1/auth/register", json=payload)
    assert response.status_code == 422
    data = response.json()
    assert "error" in data
    assert data["error"]["code"] == "VALIDATION_ERROR"


def test_public_registration_blocks_injected_admin_fields(client):
    payload = {
        "email": "injected_admin@example.com",
        "password": "SecurePassword123!",
        "full_name": "Injected Field User",
        "is_admin": True,
    }
    response = client.post("/api/v1/auth/register", json=payload)
    assert response.status_code == 422
    assert response.json()["error"]["code"] == "VALIDATION_ERROR"


def test_public_registration_defaults_to_patient_safely(client):
    payload = {
        "email": "normal_citizen@example.com",
        "password": "SecurePassword123!",
        "full_name": "Normal Citizen",
    }
    response = client.post("/api/v1/auth/register", json=payload)
    assert response.status_code == 201
    user = response.json()["user"]
    assert user["role"] == "patient"
    assert user["is_verified"] is False
    assert user["is_active"] is True


# -------------------------------------------------------------------------
# 2. User Profile Privilege Escalation Prevention Tests
# -------------------------------------------------------------------------


@pytest.mark.parametrize(
    "forbidden_payload",
    [
        {"role": "admin"},
        {"is_admin": True},
        {"is_verified": True},
        {"is_active": False},
        {"hashed_password": "new_hashed_password"},
        {"permissions": ["admin:all"]},
    ],
)
def test_user_profile_update_forbids_privileged_fields(client, forbidden_payload):
    # Register regular patient
    reg = client.post(
        "/api/v1/auth/register",
        json={
            "email": f"target_{uuid.uuid4().hex[:6]}@example.com",
            "password": "SecurePassword123!",
            "full_name": "Regular Patient",
        },
    )
    token = reg.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    # Attempt privilege escalation via PATCH /me
    res = client.patch("/api/v1/users/me", json=forbidden_payload, headers=headers)
    assert res.status_code == 422
    assert res.json()["error"]["code"] == "VALIDATION_ERROR"


def test_user_profile_safe_update_succeeds(client):
    reg = client.post(
        "/api/v1/auth/register",
        json={
            "email": "safe_update@example.com",
            "password": "SecurePassword123!",
            "full_name": "Original Name",
        },
    )
    token = reg.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    res = client.patch(
        "/api/v1/users/me",
        json={
            "full_name": "Updated Safe Name",
            "phone_number": "+19876543210",
            "preferred_language": "es",
        },
        headers=headers,
    )
    assert res.status_code == 200
    data = res.json()
    assert data["full_name"] == "Updated Safe Name"
    assert data["phone_number"] == "+19876543210"
    assert data["preferred_language"] == "es"


# -------------------------------------------------------------------------
# 3. Session Isolation & Privacy Tests
# -------------------------------------------------------------------------


def test_session_ownership_and_privacy_boundaries(client):
    # User A
    res_a = client.post(
        "/api/v1/auth/register",
        json={
            "email": "user_a@example.com",
            "password": "SecurePassword123!",
            "full_name": "User Alpha",
        },
    )
    token_a = res_a.json()["access_token"]

    # User B
    res_b = client.post(
        "/api/v1/auth/register",
        json={
            "email": "user_b@example.com",
            "password": "SecurePassword123!",
            "full_name": "User Beta",
        },
    )
    token_b = res_b.json()["access_token"]

    # User A inspects sessions
    sessions_a_res = client.get(
        "/api/v1/users/me/sessions",
        headers={"Authorization": f"Bearer {token_a}"},
    )
    assert sessions_a_res.status_code == 200
    sessions_a = sessions_a_res.json()
    assert len(sessions_a) == 1
    session_item = sessions_a[0]

    # Verify no sensitive hashes, passwords, or secrets leaked
    assert "session_token_hash" not in session_item
    assert "hashed_password" not in session_item
    assert "refresh_token" not in session_item
    assert "jwt_secret" not in session_item

    # User B inspects sessions
    sessions_b_res = client.get(
        "/api/v1/users/me/sessions",
        headers={"Authorization": f"Bearer {token_b}"},
    )
    sessions_b = sessions_b_res.json()
    assert len(sessions_b) == 1
    assert sessions_b[0]["id"] != session_item["id"]


# -------------------------------------------------------------------------
# 4. Role Authorization Matrix Tests
# -------------------------------------------------------------------------


def test_role_authorization_matrix(client, db_session):
    # Create users for each role directly in DB
    # 1. Patient
    p_res = client.post(
        "/api/v1/auth/register",
        json={
            "email": "matrix_patient@example.com",
            "password": "ValidPassword123!",
            "full_name": "Matrix Patient",
        },
    )
    patient_id = uuid.UUID(p_res.json()["user"]["id"])
    _ = p_res.json()["access_token"]

    # 2. Shopkeeper
    s_res = client.post(
        "/api/v1/auth/register",
        json={
            "email": "matrix_shopkeeper@example.com",
            "password": "ValidPassword123!",
            "full_name": "Matrix Shopkeeper",
        },
    )
    shopkeeper_user = UserRepository.get_by_id(db_session, uuid.UUID(s_res.json()["user"]["id"]))
    shopkeeper_user.role = "shopkeeper"
    db_session.commit()
    shopkeeper_token, _ = create_access_token(
        shopkeeper_user.id, shopkeeper_user.email, "shopkeeper"
    )

    # 3. Unverified Professional
    u_res = client.post(
        "/api/v1/auth/register",
        json={
            "email": "matrix_unverified@example.com",
            "password": "ValidPassword123!",
            "full_name": "Unverified Optometrist",
        },
    )
    unverified_user = UserRepository.get_by_id(db_session, uuid.UUID(u_res.json()["user"]["id"]))
    unverified_user.role = "optometrist"
    unverified_user.is_verified = False
    db_session.commit()
    unverified_token, _ = create_access_token(
        unverified_user.id, unverified_user.email, "optometrist"
    )

    # 4. Verified Professional
    v_res = client.post(
        "/api/v1/auth/register",
        json={
            "email": "matrix_verified@example.com",
            "password": "ValidPassword123!",
            "full_name": "Dr. Verified Optometrist",
        },
    )
    verified_user = UserRepository.get_by_id(db_session, uuid.UUID(v_res.json()["user"]["id"]))
    verified_user.role = "optometrist"
    verified_user.is_verified = True
    db_session.commit()
    verified_token, _ = create_access_token(verified_user.id, verified_user.email, "optometrist")

    # 5. Administrator
    a_res = client.post(
        "/api/v1/auth/register",
        json={
            "email": "matrix_admin@example.com",
            "password": "ValidPassword123!",
            "full_name": "Matrix Admin",
        },
    )
    admin_user = UserRepository.get_by_id(db_session, uuid.UUID(a_res.json()["user"]["id"]))
    admin_user.role = "admin"
    db_session.commit()
    admin_token, _ = create_access_token(admin_user.id, admin_user.email, "admin")

    # -------------------------------------------------------------
    # Test A: Shopkeeper attempting admin endpoint -> 403 Forbidden
    # -------------------------------------------------------------
    sk_admin_res = client.patch(
        f"/api/v1/users/{patient_id}/status",
        json={"is_active": False},
        headers={"Authorization": f"Bearer {shopkeeper_token}"},
    )
    assert sk_admin_res.status_code == 403

    # -------------------------------------------------------------
    # Test B: Unverified Professional attempting clinical endpoint -> 403 Forbidden
    # -------------------------------------------------------------
    unver_res = client.get(
        "/api/v1/users/clinical/review-access",
        headers={"Authorization": f"Bearer {unverified_token}"},
    )
    assert unver_res.status_code == 403
    assert (
        "requires verification by an authorized administrator"
        in unver_res.json()["error"]["message"]
    )

    # -------------------------------------------------------------
    # Test C: Verified Professional attempting clinical endpoint -> 200 OK
    # -------------------------------------------------------------
    ver_res = client.get(
        "/api/v1/users/clinical/review-access",
        headers={"Authorization": f"Bearer {verified_token}"},
    )
    assert ver_res.status_code == 200
    assert "Access granted" in ver_res.json()["message"]

    # -------------------------------------------------------------
    # Test D: Admin attempting clinical endpoint -> 200 OK
    # -------------------------------------------------------------
    admin_clin_res = client.get(
        "/api/v1/users/clinical/review-access",
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    assert admin_clin_res.status_code == 200

    # -------------------------------------------------------------
    # Test E: Admin attempting admin status update -> 200 OK
    # -------------------------------------------------------------
    admin_status_res = client.patch(
        f"/api/v1/users/{patient_id}/status",
        json={"is_verified": True},
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    assert admin_status_res.status_code == 200
    assert admin_status_res.json()["is_verified"] is True

    # -------------------------------------------------------------
    # Test F: Anonymous user attempting protected endpoint -> 401 Unauthorized
    # -------------------------------------------------------------
    anon_res = client.get("/api/v1/users/me")
    assert anon_res.status_code == 401


# -------------------------------------------------------------------------
# 5. User Enumeration & Error Consistency Tests
# -------------------------------------------------------------------------


def test_login_error_consistency_prevents_user_enumeration(client, db_session):
    # 1. Nonexistent email
    res1 = client.post(
        "/api/v1/auth/login",
        json={"email": "nonexistent_enum@example.com", "password": "WrongPassword123!"},
    )
    assert res1.status_code == 401
    assert "Invalid email or password" in res1.json()["error"]["message"]

    # 2. Existing active email with wrong password
    reg = client.post(
        "/api/v1/auth/register",
        json={
            "email": "enum_target@example.com",
            "password": "CorrectPassword123!",
            "full_name": "Enum Target",
        },
    )
    user_id = uuid.UUID(reg.json()["user"]["id"])

    res2 = client.post(
        "/api/v1/auth/login",
        json={"email": "enum_target@example.com", "password": "WrongPassword123!"},
    )
    assert res2.status_code == 401
    assert "Invalid email or password" in res2.json()["error"]["message"]

    # 3. Deactivate user and attempt login with WRONG password
    user = UserRepository.get_by_id(db_session, user_id)
    user.is_active = False
    db_session.commit()

    res3 = client.post(
        "/api/v1/auth/login",
        json={"email": "enum_target@example.com", "password": "WrongPassword123!"},
    )
    # Password verification runs first: MUST return identical 401 without revealing account status!
    assert res3.status_code == 401
    assert "Invalid email or password" in res3.json()["error"]["message"]

    # 4. Deactivated user attempting login with CORRECT password
    res4 = client.post(
        "/api/v1/auth/login",
        json={"email": "enum_target@example.com", "password": "CorrectPassword123!"},
    )
    # Once password is confirmed, status is checked -> 403 Forbidden
    assert res4.status_code == 403
    assert res4.json()["error"]["code"] == "USER_INACTIVE"


# -------------------------------------------------------------------------
# 6. Deactivated User Immediate Access Revocation Tests
# -------------------------------------------------------------------------


def test_deactivated_user_token_and_session_rejection(client, db_session):
    reg = client.post(
        "/api/v1/auth/register",
        json={
            "email": "deactivate_check@example.com",
            "password": "CorrectPassword123!",
            "full_name": "Deactivate Check",
        },
    )
    token = reg.json()["access_token"]
    refresh_token = reg.json()["refresh_token"]
    user_id = uuid.UUID(reg.json()["user"]["id"])

    # Deactivate account directly
    user = UserRepository.get_by_id(db_session, user_id)
    user.is_active = False
    db_session.commit()

    # Attempt accessing protected endpoint with existing JWT
    get_res = client.get("/api/v1/auth/me", headers={"Authorization": f"Bearer {token}"})
    assert get_res.status_code == 403
    assert get_res.json()["error"]["code"] == "USER_INACTIVE"

    # Attempt refreshing token
    refresh_res = client.post("/api/v1/auth/refresh", json={"refresh_token": refresh_token})
    assert refresh_res.status_code == 403
    assert refresh_res.json()["error"]["code"] == "USER_INACTIVE"


# -------------------------------------------------------------------------
# 7. Rate Limit Spoofing Resistance Tests
# -------------------------------------------------------------------------


def test_rate_limiter_anti_spoofing_resistance(client):
    from app.api.dependencies import _rate_limit_records

    _rate_limit_records.clear()

    # Attempt 6 registration requests, spoofing a different X-Forwarded-For each time
    for i in range(5):
        res = client.post(
            "/api/v1/auth/register",
            json={
                "email": f"spoof_{i}@example.com",
                "password": "Password123!",
                "full_name": f"Spoof User {i}",
            },
            headers={"X-Forwarded-For": f"10.0.0.{i}"},
        )
        assert res.status_code == 201

    # 6th request from same client with new spoofed header must be blocked by rate limit
    res_blocked = client.post(
        "/api/v1/auth/register",
        json={
            "email": "spoof_blocked@example.com",
            "password": "Password123!",
            "full_name": "Spoof Blocked",
        },
        headers={"X-Forwarded-For": "10.0.0.99"},
    )
    assert res_blocked.status_code == 429
    assert res_blocked.json()["error"]["code"] == "RATE_LIMIT_EXCEEDED"

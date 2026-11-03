import uuid

from app.core.security import create_access_token
from app.repositories.user_repo import UserRepository


def test_get_users_me(client):
    reg_payload = {
        "email": "user.me@example.com",
        "password": "ValidPassword123!",
        "full_name": "User Me",
    }
    reg_res = client.post("/api/v1/auth/register", json=reg_payload)
    token = reg_res.json()["access_token"]

    res = client.get("/api/v1/users/me", headers={"Authorization": f"Bearer {token}"})
    assert res.status_code == 200
    data = res.json()
    assert data["email"] == "user.me@example.com"
    assert data["full_name"] == "User Me"


def test_update_users_me(client):
    reg_payload = {
        "email": "update.me@example.com",
        "password": "ValidPassword123!",
        "full_name": "Original Name",
    }
    reg_res = client.post("/api/v1/auth/register", json=reg_payload)
    token = reg_res.json()["access_token"]

    update_payload = {
        "full_name": "Updated Clinical Name",
        "phone_number": "+19998887777",
        "preferred_language": "es",
    }
    res = client.patch(
        "/api/v1/users/me",
        json=update_payload,
        headers={"Authorization": f"Bearer {token}"},
    )
    assert res.status_code == 200
    data = res.json()
    assert data["full_name"] == "Updated Clinical Name"
    assert data["phone_number"] == "+19998887777"
    assert data["preferred_language"] == "es"


def test_list_user_sessions(client):
    reg_payload = {
        "email": "sessions.list@example.com",
        "password": "ValidPassword123!",
        "full_name": "Session Lister",
    }
    reg_res = client.post("/api/v1/auth/register", json=reg_payload)
    token = reg_res.json()["access_token"]

    # Register created 1 session; login creates a second session
    client.post(
        "/api/v1/auth/login",
        json={"email": "sessions.list@example.com", "password": "ValidPassword123!"},
    )

    res = client.get(
        "/api/v1/users/me/sessions",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert res.status_code == 200
    sessions = res.json()
    assert isinstance(sessions, list)
    assert len(sessions) >= 2
    assert "id" in sessions[0]
    assert "is_revoked" in sessions[0]
    assert "expires_at" in sessions[0]


def test_admin_update_status_forbidden_for_patient(client):
    # Patient registration
    patient_res = client.post(
        "/api/v1/auth/register",
        json={
            "email": "regular.patient@example.com",
            "password": "ValidPassword123!",
            "full_name": "Patient NonAdmin",
            "role": "patient",
        },
    )
    patient_token = patient_res.json()["access_token"]
    target_id = patient_res.json()["user"]["id"]

    # Attempt admin endpoint as patient -> 403 Forbidden
    res = client.patch(
        f"/api/v1/users/{target_id}/status",
        json={"is_active": False},
        headers={"Authorization": f"Bearer {patient_token}"},
    )
    assert res.status_code == 403
    data = res.json()
    assert data["error"]["code"] == "FORBIDDEN"


def test_admin_deactivate_user_and_revoke_sessions(client, db_session):
    # 1. Register user and promote to admin via DB (public self-registration as admin is forbidden)
    admin_res = client.post(
        "/api/v1/auth/register",
        json={
            "email": "admin.master@example.com",
            "password": "ValidPassword123!",
            "full_name": "System Administrator",
        },
    )
    admin_id = uuid.UUID(admin_res.json()["user"]["id"])
    admin_user = UserRepository.get_by_id(db_session, admin_id)
    admin_user.role = "admin"
    db_session.commit()
    admin_token, _ = create_access_token(admin_user.id, admin_user.email, "admin")

    # 2. Register target patient user
    target_res = client.post(
        "/api/v1/auth/register",
        json={
            "email": "target.patient@example.com",
            "password": "ValidPassword123!",
            "full_name": "Target Deactivate Patient",
            "role": "patient",
        },
    )
    target_id = target_res.json()["user"]["id"]
    target_refresh_token = target_res.json()["refresh_token"]

    # 3. Admin deactivates target user
    status_res = client.patch(
        f"/api/v1/users/{target_id}/status",
        json={"is_active": False},
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    assert status_res.status_code == 200
    assert status_res.json()["is_active"] is False

    # 4. Target user can no longer login (403 Forbidden - account deactivated)
    login_res = client.post(
        "/api/v1/auth/login",
        json={"email": "target.patient@example.com", "password": "ValidPassword123!"},
    )
    assert login_res.status_code == 403
    assert login_res.json()["error"]["code"] == "USER_INACTIVE"

    # 5. Target user's active refresh tokens are revoked
    refresh_res = client.post(
        "/api/v1/auth/refresh",
        json={"refresh_token": target_refresh_token},
    )
    assert refresh_res.status_code == 401

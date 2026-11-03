import uuid

from app.core.security import create_access_token
from app.repositories.screening_repository import ScreeningRepository
from app.repositories.user_repo import UserRepository


# Helper fixture to create authenticated users
def register_and_get_token(client, email, name="Screening Test User"):
    res = client.post(
        "/api/v1/auth/register",
        json={
            "email": email,
            "password": "SecurePassword123!",
            "full_name": name,
        },
    )
    assert res.status_code == 201
    return res.json()["access_token"], uuid.UUID(res.json()["user"]["id"])


# -----------------------------------------------------------------------------
# 1. Consent Management Tests
# -----------------------------------------------------------------------------


def test_get_consent_current_unauthenticated_fails(client):
    res = client.get("/api/v1/screening/consent/current")
    assert res.status_code == 401
    assert res.json()["error"]["code"] == "UNAUTHORIZED"


def test_consent_lifecycle_and_withdrawal(client, db_session):
    token, user_id = register_and_get_token(client, "consent_life@example.com")
    headers = {"Authorization": f"Bearer {token}"}

    # 1. Initial State: No consent given
    curr_res = client.get("/api/v1/screening/consent/current", headers=headers)
    assert curr_res.status_code == 200
    data = curr_res.json()
    assert data["version"] == "1.0.0"
    assert data["has_accepted"] is False
    assert data["is_active"] is False

    # 2. Reject Invalid Version
    bad_res = client.post(
        "/api/v1/screening/consent/accept",
        json={"version": "99.0.0"},
        headers=headers,
    )
    assert bad_res.status_code == 400
    assert bad_res.json()["error"]["code"] == "INVALID_CONSENT_VERSION"

    # 3. Accept Valid Consent
    accept_res = client.post(
        "/api/v1/screening/consent/accept",
        json={"version": "1.0.0"},
        headers=headers,
    )
    assert accept_res.status_code == 200
    accept_data = accept_res.json()
    assert accept_data["consent_version"] == "1.0.0"
    assert accept_data["is_active"] is True
    assert accept_data["accepted_at"] is not None
    assert accept_data["withdrawn_at"] is None

    # Check state after acceptance
    curr_res2 = client.get("/api/v1/screening/consent/current", headers=headers)
    assert curr_res2.status_code == 200
    assert curr_res2.json()["has_accepted"] is True
    assert curr_res2.json()["is_active"] is True

    # 4. Duplicate Acceptance is Idempotent
    dup_res = client.post(
        "/api/v1/screening/consent/accept",
        json={"version": "1.0.0"},
        headers=headers,
    )
    assert dup_res.status_code == 200
    assert dup_res.json()["id"] == accept_data["id"]

    # 5. Withdraw Consent
    withdraw_res = client.post("/api/v1/screening/consent/withdraw", headers=headers)
    assert withdraw_res.status_code == 200
    assert withdraw_res.json()["success"] is True

    # Check state after withdrawal
    curr_res3 = client.get("/api/v1/screening/consent/current", headers=headers)
    assert curr_res3.status_code == 200
    assert curr_res3.json()["is_active"] is False
    assert curr_res3.json()["withdrawn_at"] is not None

    # Historical record is preserved in database
    latest = ScreeningRepository.get_latest_consent(db_session, user_id)
    assert latest is not None
    assert latest.is_active is False
    assert latest.withdrawn_at is not None


# -----------------------------------------------------------------------------
# 2. Screening Session Lifecycle & Policy Tests
# -----------------------------------------------------------------------------


def test_session_creation_requires_active_consent(client):
    token, _ = register_and_get_token(client, "no_consent_session@example.com")
    headers = {"Authorization": f"Bearer {token}"}

    # Attempt to create session without accepting consent -> 403 CONSENT_REQUIRED
    res = client.post("/api/v1/screening/sessions", json={}, headers=headers)
    assert res.status_code == 403
    assert res.json()["error"]["code"] == "CONSENT_REQUIRED"


def test_session_lifecycle_complete_flow(client, db_session):
    token, _user_id = register_and_get_token(client, "lifecycle_user@example.com")
    headers = {"Authorization": f"Bearer {token}"}

    # Accept consent
    client.post("/api/v1/screening/consent/accept", json={"version": "1.0.0"}, headers=headers)

    # 1. Create Session
    create_res = client.post("/api/v1/screening/sessions", json={}, headers=headers)
    assert create_res.status_code == 201
    session_data = create_res.json()
    assert session_data["status"] == "in_progress"
    assert session_data["started_at"] is not None
    assert session_data["completed_at"] is None
    session_id = session_data["id"]

    # 2. Duplicate Active Session Policy -> 409 SESSION_ALREADY_ACTIVE
    dup_res = client.post("/api/v1/screening/sessions", json={}, headers=headers)
    assert dup_res.status_code == 409
    assert dup_res.json()["error"]["code"] == "SESSION_ALREADY_ACTIVE"

    # 3. Retrieve Session by ID
    get_res = client.get(f"/api/v1/screening/sessions/{session_id}", headers=headers)
    assert get_res.status_code == 200
    assert get_res.json()["id"] == session_id

    # 4. Complete Session
    complete_res = client.post(
        f"/api/v1/screening/sessions/{session_id}/complete",
        headers=headers,
    )
    assert complete_res.status_code == 200
    assert complete_res.json()["status"] == "completed"
    assert complete_res.json()["completed_at"] is not None

    # 5. Invalid Transition: Completed -> Completed
    recomplete_res = client.post(
        f"/api/v1/screening/sessions/{session_id}/complete",
        headers=headers,
    )
    assert recomplete_res.status_code == 400
    assert recomplete_res.json()["error"]["code"] == "INVALID_SESSION_TRANSITION"

    # 6. Invalid Transition: Completed -> Cancelled
    cancel_after_complete = client.post(
        f"/api/v1/screening/sessions/{session_id}/cancel",
        json={"reason": "attempt cancel completed"},
        headers=headers,
    )
    assert cancel_after_complete.status_code == 400
    assert cancel_after_complete.json()["error"]["code"] == "INVALID_SESSION_TRANSITION"

    # 7. Audit events generated in DB
    events = ScreeningRepository.list_audit_events_for_session(db_session, uuid.UUID(session_id))
    event_types = [e.event_type for e in events]
    assert "SESSION_CREATED" in event_types
    assert "SESSION_COMPLETED" in event_types


def test_session_cancellation_flow(client):
    token, _ = register_and_get_token(client, "cancel_user@example.com")
    headers = {"Authorization": f"Bearer {token}"}

    client.post("/api/v1/screening/consent/accept", json={"version": "1.0.0"}, headers=headers)

    # Create Session
    create_res = client.post("/api/v1/screening/sessions", json={}, headers=headers)
    session_id = create_res.json()["id"]

    # Cancel Session
    cancel_res = client.post(
        f"/api/v1/screening/sessions/{session_id}/cancel",
        json={"reason": "User felt eye fatigue"},
        headers=headers,
    )
    assert cancel_res.status_code == 200
    assert cancel_res.json()["status"] == "cancelled"
    assert cancel_res.json()["cancellation_reason"] == "User felt eye fatigue"
    assert cancel_res.json()["cancelled_at"] is not None

    # Invalid Transition: Cancelled -> Completed
    complete_after_cancel = client.post(
        f"/api/v1/screening/sessions/{session_id}/complete",
        headers=headers,
    )
    assert complete_after_cancel.status_code == 400
    assert complete_after_cancel.json()["error"]["code"] == "INVALID_SESSION_TRANSITION"

    # Invalid Transition: Cancelled -> Cancelled
    recancel = client.post(
        f"/api/v1/screening/sessions/{session_id}/cancel",
        headers=headers,
    )
    assert recancel.status_code == 400
    assert recancel.json()["error"]["code"] == "INVALID_SESSION_TRANSITION"


def test_consent_withdrawal_cancels_active_session(client):
    token, _ = register_and_get_token(client, "withdraw_auto_cancel@example.com")
    headers = {"Authorization": f"Bearer {token}"}

    client.post("/api/v1/screening/consent/accept", json={"version": "1.0.0"}, headers=headers)

    # Start an in-progress session
    session_res = client.post("/api/v1/screening/sessions", json={}, headers=headers)
    session_id = session_res.json()["id"]

    # Withdraw consent
    withdraw_res = client.post("/api/v1/screening/consent/withdraw", headers=headers)
    assert withdraw_res.status_code == 200
    assert "1 active session(s) cancelled" in withdraw_res.json()["message"]

    # Check that session is now cancelled with reason "consent_withdrawn"
    check_res = client.get(f"/api/v1/screening/sessions/{session_id}", headers=headers)
    assert check_res.status_code == 200
    assert check_res.json()["status"] == "cancelled"
    assert check_res.json()["cancellation_reason"] == "consent_withdrawn"

    # New session attempt is blocked
    new_sess_res = client.post("/api/v1/screening/sessions", json={}, headers=headers)
    assert new_sess_res.status_code == 403
    assert new_sess_res.json()["error"]["code"] == "CONSENT_REQUIRED"


# -----------------------------------------------------------------------------
# 3. Ownership & IDOR Protection Tests
# -----------------------------------------------------------------------------


def test_session_ownership_and_idor_isolation(client):
    # User Alpha
    token_a, _ = register_and_get_token(client, "user_alpha@example.com")
    headers_a = {"Authorization": f"Bearer {token_a}"}
    client.post("/api/v1/screening/consent/accept", json={"version": "1.0.0"}, headers=headers_a)
    sess_a = client.post("/api/v1/screening/sessions", json={}, headers=headers_a).json()

    # User Beta
    token_b, _ = register_and_get_token(client, "user_beta@example.com")
    headers_b = {"Authorization": f"Bearer {token_b}"}
    client.post("/api/v1/screening/consent/accept", json={"version": "1.0.0"}, headers=headers_b)
    sess_b = client.post("/api/v1/screening/sessions", json={}, headers=headers_b).json()

    # User Alpha lists sessions -> sees only session A
    list_a = client.get("/api/v1/screening/sessions", headers=headers_a).json()
    assert list_a["total"] == 1
    assert list_a["items"][0]["id"] == sess_a["id"]

    # User Beta lists sessions -> sees only session B
    list_b = client.get("/api/v1/screening/sessions", headers=headers_b).json()
    assert list_b["total"] == 1
    assert list_b["items"][0]["id"] == sess_b["id"]

    # IDOR check: User Alpha attempts to access User Beta's session -> 404 NOT_FOUND
    idor_res = client.get(f"/api/v1/screening/sessions/{sess_b['id']}", headers=headers_a)
    assert idor_res.status_code == 404
    assert idor_res.json()["error"]["code"] == "NOT_FOUND"

    # IDOR check: User Alpha attempts to complete User Beta's session -> 404 NOT_FOUND
    idor_complete = client.post(
        f"/api/v1/screening/sessions/{sess_b['id']}/complete",
        headers=headers_a,
    )
    assert idor_complete.status_code == 404

    # IDOR check: User Alpha attempts to cancel User Beta's session -> 404 NOT_FOUND
    idor_cancel = client.post(
        f"/api/v1/screening/sessions/{sess_b['id']}/cancel",
        json={"reason": "malicious cancel"},
        headers=headers_a,
    )
    assert idor_cancel.status_code == 404


# -----------------------------------------------------------------------------
# 4. Role Authorization Isolation Tests
# -----------------------------------------------------------------------------


def test_role_authorization_session_access_isolation(client, db_session):
    # Patient creates session
    token_p, _patient_id = register_and_get_token(client, "patient_isolation@example.com")
    headers_p = {"Authorization": f"Bearer {token_p}"}
    client.post("/api/v1/screening/consent/accept", json={"version": "1.0.0"}, headers=headers_p)
    patient_session = client.post("/api/v1/screening/sessions", json={}, headers=headers_p).json()
    session_id = patient_session["id"]

    # Create Shopkeeper
    _token_s, sk_id = register_and_get_token(client, "sk_isolation@example.com")
    sk_user = UserRepository.get_by_id(db_session, sk_id)
    sk_user.role = "shopkeeper"
    db_session.commit()
    sk_token, _ = create_access_token(sk_user.id, sk_user.email, "shopkeeper")
    headers_s = {"Authorization": f"Bearer {sk_token}"}

    # Shopkeeper cannot access patient's screening session -> 404 NOT_FOUND
    sk_res = client.get(f"/api/v1/screening/sessions/{session_id}", headers=headers_s)
    assert sk_res.status_code == 404

    # Create Unverified Optometrist
    _token_u, u_id = register_and_get_token(client, "unver_isolation@example.com")
    u_user = UserRepository.get_by_id(db_session, u_id)
    u_user.role = "optometrist"
    u_user.is_verified = False
    db_session.commit()
    u_token, _ = create_access_token(u_user.id, u_user.email, "optometrist")
    headers_u = {"Authorization": f"Bearer {u_token}"}

    # Unverified professional cannot access patient's session -> 404 NOT_FOUND
    u_res = client.get(f"/api/v1/screening/sessions/{session_id}", headers=headers_u)
    assert u_res.status_code == 404

    # Create Verified Optometrist
    _token_v, v_id = register_and_get_token(client, "ver_isolation@example.com")
    v_user = UserRepository.get_by_id(db_session, v_id)
    v_user.role = "optometrist"
    v_user.is_verified = True
    db_session.commit()
    v_token, _ = create_access_token(v_user.id, v_user.email, "optometrist")
    headers_v = {"Authorization": f"Bearer {v_token}"}

    # Verified professional without explicit patient referral cannot access session -> 404 NOT_FOUND
    v_res = client.get(f"/api/v1/screening/sessions/{session_id}", headers=headers_v)
    assert v_res.status_code == 404

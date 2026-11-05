import uuid

import pytest
from starlette.testclient import TestClient

from app.core.security import create_access_token
from app.models.adaptive_acuity import AdaptiveAcuityAttempt
from app.models.screening_consent import ScreeningConsent
from app.models.screening_session import ScreeningSession
from app.models.user import User


@pytest.fixture
def test_subject(db_session) -> User:
    """Creates a primary patient user."""
    user = User(
        email=f"adaptive_patient_{uuid.uuid4().hex[:8]}@example.com",
        hashed_password="argon2id$mocked$hash",
        full_name="Adaptive Test Patient",
        role="patient",
        is_active=True,
    )
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)
    return user


@pytest.fixture
def other_patient(db_session) -> User:
    """Creates a secondary patient user for IDOR testing."""
    user = User(
        email=f"adaptive_other_{uuid.uuid4().hex[:8]}@example.com",
        hashed_password="argon2id$mocked$hash",
        full_name="Other Patient",
        role="patient",
        is_active=True,
    )
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)
    return user


@pytest.fixture
def consented_session(db_session, test_subject) -> ScreeningSession:
    """Creates an active consented screening session."""
    consent = ScreeningConsent(
        user_id=test_subject.id,
        consent_version="1.0.0",
        consent_text_hash="valid_consent_hash",
        is_active=True,
    )
    db_session.add(consent)
    db_session.commit()
    db_session.refresh(consent)

    session = ScreeningSession(
        user_id=test_subject.id,
        consent_id=consent.id,
        status="in_progress",
    )
    db_session.add(session)
    db_session.commit()
    db_session.refresh(session)
    return session


def test_adaptive_acuity_unauthenticated_rejected(client: TestClient, consented_session):
    """Anonymous access to start adaptive test must be rejected with 401."""
    res = client.post(
        f"/api/v1/screening/sessions/{consented_session.id}/acuity/start",
        json={"test_eye": "right"},
    )
    assert res.status_code == 401


def test_adaptive_acuity_requires_active_consent(client: TestClient, db_session, test_subject):
    """Adaptive test cannot start without active informed consent."""
    consent = ScreeningConsent(
        user_id=test_subject.id,
        consent_version="1.0.0",
        consent_text_hash="valid_consent_hash",
        is_active=False,  # Withdrawn
    )
    db_session.add(consent)
    db_session.commit()

    session = ScreeningSession(
        user_id=test_subject.id,
        consent_id=consent.id,
        status="in_progress",
    )
    db_session.add(session)
    db_session.commit()

    token, _ = create_access_token(
        user_id=test_subject.id, email=test_subject.email, role="patient"
    )
    headers = {"Authorization": f"Bearer {token}"}

    res = client.post(
        f"/api/v1/screening/sessions/{session.id}/acuity/start",
        json={"test_eye": "right"},
        headers=headers,
    )
    assert res.status_code == 403
    assert res.json()["error"]["code"] == "CONSENT_REQUIRED"


def test_adaptive_acuity_idor_protection(
    client: TestClient, db_session, test_subject, other_patient, consented_session
):
    """Cross-tenant adaptive test operations return 404 (anti-enumeration)."""
    # Give other_patient active consent so they pass consent check and fail on IDOR
    consent_b = ScreeningConsent(
        user_id=other_patient.id,
        consent_version="1.0.0",
        consent_text_hash="valid_consent_hash_b",
        is_active=True,
    )
    db_session.add(consent_b)
    db_session.commit()

    token_b, _ = create_access_token(
        user_id=other_patient.id, email=other_patient.email, role="patient"
    )
    headers_b = {"Authorization": f"Bearer {token_b}"}

    # Patient B attempts to start test on Patient A's session -> 404
    res = client.post(
        f"/api/v1/screening/sessions/{consented_session.id}/acuity/start",
        json={"test_eye": "right"},
        headers=headers_b,
    )
    assert res.status_code == 404

    # Now Patient A starts a test
    token_a, _ = create_access_token(
        user_id=test_subject.id, email=test_subject.email, role="patient"
    )
    headers_a = {"Authorization": f"Bearer {token_a}"}

    start_res = client.post(
        f"/api/v1/screening/sessions/{consented_session.id}/acuity/start",
        json={"test_eye": "right"},
        headers=headers_a,
    )
    assert start_res.status_code == 201
    test_id = start_res.json()["test_id"]

    # Patient B attempts to access Patient A's challenge
    res_b_get = client.get(f"/api/v1/screening/acuity/tests/{test_id}/next", headers=headers_b)
    assert res_b_get.status_code == 404

    # Patient B attempts to submit response
    res_b_resp = client.post(
        f"/api/v1/screening/acuity/tests/{test_id}/response",
        json={"attempt_sequence": 1, "user_response": "UP"},
        headers=headers_b,
    )
    assert res_b_resp.status_code == 404


def test_adaptive_acuity_duplicate_active_test_prevented(
    client: TestClient, db_session, test_subject, consented_session
):
    """Cannot start a second active adaptive test for the same session, eye, and type."""
    token, _ = create_access_token(
        user_id=test_subject.id, email=test_subject.email, role="patient"
    )
    headers = {"Authorization": f"Bearer {token}"}

    # Start first test
    res1 = client.post(
        f"/api/v1/screening/sessions/{consented_session.id}/acuity/start",
        json={"test_eye": "right", "test_type": "DISTANCE"},
        headers=headers,
    )
    assert res1.status_code == 201

    # Attempt to start duplicate
    res2 = client.post(
        f"/api/v1/screening/sessions/{consented_session.id}/acuity/start",
        json={"test_eye": "right", "test_type": "DISTANCE"},
        headers=headers,
    )
    assert res2.status_code == 422
    assert "already in progress" in res2.json()["error"]["message"]


def test_adaptive_acuity_full_interactive_workflow_to_completion(
    client: TestClient, db_session, test_subject, consented_session
):
    """
    Simulates a full interactive adaptive session:
    1. Start test at Level 6 (20/40)
    2. Answer 3 challenges correctly -> Level 6 passes -> Advances to Level 7 (20/30)
    3. Answer 2 challenges incorrectly -> Level 7 fails -> Stopping criterion met!
    4. Smallest resolved level is Level 6 (20/40).
    5. Parent session's VisualAcuityAssessment is automatically linked.
    """
    token, _ = create_access_token(
        user_id=test_subject.id, email=test_subject.email, role="patient"
    )
    headers = {"Authorization": f"Bearer {token}"}

    # 1. Start Test with Tumbling E and Calibration metadata
    start_payload = {
        "test_eye": "OD",
        "test_type": "DISTANCE",
        "optotype_type": "TUMBLING_E",
        "starting_level": 6,
        "viewing_distance_meters": 3.0,
        "calibration": {
            "screen_width_px": 1920,
            "screen_height_px": 1080,
            "display_dpi": 141.0,
            "viewing_distance_cm": 300.0,
            "calibration_method": "reference_card",
        },
    }
    start_res = client.post(
        f"/api/v1/screening/sessions/{consented_session.id}/acuity/start",
        json=start_payload,
        headers=headers,
    )
    assert start_res.status_code == 201
    challenge = start_res.json()
    test_id = challenge["test_id"]
    assert challenge["attempt_sequence"] == 1
    assert challenge["current_level"] == 6
    assert challenge["level_snellen"] == "20/40"
    assert "E_" in challenge["presented_symbol"]
    assert "choices" in challenge
    assert "expected_response" not in challenge  # Zero answer leakage!

    # 2. Level 6: Answer 3 challenges correctly
    for seq in range(1, 4):
        # Query DB to get the server's expected answer for this attempt
        attempt_record = (
            db_session.query(AdaptiveAcuityAttempt)
            .filter_by(test_id=uuid.UUID(test_id), attempt_sequence=seq)
            .first()
        )
        assert attempt_record is not None
        correct_ans = attempt_record.expected_response

        step_res = client.post(
            f"/api/v1/screening/acuity/tests/{test_id}/response",
            json={
                "attempt_sequence": seq,
                "user_response": correct_ans,
                "response_duration_ms": 1200,
            },
            headers=headers,
        )
        assert step_res.status_code == 200
        step_data = step_res.json()
        assert step_data["was_correct"] is True

        if seq < 3:
            assert step_data["is_test_complete"] is False
            assert step_data["level"] == 6
        else:
            # On 3rd correct, Level 6 passes -> advanced to Level 7!
            assert step_data["is_test_complete"] is False
            assert step_data["level"] == 7
            assert step_data["next_challenge"]["current_level"] == 7
            assert step_data["next_challenge"]["level_snellen"] == "20/30"

    # 3. Level 7: Answer 2 challenges incorrectly to trigger stopping criteria
    # Current sequence is 4
    for seq in [4, 5]:
        attempt_record = (
            db_session.query(AdaptiveAcuityAttempt)
            .filter_by(test_id=uuid.UUID(test_id), attempt_sequence=seq)
            .first()
        )
        assert attempt_record is not None
        # Intentionally give wrong answer
        wrong_ans = "DOWN" if attempt_record.expected_response != "DOWN" else "UP"

        step_res = client.post(
            f"/api/v1/screening/acuity/tests/{test_id}/response",
            json={
                "attempt_sequence": seq,
                "user_response": wrong_ans,
                "response_duration_ms": 1500,
            },
            headers=headers,
        )
        assert step_res.status_code == 200
        step_data = step_res.json()
        assert step_data["was_correct"] is False

        if seq == 4:
            assert step_data["is_test_complete"] is False
        else:
            # On 2nd incorrect at Level 7, Level 7 fails -> test is COMPLETED!
            assert step_data["is_test_complete"] is True
            assert step_data["test_status"] == "COMPLETED"
            summary = step_data["result_summary"]
            assert summary is not None
            assert summary["smallest_resolved_level"] == 6
            assert summary["final_snellen"] == "20/40"
            assert summary["final_logmar"] == 0.30
            assert summary["is_calibrated"] is True
            assert summary["calibration_status"] == "SERVER_VERIFIED"
            assert "preliminary functional assessment aid" in summary["clinical_disclaimer"]

    # 4. Verify Final Result Query Endpoint
    result_res = client.get(f"/api/v1/screening/acuity/tests/{test_id}/result", headers=headers)
    assert result_res.status_code == 200
    res_data = result_res.json()
    assert res_data["status"] == "COMPLETED"
    assert res_data["final_snellen"] == "20/40"
    assert res_data["assessment_id"] is not None

    # 5. Verify Parent Screening Session received the VisualAcuityAssessment
    session_acuity = client.get(
        f"/api/v1/screening/sessions/{consented_session.id}/acuity", headers=headers
    )
    assert session_acuity.status_code == 200
    acuity_items = session_acuity.json()
    assert len(acuity_items) >= 1
    assert any(
        item["snellen_fraction"] == "20/40" and item["test_eye"] == "right" for item in acuity_items
    )


def test_adaptive_acuity_out_of_order_and_duplicate_rejected(
    client: TestClient, db_session, test_subject, consented_session
):
    """Submitting out-of-order sequence or answering the same attempt twice is rejected."""
    token, _ = create_access_token(
        user_id=test_subject.id, email=test_subject.email, role="patient"
    )
    headers = {"Authorization": f"Bearer {token}"}

    start_res = client.post(
        f"/api/v1/screening/sessions/{consented_session.id}/acuity/start",
        json={"test_eye": "OS"},
        headers=headers,
    )
    test_id = start_res.json()["test_id"]

    # Submit sequence #2 when current is #1
    bad_seq_res = client.post(
        f"/api/v1/screening/acuity/tests/{test_id}/response",
        json={"attempt_sequence": 2, "user_response": "UP"},
        headers=headers,
    )
    assert bad_seq_res.status_code == 422
    assert "Out-of-order or duplicate attempt" in bad_seq_res.json()["error"]["message"]

    # Submit valid sequence #1
    ok_res = client.post(
        f"/api/v1/screening/acuity/tests/{test_id}/response",
        json={"attempt_sequence": 1, "user_response": "UP"},
        headers=headers,
    )
    assert ok_res.status_code == 200

    # Repeat sequence #1 -> rejected
    dup_res = client.post(
        f"/api/v1/screening/acuity/tests/{test_id}/response",
        json={"attempt_sequence": 1, "user_response": "UP"},
        headers=headers,
    )
    assert dup_res.status_code == 422
    assert "Out-of-order or duplicate attempt" in dup_res.json()["error"]["message"]


def test_adaptive_acuity_cancellation_and_aliases(
    client: TestClient, db_session, test_subject, consented_session
):
    """Tests cancellation flow and top-level /api/v1/acuity canonical aliases."""
    token, _ = create_access_token(
        user_id=test_subject.id, email=test_subject.email, role="patient"
    )
    headers = {"Authorization": f"Bearer {token}"}

    start_res = client.post(
        f"/api/v1/screening/sessions/{consented_session.id}/acuity/start",
        json={"test_eye": "both"},
        headers=headers,
    )
    test_id = start_res.json()["test_id"]

    # Test canonical alias for getting challenge: /api/v1/acuity/tests/{test_id}/next
    alias_next = client.get(f"/api/v1/acuity/tests/{test_id}/next", headers=headers)
    assert alias_next.status_code == 200
    assert alias_next.json()["attempt_sequence"] == 1

    # Cancel via canonical alias: /api/v1/acuity/tests/{test_id}/cancel
    cancel_res = client.post(
        f"/api/v1/acuity/tests/{test_id}/cancel",
        json={"reason": "citizen_stopped_early"},
        headers=headers,
    )
    assert cancel_res.status_code == 200
    assert cancel_res.json()["status"] == "CANCELLED"

    # Attempting to submit response on cancelled test returns 422
    res_after_cancel = client.post(
        f"/api/v1/screening/acuity/tests/{test_id}/response",
        json={"attempt_sequence": 1, "user_response": "UP"},
        headers=headers,
    )
    assert res_after_cancel.status_code == 422
    assert (
        "Cannot submit response to test with status 'CANCELLED'"
        in res_after_cancel.json()["error"]["message"]
    )

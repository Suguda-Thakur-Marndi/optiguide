import uuid

import pytest
from starlette.testclient import TestClient

from app.core.security import create_access_token
from app.models.screening_consent import ScreeningConsent
from app.models.screening_session import ScreeningSession
from app.models.user import User


@pytest.fixture
def test_subject(db_session) -> User:
    """Creates a regular patient user for screening tests."""
    user = User(
        email=f"patient_{uuid.uuid4().hex[:8]}@example.com",
        hashed_password="argon2id$mocked$hash",
        full_name="Primary Patient",
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
        email=f"other_{uuid.uuid4().hex[:8]}@example.com",
        hashed_password="argon2id$mocked$hash",
        full_name="Second Patient",
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


def test_visual_acuity_unauthenticated_fails(client: TestClient, consented_session):
    """Anonymous requests to acuity endpoints must be rejected with 401 Unauthorized."""
    # POST acuity without token
    res = client.post(
        f"/api/v1/screening/sessions/{consented_session.id}/acuity",
        json={"test_eye": "right", "snellen_fraction": "20/20"},
    )
    assert res.status_code == 401

    # Invalid token
    res_inv = client.get(
        f"/api/v1/screening/sessions/{consented_session.id}/acuity",
        headers={"Authorization": "Bearer invalid_token_structure"},
    )
    assert res_inv.status_code == 401


def test_visual_acuity_requires_active_consent(client: TestClient, db_session, test_subject):
    """Screening acuity assessments require active informed consent."""
    # Session created without active consent (e.g. consent withdrawn afterwards)
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
        f"/api/v1/screening/sessions/{session.id}/acuity",
        json={"test_eye": "right", "snellen_fraction": "20/20"},
        headers=headers,
    )
    assert res.status_code == 403
    error_payload = res.json()["error"]
    assert error_payload["code"] == "CONSENT_REQUIRED"
    assert "Active informed consent is required" in error_payload["message"]


def test_visual_acuity_invalid_session_status(
    client: TestClient, db_session, test_subject, consented_session
):
    """Completed or cancelled sessions cannot accept new visual acuity assessments."""
    token, _ = create_access_token(
        user_id=test_subject.id, email=test_subject.email, role="patient"
    )
    headers = {"Authorization": f"Bearer {token}"}

    # Mark session completed
    consented_session.status = "completed"
    db_session.commit()

    res = client.post(
        f"/api/v1/screening/sessions/{consented_session.id}/acuity",
        json={"test_eye": "right", "snellen_fraction": "20/20"},
        headers=headers,
    )
    assert res.status_code == 400
    error_payload = res.json()["error"]
    assert error_payload["code"] == "INVALID_SESSION_TRANSITION"
    assert (
        "Cannot record assessment on screening session with status 'completed'"
        in error_payload["message"]
    )


def test_visual_acuity_idor_protection(
    client: TestClient, db_session, other_patient, consented_session
):
    """Cross-patient session access and assessment retrieval returns 404 (anti-enumeration)."""
    token, _ = create_access_token(
        user_id=other_patient.id, email=other_patient.email, role="patient"
    )
    headers = {"Authorization": f"Bearer {token}"}

    # Patient B attempts to record acuity on Patient A's session
    res = client.post(
        f"/api/v1/screening/sessions/{consented_session.id}/acuity",
        json={"test_eye": "right", "snellen_fraction": "20/20"},
        headers=headers,
    )
    assert res.status_code == 404

    # Patient B attempts to list acuity for Patient A's session
    get_res = client.get(
        f"/api/v1/screening/sessions/{consented_session.id}/acuity",
        headers=headers,
    )
    assert get_res.status_code == 404

    # Patient B attempts to get summary for Patient A's session
    sum_res = client.get(
        f"/api/v1/screening/sessions/{consented_session.id}/acuity/summary",
        headers=headers,
    )
    assert sum_res.status_code == 404


def test_distance_visual_acuity_full_lifecycle(
    client: TestClient, db_session, test_subject, consented_session
):
    """Comprehensive test of distance screening (OD, OS, OU, repeat updates, and geometry)."""
    token, _ = create_access_token(
        user_id=test_subject.id, email=test_subject.email, role="patient"
    )
    headers = {"Authorization": f"Bearer {token}"}

    # 1. Record Right Eye (OD) distance acuity with auto-calculated logMAR and decimal
    od_payload = {
        "assessment_type": "DISTANCE",
        "test_eye": "OD",
        "snellen_fraction": "20/20",
        "tested_distance_meters": 0.6,
        "is_calibrated": True,
        "calibration": {
            "screen_width_px": 1920,
            "screen_height_px": 1080,
            "display_dpi": 141.0,
            "physical_optotype_mm": 0.87,
            "viewing_distance_cm": 60.0,
        },
        "observations": "Normal baseline OD",
    }
    od_res = client.post(
        f"/api/v1/screening/sessions/{consented_session.id}/acuity",
        json=od_payload,
        headers=headers,
    )
    assert od_res.status_code == 201
    od_data = od_res.json()
    assert od_data["test_eye"] == "right"
    assert od_data["assessment_type"] == "DISTANCE"
    assert od_data["snellen_fraction"] == "20/20"
    assert od_data["logmar"] == 0.00
    assert od_data["decimal_acuity"] == 1.00
    assert od_data["is_calibrated"] is True
    assessment_id = od_data["id"]

    # 2. Record Left Eye (OS) distance acuity with explicit agreeing logMAR
    os_payload = {
        "assessment_type": "DISTANCE",
        "test_eye": "OS",
        "snellen_fraction": "20/40",
        "logmar": 0.30,
        "decimal_acuity": 0.50,
        "tested_distance_meters": 0.6,
    }
    os_res = client.post(
        f"/api/v1/screening/sessions/{consented_session.id}/acuity",
        json=os_payload,
        headers=headers,
    )
    assert os_res.status_code == 201
    os_data = os_res.json()
    assert os_data["test_eye"] == "left"
    assert os_data["logmar"] == 0.30

    # 3. Record Binocular (OU) distance acuity
    ou_payload = {
        "assessment_type": "DISTANCE",
        "test_eye": "OU",
        "snellen_fraction": "20/20",
        "tested_distance_meters": 0.6,
    }
    ou_res = client.post(
        f"/api/v1/screening/sessions/{consented_session.id}/acuity",
        json=ou_payload,
        headers=headers,
    )
    assert ou_res.status_code == 201
    ou_data = ou_res.json()
    assert ou_data["test_eye"] == "both"

    # 4. Repeat submission for OD (idempotent update check)
    update_od = {
        "assessment_type": "DISTANCE",
        "test_eye": "right",
        "snellen_fraction": "20/25",
        "tested_distance_meters": 0.6,
        "observations": "Retested OD",
    }
    retest_res = client.post(
        f"/api/v1/screening/sessions/{consented_session.id}/acuity",
        json=update_od,
        headers=headers,
    )
    assert retest_res.status_code == 201
    retest_data = retest_res.json()
    assert retest_data["id"] == assessment_id
    assert retest_data["snellen_fraction"] == "20/25"
    assert retest_data["observations"] == "Retested OD"

    # 5. List acuity for session (should contain 3 records: OD, OS, OU)
    list_res = client.get(
        f"/api/v1/screening/sessions/{consented_session.id}/acuity",
        headers=headers,
    )
    assert list_res.status_code == 200
    items = list_res.json()
    assert len(items) == 3


def test_near_visual_acuity_lifecycle(
    client: TestClient, db_session, test_subject, consented_session
):
    """Verifies near visual acuity assessment with reading distance validation."""
    token, _ = create_access_token(
        user_id=test_subject.id, email=test_subject.email, role="patient"
    )
    headers = {"Authorization": f"Bearer {token}"}

    payload = {
        "assessment_type": "NEAR",
        "test_eye": "both",
        "snellen_fraction": "20/20",
        "near_reading_label": "N6",
        "near_reading_distance_cm": 40.0,
    }
    res = client.post(
        f"/api/v1/screening/sessions/{consented_session.id}/acuity",
        json=payload,
        headers=headers,
    )
    assert res.status_code == 201
    data = res.json()
    assert data["assessment_type"] == "NEAR"
    assert data["test_eye"] == "both"
    assert data["near_reading_label"] == "N6"
    assert data["near_reading_distance_cm"] == 40.0


def test_conflicting_snellen_logmar_rejected(
    client: TestClient, db_session, test_subject, consented_session
):
    """Submitting conflicting Snellen and logMAR values returns 422 Unprocessable Content."""
    token, _ = create_access_token(
        user_id=test_subject.id, email=test_subject.email, role="patient"
    )
    headers = {"Authorization": f"Bearer {token}"}

    payload = {
        "test_eye": "right",
        "snellen_fraction": "20/20",  # Expected logMAR is 0.00
        "logmar": 0.50,  # Contradicts 20/20 by 0.50
    }
    res = client.post(
        f"/api/v1/screening/sessions/{consented_session.id}/acuity",
        json=payload,
        headers=headers,
    )
    assert res.status_code == 422
    error_payload = res.json()["error"]
    assert error_payload["code"] == "VALIDATION_ERROR"
    assert "Conflicting visual acuity values" in error_payload["message"]


def test_acuity_session_summary_and_triage(
    client: TestClient, db_session, test_subject, consented_session
):
    """Verifies deterministic summary output, referral triage, and clinical disclaimer."""
    token, _ = create_access_token(
        user_id=test_subject.id, email=test_subject.email, role="patient"
    )
    headers = {"Authorization": f"Bearer {token}"}

    # 1. Post OD 20/20 (normal) and OS 20/60 (logMAR 0.48 -> reduced vision and asymmetry)
    client.post(
        f"/api/v1/screening/sessions/{consented_session.id}/acuity",
        json={"test_eye": "right", "snellen_fraction": "20/20", "tested_distance_meters": 0.6},
        headers=headers,
    )
    client.post(
        f"/api/v1/screening/sessions/{consented_session.id}/acuity",
        json={"test_eye": "left", "snellen_fraction": "20/60", "tested_distance_meters": 0.6},
        headers=headers,
    )

    # 2. Query summary
    res = client.get(
        f"/api/v1/screening/sessions/{consented_session.id}/acuity/summary",
        headers=headers,
    )
    assert res.status_code == 200
    summary = res.json()
    assert summary["session_id"] == str(consented_session.id)
    assert summary["referral_recommended"] is True
    assert summary["interocular_difference_logmar"] == 0.48
    assert any(
        "Reduced distance visual acuity in left eye" in r for r in summary["referral_reasons"]
    )
    assert any("Interocular visual acuity asymmetry" in r for r in summary["referral_reasons"])
    assert any(
        "Binocular (OU) distance visual acuity not assessed" in m
        for m in summary["missing_observations"]
    )
    assert "preliminary functional assessment aid" in summary["clinical_disclaimer"]


def test_acuity_history_and_single_lookup(
    client: TestClient, db_session, test_subject, consented_session
):
    """Verifies user history listing and single assessment lookup endpoints."""
    token, _ = create_access_token(
        user_id=test_subject.id, email=test_subject.email, role="patient"
    )
    headers = {"Authorization": f"Bearer {token}"}

    # Record assessment
    create_res = client.post(
        f"/api/v1/screening/sessions/{consented_session.id}/acuity",
        json={"test_eye": "right", "snellen_fraction": "20/20", "tested_distance_meters": 0.6},
        headers=headers,
    )
    rec_id = create_res.json()["id"]

    # History endpoint
    hist_res = client.get("/api/v1/screening/acuity/history", headers=headers)
    assert hist_res.status_code == 200
    hist = hist_res.json()
    assert hist["total"] >= 1
    assert any(item["id"] == rec_id for item in hist["items"])

    # Single lookup endpoint
    single_res = client.get(f"/api/v1/screening/acuity/{rec_id}", headers=headers)
    assert single_res.status_code == 200
    assert single_res.json()["id"] == rec_id

    # Test canonical aliases
    alias_hist = client.get("/api/v1/acuity/history", headers=headers)
    assert alias_hist.status_code == 200
    alias_single = client.get(f"/api/v1/acuity/{rec_id}", headers=headers)
    assert alias_single.status_code == 200

import uuid

import pytest
from starlette.testclient import TestClient

from app.models.screening_consent import ScreeningConsent
from app.models.screening_session import ScreeningSession
from app.models.user import User


@pytest.fixture
def test_subject(db_session) -> User:
    """Creates a regular patient user for screening tests."""
    user = User(
        email=f"patient_{uuid.uuid4().hex[:8]}@example.com",
        hashed_password="argon2id$mocked$hash",
        full_name="Patient Subject",
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
        consent_text_hash="mock_hash_for_test",
        is_active=True,
    )
    db_session.add(consent)
    db_session.commit()
    db_session.refresh(consent)

    sess = ScreeningSession(
        user_id=test_subject.id,
        consent_id=consent.id,
        status="in_progress",
    )
    db_session.add(sess)
    db_session.commit()
    db_session.refresh(sess)
    return sess


def test_visual_acuity_recording_and_retrieval(
    client: TestClient, db_session, test_subject, consented_session
):
    """Verifies recording distance visual acuity and retrieving results."""
    from app.core.security import create_access_token

    token, _ = create_access_token(
        user_id=test_subject.id, email=test_subject.email, role="patient"
    )
    headers = {"Authorization": f"Bearer {token}"}

    payload = {
        "test_eye": "right",
        "snellen_fraction": "20/20",
        "logmar": 0.0,
        "decimal_acuity": 1.0,
        "tested_distance_meters": 0.6,
        "unassisted_or_corrected": "unassisted",
        "near_reading_label": "N6",
        "near_reading_distance_cm": 38.0,
        "is_calibrated": True,
        "calibration": {
            "screen_width_px": 1920,
            "screen_height_px": 1080,
            "display_dpi": 141.0,
            "physical_optotype_mm": 0.87,
            "viewing_distance_cm": 60.0,
            "is_verified": True,
        },
        "observations": "Clear and confident responses.",
    }

    res = client.post(
        f"/api/v1/screening/sessions/{consented_session.id}/acuity",
        json=payload,
        headers=headers,
    )
    assert res.status_code == 201
    data = res.json()
    assert data["test_eye"] == "right"
    assert data["snellen_fraction"] == "20/20"
    assert data["logmar"] == 0.0
    assert data["is_calibrated"] is True
    assert "141.0" in data["calibration_metadata"]

    # Retrieve acuity records
    get_res = client.get(
        f"/api/v1/screening/sessions/{consented_session.id}/acuity",
        headers=headers,
    )
    assert get_res.status_code == 200
    items = get_res.json()
    assert len(items) == 1
    assert items[0]["id"] == data["id"]


def test_astigmatism_dial_screening_recording(
    client: TestClient, db_session, test_subject, consented_session
):
    """Verifies recording radial clock dial / fan screening results."""
    from app.core.security import create_access_token

    token, _ = create_access_token(
        user_id=test_subject.id, email=test_subject.email, role="patient"
    )
    headers = {"Authorization": f"Bearer {token}"}

    payload = {
        "chart_type": "clock_dial",
        "has_uniform_clarity": False,
        "indicated_axes": [3, 9],
        "sharpest_meridian_hour": 3,
        "screening_observation": "Client noted the 3-9 horizontal meridian appeared darker and more distinct.",
    }

    res = client.post(
        f"/api/v1/screening/sessions/{consented_session.id}/astigmatism",
        json=payload,
        headers=headers,
    )
    assert res.status_code == 201
    data = res.json()
    assert data["has_uniform_clarity"] is False
    assert data["sharpest_meridian_hour"] == 3
    assert "[3, 9]" in data["indicated_axes"]

    # Retrieval
    get_res = client.get(
        f"/api/v1/screening/sessions/{consented_session.id}/astigmatism",
        headers=headers,
    )
    assert get_res.status_code == 200
    items = get_res.json()
    assert len(items) == 1
    assert items[0]["sharpest_meridian_hour"] == 3


def test_color_vision_plate_recording(
    client: TestClient, db_session, test_subject, consented_session
):
    """Verifies recording pseudoisochromatic plate color screening."""
    from app.core.security import create_access_token

    token, _ = create_access_token(
        user_id=test_subject.id, email=test_subject.email, role="patient"
    )
    headers = {"Authorization": f"Bearer {token}"}

    payload = {
        "test_protocol": "pseudoisochromatic_plates",
        "total_plates_presented": 4,
        "correct_plate_count": 2,
        "deficiency_indicated": True,
        "deficiency_type": "protan_deutan_red_green",
        "responses_detail": [
            {"plate": 1, "input": "12", "correct": True},
            {"plate": 2, "input": "3", "correct": False},
            {"plate": 3, "input": "70", "correct": False},
            {"plate": 4, "input": "5", "correct": True},
        ],
    }

    res = client.post(
        f"/api/v1/screening/sessions/{consented_session.id}/color-vision",
        json=payload,
        headers=headers,
    )
    assert res.status_code == 201
    data = res.json()
    assert data["deficiency_indicated"] is True
    assert data["deficiency_type"] == "protan_deutan_red_green"
    assert data["correct_plate_count"] == 2

    # Retrieval
    get_res = client.get(
        f"/api/v1/screening/sessions/{consented_session.id}/color-vision",
        headers=headers,
    )
    assert get_res.status_code == 200
    items = get_res.json()
    assert len(items) == 1
    assert items[0]["deficiency_type"] == "protan_deutan_red_green"


def test_clinical_session_summary_and_triage(
    client: TestClient, db_session, test_subject, consented_session
):
    """Verifies that the session summary aggregates all findings and triggers referral recommendations."""
    from app.core.security import create_access_token

    token, _ = create_access_token(
        user_id=test_subject.id, email=test_subject.email, role="patient"
    )
    headers = {"Authorization": f"Bearer {token}"}

    # 1. Right eye normal (20/20 = logMAR 0.0)
    client.post(
        f"/api/v1/screening/sessions/{consented_session.id}/acuity",
        json={
            "test_eye": "right",
            "snellen_fraction": "20/20",
            "logmar": 0.0,
            "decimal_acuity": 1.0,
            "tested_distance_meters": 0.6,
        },
        headers=headers,
    )

    # 2. Left eye reduced (20/70 = logMAR 0.54) -> Triggers both high logMAR and interocular asymmetry!
    client.post(
        f"/api/v1/screening/sessions/{consented_session.id}/acuity",
        json={
            "test_eye": "left",
            "snellen_fraction": "20/70",
            "logmar": 0.54,
            "decimal_acuity": 0.28,
            "tested_distance_meters": 0.6,
        },
        headers=headers,
    )

    # 3. Astigmatism non-uniform
    client.post(
        f"/api/v1/screening/sessions/{consented_session.id}/astigmatism",
        json={
            "chart_type": "clock_dial",
            "has_uniform_clarity": False,
            "sharpest_meridian_hour": 1,
        },
        headers=headers,
    )

    # 4. Color vision normal
    client.post(
        f"/api/v1/screening/sessions/{consented_session.id}/color-vision",
        json={"total_plates_presented": 4, "correct_plate_count": 4, "deficiency_indicated": False},
        headers=headers,
    )

    # Fetch summary
    summary_res = client.get(
        f"/api/v1/screening/sessions/{consented_session.id}/summary",
        headers=headers,
    )
    assert summary_res.status_code == 200
    summary = summary_res.json()
    assert summary["referral_recommended"] is True
    assert len(summary["referral_reasons"]) >= 2
    assert any("Interocular visual acuity asymmetry" in r for r in summary["referral_reasons"])
    assert any(
        "Reduced distance visual acuity in left eye" in r for r in summary["referral_reasons"]
    )
    assert "OptiGuide is a preliminary vision screening aid" in summary["clinical_disclaimer"]


def test_clinical_assessment_idor_and_status_protection(
    client: TestClient, db_session, test_subject, consented_session
):
    """Verifies that other users cannot access assessments, and completed sessions reject mutations."""
    from app.core.security import create_access_token

    # Another user
    other_user = User(
        email="stranger@example.com",
        hashed_password="mock",
        full_name="Stranger",
        role="patient",
        is_active=True,
    )
    db_session.add(other_user)
    db_session.commit()

    other_token, _ = create_access_token(
        user_id=other_user.id, email=other_user.email, role="patient"
    )
    other_headers = {"Authorization": f"Bearer {other_token}"}

    # Stranger cannot post acuity to consented_session
    res = client.post(
        f"/api/v1/screening/sessions/{consented_session.id}/acuity",
        json={
            "test_eye": "right",
            "snellen_fraction": "20/20",
            "logmar": 0.0,
            "decimal_acuity": 1.0,
        },
        headers=other_headers,
    )
    assert res.status_code == 404

    # Complete the session
    owner_token, _ = create_access_token(
        user_id=test_subject.id, email=test_subject.email, role="patient"
    )
    owner_headers = {"Authorization": f"Bearer {owner_token}"}
    client.post(
        f"/api/v1/screening/sessions/{consented_session.id}/complete",
        headers=owner_headers,
    )

    # Owner cannot record assessment on completed session
    res_after = client.post(
        f"/api/v1/screening/sessions/{consented_session.id}/acuity",
        json={
            "test_eye": "right",
            "snellen_fraction": "20/20",
            "logmar": 0.0,
            "decimal_acuity": 1.0,
        },
        headers=owner_headers,
    )
    assert res_after.status_code == 400
    assert "Cannot record assessment" in res_after.json()["error"]["message"]

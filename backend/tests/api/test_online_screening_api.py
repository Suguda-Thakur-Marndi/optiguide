"""Integration tests for the Online Vision Screening Platform API endpoints.

Covers:
- Configuration and localized module catalogs (en, hi, or)
- Display calibration flow and uncalibrated fallbacks
- Full interactive lifecycle across all 7 screening modules
- Server-side response scoring and hidden answer confidentiality
- Test instance cancellation
- Consolidated Final Screening Report generation
- Role-based access control (RBAC: patient, optometrist, shopkeeper, admin)
- IDOR prevention and active consent enforcement
"""

import uuid

import pytest
from starlette.testclient import TestClient

from app.core.security import create_access_token
from app.models.online_screening import ScreeningTestInstance
from app.models.screening_consent import ScreeningConsent
from app.models.screening_session import ScreeningSession
from app.models.user import User
from app.services.online_screening_service import OnlineScreeningService


@pytest.fixture
def patient_user(db_session) -> User:
    """Primary patient user for screening tests."""
    user = User(
        email=f"online_patient_{uuid.uuid4().hex[:8]}@example.com",
        hashed_password="argon2id$mocked$hash",
        full_name="Online Test Patient",
        role="patient",
        is_active=True,
    )
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)
    return user


@pytest.fixture
def other_patient_user(db_session) -> User:
    """Second patient user for IDOR testing."""
    user = User(
        email=f"other_patient_{uuid.uuid4().hex[:8]}@example.com",
        hashed_password="argon2id$mocked$hash",
        full_name="Secondary Patient",
        role="patient",
        is_active=True,
    )
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)
    return user


@pytest.fixture
def optometrist_user(db_session) -> User:
    """Licensed optometrist for reviewing screening reports."""
    user = User(
        email=f"optom_{uuid.uuid4().hex[:8]}@example.com",
        hashed_password="argon2id$mocked$hash",
        full_name="Dr. Optometrist",
        role="optometrist",
        is_active=True,
    )
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)
    return user


@pytest.fixture
def shopkeeper_user(db_session) -> User:
    """Optical shopkeeper user for RBAC verification."""
    user = User(
        email=f"shop_{uuid.uuid4().hex[:8]}@example.com",
        hashed_password="argon2id$mocked$hash",
        full_name="Retail Shopkeeper",
        role="shopkeeper",
        is_active=True,
    )
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)
    return user


@pytest.fixture
def patient_headers(patient_user) -> dict[str, str]:
    token, _ = create_access_token(
        user_id=patient_user.id, email=patient_user.email, role=patient_user.role
    )
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture
def other_patient_headers(other_patient_user) -> dict[str, str]:
    token, _ = create_access_token(
        user_id=other_patient_user.id,
        email=other_patient_user.email,
        role=other_patient_user.role,
    )
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture
def optometrist_headers(optometrist_user) -> dict[str, str]:
    token, _ = create_access_token(
        user_id=optometrist_user.id,
        email=optometrist_user.email,
        role=optometrist_user.role,
    )
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture
def shopkeeper_headers(shopkeeper_user) -> dict[str, str]:
    token, _ = create_access_token(
        user_id=shopkeeper_user.id,
        email=shopkeeper_user.email,
        role=shopkeeper_user.role,
    )
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture
def consented_session(db_session, patient_user) -> ScreeningSession:
    """Creates an active informed consent record and screening session for patient_user."""
    consent = ScreeningConsent(
        user_id=patient_user.id,
        consent_version="1.0.0",
        consent_text_hash="online_screening_consent_hash",
        is_active=True,
    )
    db_session.add(consent)
    db_session.commit()

    session = ScreeningSession(
        user_id=patient_user.id,
        consent_id=consent.id,
        status="in_progress",
    )
    db_session.add(session)
    db_session.commit()
    db_session.refresh(session)
    return session


# =============================================================================
# 1. Platform Configuration & Catalogs
# =============================================================================


def test_get_configuration_endpoints(client: TestClient, patient_headers):
    """Configuration endpoint returns metadata, modules, and localized instructions."""
    # Default English
    res_en = client.get("/api/v1/screening/configuration", headers=patient_headers)
    assert res_en.status_code == 200
    data_en = res_en.json()
    assert data_en["platform_name"] == "OptiGuide Online Vision Screening Platform"
    assert len(data_en["available_modules"]) == 7
    assert "VISUAL_ACUITY" in data_en["default_test_sequence"]
    assert "non-diagnostic" in data_en["clinical_notice"].lower()

    # Hindi localization
    res_hi = client.get("/api/v1/screening/configuration?lang=hi", headers=patient_headers)
    assert res_hi.status_code == 200
    data_hi = res_hi.json()
    assert any("दृष्टि" in m["title"] for m in data_hi["available_modules"])

    # Odia localization
    res_or = client.get("/api/v1/screening/configuration?lang=or", headers=patient_headers)
    assert res_or.status_code == 200
    data_or = res_or.json()
    assert len(data_or["available_modules"]) == 7

    # Module catalog
    res_list = client.get("/api/v1/screening/tests", headers=patient_headers)
    assert res_list.status_code == 200
    mods = res_list.json()
    assert len(mods) == 7

    # Specific module details
    res_mod = client.get("/api/v1/screening/tests/VISUAL_ACUITY", headers=patient_headers)
    assert res_mod.status_code == 200
    assert res_mod.json()["test_type"] == "VISUAL_ACUITY"

    # Non-existent module
    res_404 = client.get("/api/v1/screening/tests/NON_EXISTENT", headers=patient_headers)
    assert res_404.status_code == 404


# =============================================================================
# 2. Calibration Subsystem & IDOR Guardrails
# =============================================================================


def test_calibration_submission_and_retrieval(
    client: TestClient, consented_session, patient_headers, other_patient_headers
):
    """Display calibration computes PPI and enforces session ownership."""
    # Submit calibration with credit card pixel width (337px -> ~100 PPI)
    payload = {
        "device_category": "DESKTOP",
        "screen_width_px": 1920,
        "screen_height_px": 1080,
        "device_pixel_ratio": 1.0,
        "calibration_method": "STANDARD_CARD",
        "reported_card_width_px": 337.0,
        "target_viewing_distance_cm": 60.0,
        "user_confirmed_distance": True,
        "calibration_notes": "Calibrated with standard credit card.",
    }
    res = client.post(
        f"/api/v1/screening/sessions/{consented_session.id}/calibration",
        json=payload,
        headers=patient_headers,
    )
    assert res.status_code == 200
    calib = res.json()
    assert calib["calibration_status"] == "SERVER_VERIFIED"
    assert calib["computed_ppi"] is not None
    assert 95.0 <= calib["computed_ppi"] <= 105.0

    # Retrieve calibration
    res_get = client.get(
        f"/api/v1/screening/sessions/{consented_session.id}/calibration",
        headers=patient_headers,
    )
    assert res_get.status_code == 200
    assert res_get.json()["computed_ppi"] == calib["computed_ppi"]

    # IDOR check: another patient cannot access or overwrite
    res_idor = client.get(
        f"/api/v1/screening/sessions/{consented_session.id}/calibration",
        headers=other_patient_headers,
    )
    assert res_idor.status_code == 403


# =============================================================================
# 3. Session Start & Consent Enforcement
# =============================================================================


def test_session_start_requires_consent(
    client: TestClient, db_session, patient_user, patient_headers
):
    """Starting a screening session requires active informed consent."""
    # Session without active consent
    consent = ScreeningConsent(
        user_id=patient_user.id,
        consent_version="1.0.0",
        consent_text_hash="hash",
        is_active=False,
    )
    db_session.add(consent)
    db_session.commit()

    sess = ScreeningSession(
        user_id=patient_user.id,
        consent_id=consent.id,
        status="in_progress",
    )
    db_session.add(sess)
    db_session.commit()

    res = client.post(
        f"/api/v1/screening/sessions/{sess.id}/start",
        headers=patient_headers,
    )
    assert res.status_code == 403
    assert res.json()["error"]["code"] == "CONSENT_REQUIRED"


def test_session_start_success(client: TestClient, consented_session, patient_headers):
    """Session start initiates multi-module workflow."""
    res = client.post(
        f"/api/v1/screening/sessions/{consented_session.id}/start",
        headers=patient_headers,
    )
    assert res.status_code == 200
    data = res.json()
    assert data["id"] == str(consented_session.id)
    assert data["status"] == "in_progress"


# =============================================================================
# 4. Interactive Screening Journey across all 7 modules
# =============================================================================


def test_all_7_modules_journey(
    client: TestClient, db_session, consented_session, patient_headers, patient_user
):
    """Executes a full interactive screening journey covering all 7 modules end-to-end."""
    session_id = str(consented_session.id)

    # 0. Calibration setup
    res_cal = client.post(
        f"/api/v1/screening/sessions/{session_id}/calibration",
        json={
            "device_category": "DESKTOP",
            "screen_width_px": 1920,
            "screen_height_px": 1080,
            "device_pixel_ratio": 1.0,
            "calibration_method": "STANDARD_CARD",
            "reported_card_width_px": 337.0,
            "target_viewing_distance_cm": 60.0,
            "user_confirmed_distance": True,
        },
        headers=patient_headers,
    )
    assert res_cal.status_code == 200

    # 1. Module: VISUAL_ACUITY
    res_va = client.post(
        f"/api/v1/screening/sessions/{session_id}/tests/VISUAL_ACUITY/start",
        json={"eye": "OD", "viewing_condition": "WITH_GLASSES"},
        headers=patient_headers,
    )
    assert res_va.status_code == 201
    va_ch = res_va.json()
    assert va_ch["test_type"] == "VISUAL_ACUITY"
    assert "_expected_answer" not in va_ch["stimulus_content"]
    va_test_id = va_ch["test_id"]

    # Verify /next endpoint returns current challenge
    res_next = client.get(f"/api/v1/screening/tests/{va_test_id}/next", headers=patient_headers)
    assert res_next.status_code == 200
    assert res_next.json()["stimulus_id"] == va_ch["stimulus_id"]

    # Submit 5 steps of Visual Acuity
    for step in range(5):
        instance = db_session.get(ScreeningTestInstance, uuid.UUID(va_test_id))
        exp = OnlineScreeningService.get_expected_answer(instance, step_index=step)
        sub_res = client.post(
            f"/api/v1/screening/tests/{va_test_id}/responses",
            json={
                "step_index": step,
                "stimulus_id": f"VA_{step}",
                "user_response": exp,
                "response_time_ms": 420,
            },
            headers=patient_headers,
        )
        assert sub_res.status_code == 200
        if step == 4:
            assert sub_res.json()["is_completed"] is True
            assert sub_res.json()["result_summary"]["classification"] == "NO_CONCERN_REPORTED"

    # 2. Module: ASTIGMATISM
    res_astig = client.post(
        f"/api/v1/screening/sessions/{session_id}/tests/ASTIGMATISM/start",
        json={"eye": "OD"},
        headers=patient_headers,
    )
    assert res_astig.status_code == 201
    astig_id = res_astig.json()["test_id"]
    sub_astig = client.post(
        f"/api/v1/screening/tests/{astig_id}/responses",
        json={
            "step_index": 0,
            "stimulus_id": "ASTIG_1",
            "user_response": "ALL_LINES_UNIFORM",
        },
        headers=patient_headers,
    )
    assert sub_astig.status_code == 200
    assert sub_astig.json()["is_completed"] is True

    # 3. Module: CONTRAST_SENSITIVITY
    res_cs = client.post(
        f"/api/v1/screening/sessions/{session_id}/tests/CONTRAST_SENSITIVITY/start",
        json={"eye": "OU"},
        headers=patient_headers,
    )
    assert res_cs.status_code == 201
    cs_id = res_cs.json()["test_id"]
    for step in range(3):
        instance = db_session.get(ScreeningTestInstance, uuid.UUID(cs_id))
        exp = OnlineScreeningService.get_expected_answer(instance, step_index=step)
        sub_cs = client.post(
            f"/api/v1/screening/tests/{cs_id}/responses",
            json={"step_index": step, "stimulus_id": f"CS_{step}", "user_response": exp},
            headers=patient_headers,
        )
        assert sub_cs.status_code == 200

    # 4. Module: NEAR_VISION_READING
    res_nv = client.post(
        f"/api/v1/screening/sessions/{session_id}/tests/NEAR_VISION_READING/start",
        json={"eye": "OU"},
        headers=patient_headers,
    )
    assert res_nv.status_code == 201
    nv_id = res_nv.json()["test_id"]
    for step in range(3):
        sub_nv = client.post(
            f"/api/v1/screening/tests/{nv_id}/responses",
            json={
                "step_index": step,
                "stimulus_id": f"NV_{step}",
                "user_response": "CAN_READ_EASILY",
            },
            headers=patient_headers,
        )
        assert sub_nv.status_code == 200

    # 5. Module: NEAR_VISION_DUOCHROME
    res_duo = client.post(
        f"/api/v1/screening/sessions/{session_id}/tests/NEAR_VISION_DUOCHROME/start",
        json={"eye": "OU"},
        headers=patient_headers,
    )
    assert res_duo.status_code == 201
    duo_id = res_duo.json()["test_id"]
    sub_duo = client.post(
        f"/api/v1/screening/tests/{duo_id}/responses",
        json={
            "step_index": 0,
            "stimulus_id": "DUO_1",
            "user_response": "BOTH_EQUALLY_CLEAR",
        },
        headers=patient_headers,
    )
    assert sub_duo.status_code == 200
    assert sub_duo.json()["is_completed"] is True

    # 6. Module: COLOR_VISION
    res_color = client.post(
        f"/api/v1/screening/sessions/{session_id}/tests/COLOR_VISION/start",
        json={"eye": "OU"},
        headers=patient_headers,
    )
    assert res_color.status_code == 201
    color_id = res_color.json()["test_id"]
    for step in range(6):
        instance = db_session.get(ScreeningTestInstance, uuid.UUID(color_id))
        exp = OnlineScreeningService.get_expected_answer(instance, step_index=step)
        sub_col = client.post(
            f"/api/v1/screening/tests/{color_id}/responses",
            json={"step_index": step, "stimulus_id": f"COL_{step}", "user_response": exp},
            headers=patient_headers,
        )
        assert sub_col.status_code == 200

    # 7. Module: CENTRAL_VISION_AMSLER
    res_amsler = client.post(
        f"/api/v1/screening/sessions/{session_id}/tests/CENTRAL_VISION_AMSLER/start",
        json={"eye": "OD"},
        headers=patient_headers,
    )
    assert res_amsler.status_code == 201
    amsler_id = res_amsler.json()["test_id"]
    answers = ["YES_ALL_CORNERS_VISIBLE", "NO_ALL_LINES_STRAIGHT", "NO_UNIFORM_GRID"]
    for step, ans in enumerate(answers):
        sub_ams = client.post(
            f"/api/v1/screening/tests/{amsler_id}/responses",
            json={"step_index": step, "stimulus_id": f"AMS_{step}", "user_response": ans},
            headers=patient_headers,
        )
        assert sub_ams.status_code == 200

    # Verify individual test result endpoint
    res_res = client.get(f"/api/v1/screening/tests/{amsler_id}/result", headers=patient_headers)
    assert res_res.status_code == 200
    assert res_res.json()["status"] == "COMPLETED"
    assert "clinical_disclaimer" in res_res.json()

    # Generate and fetch final screening report
    res_rep = client.get(f"/api/v1/screening/sessions/{session_id}/report", headers=patient_headers)
    assert res_rep.status_code == 200
    report = res_rep.json()
    assert report["report_number"].startswith("OPT-REP-")
    assert report["completed_tests_count"] == 7
    assert report["overall_classification"] == "NO_CONCERN_REPORTED"
    assert report["professional_referral_indicated"] is False
    assert "non-diagnostic" in report["clinical_disclaimer"].lower()


# =============================================================================
# 5. Cancellation & Error Handling
# =============================================================================


def test_test_cancellation(client: TestClient, consented_session, patient_headers):
    """A test instance can be cancelled by the patient."""
    res_start = client.post(
        f"/api/v1/screening/sessions/{consented_session.id}/tests/VISUAL_ACUITY/start",
        json={"eye": "OD"},
        headers=patient_headers,
    )
    assert res_start.status_code == 201
    test_id = res_start.json()["test_id"]

    # Cancel test
    res_cancel = client.post(
        f"/api/v1/screening/tests/{test_id}/cancel",
        json={"reason": "User interrupted test"},
        headers=patient_headers,
    )
    assert res_cancel.status_code == 200
    assert res_cancel.json()["status"] == "CANCELLED"

    # Subsequent submission to cancelled test rejected
    res_sub = client.post(
        f"/api/v1/screening/tests/{test_id}/responses",
        json={"step_index": 0, "stimulus_id": "STIM_1", "user_response": "UP"},
        headers=patient_headers,
    )
    assert res_sub.status_code == 400


# =============================================================================
# 6. Report Retrieval & RBAC Protection
# =============================================================================


def test_report_rbac_and_idor(
    client: TestClient,
    consented_session,
    patient_headers,
    other_patient_headers,
    optometrist_headers,
    shopkeeper_headers,
):
    """
    Final Screening Report RBAC:
    - Session owner (patient): ALLOWED
    - Optometrist: ALLOWED
    - Unrelated patient: FORBIDDEN (403)
    - Shopkeeper: FORBIDDEN (403)
    """
    session_id = str(consented_session.id)

    # Generate report
    res_rep = client.get(f"/api/v1/screening/sessions/{session_id}/report", headers=patient_headers)
    assert res_rep.status_code == 200
    report_id = res_rep.json()["report_id"]

    # Fetch by report ID - Patient Owner
    res_own = client.get(f"/api/v1/screening/reports/{report_id}", headers=patient_headers)
    assert res_own.status_code == 200

    # Fetch by report ID - Optometrist
    res_opt = client.get(f"/api/v1/screening/reports/{report_id}", headers=optometrist_headers)
    assert res_opt.status_code == 200

    # Fetch by report ID - Another patient (IDOR)
    res_other = client.get(f"/api/v1/screening/reports/{report_id}", headers=other_patient_headers)
    assert res_other.status_code == 403

    # Fetch by report ID - Shopkeeper (Forbidden from clinical screening reports)
    res_shop = client.get(f"/api/v1/screening/reports/{report_id}", headers=shopkeeper_headers)
    assert res_shop.status_code == 403


# =============================================================================
# 7. Screening History Endpoint
# =============================================================================


def test_screening_history_listing(client: TestClient, consented_session, patient_headers):
    """Lists completed screening history with report links."""
    # Complete report
    client.get(
        f"/api/v1/screening/sessions/{consented_session.id}/report",
        headers=patient_headers,
    )

    # Fetch history
    res_hist = client.get("/api/v1/screening/history", headers=patient_headers)
    assert res_hist.status_code == 200
    hist_data = res_hist.json()
    assert hist_data["total"] >= 1
    assert any(item["session_id"] == str(consented_session.id) for item in hist_data["items"])

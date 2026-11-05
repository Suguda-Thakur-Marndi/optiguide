"""Unit tests for the Complete Online Vision Screening Platform Service."""

import uuid

import pytest
from sqlalchemy.orm import Session

from app.core.exceptions import (
    EntityNotFoundException,
    InvalidSessionTransitionException,
    ValidationException,
)
from app.models.online_screening import ScreeningTestInstance
from app.models.screening_consent import ScreeningConsent
from app.models.screening_session import ScreeningSession
from app.models.user import User
from app.schemas.online_screening import (
    CalibrationSubmitRequest,
    TestCancelRequest,
    TestResponseSubmitRequest,
    TestStartRequest,
)
from app.services.online_screening_service import (
    CLINICAL_DISCLAIMER_TEXT,
    MODULE_SEQUENCE_ORDER,
    OnlineScreeningService,
)


def _setup_user_with_consent_and_session(db: Session) -> tuple[User, ScreeningSession]:
    """Helper to provision an active patient, informed consent, and active screening session."""
    user = User(
        id=uuid.uuid4(),
        email=f"patient_{uuid.uuid4().hex[:8]}@optiguide.test",
        hashed_password="argon2_fake_hash",
        full_name="Screening Test Patient",
        role="patient",
        is_active=True,
    )
    db.add(user)
    db.flush()

    consent = ScreeningConsent(
        id=uuid.uuid4(),
        user_id=user.id,
        consent_version="v1.0",
        consent_text_hash="a" * 64,
        is_active=True,
    )
    db.add(consent)
    db.flush()

    session = ScreeningSession(
        id=uuid.uuid4(),
        user_id=user.id,
        consent_id=consent.id,
        status="in_progress",
    )
    db.add(session)
    db.commit()
    db.refresh(session)
    return user, session


def test_platform_configuration_multilingual():
    """Platform configuration must return all 7 modules with multilingual copy (en, hi, or)."""
    for lang in ["en", "hi", "or"]:
        config = OnlineScreeningService.get_platform_configuration(lang=lang)
        assert len(config.available_modules) == 7
        assert config.default_test_sequence == MODULE_SEQUENCE_ORDER
        assert CLINICAL_DISCLAIMER_TEXT in config.clinical_notice

        # Verify all module definitions exist
        types = [m.test_type for m in config.available_modules]
        for expected in MODULE_SEQUENCE_ORDER:
            assert expected in types


def test_get_module_definition_success_and_not_found():
    """Specific module definitions can be retrieved; invalid types raise EntityNotFoundException."""
    meta = OnlineScreeningService.get_module_definition("ASTIGMATISM", lang="en")
    assert meta.test_type == "ASTIGMATISM"
    assert meta.target_viewing_distance_cm == 60.0

    with pytest.raises(EntityNotFoundException):
        OnlineScreeningService.get_module_definition("INVALID_MODULE")


def test_record_and_get_calibration(db_session: Session):
    """Submitting physical card calibration computes PPI and evaluates verification status."""
    user, session = _setup_user_with_consent_and_session(db_session)

    # Valid standard card width: e.g. 337 pixels / 3.37 inches = 100.0 PPI
    req = CalibrationSubmitRequest(
        device_category="LAPTOP",
        screen_width_px=1920,
        screen_height_px=1080,
        device_pixel_ratio=1.0,
        calibration_method="STANDARD_CARD",
        reported_card_width_px=337.0,
        target_viewing_distance_cm=40.0,
        user_confirmed_distance=True,
    )
    calib = OnlineScreeningService.record_calibration(db_session, user, session.id, req)
    assert calib.calibration_status == "SERVER_VERIFIED"
    assert calib.computed_ppi == 100.0
    assert calib.user_confirmed_distance is True

    # Retrieve calibration
    retrieved = OnlineScreeningService.get_calibration(db_session, user, session.id)
    assert retrieved.id == calib.id
    assert retrieved.computed_ppi == 100.0


def test_uncalibrated_fallback(db_session: Session):
    """Missing or out-of-bounds calibration data defaults to UNCALIBRATED status."""
    user, session = _setup_user_with_consent_and_session(db_session)

    req = CalibrationSubmitRequest(
        device_category="DESKTOP",
        calibration_method="DEFAULT_UNVERIFIED",
        reported_card_width_px=None,
        target_viewing_distance_cm=300.0,
        user_confirmed_distance=False,
    )
    calib = OnlineScreeningService.record_calibration(db_session, user, session.id, req)
    assert calib.calibration_status == "UNCALIBRATED"
    assert calib.computed_ppi is None


def test_module_1_visual_acuity_workflow(db_session: Session):
    """Module 1: Visual Acuity staircase progression and server-side response scoring."""
    user, session = _setup_user_with_consent_and_session(db_session)

    # 1. Start test
    ch0 = OnlineScreeningService.start_test_instance(
        db_session, user, session.id, "VISUAL_ACUITY", TestStartRequest(eye="OD")
    )
    assert ch0.test_type == "VISUAL_ACUITY"
    assert ch0.step_index == 0
    assert ch0.total_steps == 5
    # Verify expected answer is not leaked in presentation options
    assert "_expected_answer" not in ch0.stimulus_content

    # 2. Submit responses through all 5 levels correctly
    test_id = ch0.test_id
    current_ch = ch0
    for step in range(5):
        # Determine the hidden expected answer directly for unit test simulation
        hidden_expected = OnlineScreeningService.get_expected_answer(
            db_session.get(ScreeningTestInstance, test_id),
            step_index=step,
        )

        step_res = OnlineScreeningService.submit_test_response(
            db_session,
            user,
            test_id,
            TestResponseSubmitRequest(
                step_index=step,
                stimulus_id=current_ch.stimulus_id,
                user_response=hidden_expected,
            ),
        )
        if step < 4:
            assert step_res.is_completed is False
            assert step_res.next_challenge is not None
            current_ch = step_res.next_challenge
        else:
            assert step_res.is_completed is True
            assert step_res.result_summary is not None
            assert step_res.result_summary["classification"] == "NO_CONCERN_REPORTED"
            assert step_res.result_summary["metrics"]["final_snellen"] == "20/20"


def test_module_2_astigmatism_workflow(db_session: Session):
    """Module 2: Astigmatism clock dial evaluation for uniform vs darker/sharper lines."""
    user, session = _setup_user_with_consent_and_session(db_session)

    # Case A: Uniform lines -> NO_CONCERN_REPORTED
    ch = OnlineScreeningService.start_test_instance(
        db_session, user, session.id, "ASTIGMATISM", TestStartRequest(eye="OD")
    )
    res_a = OnlineScreeningService.submit_test_response(
        db_session,
        user,
        ch.test_id,
        TestResponseSubmitRequest(
            step_index=0,
            stimulus_id=ch.stimulus_id,
            user_response="ALL_LINES_UNIFORM",
        ),
    )
    assert res_a.is_completed is True
    assert res_a.result_summary["classification"] == "NO_CONCERN_REPORTED"

    # Case B: Certain lines darker -> OBSERVATION_REQUIRES_FOLLOW_UP
    ch2 = OnlineScreeningService.start_test_instance(
        db_session, user, session.id, "ASTIGMATISM", TestStartRequest(eye="OS")
    )
    res_b = OnlineScreeningService.submit_test_response(
        db_session,
        user,
        ch2.test_id,
        TestResponseSubmitRequest(
            step_index=0,
            stimulus_id=ch2.stimulus_id,
            user_response="SOME_LINES_DARKER",
        ),
    )
    assert res_b.is_completed is True
    assert res_b.result_summary["classification"] == "OBSERVATION_REQUIRES_FOLLOW_UP"


def test_module_3_contrast_sensitivity_workflow(db_session: Session):
    """Module 3: Contrast sensitivity evaluation across low-contrast triplet challenges."""
    user, session = _setup_user_with_consent_and_session(db_session)

    ch = OnlineScreeningService.start_test_instance(
        db_session, user, session.id, "CONTRAST_SENSITIVITY", TestStartRequest(eye="OU")
    )
    assert ch.total_steps == 3

    # Answer all steps correctly
    test_id = ch.test_id
    step_res = None
    for step in range(3):
        exp = OnlineScreeningService.get_expected_answer(
            db_session.get(ScreeningTestInstance, test_id), step_index=step
        )

        step_res = OnlineScreeningService.submit_test_response(
            db_session,
            user,
            test_id,
            TestResponseSubmitRequest(
                step_index=step,
                stimulus_id=f"CS_{step}",
                user_response=exp,
            ),
        )

    assert step_res.is_completed is True
    assert step_res.result_summary["classification"] == "NO_CONCERN_REPORTED"


def test_module_4_near_vision_reading_workflow(db_session: Session):
    """Module 4: Near vision reading acuity evaluation at 40 cm."""
    user, session = _setup_user_with_consent_and_session(db_session)

    ch = OnlineScreeningService.start_test_instance(
        db_session, user, session.id, "NEAR_VISION_READING", TestStartRequest(eye="OU")
    )
    assert ch.total_steps == 3

    test_id = ch.test_id
    step_res = None
    for step in range(3):
        step_res = OnlineScreeningService.submit_test_response(
            db_session,
            user,
            test_id,
            TestResponseSubmitRequest(
                step_index=step,
                stimulus_id=f"NV_{step}",
                user_response="CAN_READ_EASILY",
            ),
        )

    assert step_res.is_completed is True
    assert step_res.result_summary["classification"] == "NO_CONCERN_REPORTED"


def test_module_5_near_vision_duochrome_workflow(db_session: Session):
    """Module 5: Duochrome red/green background focus comparison."""
    user, session = _setup_user_with_consent_and_session(db_session)

    ch = OnlineScreeningService.start_test_instance(
        db_session, user, session.id, "NEAR_VISION_DUOCHROME", TestStartRequest(eye="OU")
    )
    res = OnlineScreeningService.submit_test_response(
        db_session,
        user,
        ch.test_id,
        TestResponseSubmitRequest(
            step_index=0,
            stimulus_id=ch.stimulus_id,
            user_response="BOTH_EQUALLY_CLEAR",
        ),
    )
    assert res.is_completed is True
    assert res.result_summary["classification"] == "NO_CONCERN_REPORTED"


def test_module_6_color_vision_workflow(db_session: Session):
    """Module 6: Color vision pseudoisochromatic plate screening."""
    user, session = _setup_user_with_consent_and_session(db_session)

    ch = OnlineScreeningService.start_test_instance(
        db_session, user, session.id, "COLOR_VISION", TestStartRequest(eye="OU")
    )
    assert ch.total_steps == 6

    test_id = ch.test_id
    step_res = None
    for step in range(6):
        exp = OnlineScreeningService.get_expected_answer(
            db_session.get(ScreeningTestInstance, test_id), step_index=step
        )

        step_res = OnlineScreeningService.submit_test_response(
            db_session,
            user,
            test_id,
            TestResponseSubmitRequest(
                step_index=step,
                stimulus_id=f"PLATE_{step}",
                user_response=exp,
            ),
        )

    assert step_res.is_completed is True
    assert step_res.result_summary["classification"] == "NO_CONCERN_REPORTED"
    assert step_res.result_summary["metrics"]["correct_plates"] == 6


def test_module_7_central_vision_amsler_workflow(db_session: Session):
    """Module 7: Central vision / Amsler distortion questionnaire."""
    user, session = _setup_user_with_consent_and_session(db_session)

    # Case A: Normal grid perception
    ch_a = OnlineScreeningService.start_test_instance(
        db_session, user, session.id, "CENTRAL_VISION_AMSLER", TestStartRequest(eye="OD")
    )
    assert ch_a.total_steps == 3
    test_id_a = ch_a.test_id

    OnlineScreeningService.submit_test_response(
        db_session,
        user,
        test_id_a,
        TestResponseSubmitRequest(
            step_index=0, stimulus_id="A1", user_response="YES_ALL_CORNERS_VISIBLE"
        ),
    )
    OnlineScreeningService.submit_test_response(
        db_session,
        user,
        test_id_a,
        TestResponseSubmitRequest(
            step_index=1, stimulus_id="A2", user_response="NO_ALL_LINES_STRAIGHT"
        ),
    )
    res_a = OnlineScreeningService.submit_test_response(
        db_session,
        user,
        test_id_a,
        TestResponseSubmitRequest(step_index=2, stimulus_id="A3", user_response="NO_UNIFORM_GRID"),
    )
    assert res_a.is_completed is True
    assert res_a.result_summary["classification"] == "NO_CONCERN_REPORTED"

    # Case B: Metamorphopsia / Wavy lines reported -> Flag for urgent clinical evaluation
    ch_b = OnlineScreeningService.start_test_instance(
        db_session, user, session.id, "CENTRAL_VISION_AMSLER", TestStartRequest(eye="OS")
    )
    test_id_b = ch_b.test_id
    OnlineScreeningService.submit_test_response(
        db_session,
        user,
        test_id_b,
        TestResponseSubmitRequest(
            step_index=0, stimulus_id="B1", user_response="YES_ALL_CORNERS_VISIBLE"
        ),
    )
    OnlineScreeningService.submit_test_response(
        db_session,
        user,
        test_id_b,
        TestResponseSubmitRequest(
            step_index=1, stimulus_id="B2", user_response="YES_WAVY_OR_DISTORTED"
        ),
    )
    res_b = OnlineScreeningService.submit_test_response(
        db_session,
        user,
        test_id_b,
        TestResponseSubmitRequest(step_index=2, stimulus_id="B3", user_response="NO_UNIFORM_GRID"),
    )
    assert res_b.is_completed is True
    assert res_b.result_summary["classification"] == "OBSERVATION_REQUIRES_FOLLOW_UP"
    assert "URGENT" in res_b.result_summary["observation"]


def test_state_machine_and_sequence_enforcement(db_session: Session):
    """Enforces that out-of-order submissions or submissions to completed tests are rejected."""
    user, session = _setup_user_with_consent_and_session(db_session)

    ch = OnlineScreeningService.start_test_instance(
        db_session, user, session.id, "ASTIGMATISM", TestStartRequest(eye="OD")
    )

    # Attempting to submit step 5 when current_step is 0 must fail
    with pytest.raises(ValidationException, match="Out of sequence submission"):
        OnlineScreeningService.submit_test_response(
            db_session,
            user,
            ch.test_id,
            TestResponseSubmitRequest(step_index=5, stimulus_id="X", user_response="Y"),
        )

    # Cancel test
    OnlineScreeningService.cancel_test_instance(
        db_session, user, ch.test_id, TestCancelRequest(reason="User quit")
    )

    # Submitting to cancelled test must fail
    with pytest.raises(InvalidSessionTransitionException, match="Cannot submit response"):
        OnlineScreeningService.submit_test_response(
            db_session,
            user,
            ch.test_id,
            TestResponseSubmitRequest(step_index=0, stimulus_id="X", user_response="Y"),
        )


def test_final_screening_report_generation(db_session: Session):
    """Compiles consolidated report, flags referrals honestly, and includes clinical disclaimers."""
    user, session = _setup_user_with_consent_and_session(db_session)

    # Complete 1 normal test and 1 abnormal test
    ch1 = OnlineScreeningService.start_test_instance(
        db_session, user, session.id, "ASTIGMATISM", TestStartRequest(eye="OD")
    )
    OnlineScreeningService.submit_test_response(
        db_session,
        user,
        ch1.test_id,
        TestResponseSubmitRequest(step_index=0, stimulus_id="A", user_response="ALL_LINES_UNIFORM"),
    )

    ch2 = OnlineScreeningService.start_test_instance(
        db_session, user, session.id, "CENTRAL_VISION_AMSLER", TestStartRequest(eye="OS")
    )
    for s, ans in [
        (0, "YES_ALL_CORNERS_VISIBLE"),
        (1, "YES_WAVY_OR_DISTORTED"),
        (2, "NO_UNIFORM_GRID"),
    ]:
        OnlineScreeningService.submit_test_response(
            db_session,
            user,
            ch2.test_id,
            TestResponseSubmitRequest(step_index=s, stimulus_id=f"A_{s}", user_response=ans),
        )

    # Generate final report
    report = OnlineScreeningService.generate_final_report(db_session, user, session.id)
    assert report.session_id == session.id
    assert report.status == "COMPLETED"
    assert report.overall_classification == "OBSERVATION_REQUIRES_FOLLOW_UP"
    assert report.professional_referral_indicated is True
    assert CLINICAL_DISCLAIMER_TEXT in report.clinical_disclaimer
    assert "OPT-REP-" in report.report_number
    assert report.completed_tests_count == 2
    assert "astigmatism" in report.results
    assert "central_vision_amsler" in report.results


def test_history_listing(db_session: Session):
    """Lists historical screening sessions with report numbers."""
    user, session = _setup_user_with_consent_and_session(db_session)
    OnlineScreeningService.generate_final_report(db_session, user, session.id)

    history = OnlineScreeningService.list_user_history(db_session, user)
    assert history.total >= 1
    found = next((item for item in history.items if item.session_id == session.id), None)
    assert found is not None
    assert found.report_number is not None

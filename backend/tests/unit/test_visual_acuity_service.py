import pytest

from app.core.exceptions import ValidationException
from app.services.visual_acuity_service import AcuityEye, AssessmentType, VisualAcuityService


def test_eye_canonicalization():
    """Verifies that eye abbreviations and casings map to standard lowercase strings."""
    assert VisualAcuityService.canonicalize_eye("right") == AcuityEye.RIGHT.value
    assert VisualAcuityService.canonicalize_eye("OD") == AcuityEye.RIGHT.value
    assert VisualAcuityService.canonicalize_eye("od ") == AcuityEye.RIGHT.value
    assert VisualAcuityService.canonicalize_eye("left") == AcuityEye.LEFT.value
    assert VisualAcuityService.canonicalize_eye("OS") == AcuityEye.LEFT.value
    assert VisualAcuityService.canonicalize_eye("both") == AcuityEye.BOTH.value
    assert VisualAcuityService.canonicalize_eye("OU") == AcuityEye.BOTH.value

    with pytest.raises(ValidationException, match="Invalid test eye"):
        VisualAcuityService.canonicalize_eye("third_eye")

    with pytest.raises(ValidationException, match="Test eye must be specified"):
        VisualAcuityService.canonicalize_eye("")


def test_assessment_type_canonicalization():
    """Verifies assessment type canonicalization to DISTANCE or NEAR."""
    assert VisualAcuityService.canonicalize_assessment_type(None) == AssessmentType.DISTANCE.value
    assert (
        VisualAcuityService.canonicalize_assessment_type("distance")
        == AssessmentType.DISTANCE.value
    )
    assert (
        VisualAcuityService.canonicalize_assessment_type("DISTANCE")
        == AssessmentType.DISTANCE.value
    )
    assert VisualAcuityService.canonicalize_assessment_type("near") == AssessmentType.NEAR.value
    assert VisualAcuityService.canonicalize_assessment_type("NEAR ") == AssessmentType.NEAR.value

    with pytest.raises(ValidationException, match="Invalid assessment type"):
        VisualAcuityService.canonicalize_assessment_type("intermediate")


def test_snellen_parsing_valid():
    """Verifies parsing standard valid Snellen fractions."""
    assert VisualAcuityService.parse_snellen("20/20") == (20, 20)
    assert VisualAcuityService.parse_snellen("20 / 40") == (20, 40)
    assert VisualAcuityService.parse_snellen("6/6") == (6, 6)
    assert VisualAcuityService.parse_snellen("6/12") == (6, 12)


def test_snellen_parsing_invalid():
    """Verifies rejection of malformed or non-positive Snellen notations."""
    invalid_cases = [
        "",
        "invalid",
        "20/",
        "/20",
        "20/20/20",
        "-20/40",
        "20/-40",
        "0/20",
        "20/0",
    ]
    for case in invalid_cases:
        with pytest.raises(ValidationException):
            VisualAcuityService.parse_snellen(case)


def test_optics_conversions_imperial():
    """Verifies clinical standard Imperial Snellen to logMAR and decimal conversions."""
    # 20/20 = logMAR 0.00, decimal 1.00
    assert VisualAcuityService.snellen_to_logmar("20/20") == 0.00
    assert VisualAcuityService.snellen_to_decimal("20/20") == 1.00

    # 20/40 = logMAR 0.30, decimal 0.50
    assert VisualAcuityService.snellen_to_logmar("20/40") == 0.30
    assert VisualAcuityService.snellen_to_decimal("20/40") == 0.50

    # 20/60 = logMAR 0.48, decimal 0.33
    assert VisualAcuityService.snellen_to_logmar("20/60") == 0.48
    assert VisualAcuityService.snellen_to_decimal("20/60") == 0.33

    # 20/100 = logMAR 0.70, decimal 0.20
    assert VisualAcuityService.snellen_to_logmar("20/100") == 0.70
    assert VisualAcuityService.snellen_to_decimal("20/100") == 0.20

    # 20/200 = logMAR 1.00, decimal 0.10
    assert VisualAcuityService.snellen_to_logmar("20/200") == 1.00
    assert VisualAcuityService.snellen_to_decimal("20/200") == 0.10


def test_optics_conversions_metric():
    """Verifies clinical standard Metric Snellen to logMAR and decimal conversions."""
    # 6/6 = logMAR 0.00, decimal 1.00
    assert VisualAcuityService.snellen_to_logmar("6/6") == 0.00
    assert VisualAcuityService.snellen_to_decimal("6/6") == 1.00

    # 6/12 = logMAR 0.30, decimal 0.50
    assert VisualAcuityService.snellen_to_logmar("6/12") == 0.30
    assert VisualAcuityService.snellen_to_decimal("6/12") == 0.50

    # 6/18 = logMAR 0.48, decimal 0.33
    assert VisualAcuityService.snellen_to_logmar("6/18") == 0.48
    assert VisualAcuityService.snellen_to_decimal("6/18") == 0.33

    # 6/60 = logMAR 1.00, decimal 0.10
    assert VisualAcuityService.snellen_to_logmar("6/60") == 1.00
    assert VisualAcuityService.snellen_to_decimal("6/60") == 0.10


def test_reconcile_and_validate_auto_compute():
    """When logMAR and decimal are omitted, they are auto-computed from Snellen."""
    logmar, decimal = VisualAcuityService.reconcile_and_validate("20/40")
    assert logmar == 0.30
    assert decimal == 0.50


def test_reconcile_and_validate_with_agreeing_values():
    """When supplied logMAR and decimal agree within tolerance, validation succeeds."""
    logmar, decimal = VisualAcuityService.reconcile_and_validate(
        snellen_fraction="20/40",
        logmar=0.31,  # within 0.05 of 0.30
        decimal_acuity=0.51,  # within 0.05 of 0.50
    )
    assert logmar == 0.31
    assert decimal == 0.51


def test_reconcile_and_validate_with_conflicting_logmar():
    """When supplied logMAR conflicts with Snellen by > 0.05, ValidationException is raised."""
    with pytest.raises(ValidationException, match="Conflicting visual acuity values"):
        VisualAcuityService.reconcile_and_validate(
            snellen_fraction="20/20",  # logMAR is 0.00
            logmar=0.30,  # contradicts 20/20
        )


def test_reconcile_and_validate_with_conflicting_decimal():
    """When supplied decimal acuity conflicts with Snellen by > 0.05, ValidationException is raised."""
    with pytest.raises(ValidationException, match="Conflicting visual acuity values"):
        VisualAcuityService.reconcile_and_validate(
            snellen_fraction="20/20",  # decimal is 1.00
            decimal_acuity=0.20,
        )


def test_reconcile_and_validate_physiological_range_bounds():
    """Rejects Snellen fractions producing logMAR outside supported clinical boundaries [-0.30, 2.00]."""
    # 20/1 -> logMAR = log10(1/20) = -1.30 (substantially below -0.30)
    with pytest.raises(ValidationException, match="outside supported clinical range"):
        VisualAcuityService.reconcile_and_validate("20/1")

    # 20/3000 -> logMAR = log10(3000/20) = 2.18 (above 2.00)
    with pytest.raises(ValidationException, match="outside supported clinical range"):
        VisualAcuityService.reconcile_and_validate("20/3000")


def test_viewing_geometry_validation():
    """Verifies separate distance and near viewing geometry boundaries."""
    # Distance test geometry [0.3m, 12.0m]
    VisualAcuityService.validate_test_geometry(
        AssessmentType.DISTANCE.value, tested_distance_meters=0.6
    )
    VisualAcuityService.validate_test_geometry(
        AssessmentType.DISTANCE.value, tested_distance_meters=3.0
    )
    VisualAcuityService.validate_test_geometry(
        AssessmentType.DISTANCE.value, tested_distance_meters=6.0
    )

    with pytest.raises(ValidationException, match="positive tested_distance_meters"):
        VisualAcuityService.validate_test_geometry(
            AssessmentType.DISTANCE.value, tested_distance_meters=None
        )

    with pytest.raises(ValidationException, match="outside valid physical screening distance"):
        VisualAcuityService.validate_test_geometry(
            AssessmentType.DISTANCE.value, tested_distance_meters=0.2
        )

    with pytest.raises(ValidationException, match="outside valid physical screening distance"):
        VisualAcuityService.validate_test_geometry(
            AssessmentType.DISTANCE.value, tested_distance_meters=15.0
        )

    # Near test geometry [15cm, 100cm]
    VisualAcuityService.validate_test_geometry(
        AssessmentType.NEAR.value, near_reading_distance_cm=40.0
    )

    with pytest.raises(ValidationException, match="positive near_reading_distance_cm"):
        VisualAcuityService.validate_test_geometry(
            AssessmentType.NEAR.value, near_reading_distance_cm=None
        )

    with pytest.raises(ValidationException, match="outside valid reading distance range"):
        VisualAcuityService.validate_test_geometry(
            AssessmentType.NEAR.value, near_reading_distance_cm=10.0
        )

    with pytest.raises(ValidationException, match="outside valid reading distance range"):
        VisualAcuityService.validate_test_geometry(
            AssessmentType.NEAR.value, near_reading_distance_cm=120.0
        )


def test_calibration_claim_evaluation():
    """Tests that client boolean alone is never trusted without display geometry."""
    # Claiming true without metadata
    is_calib, meta = VisualAcuityService.evaluate_calibration_claim(True, None)
    assert is_calib is False
    assert meta is None

    # Incomplete calibration dict
    is_calib, meta = VisualAcuityService.evaluate_calibration_claim(
        True,
        {"screen_width_px": 1920},
    )
    assert is_calib is False
    assert "UNVERIFIED_CLIENT_CLAIM" in meta

    # Complete calibration dict
    is_calib, meta = VisualAcuityService.evaluate_calibration_claim(
        True,
        {
            "display_dpi": 141.0,
            "screen_width_px": 1920,
            "screen_height_px": 1080,
            "viewing_distance_cm": 60.0,
        },
    )
    assert is_calib is True
    assert "GEOMETRIC_VALIDATION_PASSED" in meta


def test_deterministic_summary_normal_vision():
    """Verifies that normal screening findings produce no referral recommendation."""

    class DummyAssessment:
        def __init__(self, eye, t_type, snellen, logmar):
            self.id = "mock-id"
            self.test_eye = eye
            self.assessment_type = t_type
            self.snellen_fraction = snellen
            self.logmar = logmar
            self.decimal_acuity = 1.0
            self.tested_distance_meters = 0.6
            self.near_reading_label = None
            self.near_reading_distance_cm = None
            self.is_calibrated = True
            self.observations = None
            self.created_at = None

    assessments = [
        DummyAssessment("right", "DISTANCE", "20/20", 0.0),
        DummyAssessment("left", "DISTANCE", "20/20", 0.0),
        DummyAssessment("both", "DISTANCE", "20/20", 0.0),
        DummyAssessment("both", "NEAR", "20/20", 0.0),
    ]

    summary = VisualAcuityService.summarize_acuity_observations(assessments)
    assert summary["referral_recommended"] is False
    assert len(summary["referral_reasons"]) == 0
    assert len(summary["missing_observations"]) == 0
    assert summary["interocular_difference_logmar"] == 0.0
    assert "preliminary functional assessment aid" in summary["clinical_disclaimer"]


def test_deterministic_summary_impaired_and_asymmetry():
    """Verifies referral triggers for reduced acuity and interocular difference."""

    class DummyAssessment:
        def __init__(self, eye, t_type, snellen, logmar):
            self.id = "mock-id"
            self.test_eye = eye
            self.assessment_type = t_type
            self.snellen_fraction = snellen
            self.logmar = logmar
            self.decimal_acuity = 0.33
            self.tested_distance_meters = 0.6
            self.near_reading_label = None
            self.near_reading_distance_cm = None
            self.is_calibrated = False
            self.observations = None
            self.created_at = None

    assessments = [
        DummyAssessment("right", "DISTANCE", "20/20", 0.0),
        DummyAssessment("left", "DISTANCE", "20/60", 0.48),  # >= 0.40 triggers referral
    ]

    summary = VisualAcuityService.summarize_acuity_observations(assessments)
    assert summary["referral_recommended"] is True
    # Should flag reduced acuity in left eye AND interocular difference of 0.48 (>= 0.30)
    assert any(
        "Reduced distance visual acuity in left eye" in r for r in summary["referral_reasons"]
    )
    assert any("Interocular visual acuity asymmetry" in r for r in summary["referral_reasons"])
    # Should detect missing binocular and near observations
    assert any(
        "Binocular (OU) distance visual acuity not assessed" in m
        for m in summary["missing_observations"]
    )
    assert any(
        "Near visual acuity screening was not conducted" in m
        for m in summary["missing_observations"]
    )

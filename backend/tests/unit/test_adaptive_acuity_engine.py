import pytest

from app.core.exceptions import ValidationException
from app.services.adaptive_acuity_engine import (
    AdaptiveAcuityEngine,
    CalibrationTier,
    OptotypeType,
)


def test_calculate_optotype_dimensions_accurate_trig():
    """Verifies that optotype physical sizing uses exact visual angle trigonometry."""
    # 20/20 standard subtends 5 arcmin. At 3 meters:
    # theta = 5 / 60 degrees. H = 2 * 3.0 * tan(theta / 2) ~ 4.363 mm
    height_mm, height_px = AdaptiveAcuityEngine.calculate_optotype_dimensions(
        arcmin=5.0,
        viewing_distance_meters=3.0,
        display_dpi=141.0,
    )
    assert 4.35 <= height_mm <= 4.38
    assert height_px is not None
    assert 23.5 <= height_px <= 25.0


def test_calculate_optotype_dimensions_invalid_inputs():
    """Non-positive distance or arcmin must be rejected."""
    with pytest.raises(ValidationException, match="Viewing distance must be a positive number"):
        AdaptiveAcuityEngine.calculate_optotype_dimensions(arcmin=5.0, viewing_distance_meters=0.0)

    with pytest.raises(ValidationException, match="Visual angle arcmin must be a positive number"):
        AdaptiveAcuityEngine.calculate_optotype_dimensions(arcmin=-1.0, viewing_distance_meters=3.0)


def test_calibration_evaluation_tiers():
    """Tests the 4-tier medical device assurance calibration model."""
    # 1. Uncalibrated
    tier, info = AdaptiveAcuityEngine.evaluate_calibration(None)
    assert tier == CalibrationTier.UNCALIBRATED
    assert info["is_calibrated"] is False

    # 2. Professionally Validated
    tier, info = AdaptiveAcuityEngine.evaluate_calibration({"is_professionally_supervised": True})
    assert tier == CalibrationTier.PROFESSIONALLY_VALIDATED
    assert info["is_calibrated"] is True

    # 3. Client Reported (unverified method)
    tier, info = AdaptiveAcuityEngine.evaluate_calibration(
        {
            "display_dpi": 141.0,
            "screen_width_px": 1920,
            "screen_height_px": 1080,
            "viewing_distance_cm": 300.0,
            "calibration_method": "client_guess",
        }
    )
    assert tier == CalibrationTier.CLIENT_REPORTED
    assert info["is_calibrated"] is False

    # 4. Server Verified (plausibility passed with standard reference card calibration)
    tier, info = AdaptiveAcuityEngine.evaluate_calibration(
        {
            "display_dpi": 141.0,
            "screen_width_px": 1920,
            "screen_height_px": 1080,
            "viewing_distance_cm": 300.0,
            "calibration_method": "reference_card",
        }
    )
    assert tier == CalibrationTier.SERVER_VERIFIED
    assert info["is_calibrated"] is True


def test_optotype_generation_tumbling_e_no_immediate_repeat():
    """Tumbling E generator returns valid directions and avoids repeating previous optotype."""
    seen_directions = set()
    prev = None

    for _ in range(50):
        symbol, expected, choices = AdaptiveAcuityEngine.generate_next_optotype(
            optotype_type=OptotypeType.TUMBLING_E.value,
            previous_optotype=prev,
        )
        assert expected in AdaptiveAcuityEngine.TUMBLING_E_DIRECTIONS
        assert symbol == f"E_{expected}"
        assert set(choices) == set(AdaptiveAcuityEngine.TUMBLING_E_DIRECTIONS)
        if prev:
            assert expected != prev, "Generated identical optotype consecutively"
        prev = expected
        seen_directions.add(expected)

    # Over 50 draws, all 4 directions should appear
    assert len(seen_directions) == 4


def test_optotype_generation_sloan_no_immediate_repeat():
    """Sloan generator returns standardized letters and avoids repeating previous letter."""
    seen_letters = set()
    prev = None

    for _ in range(50):
        symbol, expected, choices = AdaptiveAcuityEngine.generate_next_optotype(
            optotype_type=OptotypeType.SLOAN.value,
            previous_optotype=prev,
        )
        assert expected in AdaptiveAcuityEngine.SLOAN_LETTERS
        assert symbol == expected
        assert set(choices) == set(AdaptiveAcuityEngine.SLOAN_LETTERS)
        if prev:
            assert expected != prev
        prev = expected
        seen_letters.add(expected)

    assert len(seen_letters) >= 5


def test_adaptive_level_progress_ats_3_of_4_rule():
    """Evaluates 3-of-4 rule pass, fail, and continue states."""
    # 3 correct out of 3 -> PASS immediately
    assert AdaptiveAcuityEngine.evaluate_level_progress([True, True, True]) == "PASS"

    # 3 correct out of 4 -> PASS
    assert AdaptiveAcuityEngine.evaluate_level_progress([True, False, True, True]) == "PASS"

    # 2 incorrect out of 2 -> FAIL immediately (cannot reach 3 of 4)
    assert AdaptiveAcuityEngine.evaluate_level_progress([False, False]) == "FAIL"

    # 2 incorrect out of 3 -> FAIL
    assert AdaptiveAcuityEngine.evaluate_level_progress([True, False, False]) == "FAIL"

    # In progress (needs more presentations)
    assert AdaptiveAcuityEngine.evaluate_level_progress([True]) == "CONTINUE"
    assert AdaptiveAcuityEngine.evaluate_level_progress([True, False]) == "CONTINUE"


def test_determine_next_action_progression_and_stopping():
    """Verifies level advancement, step-down, and stopping criteria."""
    # Passing Level 6 advances to Level 7
    action, next_lvl, resolved = AdaptiveAcuityEngine.determine_next_action(
        current_level=6,
        level_result="PASS",
        passed_levels=set(),
    )
    assert action == "NEXT_CHALLENGE"
    assert next_lvl == 7
    assert resolved is None

    # Passing Level 10 (ceiling) stops and completes test
    action, next_lvl, resolved = AdaptiveAcuityEngine.determine_next_action(
        current_level=10,
        level_result="PASS",
        passed_levels={6, 7, 8, 9},
    )
    assert action == "STOP_COMPLETE"
    assert resolved == 10

    # Failing Level 8 when Level 7 was previously passed stops test with Level 7 as threshold
    action, next_lvl, resolved = AdaptiveAcuityEngine.determine_next_action(
        current_level=8,
        level_result="FAIL",
        passed_levels={6, 7},
    )
    assert action == "STOP_COMPLETE"
    assert resolved == 7

    # Failing starting Level 6 with no prior passes steps down to lower level
    action, next_lvl, resolved = AdaptiveAcuityEngine.determine_next_action(
        current_level=6,
        level_result="FAIL",
        passed_levels=set(),
    )
    assert action == "NEXT_CHALLENGE"
    assert next_lvl == 4

    # Failing Level 0 (largest optotype) with no prior passes stops test (< 20/200)
    action, next_lvl, resolved = AdaptiveAcuityEngine.determine_next_action(
        current_level=0,
        level_result="FAIL",
        passed_levels=set(),
    )
    assert action == "STOP_COMPLETE"
    assert resolved is None

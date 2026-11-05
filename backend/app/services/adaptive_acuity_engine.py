import math
import random
from dataclasses import dataclass
from enum import Enum
from typing import Any, ClassVar

from app.core.exceptions import ValidationException


class CalibrationTier(str, Enum):
    UNCALIBRATED = "UNCALIBRATED"
    CLIENT_REPORTED = "CLIENT_REPORTED"
    SERVER_VERIFIED = "SERVER_VERIFIED"
    PROFESSIONALLY_VALIDATED = "PROFESSIONALLY_VALIDATED"


class OptotypeType(str, Enum):
    TUMBLING_E = "TUMBLING_E"
    SLOAN = "SLOAN"
    LANDOLT_C = "LANDOLT_C"


class AdaptiveTestStatus(str, Enum):
    IN_PROGRESS = "IN_PROGRESS"
    COMPLETED = "COMPLETED"
    CANCELLED = "CANCELLED"
    EXPIRED = "EXPIRED"


@dataclass(frozen=True)
class AcuityLevelSpec:
    level: int
    snellen: str
    logmar: float
    decimal_acuity: float
    arcmin: float
    description: str


class AdaptiveAcuityEngine:
    """
    Core mathematical, geometric, and protocol engine for interactive adaptive visual acuity screening.
    Implements the ISO 8596 / ATS (Amblyopia Treatment Study) 3-of-4 staircase screening protocol.
    """

    PROTOCOL_VERSION: str = "ISO8596_ATS_V1"
    CLINICAL_DISCLAIMER: str = (
        "OptiGuide adaptive visual acuity screening is a preliminary functional assessment aid, "
        "not a certified medical diagnostic examination. It does not diagnose ocular conditions, "
        "refractive errors (myopia, hyperopia, astigmatism), or amblyopia, and cannot generate "
        "optical prescriptions. Screenings must be confirmed by a licensed eye care professional."
    )
    CLINICAL_VALIDATION_STATUS: str = "TECHNICAL FRAMEWORK IMPLEMENTED — PRELIMINARY SCREENING (NOT CLINICALLY VALIDATED AS AN INDEPENDENT MEDICAL DIAGNOSTIC DEVICE)"

    # ATS 3-of-4 Rule
    MAX_PRESENTATIONS_PER_LEVEL: int = 4
    REQUIRED_CORRECT_TO_PASS: int = 3
    MAX_FAILS_BEFORE_LEVEL_LOSS: int = 2

    # Sloan 10-Letter Standardized Set (NAS-NRC / ISO 8596)
    SLOAN_LETTERS: ClassVar[list[str]] = [
        "C",
        "D",
        "E",
        "F",
        "L",
        "N",
        "O",
        "P",
        "T",
        "Z",
    ]

    # Tumbling E Directional Set
    TUMBLING_E_DIRECTIONS: ClassVar[list[str]] = ["UP", "DOWN", "LEFT", "RIGHT"]

    # Landolt C Directional / Gap Orientation Set
    LANDOLT_C_DIRECTIONS: ClassVar[list[str]] = ["UP", "DOWN", "LEFT", "RIGHT"]

    # Standard LogMAR Progression Levels (0 = 20/200, down to 10 = 20/15)
    LEVEL_SPECS: ClassVar[dict[int, AcuityLevelSpec]] = {
        0: AcuityLevelSpec(
            0, "20/200", 1.00, 0.10, 50.00, "Severe vision reduction (Legal blindness threshold)"
        ),
        1: AcuityLevelSpec(1, "20/125", 0.80, 0.16, 31.62, "Significant visual reduction"),
        2: AcuityLevelSpec(2, "20/100", 0.70, 0.20, 25.12, "Marked visual reduction"),
        3: AcuityLevelSpec(3, "20/80", 0.60, 0.25, 19.95, "Moderate-severe visual impairment"),
        4: AcuityLevelSpec(4, "20/60", 0.48, 0.33, 15.14, "Moderate visual reduction"),
        5: AcuityLevelSpec(
            5, "20/50", 0.40, 0.40, 12.59, "Mild-moderate visual impairment (Referral trigger)"
        ),
        6: AcuityLevelSpec(
            6,
            "20/40",
            0.30,
            0.50,
            10.00,
            "Driving vision standard threshold (Common screening start)",
        ),
        7: AcuityLevelSpec(7, "20/30", 0.18, 0.67, 7.59, "Near-standard visual acuity"),
        8: AcuityLevelSpec(8, "20/25", 0.10, 0.80, 6.31, "Very good visual acuity"),
        9: AcuityLevelSpec(9, "20/20", 0.00, 1.00, 5.00, "Standard normal visual acuity"),
        10: AcuityLevelSpec(
            10, "20/15", -0.12, 1.33, 3.80, "Superior / Supra-normal visual acuity"
        ),
    }

    MIN_LEVEL: int = 0
    MAX_LEVEL: int = 10
    DEFAULT_DISTANCE_METERS: float = 3.0
    DEFAULT_NEAR_METERS: float = 0.40  # 40 cm

    # -------------------------------------------------------------------------
    # Physical Optics & Visual Angle Calculations
    # -------------------------------------------------------------------------

    @classmethod
    def calculate_optotype_dimensions(
        cls,
        arcmin: float,
        viewing_distance_meters: float,
        display_dpi: float | None = None,
    ) -> tuple[float, float | None]:
        """
        Calculates physical optotype height in millimeters and screen pixels (if DPI provided).

        Formula:
            theta_rad = (arcmin / 60) * (pi / 180)
            height_meters = 2 * viewing_distance * tan(theta_rad / 2)
            height_mm = height_meters * 1000
            height_px = (height_mm / 25.4) * DPI
        """
        if viewing_distance_meters <= 0.0:
            raise ValidationException(
                "Viewing distance must be a positive number greater than zero."
            )
        if arcmin <= 0.0:
            raise ValidationException(
                "Visual angle arcmin must be a positive number greater than zero."
            )

        theta_rad = (arcmin / 60.0) * (math.pi / 180.0)
        height_meters = 2.0 * viewing_distance_meters * math.tan(theta_rad / 2.0)
        height_mm = round(height_meters * 1000.0, 3)

        height_px = None
        if display_dpi and display_dpi > 0.0:
            height_px = round((height_mm / 25.4) * display_dpi, 1)

        return height_mm, height_px

    # -------------------------------------------------------------------------
    # Calibration Assessment
    # -------------------------------------------------------------------------

    @classmethod
    def evaluate_calibration(
        cls,
        calibration_dict: dict[str, Any] | None,
        test_type: str = "DISTANCE",
    ) -> tuple[CalibrationTier, dict[str, Any]]:
        """
        Evaluates physical display calibration parameters according to 4-tier medical assurance model.
        Never promotes client claims to verified without geometric plausibility checks.
        """
        if not calibration_dict:
            return CalibrationTier.UNCALIBRATED, {
                "tier": CalibrationTier.UNCALIBRATED.value,
                "reason": "No hardware display metadata or viewing distance provided.",
                "is_calibrated": False,
            }

        is_prof = bool(calibration_dict.get("is_professionally_supervised", False))
        if is_prof:
            return CalibrationTier.PROFESSIONALLY_VALIDATED, {
                "tier": CalibrationTier.PROFESSIONALLY_VALIDATED.value,
                "reason": "Calibration independently verified by licensed eye care professional.",
                "is_calibrated": True,
            }

        dpi = calibration_dict.get("display_dpi")
        width_px = calibration_dict.get("screen_width_px")
        height_px = calibration_dict.get("screen_height_px")
        dist_cm = calibration_dict.get("viewing_distance_cm")
        method = calibration_dict.get("calibration_method", "client_unverified")

        has_dpi = dpi is not None and (70.0 <= float(dpi) <= 1200.0)
        has_dims = (
            width_px is not None
            and height_px is not None
            and (int(width_px) >= 320 and int(height_px) >= 320)
        )

        # Distance checks
        if test_type.upper() == "NEAR":
            has_dist = dist_cm is not None and (20.0 <= float(dist_cm) <= 100.0)
        else:
            has_dist = dist_cm is not None and (50.0 <= float(dist_cm) <= 1200.0)

        if (
            has_dpi
            and has_dims
            and has_dist
            and method in ["reference_card", "ar_depth_sensor", "verified_hardware_profile"]
        ):
            return CalibrationTier.SERVER_VERIFIED, {
                "tier": CalibrationTier.SERVER_VERIFIED.value,
                "reason": "Physical screen DPI, dimensions, and viewing distance passed server geometric plausibility checks.",
                "is_calibrated": True,
                "display_dpi": float(dpi),
                "viewing_distance_cm": float(dist_cm),
            }

        return CalibrationTier.CLIENT_REPORTED, {
            "tier": CalibrationTier.CLIENT_REPORTED.value,
            "reason": "Hardware parameters submitted by client without server-validated calibration method.",
            "is_calibrated": False,
            "display_dpi": float(dpi) if dpi else None,
            "viewing_distance_cm": float(dist_cm) if dist_cm else None,
        }

    # -------------------------------------------------------------------------
    # Optotype Selection (Server-Controlled)
    # -------------------------------------------------------------------------

    @classmethod
    def generate_next_optotype(
        cls,
        optotype_type: str,
        previous_optotype: str | None = None,
        rng: random.Random | None = None,
    ) -> tuple[str, str, list[str]]:
        """
        Selects the next optotype server-side, preventing immediate repetitions.
        Returns:
            presented_symbol: What the client displays (e.g. "E_UP" or "C")
            expected_response: Canonical answer the server tests against (e.g. "UP" or "C")
            choice_options: Possible options provided to user interface
        """
        r = rng or random.Random()
        t = optotype_type.upper().strip()

        if t == OptotypeType.SLOAN.value:
            choices = cls.SLOAN_LETTERS
            available = (
                [c for c in choices if c != previous_optotype] if previous_optotype else choices
            )
            if not available:
                available = choices
            selected = r.choice(available)
            return selected, selected, choices

        if t == OptotypeType.LANDOLT_C.value:
            directions = cls.LANDOLT_C_DIRECTIONS
            available_dirs = (
                [d for d in directions if d != previous_optotype]
                if previous_optotype
                else directions
            )
            if not available_dirs:
                available_dirs = directions
            selected_dir = r.choice(available_dirs)
            symbol = f"C_{selected_dir}"
            return symbol, selected_dir, directions

        # Default to Tumbling E
        directions = cls.TUMBLING_E_DIRECTIONS
        available_dirs = (
            [d for d in directions if d != previous_optotype] if previous_optotype else directions
        )
        if not available_dirs:
            available_dirs = directions
        selected_dir = r.choice(available_dirs)
        symbol = f"E_{selected_dir}"
        return symbol, selected_dir, directions

    # -------------------------------------------------------------------------
    # Adaptive Protocol Progression & Stopping Criteria
    # -------------------------------------------------------------------------

    @classmethod
    def evaluate_level_progress(
        cls,
        level_attempts: list[bool],
    ) -> str:
        """
        Evaluates current attempts within an active difficulty level under 3-of-4 ATS rule.
        Returns:
            "PASS": 3 correct answers obtained.
            "FAIL": 2 incorrect answers obtained (impossible to reach 3 of 4).
            "CONTINUE": More presentations required at current level.
        """
        correct = sum(1 for is_cor in level_attempts if is_cor is True)
        incorrect = sum(1 for is_cor in level_attempts if is_cor is False)

        if correct >= cls.REQUIRED_CORRECT_TO_PASS:
            return "PASS"
        if incorrect >= cls.MAX_FAILS_BEFORE_LEVEL_LOSS:
            return "FAIL"
        if len(level_attempts) >= cls.MAX_PRESENTATIONS_PER_LEVEL:
            return "PASS" if correct >= cls.REQUIRED_CORRECT_TO_PASS else "FAIL"

        return "CONTINUE"

    @classmethod
    def determine_next_action(
        cls,
        current_level: int,
        level_result: str,
        passed_levels: set[int],
    ) -> tuple[str, int | None, int | None]:
        """
        Determines the next difficulty level transition or stopping event.
        Returns:
            action: "NEXT_CHALLENGE" | "STOP_COMPLETE"
            next_level: The new level index if continuing, or None if stopping
            resolved_acuity_level: The smallest reliably identified level if stopping, or None
        """
        if level_result == "PASS":
            passed_levels.add(current_level)
            if current_level >= cls.MAX_LEVEL:
                # Reached highest resolution ceiling (20/15)
                return "STOP_COMPLETE", None, current_level
            # Advance difficulty: smaller optotype
            return "NEXT_CHALLENGE", current_level + 1, None

        if level_result == "FAIL":
            if passed_levels:
                # User previously passed a level; stopping criterion met!
                smallest_resolved = max(passed_levels)
                return "STOP_COMPLETE", None, smallest_resolved

            # User failed starting level without passing any level yet
            if current_level > cls.MIN_LEVEL:
                # Step back to larger optotypes (Level 0) for broad screening
                step_down_level = max(cls.MIN_LEVEL, current_level - 2)
                return "NEXT_CHALLENGE", step_down_level, None

            # Failed at largest optotype (Level 0 = 20/200)
            return "STOP_COMPLETE", None, None

        return "NEXT_CHALLENGE", current_level, None

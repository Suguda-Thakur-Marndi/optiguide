import json
import math
import re
from enum import Enum
from typing import Any, ClassVar

from pydantic import ValidationError

from app.core.exceptions import ValidationException


class AssessmentType(str, Enum):
    DISTANCE = "DISTANCE"
    NEAR = "NEAR"


class AcuityEye(str, Enum):
    RIGHT = "right"
    LEFT = "left"
    BOTH = "both"


class VisualAcuityService:
    """
    Dedicated clinical optics mathematical conversion, validation, and summary service
    for Visual Acuity screening.

    Core clinical conversion formula:
        logMAR = log10(denominator / numerator)
    """

    LOGMAR_MIN: float = -0.30
    LOGMAR_MAX: float = 2.00
    LOGMAR_TOLERANCE: float = 0.05
    DECIMAL_TOLERANCE: float = 0.05

    SNELLEN_PATTERN = re.compile(r"^(\d+)\s*/\s*(\d+)$")

    EYE_CANONICAL_MAP: ClassVar[dict[str, str]] = {
        "right": AcuityEye.RIGHT.value,
        "od": AcuityEye.RIGHT.value,
        "right_eye": AcuityEye.RIGHT.value,
        "left": AcuityEye.LEFT.value,
        "os": AcuityEye.LEFT.value,
        "left_eye": AcuityEye.LEFT.value,
        "both": AcuityEye.BOTH.value,
        "ou": AcuityEye.BOTH.value,
        "both_eyes": AcuityEye.BOTH.value,
    }

    TYPE_CANONICAL_MAP: ClassVar[dict[str, str]] = {
        "distance": AssessmentType.DISTANCE.value,
        "near": AssessmentType.NEAR.value,
    }

    CLINICAL_DISCLAIMER = (
        "OptiGuide visual acuity screening is a preliminary functional assessment aid, "
        "not a diagnostic ophthalmic examination. It does not diagnose refractive errors "
        "(such as myopia, hyperopia, or astigmatism), amblyopia, or ocular pathologies, "
        "and cannot calculate corrective lens powers or generate optical prescriptions. "
        "Normal screening observations do not guarantee complete ocular health. "
        "A certified optometrist or ophthalmologist must perform comprehensive clinical evaluations."
    )

    # -------------------------------------------------------------------------
    # 1. Canonicalization
    # -------------------------------------------------------------------------

    @classmethod
    def canonicalize_eye(cls, eye: str) -> str:
        """Normalizes eye notation (right/left/both/od/os/ou) to standard lowercase enum."""
        if not eye:
            raise ValidationException("Test eye must be specified.")
        cleaned = eye.strip().lower()
        if cleaned not in cls.EYE_CANONICAL_MAP:
            raise ValidationException(
                f"Invalid test eye '{eye}'. Supported values: right (OD), left (OS), both (OU)."
            )
        return cls.EYE_CANONICAL_MAP[cleaned]

    @classmethod
    def canonicalize_assessment_type(cls, test_type: str | None) -> str:
        """Normalizes assessment type to uppercase DISTANCE or NEAR."""
        if not test_type:
            return AssessmentType.DISTANCE.value
        cleaned = test_type.strip().lower()
        if cleaned not in cls.TYPE_CANONICAL_MAP:
            raise ValidationException(
                f"Invalid assessment type '{test_type}'. Supported values: DISTANCE, NEAR."
            )
        return cls.TYPE_CANONICAL_MAP[cleaned]

    # -------------------------------------------------------------------------
    # 2. Snellen Parsing & Optics Mathematics
    # -------------------------------------------------------------------------

    @classmethod
    def parse_snellen(cls, snellen_str: str) -> tuple[int, int]:
        """
        Parses and validates a standard Snellen fraction string (e.g. '20/20', '6/6', '20/40').
        Rejects malformed strings, negative values, and zero numerators/denominators.
        """
        if not snellen_str or not isinstance(snellen_str, str):
            raise ValidationException("Snellen fraction must be a non-empty string.")

        match = cls.SNELLEN_PATTERN.match(snellen_str.strip())
        if not match:
            raise ValidationException(
                f"Malformed Snellen notation '{snellen_str}'. Expected format 'numerator/denominator' (e.g. '20/20', '6/12')."
            )

        try:
            num = int(match.group(1))
            denom = int(match.group(2))
        except ValueError as err:
            raise ValidationException(
                f"Invalid numeric values in Snellen fraction '{snellen_str}'."
            ) from err

        if num <= 0:
            raise ValidationException(
                f"Snellen numerator must be a positive integer greater than zero. Received: {num}."
            )
        if denom <= 0:
            raise ValidationException(
                f"Snellen denominator must be a positive integer greater than zero. Received: {denom}."
            )

        return num, denom

    @classmethod
    def snellen_to_logmar(cls, snellen_str: str) -> float:
        """
        Computes exact clinical logMAR value from Snellen notation:
            logMAR = log10(denominator / numerator)
        Rounds consistently to 2 decimal places.
        """
        num, denom = cls.parse_snellen(snellen_str)
        logmar = round(math.log10(denom / num), 2)
        return logmar

    @classmethod
    def snellen_to_decimal(cls, snellen_str: str) -> float:
        """Computes decimal acuity equivalent (numerator / denominator), rounded to 2 decimal places."""
        num, denom = cls.parse_snellen(snellen_str)
        return round(num / denom, 2)

    # -------------------------------------------------------------------------
    # 3. Clinical Data Reconciliation & Range Validation
    # -------------------------------------------------------------------------

    @classmethod
    def reconcile_and_validate(
        cls,
        snellen_fraction: str,
        logmar: float | None = None,
        decimal_acuity: float | None = None,
    ) -> tuple[float, float]:
        """
        Reconciles submitted Snellen fraction with optional logMAR and decimal acuity values.
        If logMAR or decimal are provided, verifies that they agree with the mathematical
        equivalent within tolerance. Rejects conflicting inputs.
        """
        num, denom = cls.parse_snellen(snellen_fraction)
        expected_logmar = round(math.log10(denom / num), 2)
        expected_decimal = round(num / denom, 2)

        # Validate physiological logMAR range
        if not (cls.LOGMAR_MIN <= expected_logmar <= cls.LOGMAR_MAX):
            raise ValidationException(
                f"Computed logMAR {expected_logmar} from Snellen '{snellen_fraction}' is outside "
                f"supported clinical range [{cls.LOGMAR_MIN}, {cls.LOGMAR_MAX}]."
            )

        # Verify provided logMAR agreement
        if logmar is not None:
            if not (cls.LOGMAR_MIN <= logmar <= cls.LOGMAR_MAX):
                raise ValidationException(
                    f"Provided logMAR {logmar} is outside supported clinical range [{cls.LOGMAR_MIN}, {cls.LOGMAR_MAX}]."
                )
            diff = abs(logmar - expected_logmar)
            if diff > cls.LOGMAR_TOLERANCE:
                raise ValidationException(
                    f"Conflicting visual acuity values: Snellen '{snellen_fraction}' corresponds to logMAR {expected_logmar:.2f}, "
                    f"which contradicts supplied logMAR {logmar:.2f} by more than allowable tolerance of ±{cls.LOGMAR_TOLERANCE}."
                )
            final_logmar = round(logmar, 2)
        else:
            final_logmar = expected_logmar

        # Verify provided decimal agreement
        if decimal_acuity is not None:
            if decimal_acuity <= 0.0:
                raise ValidationException("Decimal acuity must be greater than zero.")
            diff_dec = abs(decimal_acuity - expected_decimal)
            if diff_dec > cls.DECIMAL_TOLERANCE:
                raise ValidationException(
                    f"Conflicting visual acuity values: Snellen '{snellen_fraction}' corresponds to decimal {expected_decimal:.2f}, "
                    f"which contradicts supplied decimal {decimal_acuity:.2f} by more than allowable tolerance of ±{cls.DECIMAL_TOLERANCE}."
                )
            final_decimal = round(decimal_acuity, 2)
        else:
            final_decimal = expected_decimal

        return final_logmar, final_decimal

    # -------------------------------------------------------------------------
    # 4. Geometry and Calibration Verification
    # -------------------------------------------------------------------------

    @classmethod
    def validate_test_geometry(
        cls,
        assessment_type: str,
        tested_distance_meters: float | None = None,
        near_reading_distance_cm: float | None = None,
    ) -> None:
        """Validates distance and near viewing geometry separately."""
        if assessment_type == AssessmentType.DISTANCE.value:
            if tested_distance_meters is None or tested_distance_meters <= 0.0:
                raise ValidationException(
                    "Distance visual acuity assessment requires a positive tested_distance_meters value."
                )
            if not (0.3 <= tested_distance_meters <= 12.0):
                raise ValidationException(
                    f"Tested distance {tested_distance_meters}m is outside valid physical screening distance range [0.3m, 12.0m]."
                )
        elif assessment_type == AssessmentType.NEAR.value:
            if near_reading_distance_cm is None or near_reading_distance_cm <= 0.0:
                raise ValidationException(
                    "Near visual acuity assessment requires a positive near_reading_distance_cm value."
                )
            if not (15.0 <= near_reading_distance_cm <= 100.0):
                raise ValidationException(
                    f"Near reading distance {near_reading_distance_cm}cm is outside valid reading distance range [15cm, 100cm]."
                )

    @classmethod
    def evaluate_calibration_claim(
        cls,
        client_is_calibrated: bool,
        calibration_dict: dict[str, Any] | None,
    ) -> tuple[bool, str | None]:
        """
        Assesses calibration claims without trusting raw client boolean.
        A test is not clinically verified simply because client sends is_calibrated=True.
        Requires valid physical display parameters.
        """
        if not calibration_dict:
            # Client claims calibrated with no geometric evidence -> unverified
            return False, None

        has_dpi = (
            calibration_dict.get("display_dpi") is not None
            and calibration_dict.get("display_dpi", 0) > 0
        )
        has_dims = (
            calibration_dict.get("screen_width_px") is not None
            and calibration_dict.get("screen_height_px") is not None
        )
        has_distance = (
            calibration_dict.get("viewing_distance_cm") is not None
            and calibration_dict.get("viewing_distance_cm", 0) > 0
        )

        calib_data = dict(calibration_dict)
        if has_dpi and has_dims and has_distance and client_is_calibrated:
            calib_data["server_verification"] = "GEOMETRIC_VALIDATION_PASSED"
            is_calibrated = True
        else:
            calib_data["server_verification"] = "UNVERIFIED_CLIENT_CLAIM"
            is_calibrated = False

        return is_calibrated, json.dumps(calib_data)

    # -------------------------------------------------------------------------
    # 5. Deterministic Visual Acuity Session Summary Service
    # -------------------------------------------------------------------------

    @classmethod
    def summarize_acuity_observations(
        cls,
        assessments: list[Any],
        session_id: Any | None = None,
    ) -> dict[str, Any]:
        """
        Compiles a deterministic preliminary visual acuity summary across distance and near tests.
        Identifies missing observations, interocular difference, and triage triggers.
        Strictly observes non-diagnostic clinical boundaries.
        """
        distance_records: dict[str, Any] = {}
        near_records: dict[str, Any] = {}

        for a in assessments:
            t_type = (
                getattr(a, "assessment_type", AssessmentType.DISTANCE.value)
                or AssessmentType.DISTANCE.value
            )
            eye = getattr(a, "test_eye", "").lower()
            if t_type == AssessmentType.NEAR.value:
                near_records[eye] = a
            else:
                distance_records[eye] = a

        # Check for missing assessments
        missing_observations: list[str] = []
        if AcuityEye.RIGHT.value not in distance_records:
            missing_observations.append("Right eye (OD) distance visual acuity not assessed.")
        if AcuityEye.LEFT.value not in distance_records:
            missing_observations.append("Left eye (OS) distance visual acuity not assessed.")
        if AcuityEye.BOTH.value not in distance_records:
            missing_observations.append("Binocular (OU) distance visual acuity not assessed.")

        if not near_records:
            missing_observations.append("Near visual acuity screening was not conducted.")

        # Triage evaluation based on approved thresholds
        referral_reasons: list[str] = []
        interocular_difference: float | None = None

        od_a = distance_records.get(AcuityEye.RIGHT.value)
        os_a = distance_records.get(AcuityEye.LEFT.value)

        if od_a and od_a.logmar >= 0.40:
            referral_reasons.append(
                f"Reduced distance visual acuity in right eye (Snellen {od_a.snellen_fraction}, logMAR {od_a.logmar:.2f})."
            )
        if os_a and os_a.logmar >= 0.40:
            referral_reasons.append(
                f"Reduced distance visual acuity in left eye (Snellen {os_a.snellen_fraction}, logMAR {os_a.logmar:.2f})."
            )

        if od_a and os_a:
            interocular_difference = round(abs(od_a.logmar - os_a.logmar), 2)
            if interocular_difference >= 0.30:
                referral_reasons.append(
                    f"Interocular visual acuity asymmetry of {interocular_difference:.2f} logMAR between right and left eyes."
                )

        # Check near vision impairment
        for eye_key, n_a in near_records.items():
            if n_a.logmar >= 0.40:
                referral_reasons.append(
                    f"Reduced near visual acuity in {eye_key} eye (Snellen {n_a.snellen_fraction}, logMAR {n_a.logmar:.2f})."
                )

        referral_recommended = len(referral_reasons) > 0

        def format_record(rec: Any | None) -> Any | None:
            if not rec:
                return None
            try:
                from app.schemas.clinical_assessments import VisualAcuityResponse

                return VisualAcuityResponse.model_validate(rec)
            except (ValidationError, AttributeError, TypeError, ValueError):
                return {
                    "id": str(getattr(rec, "id", "")),
                    "session_id": str(getattr(rec, "session_id", session_id or "")),
                    "user_id": str(getattr(rec, "user_id", "")),
                    "assessment_type": getattr(
                        rec, "assessment_type", AssessmentType.DISTANCE.value
                    ),
                    "test_eye": getattr(rec, "test_eye", ""),
                    "snellen_fraction": getattr(rec, "snellen_fraction", ""),
                    "logmar": getattr(rec, "logmar", 0.0),
                    "decimal_acuity": getattr(rec, "decimal_acuity", 0.0),
                    "tested_distance_meters": getattr(rec, "tested_distance_meters", 0.6),
                    "unassisted_or_corrected": getattr(
                        rec, "unassisted_or_corrected", "unassisted"
                    ),
                    "near_reading_label": getattr(rec, "near_reading_label", None),
                    "near_reading_distance_cm": getattr(rec, "near_reading_distance_cm", None),
                    "is_calibrated": getattr(rec, "is_calibrated", False),
                    "calibration_metadata": getattr(rec, "calibration_metadata", None),
                    "observations": getattr(rec, "observations", None),
                    "created_at": getattr(rec, "created_at", None),
                    "updated_at": getattr(rec, "updated_at", None),
                }

        return {
            "session_id": session_id,
            "distance_assessments": {
                "right_eye": format_record(distance_records.get(AcuityEye.RIGHT.value)),
                "left_eye": format_record(distance_records.get(AcuityEye.LEFT.value)),
                "binocular": format_record(distance_records.get(AcuityEye.BOTH.value)),
            },
            "near_assessments": {
                "right_eye": format_record(near_records.get(AcuityEye.RIGHT.value)),
                "left_eye": format_record(near_records.get(AcuityEye.LEFT.value)),
                "binocular": format_record(near_records.get(AcuityEye.BOTH.value)),
            },
            "interocular_difference_logmar": interocular_difference,
            "missing_observations": missing_observations,
            "referral_recommended": referral_recommended,
            "referral_reasons": referral_reasons,
            "clinical_disclaimer": cls.CLINICAL_DISCLAIMER,
        }

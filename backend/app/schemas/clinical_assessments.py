import uuid
from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict, Field

from app.schemas.screening import ScreeningSessionResponse


class CalibrationMetadata(BaseModel):
    """Physical hardware and distance calibration parameters."""

    screen_width_px: int | None = Field(default=None, ge=100)
    screen_height_px: int | None = Field(default=None, ge=100)
    display_dpi: float | None = Field(default=None, ge=50.0, le=1200.0)
    physical_optotype_mm: float | None = Field(default=None, gt=0.0)
    viewing_distance_cm: float | None = Field(default=None, ge=20.0, le=1000.0)
    device_orientation: str | None = Field(default=None, max_length=20)
    is_verified: bool = False
    uncertainty_percentage: float | None = Field(default=None, ge=0.0, le=100.0)

    model_config = ConfigDict(extra="forbid")


# -----------------------------------------------------------------------------
# Visual Acuity Schemas
# -----------------------------------------------------------------------------


class VisualAcuityCreateRequest(BaseModel):
    """Payload for submitting visual acuity test findings."""

    assessment_type: str = Field(
        default="DISTANCE",
        pattern="^(DISTANCE|NEAR|distance|near)$",
        description="Screening test type: DISTANCE or NEAR",
    )
    test_eye: str = Field(
        ...,
        pattern="^(right|left|both|od|os|ou|RIGHT|LEFT|BOTH|OD|OS|OU)$",
        description="Eye tested: right (OD), left (OS), or both (OU)",
    )
    snellen_fraction: str = Field(
        ...,
        max_length=20,
        description="Standard Snellen notation (e.g. '20/20', '6/6', '20/40')",
        json_schema_extra={"example": "20/20"},
    )
    logmar: float | None = Field(
        default=None,
        ge=-0.3,
        le=2.0,
        description="Optional pre-computed logMAR. If supplied, must agree with Snellen within tolerance.",
    )
    decimal_acuity: float | None = Field(
        default=None,
        gt=0.0,
        le=2.5,
        description="Optional pre-computed decimal acuity equivalent.",
    )
    tested_distance_meters: float | None = Field(
        default=0.6,
        gt=0.1,
        le=12.0,
        description="Viewing distance in meters for distance screening.",
    )
    unassisted_or_corrected: str = Field(
        default="unassisted", pattern="^(unassisted|with_glasses|with_contacts)$"
    )
    near_reading_label: str | None = Field(
        default=None,
        max_length=50,
        description="Near reading acuity notation (e.g. 'N6', 'J1', '20/20').",
    )
    near_reading_distance_cm: float | None = Field(
        default=None,
        gt=0.0,
        le=200.0,
        description="Viewing distance in centimeters for near screening.",
    )
    is_calibrated: bool = False
    calibration: CalibrationMetadata | None = None
    observations: str | None = Field(default=None, max_length=500)

    model_config = ConfigDict(extra="forbid")


class VisualAcuityResponse(BaseModel):
    """Response representation of recorded visual acuity."""

    id: uuid.UUID
    session_id: uuid.UUID
    user_id: uuid.UUID
    assessment_type: str = "DISTANCE"
    test_eye: str
    snellen_fraction: str
    logmar: float
    decimal_acuity: float
    tested_distance_meters: float
    unassisted_or_corrected: str
    near_reading_label: str | None = None
    near_reading_distance_cm: float | None = None
    is_calibrated: bool
    calibration_metadata: str | None = None
    observations: str | None = None
    created_at: datetime
    updated_at: datetime | None = None

    model_config = ConfigDict(from_attributes=True)


class VisualAcuitySummaryResponse(BaseModel):
    """Preliminary visual acuity observations breakdown and clinical non-diagnostic summary."""

    session_id: uuid.UUID | None = None
    distance_assessments: dict[str, VisualAcuityResponse | dict[str, Any] | None]
    near_assessments: dict[str, VisualAcuityResponse | dict[str, Any] | None]
    interocular_difference_logmar: float | None = None
    missing_observations: list[str] = Field(default_factory=list)
    referral_recommended: bool = False
    referral_reasons: list[str] = Field(default_factory=list)
    clinical_disclaimer: str

    model_config = ConfigDict(from_attributes=True)


class VisualAcuityListResponse(BaseModel):
    """Paginated list of visual acuity assessments."""

    items: list[VisualAcuityResponse] = Field(default_factory=list)
    total: int = Field(..., description="Total count of records")
    limit: int = Field(default=20, description="Items requested per page")
    offset: int = Field(default=0, description="Page offset")

    model_config = ConfigDict(from_attributes=True)


# -----------------------------------------------------------------------------
# Astigmatism Schemas
# -----------------------------------------------------------------------------


class AstigmatismCreateRequest(BaseModel):
    """Payload for submitting radial fan/clock dial astigmatism screening."""

    chart_type: str = Field(default="clock_dial", max_length=50)
    has_uniform_clarity: bool
    indicated_axes: list[int] | None = None
    sharpest_meridian_hour: int | None = Field(default=None, ge=1, le=12)
    screening_observation: str | None = Field(default=None, max_length=500)

    model_config = ConfigDict(extra="forbid")


class AstigmatismResponse(BaseModel):
    """Response representation of recorded astigmatism screening."""

    id: uuid.UUID
    session_id: uuid.UUID
    user_id: uuid.UUID
    chart_type: str
    has_uniform_clarity: bool
    indicated_axes: str | None = None
    sharpest_meridian_hour: int | None = None
    screening_observation: str
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


# -----------------------------------------------------------------------------
# Color Vision Schemas
# -----------------------------------------------------------------------------


class ColorVisionCreateRequest(BaseModel):
    """Payload for submitting pseudoisochromatic color vision plate checks."""

    test_protocol: str = Field(default="pseudoisochromatic_plates", max_length=50)
    total_plates_presented: int = Field(default=4, ge=1, le=38)
    correct_plate_count: int = Field(..., ge=0, le=38)
    deficiency_indicated: bool
    deficiency_type: str = Field(default="none", max_length=50)
    responses_detail: list[dict[str, Any]] | None = None
    screening_observation: str | None = Field(default=None, max_length=500)

    model_config = ConfigDict(extra="forbid")


class ColorVisionResponse(BaseModel):
    """Response representation of recorded color vision screening."""

    id: uuid.UUID
    session_id: uuid.UUID
    user_id: uuid.UUID
    test_protocol: str
    total_plates_presented: int
    correct_plate_count: int
    deficiency_indicated: bool
    deficiency_type: str
    responses_detail: str | None = None
    screening_observation: str
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


# -----------------------------------------------------------------------------
# Clinical Session Summary Schema
# -----------------------------------------------------------------------------


class ClinicalSessionSummaryResponse(BaseModel):
    """Aggregated preliminary screening observation report."""

    session: ScreeningSessionResponse
    acuity_results: list[VisualAcuityResponse]
    astigmatism_results: list[AstigmatismResponse]
    color_vision_results: list[ColorVisionResponse]
    referral_recommended: bool
    referral_reasons: list[str]
    clinical_disclaimer: str

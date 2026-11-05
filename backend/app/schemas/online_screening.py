"""Pydantic schemas for the OptiGuide Complete Online Vision Screening Platform.

Defines request and response contracts for all 7 interactive screening modules:
  1. Visual Acuity
  2. Astigmatism Radial Clock Dial
  3. Contrast / Light Sensitivity
  4. Near Vision Reading Acuity
  5. Near Vision Duochrome (Red/Green)
  6. Color Vision (Pseudoisochromatic plates)
  7. Central Vision / Amsler Distortion Questionnaire
"""

import uuid
from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict, Field

# -----------------------------------------------------------------------------
# Calibration Schemas
# -----------------------------------------------------------------------------


class CalibrationSubmitRequest(BaseModel):
    """Payload for submitting display calibration and viewing distance metadata."""

    model_config = ConfigDict(extra="ignore")

    device_category: str = Field(
        "DESKTOP",
        pattern="^(DESKTOP|LAPTOP|TABLET|MOBILE)$",
        description="User hardware category.",
    )
    screen_width_px: int | None = Field(None, ge=100, le=10000)
    screen_height_px: int | None = Field(None, ge=100, le=10000)
    device_pixel_ratio: float | None = Field(None, ge=0.5, le=10.0)
    calibration_method: str = Field(
        "STANDARD_CARD",
        pattern="^(STANDARD_CARD|COIN_REFERENCE|MANUAL_MEASURE|DEFAULT_UNVERIFIED)$",
    )
    reported_card_width_px: float | None = Field(None, ge=50.0, le=5000.0)
    target_viewing_distance_cm: float = Field(
        40.0, ge=20.0, le=600.0, description="Testing distance in centimeters."
    )
    user_confirmed_distance: bool = Field(
        True, description="Whether citizen explicitly confirmed distance physical setup."
    )
    calibration_notes: str | None = Field(None, max_length=255)


class CalibrationResponse(BaseModel):
    """Response returning processed calibration verification status."""

    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    session_id: uuid.UUID
    device_category: str
    calibration_status: str
    computed_ppi: float | None
    target_viewing_distance_cm: float
    user_confirmed_distance: bool
    calibration_method: str
    created_at: datetime


# -----------------------------------------------------------------------------
# Module Definitions & Platform Configuration
# -----------------------------------------------------------------------------


class TestModuleDefinition(BaseModel):
    """Metadata describing a vision screening module."""

    __test__ = False
    model_config = ConfigDict(extra="ignore")

    test_type: str = Field(..., description="Module identifier enum.")
    title: str = Field(..., description="Localized title of the test.")
    description: str = Field(..., description="Clinical purpose of the screening module.")
    target_viewing_distance_cm: float
    supported_eyes: list[str] = Field(..., description="OD, OS, OU")
    instructions: list[str]
    estimated_duration_seconds: int
    protocol_version: str
    disclaimer: str


class ScreeningPlatformConfigResponse(BaseModel):
    """Complete catalog of screening modules and runtime configuration."""

    model_config = ConfigDict(extra="ignore")

    platform_name: str = "OptiGuide Online Vision Screening Platform"
    version: str = "1.0.0"
    supported_languages: list[str] = ["en", "hi", "or"]
    available_modules: list[TestModuleDefinition]
    default_test_sequence: list[str]
    clinical_notice: str


# -----------------------------------------------------------------------------
# Interactive Test Step & Response Schemas
# -----------------------------------------------------------------------------


class TestStartRequest(BaseModel):
    """Request payload to initiate a specific screening module."""

    __test__ = False
    model_config = ConfigDict(extra="ignore")

    eye: str = Field(
        "OU",
        pattern="^(OD|OS|OU|right|left|both)$",
        description="Target eye for screening: OD (Right), OS (Left), OU (Both).",
    )
    viewing_condition: str = Field(
        "WITH_GLASSES",
        pattern="^(WITH_GLASSES|WITHOUT_GLASSES|UNASSISTED)$",
        description="Correction condition during test.",
    )


class TestChallengeResponse(BaseModel):
    """Active challenge presentation returned to client.

    CRITICAL SECURITY RULE: Expected answer is NEVER exposed in this payload.
    """

    __test__ = False
    model_config = ConfigDict(extra="ignore")

    test_id: uuid.UUID
    test_type: str
    eye: str
    viewing_condition: str
    step_index: int
    total_steps: int
    stimulus_id: str
    stimulus_type: str
    stimulus_content: dict[str, Any]
    options: list[str]
    prompt_question: str
    target_viewing_distance_cm: float
    instructions: str


class TestResponseSubmitRequest(BaseModel):
    """Client submission of a stimulus answer.

    Client only sends user choice; server determines correctness.
    """

    __test__ = False
    model_config = ConfigDict(extra="ignore")

    step_index: int = Field(..., ge=0, description="Step number matching active challenge.")
    stimulus_id: str = Field(..., min_length=1, max_length=50)
    user_response: str = Field(..., min_length=1, max_length=100)
    response_time_ms: int | None = Field(None, ge=0, le=300000)


class TestStepResponse(BaseModel):
    """Response after evaluating a single stimulus submission."""

    __test__ = False
    model_config = ConfigDict(extra="ignore")

    test_id: uuid.UUID
    test_type: str
    status: str
    step_index: int
    total_steps: int
    is_completed: bool
    next_challenge: TestChallengeResponse | None = None
    result_summary: dict[str, Any] | None = None


class TestResultResponse(BaseModel):
    """Evaluated clinical observation and score for a completed test instance."""

    __test__ = False
    model_config = ConfigDict(extra="ignore")

    test_id: uuid.UUID
    session_id: uuid.UUID
    test_type: str
    status: str
    eye: str
    viewing_condition: str
    result_classification: str
    clinical_observation: str
    metrics: dict[str, Any]
    started_at: datetime | None
    completed_at: datetime | None
    clinical_disclaimer: str


class TestCancelRequest(BaseModel):
    """Request payload to cancel an active test module."""

    __test__ = False
    model_config = ConfigDict(extra="ignore")

    reason: str | None = Field(None, max_length=255)


# -----------------------------------------------------------------------------
# Final Screening Report Schemas
# -----------------------------------------------------------------------------


class ModuleResultReportItem(BaseModel):
    """Individual test module outcome in the consolidated report."""

    model_config = ConfigDict(extra="ignore")

    test_type: str
    status: str
    eye: str
    classification: str
    observation: str
    metrics: dict[str, Any]


class FinalScreeningReportResponse(BaseModel):
    """Consolidated vision screening report spanning all 7 modules."""

    model_config = ConfigDict(extra="ignore")

    report_id: uuid.UUID
    report_number: str
    session_id: uuid.UUID
    status: str
    created_at: datetime
    overall_classification: str
    protocol_version: str
    completed_tests_count: int
    skipped_tests_count: int
    calibration: dict[str, Any]
    results: dict[str, Any]
    follow_up_recommendation: str
    professional_referral_indicated: bool
    limitations: list[str]
    clinical_disclaimer: str


# -----------------------------------------------------------------------------
# Screening History Schemas
# -----------------------------------------------------------------------------


class ScreeningHistoryItem(BaseModel):
    """Summary item in user screening history list."""

    model_config = ConfigDict(extra="ignore")

    session_id: uuid.UUID
    status: str
    started_at: datetime
    completed_at: datetime | None
    report_id: uuid.UUID | None = None
    report_number: str | None = None
    overall_classification: str | None = None
    completed_modules: list[str]


class ScreeningHistoryResponse(BaseModel):
    """Paginated list of historical screening sessions and reports."""

    model_config = ConfigDict(extra="ignore")

    items: list[ScreeningHistoryItem]
    total: int
    limit: int
    offset: int

import uuid
from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict, Field, model_validator


class PDAssessmentCreateRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    measurement_type: str = Field(default="BINOCULAR", pattern=r"^(BINOCULAR|MONOCULAR)$")
    binocular_pd_mm: float = Field(
        ...,
        description="Pupillary distance in mm (adult: 45-80mm; pediatric: 38-55mm)",
    )
    monocular_left_pd_mm: float | None = Field(
        default=None,
        description="Left monocular pupillary distance in mm",
    )
    monocular_right_pd_mm: float | None = Field(
        default=None,
        description="Right monocular pupillary distance in mm",
    )
    estimation_method: str = Field(
        default="REFERENCE_CARD",
        pattern=r"^(REFERENCE_CARD|SENSOR_ESTIMATE|MANUAL_CLINICAL)$",
    )
    session_id: uuid.UUID | None = None
    is_pediatric: bool = Field(default=False)
    is_calibrated: bool = Field(
        default=False,
        description="Client-reported calibration claim (untrusted by server until verified)",
    )
    calibration_metadata: dict[str, Any] | None = None
    device_info: dict[str, Any] | None = None
    confidence_score: float | None = Field(
        default=None,
        ge=0.0,
        le=1.0,
        description="Client-reported confidence (untrusted by server)",
    )

    @model_validator(mode="after")
    def validate_pd_consistency(self) -> "PDAssessmentCreateRequest":
        left = self.monocular_left_pd_mm
        right = self.monocular_right_pd_mm
        total = self.binocular_pd_mm

        # Monocular sum consistency: |(left + right) - total| <= 3.0 mm
        if left is not None and right is not None:
            summed = left + right
            diff = abs(summed - total)
            if diff > 3.0:
                raise ValueError(
                    f"Monocular left ({left} mm) and right ({right} mm) sum to {summed:.1f} mm, "
                    f"which contradicts binocular measurement ({total:.1f} mm) by more than 3.0 mm."
                )
        return self
        return self


class PDRejectRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    rejection_reason: str = Field(..., min_length=3, max_length=500)


class PDProfessionalReviewRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    clinical_notes: str = Field(..., min_length=5, max_length=1000)
    measured_binocular_pd_mm: float | None = Field(default=None, ge=38.0, le=80.0)
    measured_left_pd_mm: float | None = Field(default=None, ge=18.0, le=42.0)
    measured_right_pd_mm: float | None = Field(default=None, ge=18.0, le=42.0)
    status: str = Field(
        default="PROFESSIONALLY_REVIEWED",
        pattern=r"^(PROFESSIONALLY_REVIEWED|REQUIRES_PROFESSIONAL_MEASUREMENT|REJECTED)$",
    )
    action: str | None = Field(default=None, pattern=r"^(CONFIRM|REJECT|MEASURE)$")


class PDAssessmentResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    user_id: uuid.UUID
    session_id: uuid.UUID | None = None
    measurement_type: str
    binocular_pd_mm: float
    monocular_left_pd_mm: float | None = None
    monocular_right_pd_mm: float | None = None
    unit: str
    estimation_method: str
    is_calibrated: bool
    is_server_verified: bool = False
    calibration_metadata: str | None = None
    client_confidence_score: float | None = None
    server_confidence_score: float | None = None
    confidence_score: float | None = None
    is_pediatric: bool = False
    device_info: str | None = None
    status: str
    rejection_reason: str | None = None
    reviewed_by_professional_id: uuid.UUID | None = None
    professional_review_notes: str | None = None
    recorded_at: datetime
    confirmed_at: datetime | None = None
    clinical_disclaimer: str = (
        "OptiGuide pupillary distance estimates are preliminary optical guidance values. "
        "A physical pupillometer measurement by an eye care professional is mandatory before ophthalmic lens fabrication."
    )

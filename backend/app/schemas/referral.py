import uuid
from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict, Field

from app.schemas.clinical_assessments import (
    AstigmatismResponse,
    ColorVisionResponse,
    VisualAcuityResponse,
)


class ProfessionalApplyRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    license_number: str = Field(..., min_length=3, max_length=100)
    issuing_authority: str = Field(..., min_length=3, max_length=255)
    registration_year: int = Field(..., ge=1950, le=2050)
    qualification_title: str = Field(..., min_length=2, max_length=255)


class ProfessionalProfileResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    user_id: uuid.UUID
    license_number: str
    issuing_authority: str
    registration_year: int
    qualification_title: str
    verification_status: str
    verified_at: datetime | None = None
    verified_by_admin_id: uuid.UUID | None = None
    rejection_reason: str | None = None
    created_at: datetime
    updated_at: datetime


class ProfessionalVerifyRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    action: str = Field(..., pattern=r"^(VERIFY|REJECT|SUSPEND|REACTIVATE)$")
    rejection_reason: str | None = Field(default=None, max_length=500)


class PatientReferralCreateRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    session_id: uuid.UUID
    referral_reason: str = Field(..., min_length=5, max_length=1000)
    clinical_priority: str = Field(default="ROUTINE", pattern=r"^(ROUTINE|PRIORITY|URGENT)$")
    notes: str | None = Field(default=None, max_length=1000)


class PatientReferralResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    patient_id: uuid.UUID
    session_id: uuid.UUID
    referral_reason: str
    clinical_priority: str
    status: str
    notes: str | None = None
    created_at: datetime
    updated_at: datetime
    patient_name: str | None = None
    patient_email: str | None = None


class PatientRecordShareRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    professional_id: uuid.UUID
    expires_in_days: int = Field(default=30, ge=1, le=365)


class PatientRecordShareResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    referral_id: uuid.UUID
    patient_id: uuid.UUID
    professional_id: uuid.UUID
    access_status: str
    granted_at: datetime
    expires_at: datetime | None = None
    revoked_at: datetime | None = None
    professional_name: str | None = None
    professional_license: str | None = None


class ClinicalReviewCreateRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    professional_observations: str = Field(..., min_length=5, max_length=2000)
    in_person_exam_recommended: bool = Field(default=False)
    recommended_exam_timeframe: str | None = Field(default=None, max_length=64)


class ClinicalReviewResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    referral_id: uuid.UUID
    professional_id: uuid.UUID
    review_status: str
    professional_observations: str
    in_person_exam_recommended: bool
    recommended_exam_timeframe: str | None = None
    closed_at: datetime | None = None
    created_at: datetime
    updated_at: datetime


class SharedScreeningDetailsResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    referral: PatientReferralResponse
    share: PatientRecordShareResponse
    screening_session: dict[str, Any]
    visual_acuity_assessments: list[VisualAcuityResponse]
    astigmatism_assessments: list[AstigmatismResponse]
    color_vision_assessments: list[ColorVisionResponse]
    reviews: list[ClinicalReviewResponse]
    clinical_disclaimer: str = (
        "OptiGuide screening observations are strictly preliminary. Clinical reviews "
        "and physical examinations must confirm diagnoses before prescription or intervention."
    )

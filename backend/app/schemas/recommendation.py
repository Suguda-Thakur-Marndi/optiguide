import uuid
from datetime import datetime
from decimal import Decimal
from typing import Any

from pydantic import BaseModel, ConfigDict, Field


class EyewearRecommendationRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    budget_max_inr: Decimal | None = Field(default=None, description="Maximum frame budget in INR")
    preferred_frame_shape: str | None = Field(default=None, max_length=50)
    preferred_frame_material: str | None = Field(default=None, max_length=50)
    preferred_frame_type: str | None = Field(default=None, max_length=50)
    face_shape_preference: str | None = Field(default=None, max_length=50)
    gender_target: str | None = Field(default=None, pattern=r"^(unisex|men|women|kids)$")
    session_id: uuid.UUID | None = None
    shop_id: uuid.UUID | None = None


class RecommendedProductItem(BaseModel):
    product_id: uuid.UUID
    sku: str
    name: str
    brand_name: str
    base_price_inr: Decimal
    frame_shape: str
    frame_material: str
    frame_type: str
    image_url: str | None = None
    match_score: float = Field(..., ge=0.0, le=100.0)
    match_reasons: list[str] = Field(default_factory=list)
    is_in_stock: bool = True


class EyewearRecommendationResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    user_id: uuid.UUID
    input_criteria: dict[str, Any]
    recommendations: list[RecommendedProductItem]
    clinical_disclaimer: str = (
        "OptiGuide frame recommendations are non-clinical optical style guidance. "
        "They do not determine corrective optical lens power or replace certified optometrist prescriptions."
    )
    created_at: datetime


class RecommendationFeedbackRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    selected_product_id: uuid.UUID | None = None
    rating: int = Field(..., ge=1, le=5)
    feedback_text: str | None = Field(default=None, max_length=1000)


class RecommendationFeedbackResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    recommendation_id: uuid.UUID
    user_id: uuid.UUID
    selected_product_id: uuid.UUID | None = None
    rating: int
    feedback_text: str | None = None
    created_at: datetime

import uuid
from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel, ConfigDict, Field

from app.schemas.catalog import ProductResponse


class FrameColorOption(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    hex_code: str
    name: str


class FrameTryOnAssetResponse(BaseModel):
    """Accurate physical geometry reference and transparent overlay assets for AR rendering."""

    model_config = ConfigDict(from_attributes=True)

    frame_id: uuid.UUID
    sku: str
    name: str
    brand_name: str
    category_name: str | None = None
    frame_type: str
    frame_material: str
    frame_shape: str
    gender_target: str
    base_price_inr: Decimal
    is_active: bool
    in_stock: bool = True
    image_url: str | None = None
    description: str | None = None

    # Try-On Asset Telemetry & Geometry
    try_on_asset_url: str | None = None
    try_on_asset_type: str = "2d_png"
    available_colors: list[FrameColorOption] = Field(default_factory=list)
    left_lens_center_x: float = 0.2875
    left_lens_center_y: float = 0.5
    right_lens_center_x: float = 0.7125
    right_lens_center_y: float = 0.5
    bridge_center_x: float = 0.5
    bridge_center_y: float = 0.48
    asset_scale: float = 1.0
    asset_rotation_offset: float = 0.0
    asset_version: str = "1.0.0"

    # Physical Dimensions (in millimeters)
    frame_width_mm: float | None = None
    bridge_width_mm: float | None = None
    temple_length_mm: float | None = None
    lens_width_mm: float | None = None
    lens_height_mm: float | None = None

    # Availability Notice
    is_try_on_available: bool = True
    availability_notice: str | None = None


class TryOnSessionCreateRequest(BaseModel):
    model_config = ConfigDict(extra="ignore")

    screening_session_id: uuid.UUID | None = None
    selected_product_id: uuid.UUID | None = None
    selected_color: str = "#111827"
    selected_scale: float = Field(default=1.0, ge=0.5, le=2.0)
    selected_offset_y: float = Field(default=0.0, ge=-100.0, le=100.0)
    camera_facing: str = Field(default="user", pattern=r"^(user|environment)$")
    device_type: str = Field(default="desktop", max_length=50)


class TryOnSessionResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    user_id: uuid.UUID | None = None
    screening_session_id: uuid.UUID | None = None
    selected_product_id: uuid.UUID | None = None
    selected_color: str
    selected_scale: float
    selected_offset_y: float
    camera_facing: str
    device_type: str
    snapshots_count: int
    is_active: bool
    created_at: datetime
    updated_at: datetime


class TryOnFrameSelectRequest(BaseModel):
    model_config = ConfigDict(extra="ignore")

    product_id: uuid.UUID
    selected_color: str | None = None
    selected_scale: float | None = Field(default=None, ge=0.5, le=2.0)
    selected_offset_y: float | None = Field(default=None, ge=-100.0, le=100.0)


class FavouriteToggleRequest(BaseModel):
    model_config = ConfigDict(extra="ignore")

    product_id: uuid.UUID
    selected_color: str = "#111827"
    notes: str | None = Field(default=None, max_length=500)


class FavouriteResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    user_id: uuid.UUID
    product_id: uuid.UUID
    selected_color: str
    notes: str | None = None
    created_at: datetime
    product: ProductResponse | None = None


class TryOnSnapshotRequest(BaseModel):
    model_config = ConfigDict(extra="ignore")

    product_id: uuid.UUID | None = None
    selected_color: str = "#111827"
    title: str = Field(default="AR Eyewear Preview", max_length=255)
    face_detected: bool = True


class TryOnSnapshotResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    session_id: uuid.UUID
    product_id: uuid.UUID | None = None
    selected_color: str
    title: str
    face_detected: bool
    created_at: datetime

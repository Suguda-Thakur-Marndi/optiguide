import uuid
from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel, ConfigDict, Field


class CategoryCreateRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    name: str = Field(..., min_length=2, max_length=100)
    slug: str = Field(..., min_length=2, max_length=100, pattern=r"^[a-z0-9-]+$")
    description: str | None = Field(default=None, max_length=500)


class CategoryResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    name: str
    slug: str
    description: str | None = None
    is_active: bool


class BrandCreateRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    name: str = Field(..., min_length=2, max_length=100)
    slug: str = Field(..., min_length=2, max_length=100, pattern=r"^[a-z0-9-]+$")


class BrandResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    name: str
    slug: str
    is_active: bool


class ProductCreateRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    sku: str = Field(..., min_length=3, max_length=64)
    name: str = Field(..., min_length=2, max_length=255)
    brand_id: uuid.UUID
    category_id: uuid.UUID
    frame_type: str = Field(..., min_length=2, max_length=50)
    frame_material: str = Field(..., min_length=2, max_length=50)
    frame_shape: str = Field(..., min_length=2, max_length=50)
    gender_target: str = Field(default="unisex", pattern=r"^(unisex|men|women|kids)$")
    frame_width_mm: float | None = Field(default=None, ge=50.0, le=200.0)
    bridge_width_mm: float | None = Field(default=None, ge=5.0, le=40.0)
    temple_length_mm: float | None = Field(default=None, ge=80.0, le=200.0)
    lens_width_mm: float | None = Field(default=None, ge=20.0, le=100.0)
    lens_height_mm: float | None = Field(default=None, ge=15.0, le=80.0)
    base_price_inr: Decimal = Field(..., ge=Decimal("0.00"), description="Retail base price in INR")
    image_url: str | None = Field(default=None, max_length=500)
    description: str | None = Field(default=None, max_length=2000)


class ProductUpdateRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    name: str | None = Field(default=None, min_length=2, max_length=255)
    frame_type: str | None = Field(default=None, max_length=50)
    frame_material: str | None = Field(default=None, max_length=50)
    frame_shape: str | None = Field(default=None, max_length=50)
    gender_target: str | None = Field(default=None, pattern=r"^(unisex|men|women|kids)$")
    frame_width_mm: float | None = Field(default=None, ge=50.0, le=200.0)
    bridge_width_mm: float | None = Field(default=None, ge=5.0, le=40.0)
    temple_length_mm: float | None = Field(default=None, ge=80.0, le=200.0)
    lens_width_mm: float | None = Field(default=None, ge=20.0, le=100.0)
    lens_height_mm: float | None = Field(default=None, ge=15.0, le=80.0)
    base_price_inr: Decimal | None = Field(
        default=None, ge=Decimal("0.00"), description="Retail base price in INR"
    )
    is_active: bool | None = None
    image_url: str | None = Field(default=None, max_length=500)
    description: str | None = Field(default=None, max_length=2000)


class ProductResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    sku: str
    name: str
    brand_id: uuid.UUID
    brand_name: str | None = None
    category_id: uuid.UUID
    category_name: str | None = None
    frame_type: str
    frame_material: str
    frame_shape: str
    gender_target: str
    frame_width_mm: float | None = None
    bridge_width_mm: float | None = None
    temple_length_mm: float | None = None
    lens_width_mm: float | None = None
    lens_height_mm: float | None = None
    base_price_inr: Decimal
    is_active: bool
    image_url: str | None = None
    description: str | None = None
    # Virtual Try-On Asset Telemetry & Geometry
    try_on_asset_url: str | None = None
    try_on_asset_type: str | None = "2d_png"
    frame_colors: str | None = None
    left_lens_center_x: float | None = 0.2875
    left_lens_center_y: float | None = 0.5
    right_lens_center_x: float | None = 0.7125
    right_lens_center_y: float | None = 0.5
    bridge_center_x: float | None = 0.5
    bridge_center_y: float | None = 0.48
    asset_scale: float = 1.0
    asset_rotation_offset: float = 0.0
    asset_version: str = "1.0.0"
    is_try_on_available: bool = True
    created_at: datetime
    updated_at: datetime


class ShopCreateRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    name: str = Field(..., min_length=2, max_length=255)
    location_city: str = Field(..., min_length=2, max_length=100)
    location_state: str = Field(..., min_length=2, max_length=100)
    phone_number: str | None = Field(default=None, max_length=50)


class ShopResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    name: str
    location_city: str
    location_state: str
    owner_user_id: uuid.UUID
    phone_number: str | None = None
    is_active: bool
    created_at: datetime


class ShopInventoryAdjustRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    product_id: uuid.UUID
    quantity_delta: int = Field(..., description="Positive to add, negative to deduct")
    reason: str = Field(..., pattern=r"^(RESTOCK|SALE|ADJUSTMENT|RETURN)$")
    notes: str | None = Field(default=None, max_length=500)


class ShopInventoryResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    shop_id: uuid.UUID
    product_id: uuid.UUID
    product_sku: str | None = None
    product_name: str | None = None
    stock_quantity: int
    reserved_quantity: int = 0
    available_quantity: int = 0
    low_stock_threshold: int = 3
    is_low_stock: bool = False
    updated_at: datetime


class InventoryTransactionResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    inventory_id: uuid.UUID
    operator_user_id: uuid.UUID | None = None
    quantity_delta: int
    reason: str
    notes: str | None = None
    occurred_at: datetime

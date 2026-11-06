import uuid
from datetime import UTC, datetime
from decimal import Decimal
from typing import TYPE_CHECKING

from sqlalchemy import (
    Boolean,
    CheckConstraint,
    DateTime,
    Float,
    ForeignKey,
    Integer,
    Numeric,
    String,
    Text,
    UniqueConstraint,
    Uuid,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database.base import Base

if TYPE_CHECKING:
    from app.models.user import User


class CatalogCategory(Base):
    """Product frame / eyewear categories (e.g. Full-Rim, Rimless, Progressive-Ready)."""

    __tablename__ = "catalog_categories"

    id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )
    name: Mapped[str] = mapped_column(
        String(100),
        unique=True,
        nullable=False,
    )
    slug: Mapped[str] = mapped_column(
        String(100),
        unique=True,
        nullable=False,
        index=True,
    )
    description: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )
    is_active: Mapped[bool] = mapped_column(
        Boolean,
        default=True,
        nullable=False,
    )

    # Relationships
    products: Mapped[list["CatalogProduct"]] = relationship(
        "CatalogProduct",
        back_populates="category",
    )


class CatalogBrand(Base):
    """Eyewear manufacturer / brand entities."""

    __tablename__ = "catalog_brands"

    id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )
    name: Mapped[str] = mapped_column(
        String(100),
        unique=True,
        nullable=False,
    )
    slug: Mapped[str] = mapped_column(
        String(100),
        unique=True,
        nullable=False,
        index=True,
    )
    is_active: Mapped[bool] = mapped_column(
        Boolean,
        default=True,
        nullable=False,
    )

    # Relationships
    products: Mapped[list["CatalogProduct"]] = relationship(
        "CatalogProduct",
        back_populates="brand",
    )


class CatalogProduct(Base):
    """
    Standardized eyewear product catalogue item specifying physical dimensions,
    materials, style shape, and pricing in Indian Rupees (INR).
    """

    __tablename__ = "catalog_products"

    id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )
    sku: Mapped[str] = mapped_column(
        String(64),
        unique=True,
        nullable=False,
        index=True,
    )
    name: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
        index=True,
    )
    brand_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("catalog_brands.id", ondelete="RESTRICT"),
        nullable=False,
        index=True,
    )
    category_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("catalog_categories.id", ondelete="RESTRICT"),
        nullable=False,
        index=True,
    )
    frame_type: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        index=True,
    )  # full_rim, half_rim, rimless
    frame_material: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        index=True,
    )  # acetate, metal, tr90, titanium, plastic
    frame_shape: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        index=True,
    )  # rectangular, round, square, aviator, oval, cat_eye
    gender_target: Mapped[str] = mapped_column(
        String(20),
        default="unisex",
        nullable=False,
    )  # unisex, men, women, kids
    frame_width_mm: Mapped[float | None] = mapped_column(
        Float,
        nullable=True,
    )
    bridge_width_mm: Mapped[float | None] = mapped_column(
        Float,
        nullable=True,
    )
    temple_length_mm: Mapped[float | None] = mapped_column(
        Float,
        nullable=True,
    )
    lens_width_mm: Mapped[float | None] = mapped_column(
        Float,
        nullable=True,
    )
    lens_height_mm: Mapped[float | None] = mapped_column(
        Float,
        nullable=True,
    )
    base_price_inr: Mapped[Decimal] = mapped_column(
        Numeric(10, 2),
        nullable=False,
    )
    is_active: Mapped[bool] = mapped_column(
        Boolean,
        default=True,
        nullable=False,
        index=True,
    )
    image_url: Mapped[str | None] = mapped_column(
        String(500),
        nullable=True,
    )
    # Virtual Try-On Asset Calibration & Geometry Metadata
    try_on_asset_url: Mapped[str | None] = mapped_column(
        String(500),
        nullable=True,
    )
    try_on_asset_type: Mapped[str | None] = mapped_column(
        String(50),
        default="2d_png",
        nullable=True,
    )
    frame_colors: Mapped[str | None] = mapped_column(
        String(500),
        default="#111827:Classic Black,#78350F:Amber Tortoise,#D97706:Polished Gold,#475569:Gunmetal Silver,#1E3A8A:Deep Navy",
        nullable=True,
    )
    left_lens_center_x: Mapped[float | None] = mapped_column(
        Float,
        default=0.2875,
        nullable=True,
    )
    left_lens_center_y: Mapped[float | None] = mapped_column(
        Float,
        default=0.5,
        nullable=True,
    )
    right_lens_center_x: Mapped[float | None] = mapped_column(
        Float,
        default=0.7125,
        nullable=True,
    )
    right_lens_center_y: Mapped[float | None] = mapped_column(
        Float,
        default=0.5,
        nullable=True,
    )
    bridge_center_x: Mapped[float | None] = mapped_column(
        Float,
        default=0.5,
        nullable=True,
    )
    bridge_center_y: Mapped[float | None] = mapped_column(
        Float,
        default=0.48,
        nullable=True,
    )
    asset_scale: Mapped[float] = mapped_column(
        Float,
        default=1.0,
        nullable=False,
    )
    asset_rotation_offset: Mapped[float] = mapped_column(
        Float,
        default=0.0,
        nullable=False,
    )
    asset_version: Mapped[str] = mapped_column(
        String(20),
        default="1.0.0",
        nullable=False,
    )
    description: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(UTC),
        nullable=False,
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(UTC),
        onupdate=lambda: datetime.now(UTC),
        nullable=False,
    )

    # Relationships
    brand: Mapped["CatalogBrand"] = relationship(
        "CatalogBrand",
        back_populates="products",
    )
    category: Mapped["CatalogCategory"] = relationship(
        "CatalogCategory",
        back_populates="products",
    )
    inventories: Mapped[list["ShopInventory"]] = relationship(
        "ShopInventory",
        back_populates="product",
        cascade="all, delete-orphan",
    )


class Shop(Base):
    """Optical retail store, community vision center, or partner kiosk."""

    __tablename__ = "shops"

    id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )
    name: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
    )
    location_city: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
        index=True,
    )
    location_state: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
        index=True,
    )
    owner_user_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("users.id", ondelete="RESTRICT"),
        nullable=False,
        index=True,
    )
    phone_number: Mapped[str | None] = mapped_column(
        String(50),
        nullable=True,
    )
    is_active: Mapped[bool] = mapped_column(
        Boolean,
        default=True,
        nullable=False,
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(UTC),
        nullable=False,
    )

    # Relationships
    owner: Mapped["User"] = relationship(
        "User",
        foreign_keys=[owner_user_id],
    )
    inventories: Mapped[list["ShopInventory"]] = relationship(
        "ShopInventory",
        back_populates="shop",
        cascade="all, delete-orphan",
    )


class ShopInventory(Base):
    """Live inventory tracking for a product at a specific shop."""

    __tablename__ = "shop_inventory"
    __table_args__ = (
        UniqueConstraint("shop_id", "product_id", name="uq_shop_product_inventory"),
        CheckConstraint("stock_quantity >= 0", name="ck_shop_inventory_stock_non_negative"),
        CheckConstraint("reserved_quantity >= 0", name="ck_shop_inventory_reserved_non_negative"),
        CheckConstraint(
            "reserved_quantity <= stock_quantity", name="ck_shop_inventory_reserved_le_stock"
        ),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )
    shop_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("shops.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    product_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("catalog_products.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    stock_quantity: Mapped[int] = mapped_column(
        Integer,
        default=0,
        nullable=False,
    )
    reserved_quantity: Mapped[int] = mapped_column(
        Integer,
        default=0,
        nullable=False,
    )
    low_stock_threshold: Mapped[int] = mapped_column(
        Integer,
        default=3,
        nullable=False,
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(UTC),
        onupdate=lambda: datetime.now(UTC),
        nullable=False,
    )

    # Relationships
    shop: Mapped["Shop"] = relationship(
        "Shop",
        back_populates="inventories",
    )
    product: Mapped["CatalogProduct"] = relationship(
        "CatalogProduct",
        back_populates="inventories",
    )
    transactions: Mapped[list["InventoryTransaction"]] = relationship(
        "InventoryTransaction",
        back_populates="inventory",
        cascade="all, delete-orphan",
    )


class InventoryTransaction(Base):
    """Audit log of stock quantity changes and business reasons."""

    __tablename__ = "inventory_transactions"

    id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )
    inventory_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("shop_inventory.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    operator_user_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
    )
    quantity_delta: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
    )
    reason: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
    )  # RESTOCK, SALE, ADJUSTMENT, RETURN
    notes: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )
    occurred_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(UTC),
        nullable=False,
    )

    # Relationships
    inventory: Mapped["ShopInventory"] = relationship(
        "ShopInventory",
        back_populates="transactions",
    )
    operator: Mapped["User"] = relationship(
        "User",
        foreign_keys=[operator_user_id],
    )

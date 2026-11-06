import uuid
from datetime import UTC, datetime
from typing import TYPE_CHECKING

from sqlalchemy import (
    Boolean,
    DateTime,
    Float,
    ForeignKey,
    Integer,
    String,
    Text,
    UniqueConstraint,
    Uuid,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database.base import Base

if TYPE_CHECKING:
    from app.models.catalog import CatalogProduct
    from app.models.screening_session import ScreeningSession
    from app.models.user import User


class TryOnSession(Base):
    """
    Virtual try-on interactive AR session state tracking customer frame selections,
    scale preferences, camera orientation, and capture counts.
    """

    __tablename__ = "try_on_sessions"

    id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )
    user_id: Mapped[uuid.UUID | None] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    screening_session_id: Mapped[uuid.UUID | None] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("screening_sessions.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    selected_product_id: Mapped[uuid.UUID | None] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("catalog_products.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    selected_color: Mapped[str] = mapped_column(
        String(50),
        default="#111827",
        nullable=False,
    )
    selected_scale: Mapped[float] = mapped_column(
        Float,
        default=1.0,
        nullable=False,
    )
    selected_offset_y: Mapped[float] = mapped_column(
        Float,
        default=0.0,
        nullable=False,
    )
    camera_facing: Mapped[str] = mapped_column(
        String(20),
        default="user",
        nullable=False,
    )
    device_type: Mapped[str] = mapped_column(
        String(50),
        default="desktop",
        nullable=False,
    )
    snapshots_count: Mapped[int] = mapped_column(
        Integer,
        default=0,
        nullable=False,
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
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(UTC),
        onupdate=lambda: datetime.now(UTC),
        nullable=False,
    )

    # Relationships
    user: Mapped["User | None"] = relationship("User", foreign_keys=[user_id])
    product: Mapped["CatalogProduct | None"] = relationship(
        "CatalogProduct", foreign_keys=[selected_product_id]
    )
    screening_session: Mapped["ScreeningSession | None"] = relationship(
        "ScreeningSession", foreign_keys=[screening_session_id]
    )
    snapshots: Mapped[list["TryOnSnapshot"]] = relationship(
        "TryOnSnapshot", back_populates="session", cascade="all, delete-orphan"
    )


class UserEyewearFavourite(Base):
    """
    Authenticated customer wishlist / favourite frames saved during virtual try-on
    or catalogue browsing for later purchase or optometrist discussion.
    """

    __tablename__ = "user_eyewear_favourites"
    __table_args__ = (
        UniqueConstraint("user_id", "product_id", name="uq_user_product_favourite"),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    product_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("catalog_products.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    selected_color: Mapped[str] = mapped_column(
        String(50),
        default="#111827",
        nullable=False,
    )
    notes: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(UTC),
        nullable=False,
    )

    # Relationships
    user: Mapped["User"] = relationship("User", foreign_keys=[user_id])
    product: Mapped["CatalogProduct"] = relationship(
        "CatalogProduct", foreign_keys=[product_id]
    )


class TryOnSnapshot(Base):
    """
    Metadata recording of a user-initiated AR try-on snapshot preview.
    Biometric video is strictly discarded; only user-triggered preview records are stored.
    """

    __tablename__ = "try_on_snapshots"

    id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )
    session_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("try_on_sessions.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    product_id: Mapped[uuid.UUID | None] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("catalog_products.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    selected_color: Mapped[str] = mapped_column(
        String(50),
        default="#111827",
        nullable=False,
    )
    title: Mapped[str] = mapped_column(
        String(255),
        default="AR Eyewear Preview",
        nullable=False,
    )
    face_detected: Mapped[bool] = mapped_column(
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
    session: Mapped["TryOnSession"] = relationship(
        "TryOnSession", back_populates="snapshots"
    )
    product: Mapped["CatalogProduct | None"] = relationship(
        "CatalogProduct", foreign_keys=[product_id]
    )

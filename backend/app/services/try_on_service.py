import uuid

from sqlalchemy.orm import Session

from app.core.exceptions import EntityNotFoundException, ValidationException
from app.models.catalog import CatalogProduct
from app.models.try_on import TryOnSession, TryOnSnapshot, UserEyewearFavourite
from app.models.user import User
from app.repositories.try_on_repository import TryOnRepository
from app.schemas.catalog import CategoryResponse
from app.schemas.try_on import (
    FavouriteResponse,
    FrameColorOption,
    FrameTryOnAssetResponse,
    TryOnFrameSelectRequest,
    TryOnSessionCreateRequest,
    TryOnSessionResponse,
    TryOnSnapshotRequest,
    TryOnSnapshotResponse,
)


class TryOnService:
    """Business logic for AR Virtual Eyewear Try-On, frame geometry, and session state."""

    @staticmethod
    def _parse_colors(raw_colors: str | None) -> list[FrameColorOption]:
        """Parses color definition string '#HEX:Name,#HEX:Name' into structured list."""
        if not raw_colors:
            return [
                FrameColorOption(hex_code="#111827", name="Classic Black"),
                FrameColorOption(hex_code="#78350F", name="Amber Tortoise"),
                FrameColorOption(hex_code="#475569", name="Gunmetal Silver"),
            ]
        options: list[FrameColorOption] = []
        for item in raw_colors.split(","):
            item = item.strip()
            if not item:
                continue
            if ":" in item:
                hex_c, name = item.split(":", 1)
                options.append(FrameColorOption(hex_code=hex_c.strip(), name=name.strip()))
            else:
                options.append(FrameColorOption(hex_code=item, name=item))
        return options or [FrameColorOption(hex_code="#111827", name="Classic Black")]

    @classmethod
    def format_frame_response(cls, product: CatalogProduct) -> FrameTryOnAssetResponse:
        """Transforms a CatalogProduct into an AR-ready FrameTryOnAssetResponse."""
        colors = cls._parse_colors(product.frame_colors)
        is_available = bool(product.try_on_asset_url)
        notice = None if is_available else "Virtual try-on is not available for this frame yet."

        brand_name = product.brand.name if product.brand else "OptiGuide Brand"
        cat_name = product.category.name if product.category else None

        return FrameTryOnAssetResponse(
            frame_id=product.id,
            sku=product.sku,
            name=product.name,
            brand_name=brand_name,
            category_name=cat_name,
            frame_type=product.frame_type,
            frame_material=product.frame_material,
            frame_shape=product.frame_shape,
            gender_target=product.gender_target,
            base_price_inr=product.base_price_inr,
            is_active=product.is_active,
            in_stock=True,
            image_url=product.image_url,
            description=product.description,
            try_on_asset_url=product.try_on_asset_url,
            try_on_asset_type=product.try_on_asset_type or "2d_png",
            available_colors=colors,
            left_lens_center_x=product.left_lens_center_x or 0.2875,
            left_lens_center_y=product.left_lens_center_y or 0.5,
            right_lens_center_x=product.right_lens_center_x or 0.7125,
            right_lens_center_y=product.right_lens_center_y or 0.5,
            bridge_center_x=product.bridge_center_x or 0.5,
            bridge_center_y=product.bridge_center_y or 0.48,
            asset_scale=product.asset_scale or 1.0,
            asset_rotation_offset=product.asset_rotation_offset or 0.0,
            asset_version=product.asset_version or "1.0.0",
            frame_width_mm=product.frame_width_mm,
            bridge_width_mm=product.bridge_width_mm,
            temple_length_mm=product.temple_length_mm,
            lens_width_mm=product.lens_width_mm,
            lens_height_mm=product.lens_height_mm,
            is_try_on_available=is_available,
            availability_notice=notice,
        )

    @classmethod
    def list_frames(
        cls,
        db: Session,
        shape: str | None = None,
        category: str | None = None,
        gender: str | None = None,
        search: str | None = None,
        limit: int = 50,
        offset: int = 0,
    ) -> list[FrameTryOnAssetResponse]:
        items, _total = TryOnRepository.list_frames(
            db=db,
            shape=shape,
            category=category,
            gender=gender,
            search=search,
            limit=limit,
            offset=offset,
        )
        return [cls.format_frame_response(p) for p in items]

    @classmethod
    def get_frame(cls, db: Session, frame_id: uuid.UUID) -> FrameTryOnAssetResponse:
        product = TryOnRepository.get_frame(db, frame_id)
        if not product or not product.is_active:
            raise EntityNotFoundException("Eyewear frame", frame_id)
        return cls.format_frame_response(product)

    @staticmethod
    def list_categories(db: Session) -> list[CategoryResponse]:
        cats = TryOnRepository.list_categories(db)
        return [
            CategoryResponse(
                id=c.id,
                name=c.name,
                slug=c.slug,
                description=c.description,
                is_active=c.is_active,
            )
            for c in cats
        ]

    # -------------------------------------------------------------------------
    # Sessions
    # -------------------------------------------------------------------------
    @classmethod
    def create_session(
        cls,
        db: Session,
        payload: TryOnSessionCreateRequest,
        user: User | None = None,
    ) -> TryOnSessionResponse:
        # Validate selected product if provided
        selected_prod_id = payload.selected_product_id
        if selected_prod_id:
            prod = TryOnRepository.get_frame(db, selected_prod_id)
            if not prod:
                raise ValidationException(f"Selected frame '{selected_prod_id}' not found.")

        user_id = user.id if user else None
        session = TryOnRepository.create_session(
            db=db,
            user_id=user_id,
            screening_session_id=payload.screening_session_id,
            selected_product_id=selected_prod_id,
            selected_color=payload.selected_color,
            selected_scale=payload.selected_scale,
            selected_offset_y=payload.selected_offset_y,
            camera_facing=payload.camera_facing,
            device_type=payload.device_type,
        )
        return TryOnSessionResponse.model_validate(session)

    @classmethod
    def get_session(cls, db: Session, session_id: uuid.UUID) -> TryOnSessionResponse:
        session = TryOnRepository.get_session(db, session_id)
        if not session or not session.is_active:
            raise EntityNotFoundException("Try-on session", session_id)
        return TryOnSessionResponse.model_validate(session)

    @classmethod
    def select_frame(
        cls,
        db: Session,
        session_id: uuid.UUID,
        payload: TryOnFrameSelectRequest,
    ) -> TryOnSessionResponse:
        session = TryOnRepository.get_session(db, session_id)
        if not session or not session.is_active:
            raise EntityNotFoundException("Try-on session", session_id)

        product = TryOnRepository.get_frame(db, payload.product_id)
        if not product or not product.is_active:
            raise ValidationException(f"Product frame '{payload.product_id}' not found.")

        updated = TryOnRepository.update_session_selection(
            db=db,
            session=session,
            product_id=payload.product_id,
            color=payload.selected_color,
            scale=payload.selected_scale,
            offset_y=payload.selected_offset_y,
        )
        return TryOnSessionResponse.model_validate(updated)

    @classmethod
    def close_session(cls, db: Session, session_id: uuid.UUID) -> dict[str, str]:
        session = TryOnRepository.get_session(db, session_id)
        if session:
            TryOnRepository.close_session(db, session)
        return {"status": "closed", "session_id": str(session_id)}

    # -------------------------------------------------------------------------
    # Favourites
    # -------------------------------------------------------------------------
    @classmethod
    def toggle_favourite(
        cls,
        db: Session,
        user: User,
        product_id: uuid.UUID,
        selected_color: str = "#111827",
        notes: str | None = None,
    ) -> dict:
        product = TryOnRepository.get_frame(db, product_id)
        if not product:
            raise EntityNotFoundException("Eyewear frame", product_id)

        fav, is_added = TryOnRepository.toggle_favourite(
            db=db,
            user_id=user.id,
            product_id=product_id,
            selected_color=selected_color,
            notes=notes,
        )
        return {
            "is_favourite": is_added,
            "action": "added" if is_added else "removed",
            "product_id": str(product_id),
            "favourite_id": str(fav.id) if fav else None,
            "message": "Added to favourites." if is_added else "Removed from favourites.",
        }

    @classmethod
    def list_favourites(cls, db: Session, user: User) -> list[FavouriteResponse]:
        favs = TryOnRepository.list_favourites(db, user.id)
        results: list[FavouriteResponse] = []
        for f in favs:
            results.append(
                FavouriteResponse(
                    id=f.id,
                    user_id=f.user_id,
                    product_id=f.product_id,
                    selected_color=f.selected_color,
                    notes=f.notes,
                    created_at=f.created_at,
                    product=f.product,
                )
            )
        return results

    # -------------------------------------------------------------------------
    # Snapshots
    # -------------------------------------------------------------------------
    @classmethod
    def record_snapshot(
        cls,
        db: Session,
        session_id: uuid.UUID,
        payload: TryOnSnapshotRequest,
    ) -> TryOnSnapshotResponse:
        session = TryOnRepository.get_session(db, session_id)
        if not session or not session.is_active:
            raise EntityNotFoundException("Try-on session", session_id)

        snapshot = TryOnRepository.record_snapshot(
            db=db,
            session_id=session_id,
            product_id=payload.product_id,
            selected_color=payload.selected_color or session.selected_color,
            title=payload.title,
            face_detected=payload.face_detected,
        )
        return TryOnSnapshotResponse.model_validate(snapshot)


import uuid
from datetime import UTC, datetime
from decimal import Decimal

from sqlalchemy import desc, select
from sqlalchemy.orm import Session

from app.models.catalog import CatalogBrand, CatalogCategory, CatalogProduct, Shop, ShopInventory
from app.models.try_on import TryOnSession, TryOnSnapshot, UserEyewearFavourite


class TryOnRepository:
    """Data access repository for AR Virtual Try-On sessions, assets, and favourites."""

    @staticmethod
    def seed_catalogue_if_empty(db: Session) -> None:
        """Seeds real eyewear models, categories, and brands if catalog is empty."""
        try_on_count = db.query(CatalogProduct).filter(CatalogProduct.try_on_asset_url.isnot(None)).count()
        if try_on_count >= 8:
            return

        # 1. Categories
        categories_data = [
            ("Full-Rim", "full-rim", "Complete frame enclosure offering maximum lens stability and rural durability."),
            ("Semi-Rimless", "semi-rimless", "Upper rim support with lower nylon cord suspension for wide downward view."),
            ("Rimless", "rimless", "Featherlight three-piece mount without bezel for an unobstructed field of vision."),
            ("Progressive-Ready", "progressive-ready", "Deep vertical lens profile optimized for multi-focal and bifocal screening recommendations."),
        ]
        cat_map = {}
        for name, slug, descr in categories_data:
            cat = db.query(CatalogCategory).filter(CatalogCategory.slug == slug).first()
            if not cat:
                cat = CatalogCategory(name=name, slug=slug, description=descr, is_active=True)
                db.add(cat)
                db.flush()
            cat_map[slug] = cat

        # 2. Brands
        brands_data = [
            ("OptiCare Bharat", "opticare-bharat"),
            ("Drishti Titanium", "drishti-titanium"),
            ("Vedic Eyewear", "vedic-eyewear"),
            ("Konark Optics", "konark-optics"),
        ]
        brand_map = {}
        for name, slug in brands_data:
            b = db.query(CatalogBrand).filter(CatalogBrand.slug == slug).first()
            if not b:
                b = CatalogBrand(name=name, slug=slug, is_active=True)
                db.add(b)
                db.flush()
            brand_map[slug] = b

        # 3. Real Catalogue Products with accurate AR frame geometry and dimensions
        products_data = [
            {
                "sku": "OPT-VDC-RECT-01",
                "name": "Vedic Classic Rectangular",
                "brand_slug": "vedic-eyewear",
                "cat_slug": "full-rim",
                "frame_type": "full_rim",
                "frame_material": "acetate",
                "frame_shape": "rectangular",
                "gender_target": "unisex",
                "frame_width_mm": 138.0,
                "lens_width_mm": 52.0,
                "lens_height_mm": 38.0,
                "bridge_width_mm": 18.0,
                "temple_length_mm": 142.0,
                "base_price_inr": Decimal("1199.00"),
                "image_url": "/assets/frames/frame-rectangular.svg",
                "try_on_asset_url": "/assets/frames/frame-rectangular.svg",
                "try_on_asset_type": "2d_svg",
                "frame_colors": "#111827:Classic Black,#78350F:Amber Tortoise,#475569:Slate Grey,#1E3A8A:Deep Navy",
                "left_lens_center_x": 0.2875,
                "left_lens_center_y": 0.5,
                "right_lens_center_x": 0.7125,
                "right_lens_center_y": 0.5,
                "bridge_center_x": 0.5,
                "bridge_center_y": 0.48,
                "asset_scale": 1.0,
                "description": "Ergonomic high-density cellulose acetate rectangular frame with 5-barrel German hinges. Balanced for wide Indian facial profiles.",
            },
            {
                "sku": "OPT-GRM-RND-02",
                "name": "Gramin Heritage Round",
                "brand_slug": "opticare-bharat",
                "cat_slug": "full-rim",
                "frame_type": "full_rim",
                "frame_material": "metal",
                "frame_shape": "round",
                "gender_target": "unisex",
                "frame_width_mm": 134.0,
                "lens_width_mm": 48.0,
                "lens_height_mm": 46.0,
                "bridge_width_mm": 20.0,
                "temple_length_mm": 140.0,
                "base_price_inr": Decimal("950.00"),
                "image_url": "/assets/frames/frame-round.svg",
                "try_on_asset_url": "/assets/frames/frame-round.svg",
                "try_on_asset_type": "2d_svg",
                "frame_colors": "#D97706:Antique Gold,#475569:Gunmetal,#111827:Matte Black,#B45309:Copper Bronze",
                "left_lens_center_x": 0.29,
                "left_lens_center_y": 0.5,
                "right_lens_center_x": 0.71,
                "right_lens_center_y": 0.5,
                "bridge_center_x": 0.5,
                "bridge_center_y": 0.47,
                "asset_scale": 1.0,
                "description": "Vintage circular wire rim crafted from rust-resistant monel alloy with hypoallergenic silicone nose saddles.",
            },
            {
                "sku": "OPT-KLY-SEMI-03",
                "name": "Kalyan Progressive Semi-Rimless",
                "brand_slug": "drishti-titanium",
                "cat_slug": "semi-rimless",
                "frame_type": "semi_rimless",
                "frame_material": "titanium",
                "frame_shape": "rectangular",
                "gender_target": "unisex",
                "frame_width_mm": 140.0,
                "lens_width_mm": 54.0,
                "lens_height_mm": 39.0,
                "bridge_width_mm": 17.0,
                "temple_length_mm": 145.0,
                "base_price_inr": Decimal("2850.00"),
                "image_url": "/assets/frames/frame-semi-rimless.svg",
                "try_on_asset_url": "/assets/frames/frame-semi-rimless.svg",
                "try_on_asset_type": "2d_svg",
                "frame_colors": "#111827:Satin Black,#475569:Titanium Grey,#1E3A8A:Midnight Blue",
                "left_lens_center_x": 0.285,
                "left_lens_center_y": 0.48,
                "right_lens_center_x": 0.715,
                "right_lens_center_y": 0.48,
                "bridge_center_x": 0.5,
                "bridge_center_y": 0.45,
                "asset_scale": 1.02,
                "description": "Ultra-light Japanese aerospace titanium brow bar with clear lower monofilament. Optimal vertical depth for bifocal and progressive prescriptions.",
            },
            {
                "sku": "OPT-SHY-SQR-04",
                "name": "Sahyadri BlueShield Square",
                "brand_slug": "opticare-bharat",
                "cat_slug": "full-rim",
                "frame_type": "full_rim",
                "frame_material": "tr90",
                "frame_shape": "square",
                "gender_target": "unisex",
                "frame_width_mm": 142.0,
                "lens_width_mm": 53.0,
                "lens_height_mm": 44.0,
                "bridge_width_mm": 19.0,
                "temple_length_mm": 145.0,
                "base_price_inr": Decimal("1499.00"),
                "image_url": "/assets/frames/frame-square.svg",
                "try_on_asset_url": "/assets/frames/frame-square.svg",
                "try_on_asset_type": "2d_svg",
                "frame_colors": "#111827:Matte Black,#1E40AF:Sapphire Blue,#374151:Charcoal,#065F46:Forest Green",
                "left_lens_center_x": 0.285,
                "left_lens_center_y": 0.51,
                "right_lens_center_x": 0.715,
                "right_lens_center_y": 0.51,
                "bridge_center_x": 0.5,
                "bridge_center_y": 0.49,
                "asset_scale": 1.0,
                "description": "Flexible Swiss TR90 memory thermoplastic frame engineered for all-day digital comfort, high impact endurance, and zero slippage.",
            },
            {
                "sku": "OPT-UTK-RIML-05",
                "name": "Utkal Rimless Silhouette",
                "brand_slug": "drishti-titanium",
                "cat_slug": "rimless",
                "frame_type": "rimless",
                "frame_material": "titanium",
                "frame_shape": "oval",
                "gender_target": "unisex",
                "frame_width_mm": 136.0,
                "lens_width_mm": 51.0,
                "lens_height_mm": 36.0,
                "bridge_width_mm": 18.0,
                "temple_length_mm": 140.0,
                "base_price_inr": Decimal("3200.00"),
                "image_url": "/assets/frames/frame-rimless.svg",
                "try_on_asset_url": "/assets/frames/frame-rimless.svg",
                "try_on_asset_type": "2d_svg",
                "frame_colors": "#94A3B8:Brushed Silver,#D97706:Champagne Gold,#111827:Jet Black",
                "left_lens_center_x": 0.2875,
                "left_lens_center_y": 0.5,
                "right_lens_center_x": 0.7125,
                "right_lens_center_y": 0.5,
                "bridge_center_x": 0.5,
                "bridge_center_y": 0.48,
                "asset_scale": 0.98,
                "description": "Minimalist rimless architecture with beta-titanium compression mount bridge. Weighs only 8.4 grams for completely unobtrusive vision.",
            },
            {
                "sku": "OPT-PRT-AVTR-06",
                "name": "Pratham Everyday Aviator",
                "brand_slug": "opticare-bharat",
                "cat_slug": "full-rim",
                "frame_type": "full_rim",
                "frame_material": "metal",
                "frame_shape": "aviator",
                "gender_target": "unisex",
                "frame_width_mm": 144.0,
                "lens_width_mm": 58.0,
                "lens_height_mm": 49.0,
                "bridge_width_mm": 15.0,
                "temple_length_mm": 145.0,
                "base_price_inr": Decimal("1350.00"),
                "image_url": "/assets/frames/frame-aviator.svg",
                "try_on_asset_url": "/assets/frames/frame-aviator.svg",
                "try_on_asset_type": "2d_svg",
                "frame_colors": "#D97706:Pilot Gold,#475569:Military Gunmetal,#111827:Matte Black",
                "left_lens_center_x": 0.28,
                "left_lens_center_y": 0.52,
                "right_lens_center_x": 0.72,
                "right_lens_center_y": 0.52,
                "bridge_center_x": 0.5,
                "bridge_center_y": 0.43,
                "asset_scale": 1.04,
                "description": "Iconic double-bridge stainless steel aviator with broad vertical eye coverage. Rugged solder joints suited for agrarian sunlight conditions.",
            },
            {
                "sku": "OPT-KNR-WAYF-07",
                "name": "Konark Wayfarer Bold",
                "brand_slug": "konark-optics",
                "cat_slug": "full-rim",
                "frame_type": "full_rim",
                "frame_material": "acetate",
                "frame_shape": "wayfarer",
                "gender_target": "unisex",
                "frame_width_mm": 143.0,
                "lens_width_mm": 54.0,
                "lens_height_mm": 43.0,
                "bridge_width_mm": 19.0,
                "temple_length_mm": 145.0,
                "base_price_inr": Decimal("1750.00"),
                "image_url": "/assets/frames/frame-wayfarer.svg",
                "try_on_asset_url": "/assets/frames/frame-wayfarer.svg",
                "try_on_asset_type": "2d_svg",
                "frame_colors": "#111827:Ebony Black,#78350F:Havana Tortoise,#991B1B:Oxblood Wine",
                "left_lens_center_x": 0.285,
                "left_lens_center_y": 0.5,
                "right_lens_center_x": 0.715,
                "right_lens_center_y": 0.5,
                "bridge_center_x": 0.5,
                "bridge_center_y": 0.47,
                "asset_scale": 1.02,
                "description": "Sculpted thick-rim acetate wayfarer with signature metal temple rivet accents. Offers structured presence and exceptional facial contouring.",
            },
            {
                "sku": "OPT-CLK-CATE-08",
                "name": "Chilika Cat-Eye Elegance",
                "brand_slug": "konark-optics",
                "cat_slug": "full-rim",
                "frame_type": "full_rim",
                "frame_material": "acetate",
                "frame_shape": "cat_eye",
                "gender_target": "women",
                "frame_width_mm": 137.0,
                "lens_width_mm": 52.0,
                "lens_height_mm": 41.0,
                "bridge_width_mm": 17.0,
                "temple_length_mm": 140.0,
                "base_price_inr": Decimal("1899.00"),
                "image_url": "/assets/frames/frame-cat-eye.svg",
                "try_on_asset_url": "/assets/frames/frame-cat-eye.svg",
                "try_on_asset_type": "2d_svg",
                "frame_colors": "#831843:Burgundy Plum,#111827:Midnight Onyx,#78350F:Amber Pearl",
                "left_lens_center_x": 0.285,
                "left_lens_center_y": 0.5,
                "right_lens_center_x": 0.715,
                "right_lens_center_y": 0.5,
                "bridge_center_x": 0.5,
                "bridge_center_y": 0.47,
                "asset_scale": 1.0,
                "description": "Gently upswept cat-eye silhouette designed to flatter oval, diamond, and round face geometries. Polished hand-buffed acetate finish.",
            },
        ]

        for p_data in products_data:
            cat_slug = p_data.pop("cat_slug")
            brand_slug = p_data.pop("brand_slug")
            existing = db.query(CatalogProduct).filter(CatalogProduct.sku == p_data["sku"]).first()
            if existing:
                continue
            cat = cat_map[cat_slug]
            brand = brand_map[brand_slug]
            prod = CatalogProduct(
                brand_id=brand.id,
                category_id=cat.id,
                is_active=True,
                **p_data,
            )
            db.add(prod)

        db.commit()

    @staticmethod
    def get_frame(db: Session, frame_id: uuid.UUID) -> CatalogProduct | None:
        """Retrieves a single product frame by UUID."""
        return db.query(CatalogProduct).filter(CatalogProduct.id == frame_id).first()

    @staticmethod
    def list_frames(
        db: Session,
        shape: str | None = None,
        category: str | None = None,
        gender: str | None = None,
        search: str | None = None,
        limit: int = 50,
        offset: int = 0,
    ) -> tuple[list[CatalogProduct], int]:
        """Queries active catalogue frames with filtering and pagination."""
        TryOnRepository.seed_catalogue_if_empty(db)

        query = db.query(CatalogProduct).filter(
            CatalogProduct.is_active == True,  # noqa: E712
            CatalogProduct.try_on_asset_url.isnot(None),
        )

        if shape and shape.lower() != "all":
            query = query.filter(CatalogProduct.frame_shape == shape.lower())

        if category and category.lower() != "all":
            # Match category name or slug
            query = query.join(CatalogCategory).filter(
                (CatalogCategory.slug == category.lower()) | (CatalogCategory.name.ilike(f"%{category}%"))
            )

        if gender and gender.lower() != "all":
            query = query.filter(
                (CatalogProduct.gender_target == gender.lower()) | (CatalogProduct.gender_target == "unisex")
            )

        if search:
            query = query.filter(
                (CatalogProduct.name.ilike(f"%{search}%")) | (CatalogProduct.sku.ilike(f"%{search}%"))
            )

        total = query.count()
        items = query.order_by(CatalogProduct.name.asc()).offset(offset).limit(limit).all()
        return items, total

    @staticmethod
    def list_categories(db: Session) -> list[CatalogCategory]:
        """Returns all active product categories."""
        TryOnRepository.seed_catalogue_if_empty(db)
        return db.query(CatalogCategory).filter(CatalogCategory.is_active == True).order_by(CatalogCategory.name.asc()).all()  # noqa: E712

    # -------------------------------------------------------------------------
    # Try-On Sessions
    # -------------------------------------------------------------------------
    @staticmethod
    def create_session(
        db: Session,
        user_id: uuid.UUID | None,
        screening_session_id: uuid.UUID | None,
        selected_product_id: uuid.UUID | None,
        selected_color: str = "#111827",
        selected_scale: float = 1.0,
        selected_offset_y: float = 0.0,
        camera_facing: str = "user",
        device_type: str = "desktop",
    ) -> TryOnSession:
        now = datetime.now(UTC)
        session = TryOnSession(
            user_id=user_id,
            screening_session_id=screening_session_id,
            selected_product_id=selected_product_id,
            selected_color=selected_color,
            selected_scale=selected_scale,
            selected_offset_y=selected_offset_y,
            camera_facing=camera_facing,
            device_type=device_type,
            is_active=True,
            created_at=now,
            updated_at=now,
        )
        db.add(session)
        db.commit()
        db.refresh(session)
        return session

    @staticmethod
    def get_session(db: Session, session_id: uuid.UUID) -> TryOnSession | None:
        return db.query(TryOnSession).filter(TryOnSession.id == session_id).first()

    @staticmethod
    def update_session_selection(
        db: Session,
        session: TryOnSession,
        product_id: uuid.UUID,
        color: str | None = None,
        scale: float | None = None,
        offset_y: float | None = None,
    ) -> TryOnSession:
        session.selected_product_id = product_id
        if color is not None:
            session.selected_color = color
        if scale is not None:
            session.selected_scale = scale
        if offset_y is not None:
            session.selected_offset_y = offset_y
        session.updated_at = datetime.now(UTC)
        db.commit()
        db.refresh(session)
        return session

    @staticmethod
    def close_session(db: Session, session: TryOnSession) -> None:
        session.is_active = False
        session.updated_at = datetime.now(UTC)
        db.commit()

    # -------------------------------------------------------------------------
    # Favourites
    # -------------------------------------------------------------------------
    @staticmethod
    def toggle_favourite(
        db: Session,
        user_id: uuid.UUID,
        product_id: uuid.UUID,
        selected_color: str = "#111827",
        notes: str | None = None,
    ) -> tuple[UserEyewearFavourite | None, bool]:
        """Toggles user favourite for a frame. Returns (favourite_instance, is_added)."""
        existing = (
            db.query(UserEyewearFavourite)
            .filter(
                UserEyewearFavourite.user_id == user_id,
                UserEyewearFavourite.product_id == product_id,
            )
            .first()
        )
        if existing:
            db.delete(existing)
            db.commit()
            return None, False

        fav = UserEyewearFavourite(
            user_id=user_id,
            product_id=product_id,
            selected_color=selected_color,
            notes=notes,
            created_at=datetime.now(UTC),
        )
        db.add(fav)
        db.commit()
        db.refresh(fav)
        return fav, True

    @staticmethod
    def list_favourites(db: Session, user_id: uuid.UUID) -> list[UserEyewearFavourite]:
        return (
            db.query(UserEyewearFavourite)
            .filter(UserEyewearFavourite.user_id == user_id)
            .order_by(desc(UserEyewearFavourite.created_at))
            .all()
        )

    # -------------------------------------------------------------------------
    # Snapshots
    # -------------------------------------------------------------------------
    @staticmethod
    def record_snapshot(
        db: Session,
        session_id: uuid.UUID,
        product_id: uuid.UUID | None,
        selected_color: str = "#111827",
        title: str = "AR Eyewear Preview",
        face_detected: bool = True,
    ) -> TryOnSnapshot:
        snapshot = TryOnSnapshot(
            session_id=session_id,
            product_id=product_id,
            selected_color=selected_color,
            title=title,
            face_detected=face_detected,
            created_at=datetime.now(UTC),
        )
        db.add(snapshot)

        # Update session count
        session = db.query(TryOnSession).filter(TryOnSession.id == session_id).first()
        if session:
            session.snapshots_count += 1
            session.updated_at = datetime.now(UTC)

        db.commit()
        db.refresh(snapshot)
        return snapshot

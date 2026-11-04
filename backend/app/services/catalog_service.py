import uuid
from datetime import UTC, datetime

from sqlalchemy.orm import Session

from app.core.exceptions import (
    EntityNotFoundException,
    ForbiddenException,
    ValidationException,
)
from app.models.catalog import (
    CatalogBrand,
    CatalogCategory,
    CatalogProduct,
    InventoryTransaction,
    Shop,
    ShopInventory,
)
from app.models.user import User
from app.repositories.catalog_repository import CatalogRepository
from app.schemas.auth import UserRole
from app.schemas.catalog import (
    BrandCreateRequest,
    BrandResponse,
    CategoryCreateRequest,
    CategoryResponse,
    InventoryTransactionResponse,
    ProductCreateRequest,
    ProductResponse,
    ProductUpdateRequest,
    ShopCreateRequest,
    ShopInventoryAdjustRequest,
    ShopInventoryResponse,
    ShopResponse,
)


class CatalogService:
    """Business logic for product categories, brands, frame models, shops, and live stock adjustments."""

    # -------------------------------------------------------------------------
    # Categories & Brands
    # -------------------------------------------------------------------------
    @staticmethod
    def create_category(db: Session, payload: CategoryCreateRequest) -> CategoryResponse:
        existing = CatalogRepository.get_category_by_slug(db, payload.slug)
        if existing:
            raise ValidationException(f"Category with slug '{payload.slug}' already exists.")
        category = CatalogCategory(
            name=payload.name.strip(),
            slug=payload.slug.strip().lower(),
            description=payload.description.strip() if payload.description else None,
            is_active=True,
        )
        created = CatalogRepository.create_category(db, category)
        return CategoryResponse.model_validate(created)

    @staticmethod
    def list_categories(db: Session, active_only: bool = True) -> list[CategoryResponse]:
        categories = CatalogRepository.list_categories(db, active_only=active_only)
        return [CategoryResponse.model_validate(c) for c in categories]

    @staticmethod
    def create_brand(db: Session, payload: BrandCreateRequest) -> BrandResponse:
        existing = CatalogRepository.get_brand_by_slug(db, payload.slug)
        if existing:
            raise ValidationException(f"Brand with slug '{payload.slug}' already exists.")
        brand = CatalogBrand(
            name=payload.name.strip(),
            slug=payload.slug.strip().lower(),
            is_active=True,
        )
        created = CatalogRepository.create_brand(db, brand)
        return BrandResponse.model_validate(created)

    @staticmethod
    def list_brands(db: Session, active_only: bool = True) -> list[BrandResponse]:
        brands = CatalogRepository.list_brands(db, active_only=active_only)
        return [BrandResponse.model_validate(b) for b in brands]

    # -------------------------------------------------------------------------
    # Products
    # -------------------------------------------------------------------------
    @staticmethod
    def create_product(db: Session, payload: ProductCreateRequest) -> ProductResponse:
        # Check SKU uniqueness
        if CatalogRepository.get_product_by_sku(db, payload.sku):
            raise ValidationException(f"Product with SKU '{payload.sku}' already exists.")

        # Check Category & Brand existence
        brand = CatalogRepository.get_brand_by_id(db, payload.brand_id)
        if not brand:
            raise EntityNotFoundException("CatalogBrand", str(payload.brand_id))

        category = CatalogRepository.get_category_by_id(db, payload.category_id)
        if not category:
            raise EntityNotFoundException("CatalogCategory", str(payload.category_id))

        now = datetime.now(UTC)
        product = CatalogProduct(
            sku=payload.sku.strip().upper(),
            name=payload.name.strip(),
            brand_id=brand.id,
            category_id=category.id,
            frame_type=payload.frame_type.strip().lower(),
            frame_material=payload.frame_material.strip().lower(),
            frame_shape=payload.frame_shape.strip().lower(),
            gender_target=payload.gender_target,
            frame_width_mm=payload.frame_width_mm,
            bridge_width_mm=payload.bridge_width_mm,
            temple_length_mm=payload.temple_length_mm,
            lens_width_mm=payload.lens_width_mm,
            lens_height_mm=payload.lens_height_mm,
            base_price_inr=payload.base_price_inr,
            image_url=payload.image_url.strip() if payload.image_url else None,
            description=payload.description.strip() if payload.description else None,
            is_active=True,
            created_at=now,
            updated_at=now,
        )
        created = CatalogRepository.create_product(db, product)
        resp = ProductResponse.model_validate(created)
        resp.brand_name = brand.name
        resp.category_name = category.name
        return resp

    @staticmethod
    def update_product(
        db: Session, product_id: uuid.UUID, payload: ProductUpdateRequest
    ) -> ProductResponse:
        product = CatalogRepository.get_product_by_id(db, product_id)
        if not product:
            raise EntityNotFoundException("CatalogProduct", str(product_id))

        update_dict = payload.model_dump(exclude_unset=True)
        for key, val in update_dict.items():
            setattr(product, key, val)

        updated = CatalogRepository.update_product(db, product)
        brand = CatalogRepository.get_brand_by_id(db, updated.brand_id)
        category = CatalogRepository.get_category_by_id(db, updated.category_id)
        resp = ProductResponse.model_validate(updated)
        resp.brand_name = brand.name if brand else None
        resp.category_name = category.name if category else None
        return resp

    @staticmethod
    def get_product(db: Session, product_id: uuid.UUID) -> ProductResponse:
        product = CatalogRepository.get_product_by_id(db, product_id)
        if not product:
            raise EntityNotFoundException("CatalogProduct", str(product_id))

        brand = CatalogRepository.get_brand_by_id(db, product.brand_id)
        category = CatalogRepository.get_category_by_id(db, product.category_id)
        resp = ProductResponse.model_validate(product)
        resp.brand_name = brand.name if brand else None
        resp.category_name = category.name if category else None
        return resp

    @staticmethod
    def search_products(
        db: Session,
        query: str | None = None,
        category_id: uuid.UUID | None = None,
        brand_id: uuid.UUID | None = None,
        frame_type: str | None = None,
        frame_material: str | None = None,
        frame_shape: str | None = None,
        gender_target: str | None = None,
        min_price: float | None = None,
        max_price: float | None = None,
        is_active: bool = True,
        limit: int = 20,
        offset: int = 0,
    ) -> tuple[list[ProductResponse], int]:
        items, total = CatalogRepository.search_products(
            db=db,
            query=query,
            category_id=category_id,
            brand_id=brand_id,
            frame_type=frame_type.strip().lower() if frame_type else None,
            frame_material=frame_material.strip().lower() if frame_material else None,
            frame_shape=frame_shape.strip().lower() if frame_shape else None,
            gender_target=gender_target.strip().lower() if gender_target else None,
            min_price=min_price,
            max_price=max_price,
            is_active=is_active,
            limit=limit,
            offset=offset,
        )
        results = []
        for p in items:
            brand = CatalogRepository.get_brand_by_id(db, p.brand_id)
            category = CatalogRepository.get_category_by_id(db, p.category_id)
            resp = ProductResponse.model_validate(p)
            resp.brand_name = brand.name if brand else None
            resp.category_name = category.name if category else None
            results.append(resp)
        return results, total

    # -------------------------------------------------------------------------
    # Shops & Inventory
    # -------------------------------------------------------------------------
    @staticmethod
    def create_shop(db: Session, user: User, payload: ShopCreateRequest) -> ShopResponse:
        allowed_roles = {UserRole.SHOPKEEPER.value, UserRole.ADMIN.value}
        if user.role not in allowed_roles:
            raise ForbiddenException(
                "Only registered shopkeepers or administrators can create shops."
            )

        shop = Shop(
            name=payload.name.strip(),
            location_city=payload.location_city.strip(),
            location_state=payload.location_state.strip(),
            owner_user_id=user.id,
            phone_number=payload.phone_number.strip() if payload.phone_number else None,
            is_active=True,
            created_at=datetime.now(UTC),
        )
        created = CatalogRepository.create_shop(db, shop)
        return ShopResponse.model_validate(created)

    @staticmethod
    def list_my_shops(db: Session, user: User) -> list[ShopResponse]:
        shops = CatalogRepository.list_shops_by_owner(db, user.id)
        return [ShopResponse.model_validate(s) for s in shops]

    @staticmethod
    def adjust_inventory(
        db: Session, user: User, shop_id: uuid.UUID, payload: ShopInventoryAdjustRequest
    ) -> ShopInventoryResponse:
        shop = CatalogRepository.get_shop_by_id(db, shop_id)
        if not shop:
            raise EntityNotFoundException("Shop", str(shop_id))

        if shop.owner_user_id != user.id and user.role != UserRole.ADMIN.value:
            raise ForbiddenException(
                "Access denied: You are not the authorized owner of this shop."
            )

        product = CatalogRepository.get_product_by_id(db, payload.product_id)
        if not product:
            raise EntityNotFoundException("CatalogProduct", str(payload.product_id))

        now = datetime.now(UTC)

        try:
            inventory = CatalogRepository.get_inventory(db, shop.id, product.id, for_update=True)

            if not inventory:
                if payload.quantity_delta < 0:
                    raise ValidationException(
                        "Cannot deduct stock. Product is currently not stocked at this shop."
                    )
                inventory = ShopInventory(
                    shop_id=shop.id,
                    product_id=product.id,
                    stock_quantity=payload.quantity_delta,
                    reserved_quantity=0,
                    low_stock_threshold=3,
                    updated_at=now,
                )
                db.add(inventory)
                db.flush()
            else:
                new_quantity = inventory.stock_quantity + payload.quantity_delta
                if new_quantity < 0:
                    raise ValidationException(
                        f"Insufficient stock: Current stock is {inventory.stock_quantity}. "
                        f"A delta of {payload.quantity_delta} would result in negative inventory ({new_quantity})."
                    )
                if new_quantity < inventory.reserved_quantity:
                    raise ValidationException(
                        f"Cannot reduce stock to {new_quantity}: {inventory.reserved_quantity} units are "
                        "currently reserved for pending allocations."
                    )
                inventory.stock_quantity = new_quantity
                inventory.updated_at = now
                db.add(inventory)
                db.flush()

            # Record transaction audit
            tx = InventoryTransaction(
                inventory_id=inventory.id,
                operator_user_id=user.id,
                quantity_delta=payload.quantity_delta,
                reason=payload.reason,
                notes=payload.notes.strip() if payload.notes else None,
                occurred_at=now,
            )
            db.add(tx)
            db.commit()
            db.refresh(inventory)
        except Exception:
            db.rollback()
            raise

        available_qty = max(0, inventory.stock_quantity - inventory.reserved_quantity)
        is_low = inventory.stock_quantity <= inventory.low_stock_threshold

        resp = ShopInventoryResponse.model_validate(inventory)
        resp.product_sku = product.sku
        resp.product_name = product.name
        resp.available_quantity = available_qty
        resp.is_low_stock = is_low
        return resp

    @staticmethod
    def list_shop_inventory(
        db: Session,
        shop_id: uuid.UUID,
        limit: int = 20,
        offset: int = 0,
        low_stock_only: bool = False,
    ) -> tuple[list[ShopInventoryResponse], int]:
        shop = CatalogRepository.get_shop_by_id(db, shop_id)
        if not shop:
            raise EntityNotFoundException("Shop", str(shop_id))

        items, total = CatalogRepository.list_shop_inventory(
            db, shop_id=shop.id, limit=limit, offset=offset, low_stock_only=low_stock_only
        )
        results = []
        for inv in items:
            product = CatalogRepository.get_product_by_id(db, inv.product_id)
            available_qty = max(0, inv.stock_quantity - inv.reserved_quantity)
            is_low = inv.stock_quantity <= inv.low_stock_threshold
            resp = ShopInventoryResponse.model_validate(inv)
            resp.product_sku = product.sku if product else None
            resp.product_name = product.name if product else None
            resp.available_quantity = available_qty
            resp.is_low_stock = is_low
            results.append(resp)
        return results, total

    @staticmethod
    def list_inventory_transactions(
        db: Session,
        current_user: User,
        shop_id: uuid.UUID,
        inventory_id: uuid.UUID,
        limit: int = 20,
        offset: int = 0,
    ) -> tuple[list[InventoryTransactionResponse], int]:
        shop = CatalogRepository.get_shop_by_id(db, shop_id)
        if not shop:
            raise EntityNotFoundException("Shop", str(shop_id))

        if shop.owner_user_id != current_user.id and current_user.role != UserRole.ADMIN.value:
            raise ForbiddenException(
                "Access denied: You are not authorized to view transactions for this shop."
            )

        inventory = CatalogRepository.get_inventory_by_id(db, inventory_id)
        if not inventory or inventory.shop_id != shop_id:
            raise EntityNotFoundException("ShopInventory", str(inventory_id))

        items, total = CatalogRepository.list_transactions_for_inventory(
            db, inventory_id=inventory_id, limit=limit, offset=offset
        )
        return [InventoryTransactionResponse.model_validate(t) for t in items], total

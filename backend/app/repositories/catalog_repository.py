import uuid
from datetime import UTC, datetime

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.models.catalog import (
    CatalogBrand,
    CatalogCategory,
    CatalogProduct,
    InventoryTransaction,
    Shop,
    ShopInventory,
)


class CatalogRepository:
    """Database persistence operations for product catalogue, shops, and inventory."""

    # -------------------------------------------------------------------------
    # Categories & Brands
    # -------------------------------------------------------------------------
    @staticmethod
    def get_category_by_id(db: Session, category_id: uuid.UUID) -> CatalogCategory | None:
        stmt = select(CatalogCategory).where(CatalogCategory.id == category_id)
        return db.execute(stmt).scalar_one_or_none()

    @staticmethod
    def get_category_by_slug(db: Session, slug: str) -> CatalogCategory | None:
        stmt = select(CatalogCategory).where(CatalogCategory.slug == slug)
        return db.execute(stmt).scalar_one_or_none()

    @staticmethod
    def create_category(db: Session, category: CatalogCategory) -> CatalogCategory:
        db.add(category)
        db.commit()
        db.refresh(category)
        return category

    @staticmethod
    def list_categories(db: Session, active_only: bool = True) -> list[CatalogCategory]:
        stmt = select(CatalogCategory)
        if active_only:
            stmt = stmt.where(CatalogCategory.is_active.is_(True))
        return list(db.execute(stmt.order_by(CatalogCategory.name.asc())).scalars().all())

    @staticmethod
    def get_brand_by_id(db: Session, brand_id: uuid.UUID) -> CatalogBrand | None:
        stmt = select(CatalogBrand).where(CatalogBrand.id == brand_id)
        return db.execute(stmt).scalar_one_or_none()

    @staticmethod
    def get_brand_by_slug(db: Session, slug: str) -> CatalogBrand | None:
        stmt = select(CatalogBrand).where(CatalogBrand.slug == slug)
        return db.execute(stmt).scalar_one_or_none()

    @staticmethod
    def create_brand(db: Session, brand: CatalogBrand) -> CatalogBrand:
        db.add(brand)
        db.commit()
        db.refresh(brand)
        return brand

    @staticmethod
    def list_brands(db: Session, active_only: bool = True) -> list[CatalogBrand]:
        stmt = select(CatalogBrand)
        if active_only:
            stmt = stmt.where(CatalogBrand.is_active.is_(True))
        return list(db.execute(stmt.order_by(CatalogBrand.name.asc())).scalars().all())

    # -------------------------------------------------------------------------
    # Products
    # -------------------------------------------------------------------------
    @staticmethod
    def get_product_by_id(db: Session, product_id: uuid.UUID) -> CatalogProduct | None:
        stmt = select(CatalogProduct).where(CatalogProduct.id == product_id)
        return db.execute(stmt).scalar_one_or_none()

    @staticmethod
    def get_product_by_sku(db: Session, sku: str) -> CatalogProduct | None:
        stmt = select(CatalogProduct).where(CatalogProduct.sku == sku)
        return db.execute(stmt).scalar_one_or_none()

    @staticmethod
    def create_product(db: Session, product: CatalogProduct) -> CatalogProduct:
        db.add(product)
        db.commit()
        db.refresh(product)
        return product

    @staticmethod
    def update_product(db: Session, product: CatalogProduct) -> CatalogProduct:
        product.updated_at = datetime.now(UTC)
        db.commit()
        db.refresh(product)
        return product

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
    ) -> tuple[list[CatalogProduct], int]:
        stmt = select(CatalogProduct).where(CatalogProduct.is_active == is_active)
        count_stmt = (
            select(func.count())
            .select_from(CatalogProduct)
            .where(CatalogProduct.is_active == is_active)
        )

        if query:
            search_pattern = f"%{query.strip().lower()}%"
            filter_expr = (
                func.lower(CatalogProduct.name).like(search_pattern)
                | func.lower(CatalogProduct.sku).like(search_pattern)
                | func.lower(CatalogProduct.description).like(search_pattern)
            )
            stmt = stmt.where(filter_expr)
            count_stmt = count_stmt.where(filter_expr)

        if category_id:
            stmt = stmt.where(CatalogProduct.category_id == category_id)
            count_stmt = count_stmt.where(CatalogProduct.category_id == category_id)

        if brand_id:
            stmt = stmt.where(CatalogProduct.brand_id == brand_id)
            count_stmt = count_stmt.where(CatalogProduct.brand_id == brand_id)

        if frame_type:
            stmt = stmt.where(CatalogProduct.frame_type == frame_type)
            count_stmt = count_stmt.where(CatalogProduct.frame_type == frame_type)

        if frame_material:
            stmt = stmt.where(CatalogProduct.frame_material == frame_material)
            count_stmt = count_stmt.where(CatalogProduct.frame_material == frame_material)

        if frame_shape:
            stmt = stmt.where(CatalogProduct.frame_shape == frame_shape)
            count_stmt = count_stmt.where(CatalogProduct.frame_shape == frame_shape)

        if gender_target:
            stmt = stmt.where(CatalogProduct.gender_target == gender_target)
            count_stmt = count_stmt.where(CatalogProduct.gender_target == gender_target)

        if min_price is not None:
            stmt = stmt.where(CatalogProduct.base_price_inr >= min_price)
            count_stmt = count_stmt.where(CatalogProduct.base_price_inr >= min_price)

        if max_price is not None:
            stmt = stmt.where(CatalogProduct.base_price_inr <= max_price)
            count_stmt = count_stmt.where(CatalogProduct.base_price_inr <= max_price)

        total = db.execute(count_stmt).scalar() or 0
        items = (
            db.execute(stmt.order_by(CatalogProduct.name.asc()).limit(limit).offset(offset))
            .scalars()
            .all()
        )
        return list(items), total

    # -------------------------------------------------------------------------
    # Shops & Inventory
    # -------------------------------------------------------------------------
    @staticmethod
    def create_shop(db: Session, shop: Shop) -> Shop:
        db.add(shop)
        db.commit()
        db.refresh(shop)
        return shop

    @staticmethod
    def get_shop_by_id(db: Session, shop_id: uuid.UUID) -> Shop | None:
        stmt = select(Shop).where(Shop.id == shop_id)
        return db.execute(stmt).scalar_one_or_none()

    @staticmethod
    def list_shops_by_owner(db: Session, owner_user_id: uuid.UUID) -> list[Shop]:
        stmt = select(Shop).where(Shop.owner_user_id == owner_user_id)
        return list(db.execute(stmt.order_by(Shop.created_at.desc())).scalars().all())

    @staticmethod
    def get_inventory(
        db: Session, shop_id: uuid.UUID, product_id: uuid.UUID, for_update: bool = False
    ) -> ShopInventory | None:
        stmt = select(ShopInventory).where(
            ShopInventory.shop_id == shop_id,
            ShopInventory.product_id == product_id,
        )
        if for_update and db.bind and db.bind.dialect.name == "postgresql":
            stmt = stmt.with_for_update()
        return db.execute(stmt).scalar_one_or_none()

    @staticmethod
    def get_inventory_by_id(db: Session, inventory_id: uuid.UUID) -> ShopInventory | None:
        stmt = select(ShopInventory).where(ShopInventory.id == inventory_id)
        return db.execute(stmt).scalar_one_or_none()

    @staticmethod
    def create_inventory(db: Session, inventory: ShopInventory) -> ShopInventory:
        db.add(inventory)
        db.commit()
        db.refresh(inventory)
        return inventory

    @staticmethod
    def update_inventory(db: Session, inventory: ShopInventory) -> ShopInventory:
        inventory.updated_at = datetime.now(UTC)
        db.commit()
        db.refresh(inventory)
        return inventory

    @staticmethod
    def list_shop_inventory(
        db: Session,
        shop_id: uuid.UUID,
        limit: int = 20,
        offset: int = 0,
        low_stock_only: bool = False,
    ) -> tuple[list[ShopInventory], int]:
        stmt = select(ShopInventory).where(ShopInventory.shop_id == shop_id)
        count_stmt = (
            select(func.count()).select_from(ShopInventory).where(ShopInventory.shop_id == shop_id)
        )

        if low_stock_only:
            filter_expr = ShopInventory.stock_quantity <= ShopInventory.low_stock_threshold
            stmt = stmt.where(filter_expr)
            count_stmt = count_stmt.where(filter_expr)

        total = db.execute(count_stmt).scalar() or 0
        items = (
            db.execute(stmt.order_by(ShopInventory.updated_at.desc()).limit(limit).offset(offset))
            .scalars()
            .all()
        )
        return list(items), total

    @staticmethod
    def create_transaction(db: Session, transaction: InventoryTransaction) -> InventoryTransaction:
        db.add(transaction)
        db.commit()
        db.refresh(transaction)
        return transaction

    @staticmethod
    def list_transactions_for_inventory(
        db: Session, inventory_id: uuid.UUID, limit: int = 20, offset: int = 0
    ) -> tuple[list[InventoryTransaction], int]:
        stmt = select(InventoryTransaction).where(InventoryTransaction.inventory_id == inventory_id)
        count_stmt = (
            select(func.count())
            .select_from(InventoryTransaction)
            .where(InventoryTransaction.inventory_id == inventory_id)
        )
        total = db.execute(count_stmt).scalar() or 0
        items = (
            db.execute(
                stmt.order_by(InventoryTransaction.occurred_at.desc()).limit(limit).offset(offset)
            )
            .scalars()
            .all()
        )
        return list(items), total

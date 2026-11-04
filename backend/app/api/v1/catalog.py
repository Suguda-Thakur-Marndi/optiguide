import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session

from app.api.dependencies import get_db, require_admin
from app.models.user import User
from app.schemas.catalog import (
    BrandCreateRequest,
    BrandResponse,
    CategoryCreateRequest,
    CategoryResponse,
    ProductCreateRequest,
    ProductResponse,
    ProductUpdateRequest,
)
from app.schemas.common import PaginatedResponse
from app.services.catalog_service import CatalogService

router = APIRouter()


# -----------------------------------------------------------------------------
# Categories
# -----------------------------------------------------------------------------
@router.get(
    "/categories",
    response_model=list[CategoryResponse],
    summary="List Product Categories",
)
def list_categories(
    db: Annotated[Session, Depends(get_db)],
    active_only: Annotated[bool, Query()] = True,
) -> list[CategoryResponse]:
    """Retrieves all active eyewear categories (e.g. Full-Rim, Rimless, Progressive)."""
    return CatalogService.list_categories(db, active_only=active_only)


@router.post(
    "/admin/categories",
    response_model=CategoryResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create Product Category (Admin Only)",
)
def create_category(
    payload: CategoryCreateRequest,
    _admin_user: Annotated[User, Depends(require_admin)],
    db: Annotated[Session, Depends(get_db)],
) -> CategoryResponse:
    """Adds a new frame category to the catalogue."""
    return CatalogService.create_category(db, payload)


# -----------------------------------------------------------------------------
# Brands
# -----------------------------------------------------------------------------
@router.get(
    "/brands",
    response_model=list[BrandResponse],
    summary="List Optical Brands",
)
def list_brands(
    db: Annotated[Session, Depends(get_db)],
    active_only: Annotated[bool, Query()] = True,
) -> list[BrandResponse]:
    """Retrieves list of active frame manufacturers and brands."""
    return CatalogService.list_brands(db, active_only=active_only)


@router.post(
    "/admin/brands",
    response_model=BrandResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create Optical Brand (Admin Only)",
)
def create_brand(
    payload: BrandCreateRequest,
    _admin_user: Annotated[User, Depends(require_admin)],
    db: Annotated[Session, Depends(get_db)],
) -> BrandResponse:
    """Registers an eyewear brand in the platform."""
    return CatalogService.create_brand(db, payload)


# -----------------------------------------------------------------------------
# Products
# -----------------------------------------------------------------------------
@router.get(
    "/products",
    response_model=PaginatedResponse[ProductResponse],
    summary="Search & Filter Eyewear Catalogue",
)
def search_products(
    db: Annotated[Session, Depends(get_db)],
    query: Annotated[
        str | None, Query(description="Search term for name, SKU, or description")
    ] = None,
    category_id: Annotated[uuid.UUID | None, Query()] = None,
    brand_id: Annotated[uuid.UUID | None, Query()] = None,
    frame_type: Annotated[str | None, Query()] = None,
    frame_material: Annotated[str | None, Query()] = None,
    frame_shape: Annotated[str | None, Query()] = None,
    gender_target: Annotated[str | None, Query()] = None,
    min_price: Annotated[float | None, Query(ge=0)] = None,
    max_price: Annotated[float | None, Query(ge=0)] = None,
    page: Annotated[int, Query(ge=1)] = 1,
    page_size: Annotated[int, Query(ge=1, le=100)] = 20,
) -> PaginatedResponse[ProductResponse]:
    """Multi-criteria search over active eyewear models with pagination."""
    offset = (page - 1) * page_size
    items, total = CatalogService.search_products(
        db=db,
        query=query,
        category_id=category_id,
        brand_id=brand_id,
        frame_type=frame_type,
        frame_material=frame_material,
        frame_shape=frame_shape,
        gender_target=gender_target,
        min_price=min_price,
        max_price=max_price,
        is_active=True,
        limit=page_size,
        offset=offset,
    )
    return PaginatedResponse(items=items, total=total, page=page, page_size=page_size)


@router.get(
    "/products/{product_id}",
    response_model=ProductResponse,
    summary="Get Specific Product Details",
)
def get_product(
    product_id: uuid.UUID,
    db: Annotated[Session, Depends(get_db)],
) -> ProductResponse:
    """Retrieves full specifications, pricing, and dimensions of an eyewear frame."""
    return CatalogService.get_product(db, product_id)


@router.post(
    "/admin/products",
    response_model=ProductResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create Eyewear Product (Admin Only)",
)
def create_product(
    payload: ProductCreateRequest,
    _admin_user: Annotated[User, Depends(require_admin)],
    db: Annotated[Session, Depends(get_db)],
) -> ProductResponse:
    """Adds a new SKU with optical measurements and pricing."""
    return CatalogService.create_product(db, payload)


@router.patch(
    "/admin/products/{product_id}",
    response_model=ProductResponse,
    summary="Update Eyewear Product (Admin Only)",
)
def update_product(
    product_id: uuid.UUID,
    payload: ProductUpdateRequest,
    _admin_user: Annotated[User, Depends(require_admin)],
    db: Annotated[Session, Depends(get_db)],
) -> ProductResponse:
    """Updates specifications, price, or active status of a product."""
    return CatalogService.update_product(db, product_id, payload)

import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session

from app.api.dependencies import get_current_active_user, get_db, require_roles
from app.models.user import User
from app.schemas.catalog import (
    InventoryTransactionResponse,
    ShopCreateRequest,
    ShopInventoryAdjustRequest,
    ShopInventoryResponse,
    ShopResponse,
)
from app.schemas.common import PaginatedResponse
from app.services.catalog_service import CatalogService

router = APIRouter()


@router.post(
    "",
    response_model=ShopResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create Optical Retail Shop",
)
def create_shop(
    payload: ShopCreateRequest,
    current_user: Annotated[User, Depends(require_roles("shopkeeper", "admin"))],
    db: Annotated[Session, Depends(get_db)],
) -> ShopResponse:
    """Registers a new retail shop branch or community kiosk."""
    return CatalogService.create_shop(db, current_user, payload)


@router.get(
    "/me",
    response_model=list[ShopResponse],
    summary="List Shops Owned by Current User",
)
def list_my_shops(
    current_user: Annotated[User, Depends(get_current_active_user)],
    db: Annotated[Session, Depends(get_db)],
) -> list[ShopResponse]:
    """Retrieves all shops where caller is registered as owner."""
    return CatalogService.list_my_shops(db, current_user)


@router.get(
    "/{shop_id}/inventory",
    response_model=PaginatedResponse[ShopInventoryResponse],
    summary="List Shop Inventory",
)
def list_shop_inventory(
    shop_id: uuid.UUID,
    db: Annotated[Session, Depends(get_db)],
    low_stock_only: Annotated[bool, Query()] = False,
    page: Annotated[int, Query(ge=1)] = 1,
    page_size: Annotated[int, Query(ge=1, le=100)] = 20,
) -> PaginatedResponse[ShopInventoryResponse]:
    """Retrieves live stock levels for frames at a specific shop location."""
    offset = (page - 1) * page_size
    items, total = CatalogService.list_shop_inventory(
        db, shop_id=shop_id, limit=page_size, offset=offset, low_stock_only=low_stock_only
    )
    return PaginatedResponse(items=items, total=total, page=page, page_size=page_size)


@router.post(
    "/{shop_id}/inventory/adjust",
    response_model=ShopInventoryResponse,
    summary="Adjust Shop Inventory Stock Quantity (Transactional)",
)
def adjust_shop_inventory(
    shop_id: uuid.UUID,
    payload: ShopInventoryAdjustRequest,
    current_user: Annotated[User, Depends(get_current_active_user)],
    db: Annotated[Session, Depends(get_db)],
) -> ShopInventoryResponse:
    """Atomically adds or deducts stock quantity; strictly prevents negative inventory."""
    return CatalogService.adjust_inventory(db, current_user, shop_id, payload)


@router.get(
    "/{shop_id}/inventory/{inventory_id}/transactions",
    response_model=PaginatedResponse[InventoryTransactionResponse],
    summary="List Stock Adjustment History",
)
def list_inventory_transactions(
    shop_id: uuid.UUID,
    inventory_id: uuid.UUID,
    current_user: Annotated[User, Depends(get_current_active_user)],
    db: Annotated[Session, Depends(get_db)],
    page: Annotated[int, Query(ge=1)] = 1,
    page_size: Annotated[int, Query(ge=1, le=100)] = 20,
) -> PaginatedResponse[InventoryTransactionResponse]:
    """Audits past stock changes, operator identities, and delta reasons."""
    offset = (page - 1) * page_size
    items, total = CatalogService.list_inventory_transactions(
        db,
        current_user=current_user,
        shop_id=shop_id,
        inventory_id=inventory_id,
        limit=page_size,
        offset=offset,
    )
    return PaginatedResponse(items=items, total=total, page=page, page_size=page_size)

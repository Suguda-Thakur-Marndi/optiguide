import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session

from app.api.dependencies import get_current_active_user, get_current_user_optional, get_db
from app.models.user import User
from app.schemas.catalog import CategoryResponse
from app.schemas.try_on import (
    FavouriteResponse,
    FavouriteToggleRequest,
    FrameTryOnAssetResponse,
    TryOnFrameSelectRequest,
    TryOnSessionCreateRequest,
    TryOnSessionResponse,
    TryOnSnapshotRequest,
    TryOnSnapshotResponse,
)
from app.services.try_on_service import TryOnService

router = APIRouter()


# -----------------------------------------------------------------------------
# Eyewear Frames & Catalogue (Try-On Enabled)
# -----------------------------------------------------------------------------

@router.get(
    "/frames",
    response_model=list[FrameTryOnAssetResponse],
    summary="List Eyewear Frames for Virtual Try-On",
    description="Retrieves active eyewear models with AR overlay assets, physical measurements, and color variants.",
)
def list_frames(
    db: Annotated[Session, Depends(get_db)],
    shape: Annotated[str | None, Query(description="Frame shape filter (round, square, rectangular, etc.)")] = None,
    category: Annotated[str | None, Query(description="Category slug (full-rim, rimless, etc.)")] = None,
    gender: Annotated[str | None, Query(description="Target gender (unisex, men, women, kids)")] = None,
    search: Annotated[str | None, Query(description="Search by model name or SKU")] = None,
    limit: Annotated[int, Query(ge=1, le=100)] = 50,
    offset: Annotated[int, Query(ge=0)] = 0,
) -> list[FrameTryOnAssetResponse]:
    return TryOnService.list_frames(
        db=db,
        shape=shape,
        category=category,
        gender=gender,
        search=search,
        limit=limit,
        offset=offset,
    )


@router.get(
    "/frames/categories",
    response_model=list[CategoryResponse],
    summary="List Frame Categories",
    description="Returns available eyewear style and rim categories.",
)
def list_categories(
    db: Annotated[Session, Depends(get_db)],
) -> list[CategoryResponse]:
    return TryOnService.list_categories(db)


@router.get(
    "/frames/{frame_id}",
    response_model=FrameTryOnAssetResponse,
    summary="Get Specific Frame & Asset Specs",
    description="Returns full geometric dimensions, color variants, and AR overlay assets for a specific frame.",
)
def get_frame(
    frame_id: uuid.UUID,
    db: Annotated[Session, Depends(get_db)],
) -> FrameTryOnAssetResponse:
    return TryOnService.get_frame(db, frame_id)


@router.get(
    "/frames/{frame_id}/try-on-assets",
    response_model=FrameTryOnAssetResponse,
    summary="Get Dedicated Try-On Asset Telemetry",
    description="Returns exact 2D/3D asset URLs, lens center offsets, and bridge coordinate references for AR tracking.",
)
def get_frame_try_on_assets(
    frame_id: uuid.UUID,
    db: Annotated[Session, Depends(get_db)],
) -> FrameTryOnAssetResponse:
    return TryOnService.get_frame(db, frame_id)


# -----------------------------------------------------------------------------
# Try-On Sessions & Interactions
# -----------------------------------------------------------------------------

@router.post(
    "/try-on/sessions",
    response_model=TryOnSessionResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Initiate Virtual Try-On Session",
    description="Initializes an interactive AR session tracking frame selections. Supports anonymous or authenticated users.",
)
def create_try_on_session(
    payload: TryOnSessionCreateRequest,
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[User | None, Depends(get_current_user_optional)] = None,
) -> TryOnSessionResponse:
    return TryOnService.create_session(db, payload, current_user)


@router.get(
    "/try-on/sessions/{session_id}",
    response_model=TryOnSessionResponse,
    summary="Get Try-On Session State",
    description="Retrieves active session state and current frame selection.",
)
def get_try_on_session(
    session_id: uuid.UUID,
    db: Annotated[Session, Depends(get_db)],
) -> TryOnSessionResponse:
    return TryOnService.get_session(db, session_id)


@router.post(
    "/try-on/sessions/{session_id}/select-frame",
    response_model=TryOnSessionResponse,
    summary="Select Frame in Try-On Session",
    description="Updates the active frame, color, scale, and offset for the AR session.",
)
def select_frame(
    session_id: uuid.UUID,
    payload: TryOnFrameSelectRequest,
    db: Annotated[Session, Depends(get_db)],
) -> TryOnSessionResponse:
    return TryOnService.select_frame(db, session_id, payload)


@router.post(
    "/try-on/sessions/{session_id}/favourite",
    summary="Toggle Frame Favourite",
    description="Adds or removes the selected frame from the authenticated customer's favourites list.",
)
def toggle_favourite(
    session_id: uuid.UUID,
    payload: FavouriteToggleRequest,
    current_user: Annotated[User, Depends(get_current_active_user)],
    db: Annotated[Session, Depends(get_db)],
) -> dict:
    return TryOnService.toggle_favourite(
        db=db,
        user=current_user,
        product_id=payload.product_id,
        selected_color=payload.selected_color,
        notes=payload.notes,
    )


@router.get(
    "/try-on/favourites",
    response_model=list[FavouriteResponse],
    summary="List Customer Favourite Frames",
    description="Retrieves saved frames for the authenticated patient or shopper.",
)
def list_favourites(
    current_user: Annotated[User, Depends(get_current_active_user)],
    db: Annotated[Session, Depends(get_db)],
) -> list[FavouriteResponse]:
    return TryOnService.list_favourites(db, current_user)


@router.post(
    "/try-on/sessions/{session_id}/capture",
    response_model=TryOnSnapshotResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Record AR Snapshot Preview",
    description="Registers a user-initiated try-on snapshot record. No continuous video is retained.",
)
def record_snapshot(
    session_id: uuid.UUID,
    payload: TryOnSnapshotRequest,
    db: Annotated[Session, Depends(get_db)],
) -> TryOnSnapshotResponse:
    return TryOnService.record_snapshot(db, session_id, payload)


@router.delete(
    "/try-on/sessions/{session_id}",
    summary="End Try-On Session",
    description="Gracefully closes the AR try-on session and releases server resources.",
)
def end_try_on_session(
    session_id: uuid.UUID,
    db: Annotated[Session, Depends(get_db)],
) -> dict[str, str]:
    return TryOnService.close_session(db, session_id)

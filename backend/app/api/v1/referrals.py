import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session

from app.api.dependencies import get_current_active_user, get_db
from app.models.user import User
from app.schemas.common import PaginatedResponse
from app.schemas.referral import (
    PatientRecordShareRequest,
    PatientRecordShareResponse,
    PatientReferralCreateRequest,
    PatientReferralResponse,
)
from app.services.referral_service import ReferralService

router = APIRouter()


@router.post(
    "",
    response_model=PatientReferralResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create Patient Referral From Screening Session",
)
def create_patient_referral(
    payload: PatientReferralCreateRequest,
    current_user: Annotated[User, Depends(get_current_active_user)],
    db: Annotated[Session, Depends(get_db)],
) -> PatientReferralResponse:
    """Generates a formal referral record linked to a completed or flagged screening session."""
    return ReferralService.create_referral(db, current_user, payload)


@router.get(
    "/me",
    response_model=PaginatedResponse[PatientReferralResponse],
    summary="List Patient's Own Referrals",
)
def list_my_referrals(
    current_user: Annotated[User, Depends(get_current_active_user)],
    db: Annotated[Session, Depends(get_db)],
    page: Annotated[int, Query(ge=1)] = 1,
    page_size: Annotated[int, Query(ge=1, le=100)] = 20,
) -> PaginatedResponse[PatientReferralResponse]:
    """Retrieves all historical referrals for the authenticated citizen."""
    offset = (page - 1) * page_size
    items, total = ReferralService.list_my_referrals(
        db, current_user, limit=page_size, offset=offset
    )
    return PaginatedResponse(items=items, total=total, page=page, page_size=page_size)


@router.get(
    "/{referral_id}",
    response_model=PatientReferralResponse,
    summary="Get Specific Referral Details",
)
def get_referral_details(
    referral_id: uuid.UUID,
    current_user: Annotated[User, Depends(get_current_active_user)],
    db: Annotated[Session, Depends(get_db)],
) -> PatientReferralResponse:
    """Fetches details of a referral; requires ownership or authorized professional share."""
    return ReferralService.get_referral(db, current_user, referral_id)


@router.post(
    "/{referral_id}/share",
    response_model=PatientRecordShareResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Share Screening Referral With Verified Professional",
)
def share_referral_with_professional(
    referral_id: uuid.UUID,
    payload: PatientRecordShareRequest,
    current_user: Annotated[User, Depends(get_current_active_user)],
    db: Annotated[Session, Depends(get_db)],
) -> PatientRecordShareResponse:
    """Patient-controlled explicit record sharing to an accredited optometrist."""
    return ReferralService.share_referral(db, current_user, referral_id, payload)


@router.delete(
    "/{referral_id}/share/{share_id}",
    response_model=PatientRecordShareResponse,
    summary="Revoke Record Sharing Access (DELETE alias)",
)
@router.post(
    "/{referral_id}/shares/{share_id}/revoke",
    response_model=PatientRecordShareResponse,
    summary="Revoke Record Sharing Access",
)
def revoke_referral_share(
    referral_id: uuid.UUID,
    share_id: uuid.UUID,
    current_user: Annotated[User, Depends(get_current_active_user)],
    db: Annotated[Session, Depends(get_db)],
) -> PatientRecordShareResponse:
    """Immediately revokes a professional's access to this screening referral."""
    return ReferralService.revoke_share(db, current_user, referral_id, share_id)


@router.post(
    "/{referral_id}/close",
    response_model=PatientReferralResponse,
    summary="Close Referral",
)
def close_referral(
    referral_id: uuid.UUID,
    current_user: Annotated[User, Depends(get_current_active_user)],
    db: Annotated[Session, Depends(get_db)],
) -> PatientReferralResponse:
    """Closes an active referral once consultation or clinical treatment is finalized."""
    return ReferralService.close_referral(db, current_user, referral_id)


@router.get(
    "/{referral_id}/shares",
    response_model=list[PatientRecordShareResponse],
    summary="List Active Shares For Referral",
)
def list_referral_shares(
    referral_id: uuid.UUID,
    current_user: Annotated[User, Depends(get_current_active_user)],
    db: Annotated[Session, Depends(get_db)],
) -> list[PatientRecordShareResponse]:
    """Inspects which professionals currently hold active access to this record."""
    return ReferralService.list_shares_for_referral(db, current_user, referral_id)

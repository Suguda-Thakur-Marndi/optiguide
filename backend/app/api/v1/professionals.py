import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session

from app.api.dependencies import (
    get_current_active_user,
    get_db,
    require_admin,
    require_verified_professional,
)
from app.models.user import User
from app.schemas.common import PaginatedResponse
from app.schemas.referral import (
    ClinicalReviewCreateRequest,
    ClinicalReviewResponse,
    PatientRecordShareResponse,
    ProfessionalApplyRequest,
    ProfessionalProfileResponse,
    ProfessionalVerifyRequest,
    SharedScreeningDetailsResponse,
)
from app.services.referral_service import ReferralService

router = APIRouter()


@router.post(
    "/apply",
    response_model=ProfessionalProfileResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Submit Optometrist / Eye Care Professional Credentials",
)
def apply_for_professional_verification(
    payload: ProfessionalApplyRequest,
    current_user: Annotated[User, Depends(get_current_active_user)],
    db: Annotated[Session, Depends(get_db)],
) -> ProfessionalProfileResponse:
    """Submits optometrist registration and license credentials for administrative review."""
    return ReferralService.apply_for_verification(db, current_user, payload)


@router.get(
    "/me",
    response_model=ProfessionalProfileResponse,
    summary="Get My Professional Verification Status",
)
def get_my_professional_profile(
    current_user: Annotated[User, Depends(get_current_active_user)],
    db: Annotated[Session, Depends(get_db)],
) -> ProfessionalProfileResponse:
    """Retrieves the caller's professional credentials and verification state."""
    return ReferralService.get_my_profile(db, current_user)


@router.get(
    "/admin/pending",
    response_model=PaginatedResponse[ProfessionalProfileResponse],
    summary="List Pending Professional Applications (Admin Only)",
)
def list_pending_professionals(
    _admin_user: Annotated[User, Depends(require_admin)],
    db: Annotated[Session, Depends(get_db)],
    status_filter: Annotated[str | None, Query(alias="status")] = "PENDING",
    page: Annotated[int, Query(ge=1)] = 1,
    page_size: Annotated[int, Query(ge=1, le=100)] = 20,
) -> PaginatedResponse[ProfessionalProfileResponse]:
    """Administrative endpoint to inspect unverified or suspended optometrists."""
    offset = (page - 1) * page_size
    items, total = ReferralService.list_pending_profiles(
        db, status=status_filter, limit=page_size, offset=offset
    )
    return PaginatedResponse(items=items, total=total, page=page, page_size=page_size)


@router.post(
    "/admin/{profile_id}/verify",
    response_model=ProfessionalProfileResponse,
    summary="Verify, Reject or Suspend Professional Credentials (Admin Only)",
)
def verify_professional_profile(
    profile_id: uuid.UUID,
    payload: ProfessionalVerifyRequest,
    admin_user: Annotated[User, Depends(require_admin)],
    db: Annotated[Session, Depends(get_db)],
) -> ProfessionalProfileResponse:
    """Approves, rejects, or suspends an optometrist license."""
    return ReferralService.admin_verify_professional(
        db=db,
        admin_user=admin_user,
        profile_id=profile_id,
        action=payload.action,
        rejection_reason=payload.rejection_reason,
    )


@router.get(
    "/shared-records",
    response_model=PaginatedResponse[PatientRecordShareResponse],
    summary="List Records Delegated to Verified Professional",
)
def list_shared_records(
    professional_user: Annotated[User, Depends(require_verified_professional)],
    db: Annotated[Session, Depends(get_db)],
    page: Annotated[int, Query(ge=1)] = 1,
    page_size: Annotated[int, Query(ge=1, le=100)] = 20,
) -> PaginatedResponse[PatientRecordShareResponse]:
    """Retrieves screening referrals actively delegated to this professional by citizens."""
    offset = (page - 1) * page_size
    items, total = ReferralService.list_shared_records_for_professional(
        db, professional_user, limit=page_size, offset=offset
    )
    return PaginatedResponse(items=items, total=total, page=page, page_size=page_size)


@router.get(
    "/shared-records/{referral_id}",
    response_model=SharedScreeningDetailsResponse,
    summary="Inspect Complete Screening Details for Delegated Patient",
)
def get_shared_screening_details(
    referral_id: uuid.UUID,
    professional_user: Annotated[User, Depends(require_verified_professional)],
    db: Annotated[Session, Depends(get_db)],
) -> SharedScreeningDetailsResponse:
    """Fetches full acuity, astigmatism, color vision, and audit history for delegated referral."""
    return ReferralService.get_shared_screening_details(db, professional_user, referral_id)


@router.post(
    "/reviews/{referral_id}",
    response_model=ClinicalReviewResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Record Professional Clinical Review Observations",
)
def submit_clinical_review(
    referral_id: uuid.UUID,
    payload: ClinicalReviewCreateRequest,
    professional_user: Annotated[User, Depends(require_verified_professional)],
    db: Annotated[Session, Depends(get_db)],
) -> ClinicalReviewResponse:
    """Independent professional review and in-person exam recommendation."""
    return ReferralService.create_review(db, professional_user, referral_id, payload)

import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session

from app.api.dependencies import get_current_active_user, get_db
from app.models.user import User
from app.schemas.common import PaginatedResponse
from app.schemas.pd_assessment import (
    PDAssessmentCreateRequest,
    PDAssessmentResponse,
    PDProfessionalReviewRequest,
    PDRejectRequest,
)
from app.services.pd_service import PDService

router = APIRouter()


@router.post(
    "/assessments",
    response_model=PDAssessmentResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Record Pupillary Distance (PD) Assessment",
)
def record_pd_assessment(
    payload: PDAssessmentCreateRequest,
    current_user: Annotated[User, Depends(get_current_active_user)],
    db: Annotated[Session, Depends(get_db)],
) -> PDAssessmentResponse:
    """
    Persists a binocular or monocular millimeter pupillary distance measurement.
    Enforces physiological human boundaries (45.0 - 80.0 mm binocular).
    """
    return PDService.record_assessment(db, current_user, payload)


@router.get(
    "/assessments/me",
    response_model=PaginatedResponse[PDAssessmentResponse],
    summary="List Patient's Own PD Assessments",
)
def list_my_pd_assessments(
    current_user: Annotated[User, Depends(get_current_active_user)],
    db: Annotated[Session, Depends(get_db)],
    page: Annotated[int, Query(ge=1)] = 1,
    page_size: Annotated[int, Query(ge=1, le=100)] = 20,
) -> PaginatedResponse[PDAssessmentResponse]:
    """Retrieves all historical PD assessments for the authenticated citizen."""
    offset = (page - 1) * page_size
    items, total = PDService.list_my_assessments(db, current_user, limit=page_size, offset=offset)
    return PaginatedResponse(items=items, total=total, page=page, page_size=page_size)


@router.get(
    "/assessments/{assessment_id}",
    response_model=PDAssessmentResponse,
    summary="Get Specific PD Assessment Details",
)
def get_pd_assessment(
    assessment_id: uuid.UUID,
    current_user: Annotated[User, Depends(get_current_active_user)],
    db: Annotated[Session, Depends(get_db)],
) -> PDAssessmentResponse:
    """Fetches details of a PD assessment; checks ownership or clinical sharing permissions."""
    return PDService.get_assessment(db, current_user, assessment_id)


@router.patch(
    "/assessments/{assessment_id}/confirm",
    response_model=PDAssessmentResponse,
    summary="Patient Confirms PD Measurement",
)
def confirm_pd_assessment(
    assessment_id: uuid.UUID,
    current_user: Annotated[User, Depends(get_current_active_user)],
    db: Annotated[Session, Depends(get_db)],
) -> PDAssessmentResponse:
    """Marks a PD measurement as user-confirmed."""
    return PDService.confirm_assessment(db, current_user, assessment_id)


@router.post(
    "/assessments/{assessment_id}/reject",
    response_model=PDAssessmentResponse,
    summary="Patient Rejects PD Measurement",
)
def reject_pd_assessment(
    assessment_id: uuid.UUID,
    payload: PDRejectRequest,
    current_user: Annotated[User, Depends(get_current_active_user)],
    db: Annotated[Session, Depends(get_db)],
) -> PDAssessmentResponse:
    """Records user rejection of measurement with audit rationale."""
    return PDService.reject_assessment(db, current_user, assessment_id, payload.rejection_reason)


@router.post(
    "/assessments/{assessment_id}/professional-review",
    response_model=PDAssessmentResponse,
    summary="Optometrist Professionally Reviews PD Measurement",
)
def review_pd_assessment_by_professional(
    assessment_id: uuid.UUID,
    payload: PDProfessionalReviewRequest,
    current_user: Annotated[User, Depends(get_current_active_user)],
    db: Annotated[Session, Depends(get_db)],
) -> PDAssessmentResponse:
    """Verified optometrist clinical verification of pupillary distance."""
    return PDService.review_assessment_by_professional(db, current_user, assessment_id, payload)

import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session

from app.api.dependencies import get_current_active_user, get_db
from app.models.user import User
from app.schemas.recommendation import (
    EyewearRecommendationRequest,
    EyewearRecommendationResponse,
    RecommendationFeedbackRequest,
    RecommendationFeedbackResponse,
)
from app.services.recommendation_service import RecommendationService

router = APIRouter()


@router.post(
    "/eyewear",
    response_model=EyewearRecommendationResponse,
    status_code=status.HTTP_200_OK,
    summary="Generate Deterministic Eyewear Recommendations",
)
def generate_eyewear_recommendations(
    payload: EyewearRecommendationRequest,
    current_user: Annotated[User, Depends(get_current_active_user)],
    db: Annotated[Session, Depends(get_db)],
    limit: Annotated[int, Query(ge=1, le=20)] = 5,
) -> EyewearRecommendationResponse:
    """
    Ranks active catalogue frames against citizen preferences (budget, shape, material,
    face-shape aesthetics, and shop stock availability).
    Strictly non-diagnostic: Never infers or calculates optical lens prescriptions.
    """
    return RecommendationService.generate_recommendations(
        db=db, user=current_user, criteria=payload, limit=limit
    )


@router.get(
    "/eyewear/{recommendation_id}",
    response_model=EyewearRecommendationResponse,
    summary="Retrieve Saved Eyewear Recommendation",
)
def get_eyewear_recommendation(
    recommendation_id: uuid.UUID,
    current_user: Annotated[User, Depends(get_current_active_user)],
    db: Annotated[Session, Depends(get_db)],
) -> EyewearRecommendationResponse:
    """Retrieves ranked matches and explanation rationales for a historical recommendation session."""
    return RecommendationService.get_recommendation(db, current_user, recommendation_id)


@router.post(
    "/{recommendation_id}/feedback",
    response_model=RecommendationFeedbackResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Submit User Feedback on Eyewear Recommendations",
)
def submit_recommendation_feedback(
    recommendation_id: uuid.UUID,
    payload: RecommendationFeedbackRequest,
    current_user: Annotated[User, Depends(get_current_active_user)],
    db: Annotated[Session, Depends(get_db)],
) -> RecommendationFeedbackResponse:
    """Records rating and frame selection feedback to validate recommendation relevance."""
    return RecommendationService.submit_feedback(db, current_user, recommendation_id, payload)

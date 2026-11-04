import uuid

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.models.recommendation import EyewearRecommendation, RecommendationFeedback


class RecommendationRepository:
    """Database operations for eyewear recommendations and user feedback."""

    @staticmethod
    def create_recommendation(
        db: Session, recommendation: EyewearRecommendation
    ) -> EyewearRecommendation:
        db.add(recommendation)
        db.commit()
        db.refresh(recommendation)
        return recommendation

    @staticmethod
    def get_recommendation_by_id(
        db: Session, recommendation_id: uuid.UUID
    ) -> EyewearRecommendation | None:
        stmt = select(EyewearRecommendation).where(EyewearRecommendation.id == recommendation_id)
        return db.execute(stmt).scalar_one_or_none()

    @staticmethod
    def list_recommendations_for_user(
        db: Session, user_id: uuid.UUID, limit: int = 20, offset: int = 0
    ) -> tuple[list[EyewearRecommendation], int]:
        stmt = select(EyewearRecommendation).where(EyewearRecommendation.user_id == user_id)
        count_stmt = (
            select(func.count())
            .select_from(EyewearRecommendation)
            .where(EyewearRecommendation.user_id == user_id)
        )
        total = db.execute(count_stmt).scalar() or 0
        items = (
            db.execute(
                stmt.order_by(EyewearRecommendation.created_at.desc()).limit(limit).offset(offset)
            )
            .scalars()
            .all()
        )
        return list(items), total

    @staticmethod
    def create_feedback(db: Session, feedback: RecommendationFeedback) -> RecommendationFeedback:
        db.add(feedback)
        db.commit()
        db.refresh(feedback)
        return feedback

    @staticmethod
    def list_feedback_for_recommendation(
        db: Session, recommendation_id: uuid.UUID
    ) -> list[RecommendationFeedback]:
        stmt = select(RecommendationFeedback).where(
            RecommendationFeedback.recommendation_id == recommendation_id
        )
        return list(
            db.execute(stmt.order_by(RecommendationFeedback.created_at.desc())).scalars().all()
        )

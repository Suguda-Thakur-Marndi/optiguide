import uuid

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.models.pd_assessment import PDAssessment


class PDRepository:
    """Database persistence operations for Pupillary Distance (PD) measurements."""

    @staticmethod
    def create_assessment(db: Session, assessment: PDAssessment) -> PDAssessment:
        db.add(assessment)
        db.commit()
        db.refresh(assessment)
        return assessment

    @staticmethod
    def get_assessment_by_id(db: Session, assessment_id: uuid.UUID) -> PDAssessment | None:
        stmt = select(PDAssessment).where(PDAssessment.id == assessment_id)
        return db.execute(stmt).scalar_one_or_none()

    @staticmethod
    def list_assessments_for_user(
        db: Session, user_id: uuid.UUID, limit: int = 20, offset: int = 0
    ) -> tuple[list[PDAssessment], int]:
        stmt = select(PDAssessment).where(PDAssessment.user_id == user_id)
        count_stmt = (
            select(func.count()).select_from(PDAssessment).where(PDAssessment.user_id == user_id)
        )
        total = db.execute(count_stmt).scalar() or 0
        items = (
            db.execute(stmt.order_by(PDAssessment.recorded_at.desc()).limit(limit).offset(offset))
            .scalars()
            .all()
        )
        return list(items), total

    @staticmethod
    def update_assessment(db: Session, assessment: PDAssessment) -> PDAssessment:
        db.commit()
        db.refresh(assessment)
        return assessment

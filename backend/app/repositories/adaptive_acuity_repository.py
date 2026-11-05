import uuid

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.adaptive_acuity import (
    AdaptiveAcuityAttempt,
    AdaptiveAcuityTest,
)


class AdaptiveAcuityRepository:
    """Data access repository for adaptive visual acuity test sessions and presentation attempts."""

    @staticmethod
    def create_test(db: Session, test: AdaptiveAcuityTest) -> AdaptiveAcuityTest:
        """Persists a new adaptive visual acuity test session."""
        db.add(test)
        db.commit()
        db.refresh(test)
        return test

    @staticmethod
    def get_test_by_id(
        db: Session,
        test_id: uuid.UUID,
        for_update: bool = False,
    ) -> AdaptiveAcuityTest | None:
        """Retrieves an adaptive test session by its ID with optional dialect-safe row locking."""
        stmt = select(AdaptiveAcuityTest).where(AdaptiveAcuityTest.id == test_id)
        if for_update and db.bind and db.bind.dialect.name == "postgresql":
            stmt = stmt.with_for_update()
        return db.execute(stmt).scalar_one_or_none()

    @staticmethod
    def get_active_test_for_config(
        db: Session,
        session_id: uuid.UUID,
        test_eye: str,
        test_type: str,
    ) -> AdaptiveAcuityTest | None:
        """Checks if an in-progress adaptive test already exists for the same screening session, eye, and type."""
        stmt = select(AdaptiveAcuityTest).where(
            AdaptiveAcuityTest.session_id == session_id,
            AdaptiveAcuityTest.test_eye == test_eye,
            AdaptiveAcuityTest.test_type == test_type,
            AdaptiveAcuityTest.status == "IN_PROGRESS",
        )
        return db.execute(stmt).scalars().first()

    @staticmethod
    def update_test(db: Session, test: AdaptiveAcuityTest) -> AdaptiveAcuityTest:
        """Commits and refreshes changes to an adaptive acuity test."""
        db.commit()
        db.refresh(test)
        return test

    @staticmethod
    def create_attempt(db: Session, attempt: AdaptiveAcuityAttempt) -> AdaptiveAcuityAttempt:
        """Persists a new optotype presentation attempt."""
        db.add(attempt)
        db.commit()
        db.refresh(attempt)
        return attempt

    @staticmethod
    def get_attempt(
        db: Session,
        test_id: uuid.UUID,
        attempt_sequence: int,
    ) -> AdaptiveAcuityAttempt | None:
        """Retrieves a specific presentation attempt by test ID and sequence number."""
        stmt = select(AdaptiveAcuityAttempt).where(
            AdaptiveAcuityAttempt.test_id == test_id,
            AdaptiveAcuityAttempt.attempt_sequence == attempt_sequence,
        )
        return db.execute(stmt).scalar_one_or_none()

    @staticmethod
    def list_attempts_for_test(
        db: Session,
        test_id: uuid.UUID,
    ) -> list[AdaptiveAcuityAttempt]:
        """Lists all presentation attempts for a test session ordered by sequence number."""
        stmt = (
            select(AdaptiveAcuityAttempt)
            .where(AdaptiveAcuityAttempt.test_id == test_id)
            .order_by(AdaptiveAcuityAttempt.attempt_sequence.asc())
        )
        return list(db.execute(stmt).scalars().all())

    @staticmethod
    def list_attempts_for_level(
        db: Session,
        test_id: uuid.UUID,
        level: int,
    ) -> list[AdaptiveAcuityAttempt]:
        """Lists all answered attempts for a specific difficulty level in a test."""
        stmt = (
            select(AdaptiveAcuityAttempt)
            .where(
                AdaptiveAcuityAttempt.test_id == test_id,
                AdaptiveAcuityAttempt.level == level,
                AdaptiveAcuityAttempt.is_correct.is_not(None),
            )
            .order_by(AdaptiveAcuityAttempt.attempt_sequence.asc())
        )
        return list(db.execute(stmt).scalars().all())

    @staticmethod
    def update_attempt(db: Session, attempt: AdaptiveAcuityAttempt) -> AdaptiveAcuityAttempt:
        """Commits and refreshes updates to an attempt."""
        db.commit()
        db.refresh(attempt)
        return attempt

"""Data access repository for the Complete Online Vision Screening Platform."""

import uuid

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.models.online_screening import (
    ScreeningCalibration,
    ScreeningFinalReport,
    ScreeningTestInstance,
    ScreeningTestResponse,
)


class OnlineScreeningRepository:
    """Repository handling CRUD and queries for online vision screening modules, calibration, and reports."""

    # -------------------------------------------------------------------------
    # Calibration Operations
    # -------------------------------------------------------------------------

    @staticmethod
    def get_calibration_by_session(
        db: Session, session_id: uuid.UUID
    ) -> ScreeningCalibration | None:
        stmt = (
            select(ScreeningCalibration)
            .where(ScreeningCalibration.session_id == session_id)
            .order_by(ScreeningCalibration.created_at.desc())
        )
        return db.execute(stmt).scalars().first()

    @staticmethod
    def create_or_update_calibration(
        db: Session, calibration: ScreeningCalibration
    ) -> ScreeningCalibration:
        db.add(calibration)
        db.commit()
        db.refresh(calibration)
        return calibration

    # -------------------------------------------------------------------------
    # Test Instance Operations
    # -------------------------------------------------------------------------

    @staticmethod
    def create_test_instance(db: Session, instance: ScreeningTestInstance) -> ScreeningTestInstance:
        db.add(instance)
        db.commit()
        db.refresh(instance)
        return instance

    @staticmethod
    def get_test_instance_by_id(db: Session, test_id: uuid.UUID) -> ScreeningTestInstance | None:
        stmt = select(ScreeningTestInstance).where(ScreeningTestInstance.id == test_id)
        return db.execute(stmt).scalars().first()

    @staticmethod
    def get_test_instances_for_session(
        db: Session, session_id: uuid.UUID
    ) -> list[ScreeningTestInstance]:
        stmt = (
            select(ScreeningTestInstance)
            .where(ScreeningTestInstance.session_id == session_id)
            .order_by(ScreeningTestInstance.created_at.asc())
        )
        return list(db.execute(stmt).scalars().all())

    @staticmethod
    def get_active_test_instance(
        db: Session, session_id: uuid.UUID, test_type: str, eye: str
    ) -> ScreeningTestInstance | None:
        stmt = (
            select(ScreeningTestInstance)
            .where(
                ScreeningTestInstance.session_id == session_id,
                ScreeningTestInstance.test_type == test_type,
                ScreeningTestInstance.eye == eye,
                ScreeningTestInstance.status == "IN_PROGRESS",
            )
            .order_by(ScreeningTestInstance.created_at.desc())
        )
        return db.execute(stmt).scalars().first()

    # -------------------------------------------------------------------------
    # Test Response Operations
    # -------------------------------------------------------------------------

    @staticmethod
    def create_test_response(db: Session, response: ScreeningTestResponse) -> ScreeningTestResponse:
        db.add(response)
        db.commit()
        db.refresh(response)
        return response

    @staticmethod
    def get_responses_for_test(db: Session, test_id: uuid.UUID) -> list[ScreeningTestResponse]:
        stmt = (
            select(ScreeningTestResponse)
            .where(ScreeningTestResponse.test_instance_id == test_id)
            .order_by(ScreeningTestResponse.step_index.asc())
        )
        return list(db.execute(stmt).scalars().all())

    # -------------------------------------------------------------------------
    # Final Report Operations
    # -------------------------------------------------------------------------

    @staticmethod
    def create_final_report(db: Session, report: ScreeningFinalReport) -> ScreeningFinalReport:
        db.add(report)
        db.commit()
        db.refresh(report)
        return report

    @staticmethod
    def get_final_report_by_session(
        db: Session, session_id: uuid.UUID
    ) -> ScreeningFinalReport | None:
        stmt = select(ScreeningFinalReport).where(ScreeningFinalReport.session_id == session_id)
        return db.execute(stmt).scalars().first()

    @staticmethod
    def get_final_report_by_id(db: Session, report_id: uuid.UUID) -> ScreeningFinalReport | None:
        stmt = select(ScreeningFinalReport).where(ScreeningFinalReport.id == report_id)
        return db.execute(stmt).scalars().first()

    @staticmethod
    def get_final_report_by_number(db: Session, report_number: str) -> ScreeningFinalReport | None:
        stmt = select(ScreeningFinalReport).where(
            ScreeningFinalReport.report_number == report_number
        )
        return db.execute(stmt).scalars().first()

    @staticmethod
    def count_user_reports(db: Session, user_id: uuid.UUID) -> int:
        stmt = (
            select(func.count())
            .select_from(ScreeningFinalReport)
            .where(ScreeningFinalReport.user_id == user_id)
        )
        return db.execute(stmt).scalar() or 0

    @staticmethod
    def list_user_reports(
        db: Session, user_id: uuid.UUID, limit: int = 20, offset: int = 0
    ) -> list[ScreeningFinalReport]:
        stmt = (
            select(ScreeningFinalReport)
            .where(ScreeningFinalReport.user_id == user_id)
            .order_by(ScreeningFinalReport.created_at.desc())
            .limit(limit)
            .offset(offset)
        )
        return list(db.execute(stmt).scalars().all())

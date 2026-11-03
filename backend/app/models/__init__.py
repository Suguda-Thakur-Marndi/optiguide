"""Declarative ORM models package.

All domain models are registered here for Alembic discovery and metadata reflection.
"""

from app.database.base import Base
from app.models.screening_assessment import (
    AstigmatismAssessment,
    ColorVisionAssessment,
    VisualAcuityAssessment,
)
from app.models.screening_audit_event import ScreeningAuditEvent
from app.models.screening_consent import ScreeningConsent
from app.models.screening_session import ScreeningSession
from app.models.session import UserSession
from app.models.user import User

__all__ = [
    "AstigmatismAssessment",
    "Base",
    "ColorVisionAssessment",
    "ScreeningAuditEvent",
    "ScreeningConsent",
    "ScreeningSession",
    "User",
    "UserSession",
    "VisualAcuityAssessment",
]

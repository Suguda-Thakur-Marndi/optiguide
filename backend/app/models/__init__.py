"""Declarative ORM models package.

All domain models are registered here for Alembic discovery and metadata reflection.
"""

from app.database.base import Base
from app.models.catalog import (
    CatalogBrand,
    CatalogCategory,
    CatalogProduct,
    InventoryTransaction,
    Shop,
    ShopInventory,
)
from app.models.pd_assessment import PDAssessment
from app.models.recommendation import (
    EyewearRecommendation,
    RecommendationFeedback,
)
from app.models.referral import (
    ClinicalReview,
    PatientRecordShare,
    PatientReferral,
    ProfessionalProfile,
    ReferralAuditEvent,
)
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
    "CatalogBrand",
    "CatalogCategory",
    "CatalogProduct",
    "ClinicalReview",
    "ColorVisionAssessment",
    "EyewearRecommendation",
    "InventoryTransaction",
    "PDAssessment",
    "PatientRecordShare",
    "PatientReferral",
    "ProfessionalProfile",
    "RecommendationFeedback",
    "ReferralAuditEvent",
    "ScreeningAuditEvent",
    "ScreeningConsent",
    "ScreeningSession",
    "Shop",
    "ShopInventory",
    "User",
    "UserSession",
    "VisualAcuityAssessment",
]

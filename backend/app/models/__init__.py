"""SQLAlchemy declarative models for OptiGuide.

Phase 1 establishes the metadata base. Concrete business entities (users,
screenings, prescriptions, reports) will be migrated in subsequent phases.
"""

from backend.app.database.base import Base

__all__ = ["Base"]

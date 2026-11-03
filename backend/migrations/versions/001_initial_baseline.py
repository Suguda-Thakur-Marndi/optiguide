"""Initial baseline migration

Revision ID: 001_initial_baseline
Revises:
Create Date: 2026-11-02 01:00:00.000000

Phase 1 Baseline Migration:
Establishes the Alembic revision tracking baseline.
This migration is intentionally empty for Phase 1. It anchors the migration
tree and validates that the database connection, Alembic version table,
and upgrade/downgrade lifecycles work correctly across environments.
Application domain models (users, screenings, prescriptions, eyewear)
will be introduced via dedicated migrations in Phase 2.
"""

from collections.abc import Sequence

revision: str = "001_initial_baseline"
down_revision: str | None = None
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    # Baseline schema placeholder for Phase 1.
    # Future domain models will be added in Phase 2.
    pass


def downgrade() -> None:
    # Baseline schema placeholder for Phase 1.
    pass

"""Initial baseline migration

Revision ID: 001_initial_baseline
Revises:
Create Date: 2026-11-02 01:00:00.000000

"""

from collections.abc import Sequence

revision: str = "001_initial_baseline"
down_revision: str | None = None
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    # Baseline schema placeholder for Phase 1
    # Future tables (users, screenings, prescriptions) will be added in Phase 2
    pass


def downgrade() -> None:
    pass

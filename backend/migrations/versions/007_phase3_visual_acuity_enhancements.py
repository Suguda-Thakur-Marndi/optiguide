"""Add visual acuity assessment type and updated timestamp

Revision ID: 007_phase3_visual_acuity_enhancements
Revises: 006_phase4_1_inventory_constraints_and_referral_audit
Create Date: 2026-11-04 20:30:00.000000

Phase 3.2 Visual Acuity Enhancement Migration:
- Adds assessment_type (DISTANCE / NEAR) with index to visual_acuity_assessments.
- Adds updated_at timestamp to visual_acuity_assessments.
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = "007_phase3_visual_acuity_enhancements"
down_revision: str | None = "006_phase4_1_inventory_constraints_and_referral_audit"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    with op.batch_alter_table("visual_acuity_assessments", schema=None) as batch_op:
        batch_op.add_column(
            sa.Column(
                "assessment_type",
                sa.String(length=20),
                server_default=sa.text("'DISTANCE'"),
                nullable=False,
            )
        )
        batch_op.add_column(
            sa.Column(
                "updated_at",
                sa.DateTime(timezone=True),
                server_default=sa.text("CURRENT_TIMESTAMP"),
                nullable=False,
            )
        )
        batch_op.create_index(
            "ix_visual_acuity_assessments_assessment_type",
            ["assessment_type"],
            unique=False,
        )


def downgrade() -> None:
    with op.batch_alter_table("visual_acuity_assessments", schema=None) as batch_op:
        batch_op.drop_index("ix_visual_acuity_assessments_assessment_type")
        batch_op.drop_column("updated_at")
        batch_op.drop_column("assessment_type")

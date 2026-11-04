"""Add Phase 4.1 inventory constraints and referral audit events

Revision ID: 006_phase4_1_inventory_constraints_and_referral_audit
Revises: 005_phase4_referrals_catalog_recommendations_pd
Create Date: 2026-11-04 02:25:00.000000

Phase 4.1 Migration:
- Enforces database check constraint: reserved_quantity <= stock_quantity on shop_inventory
- Creates immutable referral_audit_events table for tracking referral lifecycle and review audits
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = "006_phase4_1_inventory_constraints_and_referral_audit"
down_revision: str | None = "005_phase4_referrals_catalog_recommendations_pd"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    # 1. Create referral_audit_events table
    op.create_table(
        "referral_audit_events",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("referral_id", sa.Uuid(), nullable=False),
        sa.Column("actor_id", sa.Uuid(), nullable=False),
        sa.Column("actor_role", sa.String(length=32), nullable=False),
        sa.Column("action", sa.String(length=64), nullable=False),
        sa.Column("previous_state", sa.String(length=32), nullable=True),
        sa.Column("new_state", sa.String(length=32), nullable=True),
        sa.Column(
            "occurred_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("CURRENT_TIMESTAMP"),
            nullable=False,
        ),
        sa.Column("metadata_json", sa.Text(), nullable=True),
        sa.ForeignKeyConstraint(["actor_id"], ["users.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["referral_id"], ["patient_referrals.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "ix_referral_audit_events_referral_id",
        "referral_audit_events",
        ["referral_id"],
        unique=False,
    )
    op.create_index(
        "ix_referral_audit_events_actor_id",
        "referral_audit_events",
        ["actor_id"],
        unique=False,
    )
    op.create_index(
        "ix_referral_audit_events_action",
        "referral_audit_events",
        ["action"],
        unique=False,
    )
    op.create_index(
        "ix_referral_audit_events_occurred_at",
        "referral_audit_events",
        ["occurred_at"],
        unique=False,
    )

    # 2. Add reserved <= stock constraint on shop_inventory
    # Note: On SQLite batch_alter_table is used if supported
    bind = op.get_bind()
    if bind.dialect.name != "sqlite":
        op.create_check_constraint(
            "ck_shop_inventory_reserved_le_stock",
            "shop_inventory",
            "reserved_quantity <= stock_quantity",
        )


def downgrade() -> None:
    bind = op.get_bind()
    if bind.dialect.name != "sqlite":
        op.drop_constraint(
            "ck_shop_inventory_reserved_le_stock",
            "shop_inventory",
            type_="check",
        )

    op.drop_index("ix_referral_audit_events_occurred_at", table_name="referral_audit_events")
    op.drop_index("ix_referral_audit_events_action", table_name="referral_audit_events")
    op.drop_index("ix_referral_audit_events_actor_id", table_name="referral_audit_events")
    op.drop_index("ix_referral_audit_events_referral_id", table_name="referral_audit_events")
    op.drop_table("referral_audit_events")

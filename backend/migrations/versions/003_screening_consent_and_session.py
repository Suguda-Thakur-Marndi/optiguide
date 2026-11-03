"""Add screening_consents, screening_sessions, and screening_audit_events tables

Revision ID: 003_screening_consent_and_session
Revises: 002_user_and_auth
Create Date: 2026-11-03 18:00:00.000000

Phase 3.1 Migration:
Creates informed consent, screening session lifecycle tracking,
and privacy-conscious audit telemetry tables for OptiGuide.
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = "003_screening_consent_and_session"
down_revision: str | None = "002_user_and_auth"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    # -------------------------------------------------------------------------
    # 1. screening_consents
    # -------------------------------------------------------------------------
    op.create_table(
        "screening_consents",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("user_id", sa.Uuid(), nullable=False),
        sa.Column("consent_version", sa.String(length=50), nullable=False),
        sa.Column("consent_text_hash", sa.String(length=64), nullable=False),
        sa.Column(
            "accepted_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("CURRENT_TIMESTAMP"),
            nullable=False,
        ),
        sa.Column("withdrawn_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("is_active", sa.Boolean(), server_default=sa.text("true"), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("CURRENT_TIMESTAMP"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("CURRENT_TIMESTAMP"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "ix_screening_consents_user_id", "screening_consents", ["user_id"], unique=False
    )
    op.create_index(
        "ix_screening_consents_consent_version",
        "screening_consents",
        ["consent_version"],
        unique=False,
    )
    op.create_index(
        "ix_screening_consents_is_active", "screening_consents", ["is_active"], unique=False
    )

    # -------------------------------------------------------------------------
    # 2. screening_sessions
    # -------------------------------------------------------------------------
    op.create_table(
        "screening_sessions",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("user_id", sa.Uuid(), nullable=False),
        sa.Column("consent_id", sa.Uuid(), nullable=False),
        sa.Column("status", sa.String(length=50), server_default="in_progress", nullable=False),
        sa.Column("cancellation_reason", sa.String(length=255), nullable=True),
        sa.Column(
            "started_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("CURRENT_TIMESTAMP"),
            nullable=False,
        ),
        sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("cancelled_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("CURRENT_TIMESTAMP"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("CURRENT_TIMESTAMP"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["consent_id"], ["screening_consents.id"], ondelete="RESTRICT"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "ix_screening_sessions_user_id", "screening_sessions", ["user_id"], unique=False
    )
    op.create_index(
        "ix_screening_sessions_consent_id", "screening_sessions", ["consent_id"], unique=False
    )
    op.create_index("ix_screening_sessions_status", "screening_sessions", ["status"], unique=False)
    op.create_index(
        "ix_screening_sessions_started_at", "screening_sessions", ["started_at"], unique=False
    )

    # -------------------------------------------------------------------------
    # 3. screening_audit_events
    # -------------------------------------------------------------------------
    op.create_table(
        "screening_audit_events",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("user_id", sa.Uuid(), nullable=False),
        sa.Column("session_id", sa.Uuid(), nullable=True),
        sa.Column("event_type", sa.String(length=50), nullable=False),
        sa.Column(
            "occurred_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("CURRENT_TIMESTAMP"),
            nullable=False,
        ),
        sa.Column("metadata_json", sa.Text(), nullable=True),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["session_id"], ["screening_sessions.id"], ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "ix_screening_audit_events_user_id", "screening_audit_events", ["user_id"], unique=False
    )
    op.create_index(
        "ix_screening_audit_events_session_id",
        "screening_audit_events",
        ["session_id"],
        unique=False,
    )
    op.create_index(
        "ix_screening_audit_events_event_type",
        "screening_audit_events",
        ["event_type"],
        unique=False,
    )
    op.create_index(
        "ix_screening_audit_events_occurred_at",
        "screening_audit_events",
        ["occurred_at"],
        unique=False,
    )


def downgrade() -> None:
    # Drop screening_audit_events
    op.drop_index("ix_screening_audit_events_occurred_at", table_name="screening_audit_events")
    op.drop_index("ix_screening_audit_events_event_type", table_name="screening_audit_events")
    op.drop_index("ix_screening_audit_events_session_id", table_name="screening_audit_events")
    op.drop_index("ix_screening_audit_events_user_id", table_name="screening_audit_events")
    op.drop_table("screening_audit_events")

    # Drop screening_sessions
    op.drop_index("ix_screening_sessions_started_at", table_name="screening_sessions")
    op.drop_index("ix_screening_sessions_status", table_name="screening_sessions")
    op.drop_index("ix_screening_sessions_consent_id", table_name="screening_sessions")
    op.drop_index("ix_screening_sessions_user_id", table_name="screening_sessions")
    op.drop_table("screening_sessions")

    # Drop screening_consents
    op.drop_index("ix_screening_consents_is_active", table_name="screening_consents")
    op.drop_index("ix_screening_consents_consent_version", table_name="screening_consents")
    op.drop_index("ix_screening_consents_user_id", table_name="screening_consents")
    op.drop_table("screening_consents")

"""Add clinical assessment tables (visual acuity, astigmatism, color vision)

Revision ID: 004_screening_clinical_assessments
Revises: 003_screening_consent_and_session
Create Date: 2026-11-03 23:15:00.000000

Phase 3 Migration:
Creates relational clinical assessment models for visual acuity (Snellen/logMAR),
astigmatism radial clock dial screening, and pseudoisochromatic color vision plate tests,
with support for physical screen calibration metadata.
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = "004_screening_clinical_assessments"
down_revision: str | None = "003_screening_consent_and_session"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    # -------------------------------------------------------------------------
    # 1. Update screening_sessions with optional notes and device_info
    # -------------------------------------------------------------------------
    with op.batch_alter_table("screening_sessions", schema=None) as batch_op:
        batch_op.add_column(sa.Column("notes", sa.String(length=500), nullable=True))
        batch_op.add_column(sa.Column("device_info", sa.Text(), nullable=True))

    # -------------------------------------------------------------------------
    # 2. visual_acuity_assessments
    # -------------------------------------------------------------------------
    op.create_table(
        "visual_acuity_assessments",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("session_id", sa.Uuid(), nullable=False),
        sa.Column("user_id", sa.Uuid(), nullable=False),
        sa.Column("test_eye", sa.String(length=20), nullable=False),
        sa.Column("snellen_fraction", sa.String(length=20), nullable=False),
        sa.Column("logmar", sa.Float(), nullable=False),
        sa.Column("decimal_acuity", sa.Float(), nullable=False),
        sa.Column(
            "tested_distance_meters",
            sa.Float(),
            server_default=sa.text("0.6"),
            nullable=False,
        ),
        sa.Column(
            "unassisted_or_corrected",
            sa.String(length=30),
            server_default=sa.text("'unassisted'"),
            nullable=False,
        ),
        sa.Column("near_reading_label", sa.String(length=20), nullable=True),
        sa.Column("near_reading_distance_cm", sa.Float(), nullable=True),
        sa.Column(
            "is_calibrated",
            sa.Boolean(),
            server_default=sa.text("false"),
            nullable=False,
        ),
        sa.Column("calibration_metadata", sa.Text(), nullable=True),
        sa.Column("observations", sa.String(length=500), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("CURRENT_TIMESTAMP"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(["session_id"], ["screening_sessions.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "ix_visual_acuity_assessments_session_id",
        "visual_acuity_assessments",
        ["session_id"],
        unique=False,
    )
    op.create_index(
        "ix_visual_acuity_assessments_user_id",
        "visual_acuity_assessments",
        ["user_id"],
        unique=False,
    )
    op.create_index(
        "ix_visual_acuity_assessments_test_eye",
        "visual_acuity_assessments",
        ["test_eye"],
        unique=False,
    )

    # -------------------------------------------------------------------------
    # 3. astigmatism_assessments
    # -------------------------------------------------------------------------
    op.create_table(
        "astigmatism_assessments",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("session_id", sa.Uuid(), nullable=False),
        sa.Column("user_id", sa.Uuid(), nullable=False),
        sa.Column(
            "chart_type",
            sa.String(length=50),
            server_default=sa.text("'clock_dial'"),
            nullable=False,
        ),
        sa.Column("has_uniform_clarity", sa.Boolean(), nullable=False),
        sa.Column("indicated_axes", sa.Text(), nullable=True),
        sa.Column("sharpest_meridian_hour", sa.Integer(), nullable=True),
        sa.Column("screening_observation", sa.String(length=500), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("CURRENT_TIMESTAMP"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(["session_id"], ["screening_sessions.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "ix_astigmatism_assessments_session_id",
        "astigmatism_assessments",
        ["session_id"],
        unique=False,
    )
    op.create_index(
        "ix_astigmatism_assessments_user_id",
        "astigmatism_assessments",
        ["user_id"],
        unique=False,
    )

    # -------------------------------------------------------------------------
    # 4. color_vision_assessments
    # -------------------------------------------------------------------------
    op.create_table(
        "color_vision_assessments",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("session_id", sa.Uuid(), nullable=False),
        sa.Column("user_id", sa.Uuid(), nullable=False),
        sa.Column(
            "test_protocol",
            sa.String(length=50),
            server_default=sa.text("'pseudoisochromatic_plates'"),
            nullable=False,
        ),
        sa.Column("total_plates_presented", sa.Integer(), nullable=False),
        sa.Column("correct_plate_count", sa.Integer(), nullable=False),
        sa.Column("deficiency_indicated", sa.Boolean(), nullable=False),
        sa.Column(
            "deficiency_type",
            sa.String(length=50),
            server_default=sa.text("'none'"),
            nullable=False,
        ),
        sa.Column("responses_detail", sa.Text(), nullable=True),
        sa.Column("screening_observation", sa.String(length=500), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("CURRENT_TIMESTAMP"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(["session_id"], ["screening_sessions.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "ix_color_vision_assessments_session_id",
        "color_vision_assessments",
        ["session_id"],
        unique=False,
    )
    op.create_index(
        "ix_color_vision_assessments_user_id",
        "color_vision_assessments",
        ["user_id"],
        unique=False,
    )


def downgrade() -> None:
    # Drop assessment tables in reverse order
    op.drop_index("ix_color_vision_assessments_user_id", table_name="color_vision_assessments")
    op.drop_index("ix_color_vision_assessments_session_id", table_name="color_vision_assessments")
    op.drop_table("color_vision_assessments")

    op.drop_index("ix_astigmatism_assessments_user_id", table_name="astigmatism_assessments")
    op.drop_index("ix_astigmatism_assessments_session_id", table_name="astigmatism_assessments")
    op.drop_table("astigmatism_assessments")

    op.drop_index("ix_visual_acuity_assessments_test_eye", table_name="visual_acuity_assessments")
    op.drop_index("ix_visual_acuity_assessments_user_id", table_name="visual_acuity_assessments")
    op.drop_index("ix_visual_acuity_assessments_session_id", table_name="visual_acuity_assessments")
    op.drop_table("visual_acuity_assessments")

    with op.batch_alter_table("screening_sessions", schema=None) as batch_op:
        batch_op.drop_column("device_info")
        batch_op.drop_column("notes")

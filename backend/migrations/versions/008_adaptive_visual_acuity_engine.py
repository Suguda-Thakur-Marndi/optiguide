"""phase3_adaptive_visual_acuity_engine

Revision ID: 008_adaptive_visual_acuity_engine
Revises: 007_phase3_visual_acuity_enhancements
Create Date: 2026-11-04 21:05:00.000000

"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = "008_adaptive_visual_acuity_engine"
down_revision: str | None = "007_phase3_visual_acuity_enhancements"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    # 1. Create adaptive_acuity_tests table
    op.create_table(
        "adaptive_acuity_tests",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("session_id", sa.Uuid(), nullable=False),
        sa.Column("user_id", sa.Uuid(), nullable=False),
        sa.Column("test_type", sa.String(length=20), server_default="DISTANCE", nullable=False),
        sa.Column("test_eye", sa.String(length=20), nullable=False),
        sa.Column(
            "optotype_type", sa.String(length=30), server_default="TUMBLING_E", nullable=False
        ),
        sa.Column(
            "protocol_version",
            sa.String(length=50),
            server_default="ISO8596_ATS_V1",
            nullable=False,
        ),
        sa.Column("status", sa.String(length=20), server_default="IN_PROGRESS", nullable=False),
        sa.Column(
            "calibration_status",
            sa.String(length=30),
            server_default="UNCALIBRATED",
            nullable=False,
        ),
        sa.Column("calibration_data", sa.Text(), nullable=True),
        sa.Column("viewing_distance_meters", sa.Float(), server_default="3.0", nullable=False),
        sa.Column("user_reported_occlusion", sa.Boolean(), server_default="1", nullable=False),
        sa.Column("current_level", sa.Integer(), server_default="0", nullable=False),
        sa.Column("current_attempt_sequence", sa.Integer(), server_default="1", nullable=False),
        sa.Column("current_optotype", sa.String(length=50), nullable=True),
        sa.Column("current_expected_response", sa.String(length=50), nullable=True),
        sa.Column("total_attempts", sa.Integer(), server_default="0", nullable=False),
        sa.Column("correct_attempts", sa.Integer(), server_default="0", nullable=False),
        sa.Column("incorrect_attempts", sa.Integer(), server_default="0", nullable=False),
        sa.Column("smallest_resolved_level", sa.Integer(), nullable=True),
        sa.Column("final_snellen", sa.String(length=20), nullable=True),
        sa.Column("final_logmar", sa.Float(), nullable=True),
        sa.Column("final_decimal", sa.Float(), nullable=True),
        sa.Column("assessment_id", sa.Uuid(), nullable=True),
        sa.Column("started_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("cancelled_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("cancellation_reason", sa.String(length=255), nullable=True),
        sa.ForeignKeyConstraint(
            ["assessment_id"], ["visual_acuity_assessments.id"], ondelete="SET NULL"
        ),
        sa.ForeignKeyConstraint(["session_id"], ["screening_sessions.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_adaptive_acuity_tests_session_id", "adaptive_acuity_tests", ["session_id"])
    op.create_index("ix_adaptive_acuity_tests_user_id", "adaptive_acuity_tests", ["user_id"])
    op.create_index("ix_adaptive_acuity_tests_status", "adaptive_acuity_tests", ["status"])
    op.create_index(
        "ix_adaptive_acuity_tests_assessment_id", "adaptive_acuity_tests", ["assessment_id"]
    )
    op.create_index("ix_adaptive_test_user_status", "adaptive_acuity_tests", ["user_id", "status"])
    op.create_index(
        "ix_adaptive_test_session_status", "adaptive_acuity_tests", ["session_id", "status"]
    )

    # 2. Create adaptive_acuity_attempts table
    op.create_table(
        "adaptive_acuity_attempts",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("test_id", sa.Uuid(), nullable=False),
        sa.Column("attempt_sequence", sa.Integer(), nullable=False),
        sa.Column("level", sa.Integer(), nullable=False),
        sa.Column("optotype_type", sa.String(length=30), nullable=False),
        sa.Column("presented_symbol", sa.String(length=50), nullable=False),
        sa.Column("expected_response", sa.String(length=50), nullable=False),
        sa.Column("user_response", sa.String(length=50), nullable=True),
        sa.Column("is_correct", sa.Boolean(), nullable=True),
        sa.Column("response_duration_ms", sa.Integer(), nullable=True),
        sa.Column("target_size_arcmin", sa.Float(), nullable=False),
        sa.Column("target_height_mm", sa.Float(), nullable=True),
        sa.Column("target_height_px", sa.Float(), nullable=True),
        sa.Column("presented_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("answered_at", sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(["test_id"], ["adaptive_acuity_tests.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("test_id", "attempt_sequence", name="uq_test_attempt_sequence"),
    )
    op.create_index("ix_adaptive_acuity_attempts_test_id", "adaptive_acuity_attempts", ["test_id"])
    op.create_index(
        "ix_adaptive_attempt_test_seq", "adaptive_acuity_attempts", ["test_id", "attempt_sequence"]
    )


def downgrade() -> None:
    op.drop_index("ix_adaptive_attempt_test_seq", table_name="adaptive_acuity_attempts")
    op.drop_index("ix_adaptive_acuity_attempts_test_id", table_name="adaptive_acuity_attempts")
    op.drop_table("adaptive_acuity_attempts")

    op.drop_index("ix_adaptive_test_session_status", table_name="adaptive_acuity_tests")
    op.drop_index("ix_adaptive_test_user_status", table_name="adaptive_acuity_tests")
    op.drop_index("ix_adaptive_acuity_tests_assessment_id", table_name="adaptive_acuity_tests")
    op.drop_index("ix_adaptive_acuity_tests_status", table_name="adaptive_acuity_tests")
    op.drop_index("ix_adaptive_acuity_tests_user_id", table_name="adaptive_acuity_tests")
    op.drop_index("ix_adaptive_acuity_tests_session_id", table_name="adaptive_acuity_tests")
    op.drop_table("adaptive_acuity_tests")

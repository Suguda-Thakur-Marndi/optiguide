"""online_vision_screening_platform

Revision ID: 009_online_vision_screening_platform
Revises: 008_adaptive_visual_acuity_engine
Create Date: 2026-11-05 01:25:00.000000

"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = "009_online_vision_screening_platform"
down_revision: str | None = "008_adaptive_visual_acuity_engine"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    # 1. Create screening_calibrations table
    op.create_table(
        "screening_calibrations",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("session_id", sa.Uuid(), nullable=False),
        sa.Column("user_id", sa.Uuid(), nullable=False),
        sa.Column("device_category", sa.String(length=50), server_default="DESKTOP", nullable=False),
        sa.Column("screen_width_px", sa.Integer(), nullable=True),
        sa.Column("screen_height_px", sa.Integer(), nullable=True),
        sa.Column("device_pixel_ratio", sa.Float(), nullable=True),
        sa.Column("calibration_method", sa.String(length=50), server_default="STANDARD_CARD", nullable=False),
        sa.Column("calibration_status", sa.String(length=50), server_default="UNCALIBRATED", nullable=False),
        sa.Column("computed_ppi", sa.Float(), nullable=True),
        sa.Column("target_viewing_distance_cm", sa.Float(), server_default="40.0", nullable=False),
        sa.Column("user_confirmed_distance", sa.Boolean(), server_default=sa.text("0"), nullable=False),
        sa.Column("calibration_notes", sa.String(length=255), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["session_id"], ["screening_sessions.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_screening_calibrations_session_id", "screening_calibrations", ["session_id"])
    op.create_index("ix_screening_calibrations_user_id", "screening_calibrations", ["user_id"])

    # 2. Create screening_test_instances table
    op.create_table(
        "screening_test_instances",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("session_id", sa.Uuid(), nullable=False),
        sa.Column("user_id", sa.Uuid(), nullable=False),
        sa.Column("test_type", sa.String(length=50), nullable=False),
        sa.Column("status", sa.String(length=30), server_default="NOT_STARTED", nullable=False),
        sa.Column("eye", sa.String(length=20), server_default="OU", nullable=False),
        sa.Column("viewing_condition", sa.String(length=30), server_default="WITH_GLASSES", nullable=False),
        sa.Column("current_step", sa.Integer(), server_default="0", nullable=False),
        sa.Column("total_steps", sa.Integer(), server_default="1", nullable=False),
        sa.Column("protocol_version", sa.String(length=50), server_default="OPTIGUIDE_V1", nullable=False),
        sa.Column("result_classification", sa.String(length=50), nullable=True),
        sa.Column("result_details", sa.Text(), nullable=True),
        sa.Column("clinical_observation", sa.String(length=500), nullable=True),
        sa.Column("started_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("cancelled_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("cancellation_reason", sa.String(length=255), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["session_id"], ["screening_sessions.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_screening_test_instances_session_id", "screening_test_instances", ["session_id"])
    op.create_index("ix_screening_test_instances_user_id", "screening_test_instances", ["user_id"])
    op.create_index("ix_screening_test_instances_test_type", "screening_test_instances", ["test_type"])
    op.create_index("ix_screening_test_instances_status", "screening_test_instances", ["status"])
    op.create_index("ix_test_inst_session_type", "screening_test_instances", ["session_id", "test_type"])
    op.create_index("ix_test_inst_user_status", "screening_test_instances", ["user_id", "status"])

    # 3. Create screening_test_responses table
    op.create_table(
        "screening_test_responses",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("test_instance_id", sa.Uuid(), nullable=False),
        sa.Column("step_index", sa.Integer(), nullable=False),
        sa.Column("stimulus_id", sa.String(length=50), nullable=False),
        sa.Column("stimulus_version", sa.String(length=50), server_default="1.0", nullable=False),
        sa.Column("expected_answer", sa.String(length=100), nullable=False),
        sa.Column("user_response", sa.String(length=100), nullable=False),
        sa.Column("is_correct", sa.Boolean(), nullable=True),
        sa.Column("response_time_ms", sa.Integer(), nullable=True),
        sa.Column("details", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["test_instance_id"], ["screening_test_instances.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("test_instance_id", "step_index", name="uq_test_response_step"),
    )
    op.create_index("ix_screening_test_responses_test_instance_id", "screening_test_responses", ["test_instance_id"])

    # 4. Create screening_final_reports table
    op.create_table(
        "screening_final_reports",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("session_id", sa.Uuid(), nullable=False),
        sa.Column("user_id", sa.Uuid(), nullable=False),
        sa.Column("report_number", sa.String(length=50), nullable=False),
        sa.Column("overall_classification", sa.String(length=50), nullable=False),
        sa.Column("protocol_version", sa.String(length=50), server_default="OPTIGUIDE_V1", nullable=False),
        sa.Column("completed_tests_count", sa.Integer(), server_default="0", nullable=False),
        sa.Column("skipped_tests_count", sa.Integer(), server_default="0", nullable=False),
        sa.Column("summary_content", sa.Text(), nullable=False),
        sa.Column("follow_up_recommendation", sa.String(length=500), nullable=False),
        sa.Column("professional_referral_indicated", sa.Boolean(), server_default=sa.text("0"), nullable=False),
        sa.Column("limitations_disclaimer", sa.Text(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["session_id"], ["screening_sessions.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("session_id"),
        sa.UniqueConstraint("report_number"),
    )
    op.create_index("ix_screening_final_reports_session_id", "screening_final_reports", ["session_id"])
    op.create_index("ix_screening_final_reports_user_id", "screening_final_reports", ["user_id"])
    op.create_index("ix_screening_final_reports_report_number", "screening_final_reports", ["report_number"])


def downgrade() -> None:
    op.drop_table("screening_final_reports")
    op.drop_table("screening_test_responses")
    op.drop_table("screening_test_instances")
    op.drop_table("screening_calibrations")

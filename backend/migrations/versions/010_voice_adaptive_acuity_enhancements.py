"""voice_adaptive_acuity_enhancements

Revision ID: 010_voice_adaptive_acuity_enhancements
Revises: 009_online_vision_screening_platform
Create Date: 2026-11-05 02:25:00.000000

"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = "010_voice_adaptive_acuity_enhancements"
down_revision: str | None = "009_online_vision_screening_platform"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    # Add voice telemetry and STT columns to adaptive_acuity_attempts
    with op.batch_alter_table("adaptive_acuity_attempts") as batch_op:
        batch_op.add_column(
            sa.Column(
                "input_modality",
                sa.String(length=20),
                server_default="MANUAL",
                nullable=False,
            )
        )
        batch_op.add_column(
            sa.Column(
                "transcription_confidence",
                sa.Float(),
                nullable=True,
            )
        )
        batch_op.add_column(
            sa.Column(
                "stt_provider",
                sa.String(length=50),
                nullable=True,
            )
        )
        batch_op.add_column(
            sa.Column(
                "raw_transcript",
                sa.String(length=255),
                nullable=True,
            )
        )
        batch_op.add_column(
            sa.Column(
                "recognition_status",
                sa.String(length=30),
                nullable=True,
            )
        )


def downgrade() -> None:
    with op.batch_alter_table("adaptive_acuity_attempts") as batch_op:
        batch_op.drop_column("recognition_status")
        batch_op.drop_column("raw_transcript")
        batch_op.drop_column("stt_provider")
        batch_op.drop_column("transcription_confidence")
        batch_op.drop_column("input_modality")

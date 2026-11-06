"""virtual_try_on_and_eyewear_ar

Revision ID: 011_virtual_try_on_and_eyewear_ar
Revises: 010_voice_adaptive_acuity_enhancements
Create Date: 2026-11-07 01:40:00.000000

"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = "011_virtual_try_on_and_eyewear_ar"
down_revision: str | None = "010_voice_adaptive_acuity_enhancements"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    # 1. Add try-on metadata columns to catalog_products
    with op.batch_alter_table("catalog_products") as batch_op:
        batch_op.add_column(
            sa.Column("try_on_asset_url", sa.String(length=500), nullable=True)
        )
        batch_op.add_column(
            sa.Column(
                "try_on_asset_type",
                sa.String(length=50),
                server_default="2d_png",
                nullable=True,
            )
        )
        batch_op.add_column(
            sa.Column(
                "frame_colors",
                sa.String(length=500),
                server_default="#111827:Classic Black,#78350F:Amber Tortoise,#D97706:Polished Gold,#475569:Gunmetal Silver,#1E3A8A:Deep Navy",
                nullable=True,
            )
        )
        batch_op.add_column(
            sa.Column("left_lens_center_x", sa.Float(), server_default="0.2875", nullable=True)
        )
        batch_op.add_column(
            sa.Column("left_lens_center_y", sa.Float(), server_default="0.5", nullable=True)
        )
        batch_op.add_column(
            sa.Column("right_lens_center_x", sa.Float(), server_default="0.7125", nullable=True)
        )
        batch_op.add_column(
            sa.Column("right_lens_center_y", sa.Float(), server_default="0.5", nullable=True)
        )
        batch_op.add_column(
            sa.Column("bridge_center_x", sa.Float(), server_default="0.5", nullable=True)
        )
        batch_op.add_column(
            sa.Column("bridge_center_y", sa.Float(), server_default="0.48", nullable=True)
        )
        batch_op.add_column(
            sa.Column("asset_scale", sa.Float(), server_default="1.0", nullable=False)
        )
        batch_op.add_column(
            sa.Column("asset_rotation_offset", sa.Float(), server_default="0.0", nullable=False)
        )
        batch_op.add_column(
            sa.Column(
                "asset_version", sa.String(length=20), server_default="1.0.0", nullable=False
            )
        )

    # 2. Create try_on_sessions table
    op.create_table(
        "try_on_sessions",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("user_id", sa.Uuid(), nullable=True),
        sa.Column("screening_session_id", sa.Uuid(), nullable=True),
        sa.Column("selected_product_id", sa.Uuid(), nullable=True),
        sa.Column("selected_color", sa.String(length=50), server_default="#111827", nullable=False),
        sa.Column("selected_scale", sa.Float(), server_default="1.0", nullable=False),
        sa.Column("selected_offset_y", sa.Float(), server_default="0.0", nullable=False),
        sa.Column("camera_facing", sa.String(length=20), server_default="user", nullable=False),
        sa.Column("device_type", sa.String(length=50), server_default="desktop", nullable=False),
        sa.Column("snapshots_count", sa.Integer(), server_default="0", nullable=False),
        sa.Column("is_active", sa.Boolean(), server_default="1", nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(
            ["screening_session_id"], ["screening_sessions.id"], ondelete="SET NULL"
        ),
        sa.ForeignKeyConstraint(
            ["selected_product_id"], ["catalog_products.id"], ondelete="SET NULL"
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    with op.batch_alter_table("try_on_sessions") as batch_op:
        batch_op.create_index("ix_try_on_sessions_user_id", ["user_id"])
        batch_op.create_index(
            "ix_try_on_sessions_screening_session_id", ["screening_session_id"]
        )
        batch_op.create_index(
            "ix_try_on_sessions_selected_product_id", ["selected_product_id"]
        )

    # 3. Create user_eyewear_favourites table
    op.create_table(
        "user_eyewear_favourites",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("user_id", sa.Uuid(), nullable=False),
        sa.Column("product_id", sa.Uuid(), nullable=False),
        sa.Column("selected_color", sa.String(length=50), server_default="#111827", nullable=False),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["product_id"], ["catalog_products.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("user_id", "product_id", name="uq_user_product_favourite"),
    )
    with op.batch_alter_table("user_eyewear_favourites") as batch_op:
        batch_op.create_index("ix_user_eyewear_favourites_user_id", ["user_id"])
        batch_op.create_index("ix_user_eyewear_favourites_product_id", ["product_id"])

    # 4. Create try_on_snapshots table
    op.create_table(
        "try_on_snapshots",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("session_id", sa.Uuid(), nullable=False),
        sa.Column("product_id", sa.Uuid(), nullable=True),
        sa.Column("selected_color", sa.String(length=50), server_default="#111827", nullable=False),
        sa.Column("title", sa.String(length=255), server_default="AR Eyewear Preview", nullable=False),
        sa.Column("face_detected", sa.Boolean(), server_default="1", nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["session_id"], ["try_on_sessions.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(
            ["product_id"], ["catalog_products.id"], ondelete="SET NULL"
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    with op.batch_alter_table("try_on_snapshots") as batch_op:
        batch_op.create_index("ix_try_on_snapshots_session_id", ["session_id"])
        batch_op.create_index("ix_try_on_snapshots_product_id", ["product_id"])


def downgrade() -> None:
    op.drop_table("try_on_snapshots")
    op.drop_table("user_eyewear_favourites")
    op.drop_table("try_on_sessions")
    with op.batch_alter_table("catalog_products") as batch_op:
        batch_op.drop_column("asset_version")
        batch_op.drop_column("asset_rotation_offset")
        batch_op.drop_column("asset_scale")
        batch_op.drop_column("bridge_center_y")
        batch_op.drop_column("bridge_center_x")
        batch_op.drop_column("right_lens_center_y")
        batch_op.drop_column("right_lens_center_x")
        batch_op.drop_column("left_lens_center_y")
        batch_op.drop_column("left_lens_center_x")
        batch_op.drop_column("frame_colors")
        batch_op.drop_column("try_on_asset_type")
        batch_op.drop_column("try_on_asset_url")

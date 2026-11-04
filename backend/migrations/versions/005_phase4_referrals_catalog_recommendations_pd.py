"""Add Phase 4 models: professional verification, referrals, sharing, catalog, inventory, recommendations, pd

Revision ID: 005_phase4_referrals_catalog_recommendations_pd
Revises: 004_screening_clinical_assessments
Create Date: 2026-11-03 23:55:00.000000

Phase 4 Migration:
Creates relational tables for:
- Professional verification (professional_profiles)
- Patient referrals & sharing (patient_referrals, patient_record_shares, clinical_reviews)
- Eyewear product catalog & shops (catalog_categories, catalog_brands, catalog_products, shops, shop_inventory, inventory_transactions)
- Eyewear guidance recommendations (eyewear_recommendations, recommendation_feedbacks)
- Pupillary distance assessments (pd_assessments)
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = "005_phase4_referrals_catalog_recommendations_pd"
down_revision: str | None = "004_screening_clinical_assessments"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    # -------------------------------------------------------------------------
    # 1. professional_profiles
    # -------------------------------------------------------------------------
    op.create_table(
        "professional_profiles",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("user_id", sa.Uuid(), nullable=False),
        sa.Column("license_number", sa.String(length=100), nullable=False),
        sa.Column("issuing_authority", sa.String(length=255), nullable=False),
        sa.Column("registration_year", sa.Integer(), nullable=False),
        sa.Column("qualification_title", sa.String(length=255), nullable=False),
        sa.Column(
            "verification_status",
            sa.String(length=32),
            server_default=sa.text("'PENDING'"),
            nullable=False,
        ),
        sa.Column("verified_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("verified_by_admin_id", sa.Uuid(), nullable=True),
        sa.Column("rejection_reason", sa.Text(), nullable=True),
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
        sa.ForeignKeyConstraint(["verified_by_admin_id"], ["users.id"], ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("user_id"),
    )
    op.create_index(
        "ix_professional_profiles_user_id", "professional_profiles", ["user_id"], unique=True
    )
    op.create_index(
        "ix_professional_profiles_license_number",
        "professional_profiles",
        ["license_number"],
        unique=False,
    )
    op.create_index(
        "ix_professional_profiles_verification_status",
        "professional_profiles",
        ["verification_status"],
        unique=False,
    )

    # -------------------------------------------------------------------------
    # 2. patient_referrals
    # -------------------------------------------------------------------------
    op.create_table(
        "patient_referrals",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("patient_id", sa.Uuid(), nullable=False),
        sa.Column("session_id", sa.Uuid(), nullable=False),
        sa.Column("referral_reason", sa.Text(), nullable=False),
        sa.Column(
            "clinical_priority",
            sa.String(length=32),
            server_default=sa.text("'ROUTINE'"),
            nullable=False,
        ),
        sa.Column(
            "status",
            sa.String(length=32),
            server_default=sa.text("'PENDING'"),
            nullable=False,
        ),
        sa.Column("notes", sa.Text(), nullable=True),
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
        sa.ForeignKeyConstraint(["patient_id"], ["users.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["session_id"], ["screening_sessions.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "ix_patient_referrals_patient_id", "patient_referrals", ["patient_id"], unique=False
    )
    op.create_index(
        "ix_patient_referrals_session_id", "patient_referrals", ["session_id"], unique=False
    )
    op.create_index("ix_patient_referrals_status", "patient_referrals", ["status"], unique=False)
    op.create_index(
        "ix_patient_referrals_clinical_priority",
        "patient_referrals",
        ["clinical_priority"],
        unique=False,
    )

    # -------------------------------------------------------------------------
    # 3. patient_record_shares
    # -------------------------------------------------------------------------
    op.create_table(
        "patient_record_shares",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("referral_id", sa.Uuid(), nullable=False),
        sa.Column("patient_id", sa.Uuid(), nullable=False),
        sa.Column("professional_id", sa.Uuid(), nullable=False),
        sa.Column(
            "access_status",
            sa.String(length=32),
            server_default=sa.text("'ACTIVE'"),
            nullable=False,
        ),
        sa.Column(
            "granted_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("CURRENT_TIMESTAMP"),
            nullable=False,
        ),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("revoked_at", sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(["referral_id"], ["patient_referrals.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["patient_id"], ["users.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["professional_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "ix_patient_record_shares_referral_id",
        "patient_record_shares",
        ["referral_id"],
        unique=False,
    )
    op.create_index(
        "ix_patient_record_shares_patient_id", "patient_record_shares", ["patient_id"], unique=False
    )
    op.create_index(
        "ix_patient_record_shares_professional_id",
        "patient_record_shares",
        ["professional_id"],
        unique=False,
    )
    op.create_index(
        "ix_patient_record_shares_access_status",
        "patient_record_shares",
        ["access_status"],
        unique=False,
    )

    # -------------------------------------------------------------------------
    # 4. clinical_reviews
    # -------------------------------------------------------------------------
    op.create_table(
        "clinical_reviews",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("referral_id", sa.Uuid(), nullable=False),
        sa.Column("professional_id", sa.Uuid(), nullable=False),
        sa.Column(
            "review_status",
            sa.String(length=32),
            server_default=sa.text("'IN_PROGRESS'"),
            nullable=False,
        ),
        sa.Column("professional_observations", sa.Text(), nullable=False),
        sa.Column(
            "in_person_exam_recommended",
            sa.Boolean(),
            server_default=sa.text("false"),
            nullable=False,
        ),
        sa.Column("recommended_exam_timeframe", sa.String(length=64), nullable=True),
        sa.Column("closed_at", sa.DateTime(timezone=True), nullable=True),
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
        sa.ForeignKeyConstraint(["referral_id"], ["patient_referrals.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["professional_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "ix_clinical_reviews_referral_id", "clinical_reviews", ["referral_id"], unique=False
    )
    op.create_index(
        "ix_clinical_reviews_professional_id", "clinical_reviews", ["professional_id"], unique=False
    )
    op.create_index(
        "ix_clinical_reviews_review_status", "clinical_reviews", ["review_status"], unique=False
    )

    # -------------------------------------------------------------------------
    # 5. catalog_categories
    # -------------------------------------------------------------------------
    op.create_table(
        "catalog_categories",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("name", sa.String(length=100), nullable=False),
        sa.Column("slug", sa.String(length=100), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("is_active", sa.Boolean(), server_default=sa.text("true"), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("name"),
        sa.UniqueConstraint("slug"),
    )
    op.create_index("ix_catalog_categories_slug", "catalog_categories", ["slug"], unique=True)

    # -------------------------------------------------------------------------
    # 6. catalog_brands
    # -------------------------------------------------------------------------
    op.create_table(
        "catalog_brands",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("name", sa.String(length=100), nullable=False),
        sa.Column("slug", sa.String(length=100), nullable=False),
        sa.Column("is_active", sa.Boolean(), server_default=sa.text("true"), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("name"),
        sa.UniqueConstraint("slug"),
    )
    op.create_index("ix_catalog_brands_slug", "catalog_brands", ["slug"], unique=True)

    # -------------------------------------------------------------------------
    # 7. catalog_products
    # -------------------------------------------------------------------------
    op.create_table(
        "catalog_products",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("sku", sa.String(length=64), nullable=False),
        sa.Column("name", sa.String(length=255), nullable=False),
        sa.Column("brand_id", sa.Uuid(), nullable=False),
        sa.Column("category_id", sa.Uuid(), nullable=False),
        sa.Column("frame_type", sa.String(length=50), nullable=False),
        sa.Column("frame_material", sa.String(length=50), nullable=False),
        sa.Column("frame_shape", sa.String(length=50), nullable=False),
        sa.Column(
            "gender_target",
            sa.String(length=20),
            server_default=sa.text("'unisex'"),
            nullable=False,
        ),
        sa.Column("frame_width_mm", sa.Float(), nullable=True),
        sa.Column("bridge_width_mm", sa.Float(), nullable=True),
        sa.Column("temple_length_mm", sa.Float(), nullable=True),
        sa.Column("lens_width_mm", sa.Float(), nullable=True),
        sa.Column("lens_height_mm", sa.Float(), nullable=True),
        sa.Column("base_price_inr", sa.Numeric(10, 2), nullable=False),
        sa.Column("is_active", sa.Boolean(), server_default=sa.text("true"), nullable=False),
        sa.Column("image_url", sa.String(length=500), nullable=True),
        sa.Column("description", sa.Text(), nullable=True),
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
        sa.ForeignKeyConstraint(["brand_id"], ["catalog_brands.id"], ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(["category_id"], ["catalog_categories.id"], ondelete="RESTRICT"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("sku"),
    )
    op.create_index("ix_catalog_products_sku", "catalog_products", ["sku"], unique=True)
    op.create_index("ix_catalog_products_name", "catalog_products", ["name"], unique=False)
    op.create_index("ix_catalog_products_brand_id", "catalog_products", ["brand_id"], unique=False)
    op.create_index(
        "ix_catalog_products_category_id", "catalog_products", ["category_id"], unique=False
    )
    op.create_index(
        "ix_catalog_products_frame_type", "catalog_products", ["frame_type"], unique=False
    )
    op.create_index(
        "ix_catalog_products_frame_material", "catalog_products", ["frame_material"], unique=False
    )
    op.create_index(
        "ix_catalog_products_frame_shape", "catalog_products", ["frame_shape"], unique=False
    )
    op.create_index(
        "ix_catalog_products_is_active", "catalog_products", ["is_active"], unique=False
    )

    # -------------------------------------------------------------------------
    # 8. shops
    # -------------------------------------------------------------------------
    op.create_table(
        "shops",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("name", sa.String(length=255), nullable=False),
        sa.Column("location_city", sa.String(length=100), nullable=False),
        sa.Column("location_state", sa.String(length=100), nullable=False),
        sa.Column("owner_user_id", sa.Uuid(), nullable=False),
        sa.Column("phone_number", sa.String(length=50), nullable=True),
        sa.Column("is_active", sa.Boolean(), server_default=sa.text("true"), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("CURRENT_TIMESTAMP"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(["owner_user_id"], ["users.id"], ondelete="RESTRICT"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_shops_location_city", "shops", ["location_city"], unique=False)
    op.create_index("ix_shops_location_state", "shops", ["location_state"], unique=False)
    op.create_index("ix_shops_owner_user_id", "shops", ["owner_user_id"], unique=False)

    # -------------------------------------------------------------------------
    # 9. shop_inventory
    # -------------------------------------------------------------------------
    op.create_table(
        "shop_inventory",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("shop_id", sa.Uuid(), nullable=False),
        sa.Column("product_id", sa.Uuid(), nullable=False),
        sa.Column("stock_quantity", sa.Integer(), server_default=sa.text("0"), nullable=False),
        sa.Column("reserved_quantity", sa.Integer(), server_default=sa.text("0"), nullable=False),
        sa.Column("low_stock_threshold", sa.Integer(), server_default=sa.text("3"), nullable=False),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("CURRENT_TIMESTAMP"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(["product_id"], ["catalog_products.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["shop_id"], ["shops.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("shop_id", "product_id", name="uq_shop_product_inventory"),
        sa.CheckConstraint("stock_quantity >= 0", name="ck_shop_inventory_stock_non_negative"),
        sa.CheckConstraint(
            "reserved_quantity >= 0", name="ck_shop_inventory_reserved_non_negative"
        ),
    )
    op.create_index("ix_shop_inventory_shop_id", "shop_inventory", ["shop_id"], unique=False)
    op.create_index("ix_shop_inventory_product_id", "shop_inventory", ["product_id"], unique=False)

    # -------------------------------------------------------------------------
    # 10. inventory_transactions
    # -------------------------------------------------------------------------
    op.create_table(
        "inventory_transactions",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("inventory_id", sa.Uuid(), nullable=False),
        sa.Column("operator_user_id", sa.Uuid(), nullable=True),
        sa.Column("quantity_delta", sa.Integer(), nullable=False),
        sa.Column("reason", sa.String(length=100), nullable=False),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.Column(
            "occurred_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("CURRENT_TIMESTAMP"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(["inventory_id"], ["shop_inventory.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["operator_user_id"], ["users.id"], ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "ix_inventory_transactions_inventory_id",
        "inventory_transactions",
        ["inventory_id"],
        unique=False,
    )

    # -------------------------------------------------------------------------
    # 11. eyewear_recommendations
    # -------------------------------------------------------------------------
    op.create_table(
        "eyewear_recommendations",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("user_id", sa.Uuid(), nullable=False),
        sa.Column("session_id", sa.Uuid(), nullable=True),
        sa.Column("input_criteria", sa.Text(), nullable=False),
        sa.Column("recommendations_json", sa.Text(), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("CURRENT_TIMESTAMP"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(["session_id"], ["screening_sessions.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "ix_eyewear_recommendations_user_id", "eyewear_recommendations", ["user_id"], unique=False
    )
    op.create_index(
        "ix_eyewear_recommendations_session_id",
        "eyewear_recommendations",
        ["session_id"],
        unique=False,
    )

    # -------------------------------------------------------------------------
    # 12. recommendation_feedbacks
    # -------------------------------------------------------------------------
    op.create_table(
        "recommendation_feedbacks",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("recommendation_id", sa.Uuid(), nullable=False),
        sa.Column("user_id", sa.Uuid(), nullable=False),
        sa.Column("selected_product_id", sa.Uuid(), nullable=True),
        sa.Column("rating", sa.Integer(), nullable=False),
        sa.Column("feedback_text", sa.Text(), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("CURRENT_TIMESTAMP"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(
            ["recommendation_id"], ["eyewear_recommendations.id"], ondelete="CASCADE"
        ),
        sa.ForeignKeyConstraint(
            ["selected_product_id"], ["catalog_products.id"], ondelete="SET NULL"
        ),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "ix_recommendation_feedbacks_recommendation_id",
        "recommendation_feedbacks",
        ["recommendation_id"],
        unique=False,
    )
    op.create_index(
        "ix_recommendation_feedbacks_user_id",
        "recommendation_feedbacks",
        ["user_id"],
        unique=False,
    )

    # -------------------------------------------------------------------------
    # 13. pd_assessments
    # -------------------------------------------------------------------------
    op.create_table(
        "pd_assessments",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("user_id", sa.Uuid(), nullable=False),
        sa.Column("session_id", sa.Uuid(), nullable=True),
        sa.Column(
            "measurement_type",
            sa.String(length=20),
            server_default=sa.text("'BINOCULAR'"),
            nullable=False,
        ),
        sa.Column("binocular_pd_mm", sa.Float(), nullable=False),
        sa.Column("monocular_left_pd_mm", sa.Float(), nullable=True),
        sa.Column("monocular_right_pd_mm", sa.Float(), nullable=True),
        sa.Column("unit", sa.String(length=10), server_default=sa.text("'mm'"), nullable=False),
        sa.Column(
            "estimation_method",
            sa.String(length=64),
            server_default=sa.text("'REFERENCE_CARD'"),
            nullable=False,
        ),
        sa.Column(
            "is_calibrated",
            sa.Boolean(),
            server_default=sa.text("false"),
            nullable=False,
        ),
        sa.Column(
            "is_server_verified",
            sa.Boolean(),
            server_default=sa.text("false"),
            nullable=False,
        ),
        sa.Column("calibration_metadata", sa.Text(), nullable=True),
        sa.Column("client_confidence_score", sa.Float(), nullable=True),
        sa.Column("server_confidence_score", sa.Float(), nullable=True),
        sa.Column("confidence_score", sa.Float(), nullable=True),
        sa.Column(
            "is_pediatric",
            sa.Boolean(),
            server_default=sa.text("false"),
            nullable=False,
        ),
        sa.Column("device_info", sa.Text(), nullable=True),
        sa.Column(
            "status",
            sa.String(length=32),
            server_default=sa.text("'ESTIMATED'"),
            nullable=False,
        ),
        sa.Column("rejection_reason", sa.Text(), nullable=True),
        sa.Column("reviewed_by_professional_id", sa.Uuid(), nullable=True),
        sa.Column("professional_review_notes", sa.Text(), nullable=True),
        sa.Column(
            "recorded_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("CURRENT_TIMESTAMP"),
            nullable=False,
        ),
        sa.Column("confirmed_at", sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(["reviewed_by_professional_id"], ["users.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["session_id"], ["screening_sessions.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_pd_assessments_user_id", "pd_assessments", ["user_id"], unique=False)
    op.create_index("ix_pd_assessments_session_id", "pd_assessments", ["session_id"], unique=False)
    op.create_index("ix_pd_assessments_status", "pd_assessments", ["status"], unique=False)


def downgrade() -> None:
    # Drop tables in reverse topological order
    op.drop_table("pd_assessments")
    op.drop_table("recommendation_feedbacks")
    op.drop_table("eyewear_recommendations")
    op.drop_table("inventory_transactions")
    op.drop_table("shop_inventory")
    op.drop_table("shops")
    op.drop_table("catalog_products")
    op.drop_table("catalog_brands")
    op.drop_table("catalog_categories")
    op.drop_table("clinical_reviews")
    op.drop_table("patient_record_shares")
    op.drop_table("patient_referrals")
    op.drop_table("professional_profiles")

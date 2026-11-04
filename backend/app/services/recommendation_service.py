import json
import uuid
from datetime import UTC, datetime
from decimal import Decimal
from typing import ClassVar

from sqlalchemy.orm import Session

from app.core.exceptions import EntityNotFoundException
from app.models.catalog import CatalogProduct
from app.models.recommendation import EyewearRecommendation, RecommendationFeedback
from app.models.user import User
from app.repositories.catalog_repository import CatalogRepository
from app.repositories.recommendation_repository import RecommendationRepository
from app.schemas.recommendation import (
    EyewearRecommendationRequest,
    EyewearRecommendationResponse,
    RecommendationFeedbackRequest,
    RecommendationFeedbackResponse,
    RecommendedProductItem,
)


class RecommendationService:
    """Deterministic, transparent, and explainable eyewear recommendation scoring engine."""

    # Complementary face shape to frame shape optical aesthetics map
    FACE_SHAPE_COMPATIBILITY: ClassVar[dict[str, list[str]]] = {
        "round": ["rectangular", "square", "wayfarer", "geometric"],
        "square": ["round", "oval", "aviator"],
        "oval": ["rectangular", "round", "square", "aviator", "cat_eye"],
        "heart": ["oval", "round", "rimless", "light_metal"],
        "diamond": ["oval", "cat_eye", "rimless"],
    }

    @classmethod
    def score_product(
        cls, product: CatalogProduct, criteria: EyewearRecommendationRequest, is_in_stock: bool
    ) -> tuple[float, list[str]]:
        score = 0.0
        reasons: list[str] = []
        price = Decimal(str(product.base_price_inr))

        # 1. Budget Compatibility (Max 30 points)
        if criteria.budget_max_inr is not None:
            budget = Decimal(str(criteria.budget_max_inr))
            if budget <= Decimal("0.00"):
                score += 0.0
                reasons.append(
                    f"Priced at ₹{price:.2f}. Budget limit is ₹{budget:.2f} (zero or negative), awarding 0 budget points."
                )
            elif price <= budget:
                score += 30.0
                reasons.append(
                    f"Priced at ₹{price:.2f}, comfortably within your budget limit of ₹{budget:.2f}."
                )
            elif price <= budget * Decimal("1.5"):
                # Pro-rated scale from 30 down to 0 points for up to 50% over budget
                excess = price - budget
                ratio = float(excess / (budget * Decimal("0.5")))
                budget_pts = max(0.0, 30.0 * (1.0 - ratio))
                score += budget_pts
                reasons.append(
                    f"Priced at ₹{price:.2f}, slightly above your target budget limit of ₹{budget:.2f}."
                )
            else:
                score += 0.0
                reasons.append(f"Priced at ₹{price:.2f}, exceeds target budget limit.")
        else:
            score += 15.0  # Neutral midpoint (15/30) when budget is unspecified

        # 2. Frame Shape Preference & Face Shape Aesthetics (Max 25 points)
        prod_shape = product.frame_shape.lower()
        if criteria.preferred_frame_shape:
            pref_shape = criteria.preferred_frame_shape.lower()
            if prod_shape == pref_shape:
                score += 25.0
                reasons.append(
                    f"Directly matches your preferred {product.frame_shape.title()} shape."
                )
            elif criteria.face_shape_preference:
                face = criteria.face_shape_preference.lower()
                compl = cls.FACE_SHAPE_COMPATIBILITY.get(face, [])
                if prod_shape in compl:
                    score += 20.0
                    reasons.append(
                        f"{product.frame_shape.title()} shape complements your {face.title()} facial profile."
                    )
                else:
                    score += 10.0
            else:
                score += 10.0
        elif criteria.face_shape_preference:
            face = criteria.face_shape_preference.lower()
            compl = cls.FACE_SHAPE_COMPATIBILITY.get(face, [])
            if prod_shape in compl:
                score += 25.0
                reasons.append(
                    f"{product.frame_shape.title()} shape provides optimal harmony for a {face.title()} face shape."
                )
            else:
                score += 10.0
        else:
            score += 12.5  # Neutral midpoint (12.5/25) when shape is unspecified

        # 3. Material Compatibility (Max 20 points)
        if criteria.preferred_frame_material:
            pref_mat = criteria.preferred_frame_material.lower()
            if product.frame_material.lower() == pref_mat:
                score += 20.0
                reasons.append(
                    f"Manufactured from high-durability {product.frame_material.title()} material as specified."
                )
            else:
                score += 5.0
        else:
            score += 10.0  # Neutral midpoint (10/20)

        # 4. Frame Type (Max 15 points)
        if criteria.preferred_frame_type:
            pref_type = criteria.preferred_frame_type.lower()
            if product.frame_type.lower() == pref_type:
                score += 15.0
                reasons.append(
                    f"Features your requested {product.frame_type.replace('_', ' ').title()} frame build."
                )
            else:
                score += 5.0
        else:
            score += 7.5  # Neutral midpoint (7.5/15)

        # 5. Availability & Stock Presence (Max 10 points)
        if is_in_stock:
            score += 10.0
            reasons.append("Currently in stock and ready for immediate fitting.")
        else:
            reasons.append(
                "Available for catalogue order (currently out of stock at selected kiosk)."
            )

        # Cap score between 0 and 100 exactly
        final_score = min(100.0, max(0.0, round(score, 1)))
        return final_score, reasons

    @staticmethod
    def generate_recommendations(
        db: Session, user: User, criteria: EyewearRecommendationRequest, limit: int = 5
    ) -> EyewearRecommendationResponse:
        # Query active catalogue products
        products, _ = CatalogRepository.search_products(
            db=db,
            gender_target=criteria.gender_target,
            is_active=True,
            limit=100,
            offset=0,
        )

        ranked_items: list[tuple[float, RecommendedProductItem]] = []

        for p in products:
            # Check shop stock if shop_id provided
            is_in_stock = True
            if criteria.shop_id:
                inv = CatalogRepository.get_inventory(db, criteria.shop_id, p.id)
                is_in_stock = inv is not None and (inv.stock_quantity - inv.reserved_quantity) > 0

            score, reasons = RecommendationService.score_product(p, criteria, is_in_stock)
            brand = CatalogRepository.get_brand_by_id(db, p.brand_id)

            item = RecommendedProductItem(
                product_id=p.id,
                sku=p.sku,
                name=p.name,
                brand_name=brand.name if brand else "OptiGuide Partner",
                base_price_inr=p.base_price_inr,
                frame_shape=p.frame_shape,
                frame_material=p.frame_material,
                frame_type=p.frame_type,
                image_url=p.image_url,
                match_score=score,
                match_reasons=reasons,
                is_in_stock=is_in_stock,
            )
            ranked_items.append((score, item))

        # Sort descending by match score
        ranked_items.sort(key=lambda x: x[0], reverse=True)
        top_matches = [item for _, item in ranked_items[:limit]]

        now = datetime.now(UTC)
        criteria_dict = criteria.model_dump(mode="json", exclude_none=True)
        matches_dict = [m.model_dump(mode="json") for m in top_matches]

        # Persist recommendation record
        rec_model = EyewearRecommendation(
            user_id=user.id,
            session_id=criteria.session_id,
            input_criteria=json.dumps(criteria_dict),
            recommendations_json=json.dumps(matches_dict),
            created_at=now,
        )
        created = RecommendationRepository.create_recommendation(db, rec_model)

        return EyewearRecommendationResponse(
            id=created.id,
            user_id=user.id,
            input_criteria=criteria_dict,
            recommendations=top_matches,
            created_at=now,
        )

    @staticmethod
    def get_recommendation(
        db: Session, user: User, recommendation_id: uuid.UUID
    ) -> EyewearRecommendationResponse:
        rec = RecommendationRepository.get_recommendation_by_id(db, recommendation_id)
        if not rec or rec.user_id != user.id:
            raise EntityNotFoundException("EyewearRecommendation", str(recommendation_id))

        input_criteria = json.loads(rec.input_criteria) if rec.input_criteria else {}
        recs_data = json.loads(rec.recommendations_json) if rec.recommendations_json else []
        items = [RecommendedProductItem.model_validate(r) for r in recs_data]

        return EyewearRecommendationResponse(
            id=rec.id,
            user_id=rec.user_id,
            input_criteria=input_criteria,
            recommendations=items,
            created_at=rec.created_at,
        )

    @staticmethod
    def submit_feedback(
        db: Session,
        user: User,
        recommendation_id: uuid.UUID,
        payload: RecommendationFeedbackRequest,
    ) -> RecommendationFeedbackResponse:
        rec = RecommendationRepository.get_recommendation_by_id(db, recommendation_id)
        if not rec or rec.user_id != user.id:
            raise EntityNotFoundException("EyewearRecommendation", str(recommendation_id))

        if payload.selected_product_id:
            product = CatalogRepository.get_product_by_id(db, payload.selected_product_id)
            if not product:
                raise EntityNotFoundException("CatalogProduct", str(payload.selected_product_id))

        now = datetime.now(UTC)
        feedback = RecommendationFeedback(
            recommendation_id=rec.id,
            user_id=user.id,
            selected_product_id=payload.selected_product_id,
            rating=payload.rating,
            feedback_text=payload.feedback_text.strip() if payload.feedback_text else None,
            created_at=now,
        )
        created = RecommendationRepository.create_feedback(db, feedback)
        return RecommendationFeedbackResponse.model_validate(created)

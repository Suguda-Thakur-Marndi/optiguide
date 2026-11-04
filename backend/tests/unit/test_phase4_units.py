import pytest

from app.core.exceptions import ValidationException
from app.models.catalog import CatalogProduct
from app.schemas.pd_assessment import PDAssessmentCreateRequest
from app.schemas.recommendation import EyewearRecommendationRequest
from app.services.pd_service import PDService
from app.services.recommendation_service import RecommendationService


def test_recommendation_scoring_within_budget():
    """Verifies that products within budget receive full 30 points and positive reason."""
    product = CatalogProduct(
        sku="TEST-001",
        name="Classic Acetate Frame",
        brand_id=None,
        category_id=None,
        frame_type="full_rim",
        frame_material="acetate",
        frame_shape="rectangular",
        base_price_inr=1500.0,
    )
    req = EyewearRecommendationRequest(
        budget_max_inr=2000.0,
        preferred_frame_shape="rectangular",
        preferred_frame_material="acetate",
        preferred_frame_type="full_rim",
    )
    score, reasons = RecommendationService.score_product(product, req, is_in_stock=True)
    assert score == 100.0
    assert any("comfortably within your budget" in r for r in reasons)
    assert any(
        "Matches your preferred Rectangular" in r or "rectangular" in r.lower() for r in reasons
    )
    assert any("Acetate" in r for r in reasons)


def test_recommendation_scoring_face_shape_aesthetics():
    """Verifies face-shape complementary frame matching."""
    product = CatalogProduct(
        sku="TEST-002",
        name="Round Metal Wire Frame",
        brand_id=None,
        category_id=None,
        frame_type="full_rim",
        frame_material="metal",
        frame_shape="round",
        base_price_inr=1200.0,
    )
    req = EyewearRecommendationRequest(
        face_shape_preference="square",  # Square face complements round frames
        budget_max_inr=1500.0,
    )
    score, reasons = RecommendationService.score_product(product, req, is_in_stock=False)
    assert score >= 60.0
    assert any("Square face shape" in r or "square" in r.lower() for r in reasons)


def test_pd_assessment_physiological_range_validation():
    """Verifies adult human PD physiological boundaries."""
    # Normal adult binocular PD
    valid_req = PDAssessmentCreateRequest(
        binocular_pd_mm=63.0,
        monocular_left_pd_mm=31.5,
        monocular_right_pd_mm=31.5,
        estimation_method="REFERENCE_CARD",
    )
    PDService.validate_measurement(valid_req)

    # Implausibly small binocular PD (< 45 mm)
    too_small = PDAssessmentCreateRequest(
        binocular_pd_mm=30.0,
        estimation_method="REFERENCE_CARD",
    )
    with pytest.raises(ValidationException) as exc_info:
        PDService.validate_measurement(too_small)
    assert "outside physiological human range" in str(exc_info.value)

    # Implausibly large binocular PD (> 80 mm)
    too_large = PDAssessmentCreateRequest(
        binocular_pd_mm=95.0,
        estimation_method="REFERENCE_CARD",
    )
    with pytest.raises(ValidationException) as exc_info:
        PDService.validate_measurement(too_large)
    assert "outside physiological human range" in str(exc_info.value)


def test_pd_assessment_monocular_sum_consistency():
    """Verifies that contradictory monocular and binocular values are rejected by schema."""
    with pytest.raises(ValueError) as exc_info:
        PDAssessmentCreateRequest(
            binocular_pd_mm=62.0,
            monocular_left_pd_mm=36.0,
            monocular_right_pd_mm=36.0,  # Sum = 72.0 mm, contradiction > 3 mm!
            estimation_method="REFERENCE_CARD",
        )
    assert "contradicts binocular measurement" in str(exc_info.value)

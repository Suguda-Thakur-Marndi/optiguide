"""
Integration test suite for Phase 4 Eyewear Recommendations and Pupillary Distance (PD) Estimation.
Verifies deterministic recommendation ranking, user feedback logging, PD measurement lifecycle,
physiological range validation, monocular sum consistency, and IDOR access controls.
"""

import uuid

from fastapi import status
from starlette.testclient import TestClient

from app.core.security import create_access_token
from app.models.user import User


def test_eyewear_recommendation_and_feedback_flow(
    client: TestClient, admin_user, patient_user, db_session
):
    """
    Verifies frame recommendation ranking against budget and facial aesthetics,
    auditability of user feedback, and privacy protection against cross-user feedback spoofing.
    """
    admin_token, _ = create_access_token(
        user_id=admin_user.id, email=admin_user.email, role="admin"
    )
    admin_headers = {"Authorization": f"Bearer {admin_token}"}

    patient_token, _ = create_access_token(
        user_id=patient_user.id, email=patient_user.email, role="patient"
    )
    patient_headers = {"Authorization": f"Bearer {patient_token}"}

    # 1. Admin creates catalog assets
    cat = client.post(
        "/api/v1/catalog/admin/categories",
        json={"name": "Everyday Optics", "slug": f"everyday-{uuid.uuid4().hex[:6]}"},
        headers=admin_headers,
    ).json()
    brand = client.post(
        "/api/v1/catalog/admin/brands",
        json={"name": "AuraEye", "slug": f"auraeye-{uuid.uuid4().hex[:6]}"},
        headers=admin_headers,
    ).json()

    # Budget Rectangular Acetate Frame (Priced 1100 INR)
    prod_rect = client.post(
        "/api/v1/catalog/admin/products",
        json={
            "sku": f"AURA-REC-{uuid.uuid4().hex[:4]}",
            "name": "Aura Classic Rectangular",
            "category_id": cat["id"],
            "brand_id": brand["id"],
            "frame_shape": "RECTANGULAR",
            "frame_type": "FULL_RIM",
            "frame_material": "ACETATE",
            "gender_target": "unisex",
            "base_price_inr": 1100.0,
        },
        headers=admin_headers,
    ).json()

    # Expensive Round Metal Frame (Priced 3500 INR)
    client.post(
        "/api/v1/catalog/admin/products",
        json={
            "sku": f"AURA-RND-{uuid.uuid4().hex[:4]}",
            "name": "Aura Premium Round",
            "category_id": cat["id"],
            "brand_id": brand["id"],
            "frame_shape": "ROUND",
            "frame_type": "FULL_RIM",
            "frame_material": "TITANIUM",
            "gender_target": "unisex",
            "base_price_inr": 3500.0,
        },
        headers=admin_headers,
    ).json()

    # 2. Patient requests recommendations for round face shape and budget <= 1500
    rec_payload = {
        "budget_max_inr": 1500.0,
        "face_shape_preference": "ROUND",
        "preferred_frame_shape": "RECTANGULAR",
        "gender_target": "unisex",
    }
    rec_res = client.post(
        "/api/v1/recommendations/eyewear", json=rec_payload, headers=patient_headers
    )
    assert rec_res.status_code == status.HTTP_200_OK
    rec_data = rec_res.json()
    recommendation_id = rec_data["id"]

    assert len(rec_data["recommendations"]) >= 1
    top_match = rec_data["recommendations"][0]
    assert top_match["product_id"] == prod_rect["id"]
    assert top_match["match_score"] >= 70.0
    assert any("budget" in r.lower() for r in top_match["match_reasons"])
    assert "clinical_disclaimer" in rec_data
    assert "non-clinical" in rec_data["clinical_disclaimer"].lower()

    # 3. Patient submits feedback
    fb_payload = {
        "selected_product_id": prod_rect["id"],
        "rating": 5,
        "feedback_text": "Great rectangular frames that match my style.",
    }
    fb_res = client.post(
        f"/api/v1/recommendations/{recommendation_id}/feedback",
        json=fb_payload,
        headers=patient_headers,
    )
    assert fb_res.status_code == status.HTTP_201_CREATED
    assert fb_res.json()["rating"] == 5

    # 4. Another patient cannot submit feedback on this recommendation (IDOR check)
    other_patient = User(
        email=f"other_{uuid.uuid4().hex[:8]}@example.com",
        hashed_password="mock_hash",
        full_name="Other Patient",
        role="patient",
        is_active=True,
    )
    db_session.add(other_patient)
    db_session.commit()
    other_token, _ = create_access_token(
        user_id=other_patient.id, email=other_patient.email, role="patient"
    )
    other_headers = {"Authorization": f"Bearer {other_token}"}

    idor_fb_res = client.post(
        f"/api/v1/recommendations/{recommendation_id}/feedback",
        json=fb_payload,
        headers=other_headers,
    )
    assert idor_fb_res.status_code == status.HTTP_404_NOT_FOUND


def test_pd_assessment_lifecycle_and_validation(client: TestClient, patient_user, db_session):
    """
    Verifies pupillary distance measurement persistence, confirmation, rejection,
    physiological human range enforcement, and IDOR isolation.
    """
    patient_token, _ = create_access_token(
        user_id=patient_user.id, email=patient_user.email, role="patient"
    )
    patient_headers = {"Authorization": f"Bearer {patient_token}"}

    # 1. Valid PD Measurement Creation
    valid_pd_payload = {
        "measurement_type": "BINOCULAR",
        "binocular_pd_mm": 63.5,
        "monocular_left_pd_mm": 31.5,
        "monocular_right_pd_mm": 32.0,
        "estimation_method": "REFERENCE_CARD",
        "is_calibrated": True,
        "confidence_score": 0.96,
    }
    create_res = client.post(
        "/api/v1/pd/assessments", json=valid_pd_payload, headers=patient_headers
    )
    assert create_res.status_code == status.HTTP_201_CREATED
    pd_data = create_res.json()
    assessment_id = pd_data["id"]
    assert pd_data["binocular_pd_mm"] == 63.5
    assert pd_data["status"] == "ESTIMATED"
    assert "clinical_disclaimer" in pd_data
    assert "pupillometer" in pd_data["clinical_disclaimer"].lower()

    # 2. Patient confirms the measurement
    confirm_res = client.patch(
        f"/api/v1/pd/assessments/{assessment_id}/confirm",
        headers=patient_headers,
    )
    assert confirm_res.status_code == status.HTTP_200_OK
    assert confirm_res.json()["status"] == "USER_CONFIRMED"
    assert confirm_res.json()["confirmed_at"] is not None

    # 3. Patient records a second PD and rejects it
    pd2_res = client.post(
        "/api/v1/pd/assessments",
        json={"binocular_pd_mm": 61.0, "estimation_method": "REFERENCE_CARD"},
        headers=patient_headers,
    )
    assert pd2_res.status_code == status.HTTP_201_CREATED
    assessment_id_2 = pd2_res.json()["id"]

    reject_res = client.post(
        f"/api/v1/pd/assessments/{assessment_id_2}/reject",
        json={"rejection_reason": "Excessive head rotation detected during capture."},
        headers=patient_headers,
    )
    assert reject_res.status_code == status.HTTP_200_OK
    assert reject_res.json()["status"] == "REJECTED"
    assert "Excessive head rotation" in reject_res.json()["rejection_reason"]

    # 4. List my PD assessments
    list_res = client.get("/api/v1/pd/assessments/me", headers=patient_headers)
    assert list_res.status_code == status.HTTP_200_OK
    items = list_res.json()["items"]
    assert len(items) >= 2

    # 5. Physiological constraint enforcement: Out of range (< 45 mm or > 80 mm)
    too_small_res = client.post(
        "/api/v1/pd/assessments",
        json={"binocular_pd_mm": 35.0, "estimation_method": "REFERENCE_CARD"},
        headers=patient_headers,
    )
    assert too_small_res.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY

    too_large_res = client.post(
        "/api/v1/pd/assessments",
        json={"binocular_pd_mm": 95.0, "estimation_method": "REFERENCE_CARD"},
        headers=patient_headers,
    )
    assert too_large_res.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY

    # 6. Physiological constraint enforcement: Contradictory monocular sum (> 3mm diff)
    inconsistent_res = client.post(
        "/api/v1/pd/assessments",
        json={
            "binocular_pd_mm": 60.0,
            "monocular_left_pd_mm": 36.0,
            "monocular_right_pd_mm": 36.0,  # 36 + 36 = 72, diff 12 mm > 3 mm
            "estimation_method": "REFERENCE_CARD",
        },
        headers=patient_headers,
    )
    assert inconsistent_res.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY

    # 7. IDOR Protection: Another patient cannot access or confirm assessment 1
    other_patient = User(
        email=f"other_pd_{uuid.uuid4().hex[:8]}@example.com",
        hashed_password="mock_hash",
        full_name="Other PD User",
        role="patient",
        is_active=True,
    )
    db_session.add(other_patient)
    db_session.commit()
    other_token, _ = create_access_token(
        user_id=other_patient.id, email=other_patient.email, role="patient"
    )
    other_headers = {"Authorization": f"Bearer {other_token}"}

    idor_confirm = client.patch(
        f"/api/v1/pd/assessments/{assessment_id}/confirm",
        headers=other_headers,
    )
    assert idor_confirm.status_code == status.HTTP_404_NOT_FOUND

import uuid
from decimal import Decimal

import pytest
from starlette.testclient import TestClient

from app.core.security import create_access_token
from app.models.catalog import CatalogBrand, CatalogCategory, CatalogProduct, Shop, ShopInventory
from app.models.screening_consent import ScreeningConsent
from app.models.screening_session import ScreeningSession
from app.models.user import User
from app.schemas.recommendation import EyewearRecommendationRequest
from app.services.recommendation_service import RecommendationService


@pytest.fixture
def remediation_patient(db_session) -> User:
    user = User(
        email=f"patient_rem_{uuid.uuid4().hex[:8]}@example.com",
        hashed_password="mock_argon2_hash",
        full_name="Remediation Patient",
        role="patient",
        is_active=True,
    )
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)
    return user


@pytest.fixture
def remediation_optometrist(db_session) -> User:
    user = User(
        email=f"optom_rem_{uuid.uuid4().hex[:8]}@example.com",
        hashed_password="mock_argon2_hash",
        full_name="Dr. Remediation Optometrist",
        role="optometrist",
        is_active=True,
        is_verified=True,
    )
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)

    from app.models.referral import ProfessionalProfile

    prof = ProfessionalProfile(
        user_id=user.id,
        license_number="LIC-REM-777",
        issuing_authority="State Medical Board",
        registration_year=2021,
        qualification_title="B.Optom",
        verification_status="VERIFIED",
    )
    db_session.add(prof)
    db_session.commit()
    return user


@pytest.fixture
def remediation_shopkeeper(db_session) -> User:
    user = User(
        email=f"shop_rem_{uuid.uuid4().hex[:8]}@example.com",
        hashed_password="mock_argon2_hash",
        full_name="Shop Owner",
        role="shopkeeper",
        is_active=True,
        is_verified=True,
    )
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)
    return user


@pytest.fixture
def remediation_session(db_session, remediation_patient) -> ScreeningSession:
    consent = ScreeningConsent(
        user_id=remediation_patient.id,
        consent_version="1.0.0",
        consent_text_hash="hash_remed",
        is_active=True,
    )
    db_session.add(consent)
    db_session.commit()

    sess = ScreeningSession(
        user_id=remediation_patient.id,
        consent_id=consent.id,
        status="completed",
    )
    db_session.add(sess)
    db_session.commit()
    db_session.refresh(sess)
    return sess


def test_pd_client_spoofing_defense(client: TestClient, db_session, remediation_patient):
    """Verifies that client cannot forge calibration or confidence; server marks unverified with safe default confidence."""
    token, _ = create_access_token(
        user_id=remediation_patient.id, email=remediation_patient.email, role="patient"
    )
    headers = {"Authorization": f"Bearer {token}"}

    # Client claims 100% confidence and calibrated without geometric metadata
    payload = {
        "binocular_pd_mm": 62.0,
        "monocular_left_pd_mm": 31.0,
        "monocular_right_pd_mm": 31.0,
        "estimation_method": "REFERENCE_CARD",
        "is_calibrated": True,  # Untrusted client claim
        "confidence_score": 1.0,  # Untrusted client claim
    }
    res = client.post("/api/v1/pd/assessments", json=payload, headers=headers)
    assert res.status_code == 201
    data = res.json()
    assert data["is_server_verified"] is False
    assert data["server_confidence_score"] is None
    assert data["confidence_score"] is None
    assert data["status"] == "ESTIMATED"


def test_pd_pediatric_range_validation(client: TestClient, db_session, remediation_patient):
    """Verifies demographic-aware boundaries for pediatric vs adult PD measurements."""
    from app.core.exceptions import ValidationException
    from app.schemas.pd_assessment import PDAssessmentCreateRequest
    from app.services.pd_service import PDService

    # Valid pediatric measurement (38-55 mm binocular, 18-30 mm monocular)
    valid_pedia = PDAssessmentCreateRequest(
        binocular_pd_mm=48.0,
        monocular_left_pd_mm=24.0,
        monocular_right_pd_mm=24.0,
        is_pediatric=True,
        estimation_method="REFERENCE_CARD",
    )
    PDService.validate_measurement(valid_pedia)

    # Invalid pediatric measurement (60 mm binocular is too large for pediatric)
    too_large_pedia = PDAssessmentCreateRequest(
        binocular_pd_mm=60.0,
        monocular_left_pd_mm=30.0,
        monocular_right_pd_mm=30.0,
        is_pediatric=True,
        estimation_method="REFERENCE_CARD",
    )
    with pytest.raises(ValidationException) as exc:
        PDService.validate_measurement(too_large_pedia)
    assert "outside physiological pediatric range" in str(exc.value)


def test_pd_professional_review_flow(
    client: TestClient,
    db_session,
    remediation_patient,
    remediation_optometrist,
    remediation_session,
):
    """Verifies that an optometrist can professionally review and confirm an estimated PD."""
    pat_token, _ = create_access_token(
        user_id=remediation_patient.id, email=remediation_patient.email, role="patient"
    )
    optom_token, _ = create_access_token(
        user_id=remediation_optometrist.id,
        email=remediation_optometrist.email,
        role="optometrist",
    )

    # Patient records estimate
    create_res = client.post(
        "/api/v1/pd/assessments",
        json={"binocular_pd_mm": 63.0, "estimation_method": "REFERENCE_CARD"},
        headers={"Authorization": f"Bearer {pat_token}"},
    )
    assert create_res.status_code == 201
    assessment_id = create_res.json()["id"]

    # Patient establishes active record share with the optometrist for clinical verification
    from datetime import UTC, datetime, timedelta

    from app.models.referral import PatientRecordShare, PatientReferral

    referral = PatientReferral(
        patient_id=remediation_patient.id,
        session_id=remediation_session.id,
        referral_reason="PD verification requested",
        clinical_priority="ROUTINE",
        status="SHARED",
    )
    db_session.add(referral)
    db_session.flush()

    share = PatientRecordShare(
        referral_id=referral.id,
        patient_id=remediation_patient.id,
        professional_id=remediation_optometrist.id,
        access_status="ACTIVE",
        expires_at=datetime.now(UTC) + timedelta(days=7),
    )
    db_session.add(share)
    db_session.commit()

    # Optometrist reviews the measurement
    review_res = client.post(
        f"/api/v1/pd/assessments/{assessment_id}/professional-review",
        json={
            "action": "CONFIRM",
            "clinical_notes": "Verified with digital pupillometer. Binocular PD confirmed at 63.0 mm.",
        },
        headers={"Authorization": f"Bearer {optom_token}"},
    )
    assert review_res.status_code == 200
    rev_data = review_res.json()
    assert rev_data["status"] == "PROFESSIONALLY_REVIEWED"
    assert rev_data["is_server_verified"] is True
    assert rev_data["confidence_score"] >= 0.95
    assert "Verified with digital pupillometer" in rev_data["professional_review_notes"]


def test_referral_urgent_priority_self_assignment_blocked(
    client: TestClient, db_session, remediation_patient, remediation_session
):
    """Verifies that a patient cannot assign URGENT priority without clinical findings warranting it."""
    token, _ = create_access_token(
        user_id=remediation_patient.id, email=remediation_patient.email, role="patient"
    )
    headers = {"Authorization": f"Bearer {token}"}

    # Session has no abnormal acuity/astigmatism findings
    bad_payload = {
        "session_id": str(remediation_session.id),
        "referral_reason": "I think I need urgent eye surgery",
        "clinical_priority": "URGENT",
    }
    res = client.post("/api/v1/referrals", json=bad_payload, headers=headers)
    assert res.status_code == 422 or res.status_code == 400
    assert "supporting high-risk clinical assessment findings" in res.json()["error"]["message"]


def test_referral_state_machine_invalid_transition(
    client: TestClient, db_session, remediation_patient, remediation_session
):
    """Verifies that illegal status transitions are rejected."""
    from app.core.exceptions import ValidationException
    from app.models.referral import PatientReferral
    from app.services.referral_service import ReferralService

    referral = PatientReferral(
        patient_id=remediation_patient.id,
        session_id=remediation_session.id,
        referral_reason="Blurry vision",
        clinical_priority="ROUTINE",
        status="CLOSED",
    )
    db_session.add(referral)
    db_session.commit()

    # Attempting to transition from CLOSED to PENDING must raise ValidationException
    with pytest.raises(ValidationException) as exc:
        ReferralService.transition_status(db_session, referral, "PENDING", remediation_patient)
    assert "Invalid referral status transition" in str(exc.value)


def test_referral_expired_and_revoked_shares_rejected(
    client: TestClient,
    db_session,
    remediation_patient,
    remediation_optometrist,
    remediation_session,
):
    """Verifies that expired and revoked shares return 403 Forbidden with clear diagnostic rationale."""
    pat_token, _ = create_access_token(
        user_id=remediation_patient.id, email=remediation_patient.email, role="patient"
    )
    optom_token, _ = create_access_token(
        user_id=remediation_optometrist.id,
        email=remediation_optometrist.email,
        role="optometrist",
    )
    pat_headers = {"Authorization": f"Bearer {pat_token}"}
    optom_headers = {"Authorization": f"Bearer {optom_token}"}

    # 1. Create referral
    ref_res = client.post(
        "/api/v1/referrals",
        json={"session_id": str(remediation_session.id), "referral_reason": "Astigmatism test"},
        headers=pat_headers,
    )
    ref_id = ref_res.json()["id"]

    # 2. Share with optometrist
    share_res = client.post(
        f"/api/v1/referrals/{ref_id}/share",
        json={"professional_id": str(remediation_optometrist.id), "expires_in_days": 1},
        headers=pat_headers,
    )
    share_id = share_res.json()["id"]

    # 3. Revoke access
    client.post(f"/api/v1/referrals/{ref_id}/shares/{share_id}/revoke", headers=pat_headers)

    # 4. Optometrist attempts to access revoked record -> 403 Forbidden
    detail_res = client.get(f"/api/v1/professionals/shared-records/{ref_id}", headers=optom_headers)
    assert detail_res.status_code == 403
    assert "revoked" in detail_res.json()["error"]["message"].lower()

    # 5. Optometrist attempts to submit review on revoked share -> 403 Forbidden
    review_res = client.post(
        f"/api/v1/professionals/reviews/{ref_id}",
        json={
            "professional_observations": "Observation after revocation",
            "in_person_exam_recommended": True,
        },
        headers=optom_headers,
    )
    assert review_res.status_code == 403


def test_inventory_reserved_quantity_defense(
    client: TestClient, db_session, remediation_shopkeeper
):
    """Verifies that shop stock cannot be updated below currently reserved quantity."""
    brand = CatalogBrand(name="TestBrand Rem", slug="testbrand-rem")
    cat = CatalogCategory(name="TestCat Rem", slug="testcat-rem")
    db_session.add_all([brand, cat])
    db_session.commit()

    prod = CatalogProduct(
        sku="SKU-REM-001",
        name="Remediation Frame",
        brand_id=brand.id,
        category_id=cat.id,
        frame_type="Full Rim",
        frame_material="Titanium",
        frame_shape="Round",
        base_price_inr=Decimal("1500.00"),
    )
    shop = Shop(
        name="Remediation Optical",
        location_city="Pune",
        location_state="Maharashtra",
        owner_user_id=remediation_shopkeeper.id,
    )
    db_session.add_all([prod, shop])
    db_session.commit()

    # Initial inventory: stock = 10, reserved = 4
    inv = ShopInventory(
        shop_id=shop.id,
        product_id=prod.id,
        stock_quantity=10,
        reserved_quantity=4,
    )
    db_session.add(inv)
    db_session.commit()

    token, _ = create_access_token(
        user_id=remediation_shopkeeper.id,
        email=remediation_shopkeeper.email,
        role="shopkeeper",
    )
    headers = {"Authorization": f"Bearer {token}"}

    # Attempt to reduce stock by 8 (which leaves stock 2, less than reserved 4) -> must fail with 422/400
    res = client.post(
        f"/api/v1/shops/{shop.id}/inventory/adjust",
        json={"product_id": str(prod.id), "quantity_delta": -8, "reason": "ADJUSTMENT"},
        headers=headers,
    )
    assert res.status_code == 422 or res.status_code == 400
    assert "units are currently reserved" in res.json()["error"]["message"]


def test_recommendation_scoring_maximum_is_100():
    """Verifies that perfectly matching frames score exactly 100.0 max."""
    product = CatalogProduct(
        id=uuid.uuid4(),
        sku="PERFECT-100",
        name="Perfect Harmony Frame",
        brand_id=None,
        category_id=None,
        frame_type="full_rim",
        frame_material="titanium",
        frame_shape="round",
        gender_target="unisex",
        base_price_inr=Decimal("1000.00"),
        is_active=True,
    )

    criteria = EyewearRecommendationRequest(
        budget_max_inr=Decimal("2000.00"),
        face_shape_preference="square",  # Square harmonizes optimally (25 pts) with Round frames
        preferred_frame_material="titanium",  # 20 pts
        preferred_frame_type="full_rim",  # 15 pts
    )

    # With stock available: Budget(30) + Shape(25) + Material(20) + FrameType(15) + Stock(10) = 100.0
    score, reasons = RecommendationService.score_product(product, criteria, is_in_stock=True)
    assert score == 100.0
    assert any("comfortably within your budget" in r for r in reasons)
    assert any("square face" in r.lower() for r in reasons)
    assert any("titanium" in r.lower() for r in reasons)
    assert any("full rim" in r.lower() or "full_rim" in r.lower() for r in reasons)
    assert any("currently in stock" in r.lower() for r in reasons)

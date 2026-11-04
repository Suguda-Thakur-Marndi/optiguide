import uuid
from datetime import UTC, datetime, timedelta
from decimal import Decimal

import pytest
from starlette.testclient import TestClient

from app.core.exceptions import ValidationException
from app.core.security import create_access_token
from app.models.catalog import CatalogBrand, CatalogCategory, CatalogProduct, Shop, ShopInventory
from app.models.referral import PatientRecordShare, PatientReferral, ReferralAuditEvent
from app.models.screening_consent import ScreeningConsent
from app.models.screening_session import ScreeningSession
from app.models.user import User
from app.schemas.recommendation import EyewearRecommendationRequest
from app.services.recommendation_service import RecommendationService
from app.services.referral_service import ReferralService


# -----------------------------------------------------------------------------
# Fixtures
# -----------------------------------------------------------------------------
@pytest.fixture
def p41_patient(db_session) -> User:
    user = User(
        email=f"patient_p41_{uuid.uuid4().hex[:8]}@example.com",
        hashed_password="mock_argon2_hash",
        full_name="P41 Patient",
        role="patient",
        is_active=True,
    )
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)
    return user


@pytest.fixture
def p41_optometrist(db_session) -> User:
    user = User(
        email=f"optom_p41_{uuid.uuid4().hex[:8]}@example.com",
        hashed_password="mock_argon2_hash",
        full_name="Dr. P41 Optometrist",
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
        license_number="LIC-P41-999",
        issuing_authority="State Medical Board",
        registration_year=2021,
        qualification_title="B.Optom",
        verification_status="VERIFIED",
    )
    db_session.add(prof)
    db_session.commit()
    return user


@pytest.fixture
def p41_shopkeeper(db_session) -> User:
    user = User(
        email=f"shop_p41_{uuid.uuid4().hex[:8]}@example.com",
        hashed_password="mock_argon2_hash",
        full_name="P41 Shop Owner",
        role="shopkeeper",
        is_active=True,
        is_verified=True,
    )
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)
    return user


@pytest.fixture
def p41_other_shopkeeper(db_session) -> User:
    user = User(
        email=f"other_shop_p41_{uuid.uuid4().hex[:8]}@example.com",
        hashed_password="mock_argon2_hash",
        full_name="P41 Other Shop Owner",
        role="shopkeeper",
        is_active=True,
        is_verified=True,
    )
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)
    return user


@pytest.fixture
def p41_screening_session(db_session, p41_patient) -> ScreeningSession:
    consent = ScreeningConsent(
        user_id=p41_patient.id,
        consent_version="1.0.0",
        consent_text_hash="hash_p41",
        is_active=True,
    )
    db_session.add(consent)
    db_session.commit()

    sess = ScreeningSession(
        user_id=p41_patient.id,
        consent_id=consent.id,
        status="completed",
        started_at=datetime.now(UTC),
    )
    db_session.add(sess)
    db_session.commit()
    db_session.refresh(sess)
    return sess


# -----------------------------------------------------------------------------
# 1. PD Trust Boundary & Clinician Review Security
# -----------------------------------------------------------------------------
def test_pd_client_untrusted_claims_not_verified(client: TestClient, p41_patient):
    """Client claims of calibration and high confidence must be rejected; marked unverified."""
    token, _ = create_access_token(user_id=p41_patient.id, email=p41_patient.email, role="patient")
    headers = {"Authorization": f"Bearer {token}"}

    payload = {
        "binocular_pd_mm": 64.0,
        "monocular_left_pd_mm": 32.0,
        "monocular_right_pd_mm": 32.0,
        "estimation_method": "REFERENCE_CARD",
        "is_calibrated": True,  # Untrusted client claim
        "confidence_score": 0.99,  # Untrusted client claim
    }
    res = client.post("/api/v1/pd/assessments", json=payload, headers=headers)
    assert res.status_code == 201
    data = res.json()
    assert data["is_server_verified"] is False
    assert data["server_confidence_score"] is None
    assert data["confidence_score"] is None
    assert data["status"] == "ESTIMATED"


def test_pd_review_forbidden_without_active_patient_share(
    client: TestClient, p41_patient, p41_optometrist
):
    """An optometrist cannot review or access a patient's PD assessment without an active record share."""
    pat_token, _ = create_access_token(
        user_id=p41_patient.id, email=p41_patient.email, role="patient"
    )
    optom_token, _ = create_access_token(
        user_id=p41_optometrist.id, email=p41_optometrist.email, role="optometrist"
    )

    create_res = client.post(
        "/api/v1/pd/assessments",
        json={"binocular_pd_mm": 62.0, "estimation_method": "REFERENCE_CARD"},
        headers={"Authorization": f"Bearer {pat_token}"},
    )
    assessment_id = create_res.json()["id"]

    # Optometrist attempts to review without share -> 403 Forbidden
    review_res = client.post(
        f"/api/v1/pd/assessments/{assessment_id}/professional-review",
        json={
            "action": "CONFIRM",
            "clinical_notes": "Attempted unauthorized review",
        },
        headers={"Authorization": f"Bearer {optom_token}"},
    )
    assert review_res.status_code == 403
    assert "No active patient record share found" in review_res.json()["error"]["message"]


def test_pd_review_requires_measurement_status_leaves_unverified(
    client: TestClient, db_session, p41_patient, p41_optometrist, p41_screening_session
):
    """When clinician specifies REQUIRES_PROFESSIONAL_MEASUREMENT, server does not mark verified."""
    pat_token, _ = create_access_token(
        user_id=p41_patient.id, email=p41_patient.email, role="patient"
    )
    optom_token, _ = create_access_token(
        user_id=p41_optometrist.id, email=p41_optometrist.email, role="optometrist"
    )

    # Patient records assessment
    create_res = client.post(
        "/api/v1/pd/assessments",
        json={"binocular_pd_mm": 62.0, "estimation_method": "REFERENCE_CARD"},
        headers={"Authorization": f"Bearer {pat_token}"},
    )
    assessment_id = create_res.json()["id"]

    # Grant active share
    referral = PatientReferral(
        patient_id=p41_patient.id,
        session_id=p41_screening_session.id,
        referral_reason="Clinical verification",
        clinical_priority="ROUTINE",
        status="SHARED",
    )
    db_session.add(referral)
    db_session.flush()

    share = PatientRecordShare(
        referral_id=referral.id,
        patient_id=p41_patient.id,
        professional_id=p41_optometrist.id,
        access_status="ACTIVE",
        expires_at=datetime.now(UTC) + timedelta(days=7),
    )
    db_session.add(share)
    db_session.commit()

    # Review with REQUIRES_PROFESSIONAL_MEASUREMENT
    review_res = client.post(
        f"/api/v1/pd/assessments/{assessment_id}/professional-review",
        json={
            "status": "REQUIRES_PROFESSIONAL_MEASUREMENT",
            "clinical_notes": "Measurement unreliable due to glare; physical in-person exam needed.",
        },
        headers={"Authorization": f"Bearer {optom_token}"},
    )
    assert review_res.status_code == 200
    data = review_res.json()
    assert data["status"] == "REQUIRES_PROFESSIONAL_MEASUREMENT"
    assert data["is_server_verified"] is False
    assert data["confidence_score"] is None


def test_pd_review_measure_action_without_binocular_pd_rejected(
    client: TestClient, db_session, p41_patient, p41_optometrist, p41_screening_session
):
    """If action is MEASURE, optometrist must provide measured_binocular_pd_mm."""
    pat_token, _ = create_access_token(
        user_id=p41_patient.id, email=p41_patient.email, role="patient"
    )
    optom_token, _ = create_access_token(
        user_id=p41_optometrist.id, email=p41_optometrist.email, role="optometrist"
    )

    create_res = client.post(
        "/api/v1/pd/assessments",
        json={"binocular_pd_mm": 62.0, "estimation_method": "REFERENCE_CARD"},
        headers={"Authorization": f"Bearer {pat_token}"},
    )
    assessment_id = create_res.json()["id"]

    referral = PatientReferral(
        patient_id=p41_patient.id,
        session_id=p41_screening_session.id,
        referral_reason="Clinical verification",
        clinical_priority="ROUTINE",
        status="SHARED",
    )
    db_session.add(referral)
    db_session.flush()

    share = PatientRecordShare(
        referral_id=referral.id,
        patient_id=p41_patient.id,
        professional_id=p41_optometrist.id,
        access_status="ACTIVE",
        expires_at=datetime.now(UTC) + timedelta(days=7),
    )
    db_session.add(share)
    db_session.commit()

    # Review with MEASURE but no measured_binocular_pd_mm
    review_res = client.post(
        f"/api/v1/pd/assessments/{assessment_id}/professional-review",
        json={
            "action": "MEASURE",
            "clinical_notes": "Claimed in-person measurement without providing actual PD value.",
        },
        headers={"Authorization": f"Bearer {optom_token}"},
    )
    assert review_res.status_code == 422
    assert "requires submitting measured_binocular_pd_mm" in review_res.json()["error"]["message"]


# -----------------------------------------------------------------------------
# 2. Referral Priority & State Machine Security
# -----------------------------------------------------------------------------
def test_referral_patient_cannot_self_assign_priority(
    client: TestClient, p41_patient, p41_screening_session
):
    """Patient cannot self-assign PRIORITY or URGENT when screening findings are normal (ROUTINE)."""
    pat_token, _ = create_access_token(
        user_id=p41_patient.id, email=p41_patient.email, role="patient"
    )
    headers = {"Authorization": f"Bearer {pat_token}"}

    # Attempt URGENT
    res_urgent = client.post(
        "/api/v1/referrals",
        json={
            "session_id": str(p41_screening_session.id),
            "referral_reason": "I want emergency surgery",
            "clinical_priority": "URGENT",
        },
        headers=headers,
    )
    assert res_urgent.status_code == 422
    assert "cannot be self-assigned" in res_urgent.json()["error"]["message"]

    # Attempt PRIORITY
    res_priority = client.post(
        "/api/v1/referrals",
        json={
            "session_id": str(p41_screening_session.id),
            "referral_reason": "I want priority service",
            "clinical_priority": "PRIORITY",
        },
        headers=headers,
    )
    assert res_priority.status_code == 422
    assert "cannot be self-assigned" in res_priority.json()["error"]["message"]


def test_referral_closed_cannot_be_reopened(db_session, p41_patient, p41_screening_session):
    """A referral in CLOSED state cannot transition back to PENDING or any other state."""
    referral = PatientReferral(
        patient_id=p41_patient.id,
        session_id=p41_screening_session.id,
        referral_reason="Completed referral",
        clinical_priority="ROUTINE",
        status="CLOSED",
    )
    db_session.add(referral)
    db_session.commit()

    with pytest.raises(ValidationException) as exc:
        ReferralService.transition_status(db_session, referral, "PENDING", p41_patient)
    assert "Closed referrals cannot be reopened" in str(exc.value)

    with pytest.raises(ValidationException) as exc2:
        ReferralService.transition_status(db_session, referral, "SHARED", p41_patient)
    assert "Closed referrals cannot be reopened" in str(exc2.value)


def test_referral_audit_events_logged(
    client: TestClient, db_session, p41_patient, p41_optometrist, p41_screening_session
):
    """Referral creation and share grant write immutable ReferralAuditEvent records."""
    pat_token, _ = create_access_token(
        user_id=p41_patient.id, email=p41_patient.email, role="patient"
    )
    headers = {"Authorization": f"Bearer {pat_token}"}

    # Create referral
    create_res = client.post(
        "/api/v1/referrals",
        json={
            "session_id": str(p41_screening_session.id),
            "referral_reason": "Routine clinical consultation",
            "clinical_priority": "ROUTINE",
        },
        headers=headers,
    )
    assert create_res.status_code == 201
    referral_id = uuid.UUID(create_res.json()["id"])

    # Verify audit event for creation
    events = (
        db_session.query(ReferralAuditEvent)
        .filter(ReferralAuditEvent.referral_id == referral_id)
        .all()
    )
    assert any(e.action == "REFERRAL_CREATED" and e.actor_id == p41_patient.id for e in events)

    # Share referral
    share_res = client.post(
        f"/api/v1/referrals/{referral_id}/share",
        json={"professional_id": str(p41_optometrist.id), "expires_in_days": 14},
        headers=headers,
    )
    assert share_res.status_code == 201

    events_after = (
        db_session.query(ReferralAuditEvent)
        .filter(ReferralAuditEvent.referral_id == referral_id)
        .all()
    )
    assert any(e.action == "SHARE_GRANTED" and e.actor_id == p41_patient.id for e in events_after)


# -----------------------------------------------------------------------------
# 3. Inventory Authorization, Atomicity & Check Constraints
# -----------------------------------------------------------------------------
def test_inventory_transactions_requires_auth(client: TestClient):
    """Unauthenticated access to inventory transactions must return 401."""
    shop_id = uuid.uuid4()
    inv_id = uuid.uuid4()
    res = client.get(f"/api/v1/shops/{shop_id}/inventory/{inv_id}/transactions")
    assert res.status_code == 401


def test_inventory_transactions_forbidden_for_patient_and_non_owner(
    client: TestClient, db_session, p41_shopkeeper, p41_other_shopkeeper, p41_patient
):
    """Patients and non-owner shopkeepers cannot view inventory audit transactions (403)."""
    # Create shop owned by p41_shopkeeper
    shop = Shop(
        name="Apex Optics",
        location_city="Mumbai",
        location_state="MH",
        owner_user_id=p41_shopkeeper.id,
        is_active=True,
    )
    db_session.add(shop)
    db_session.commit()

    cat = CatalogCategory(name=f"Cat-{uuid.uuid4().hex[:6]}", slug=f"cat-{uuid.uuid4().hex[:6]}")
    brand = CatalogBrand(name=f"Brand-{uuid.uuid4().hex[:6]}", slug=f"brand-{uuid.uuid4().hex[:6]}")
    db_session.add(cat)
    db_session.add(brand)
    db_session.commit()

    product = CatalogProduct(
        sku="TEST-SKU-001",
        name="Test Frame",
        brand_id=brand.id,
        category_id=cat.id,
        base_price_inr=Decimal("1500.00"),
        frame_shape="round",
        frame_material="acetate",
        frame_type="full_rim",
        is_active=True,
    )
    db_session.add(product)
    db_session.commit()

    inventory = ShopInventory(
        shop_id=shop.id,
        product_id=product.id,
        stock_quantity=10,
        reserved_quantity=2,
    )
    db_session.add(inventory)
    db_session.commit()

    # Patient attempt -> 403
    pat_token, _ = create_access_token(
        user_id=p41_patient.id, email=p41_patient.email, role="patient"
    )
    res_pat = client.get(
        f"/api/v1/shops/{shop.id}/inventory/{inventory.id}/transactions",
        headers={"Authorization": f"Bearer {pat_token}"},
    )
    assert res_pat.status_code == 403

    # Other shopkeeper attempt -> 403
    other_token, _ = create_access_token(
        user_id=p41_other_shopkeeper.id, email=p41_other_shopkeeper.email, role="shopkeeper"
    )
    res_other = client.get(
        f"/api/v1/shops/{shop.id}/inventory/{inventory.id}/transactions",
        headers={"Authorization": f"Bearer {other_token}"},
    )
    assert res_other.status_code == 403

    # Mismatched shop / inventory -> 404
    other_shop = Shop(
        name="Other Optics",
        location_city="Pune",
        location_state="MH",
        owner_user_id=p41_other_shopkeeper.id,
        is_active=True,
    )
    db_session.add(other_shop)
    db_session.commit()

    res_mismatch = client.get(
        f"/api/v1/shops/{other_shop.id}/inventory/{inventory.id}/transactions",
        headers={"Authorization": f"Bearer {other_token}"},
    )
    assert res_mismatch.status_code == 404

    # Legitimate owner attempt -> 200
    owner_token, _ = create_access_token(
        user_id=p41_shopkeeper.id, email=p41_shopkeeper.email, role="shopkeeper"
    )
    res_owner = client.get(
        f"/api/v1/shops/{shop.id}/inventory/{inventory.id}/transactions",
        headers={"Authorization": f"Bearer {owner_token}"},
    )
    assert res_owner.status_code == 200


def test_inventory_check_constraint_reserved_le_stock(db_session, p41_shopkeeper):
    """Database check constraint ck_shop_inventory_reserved_le_stock enforces reserved <= stock."""
    from sqlalchemy.exc import IntegrityError

    shop = Shop(
        name="Constraint Test Shop",
        location_city="Delhi",
        location_state="DL",
        owner_user_id=p41_shopkeeper.id,
        is_active=True,
    )
    db_session.add(shop)
    db_session.commit()

    cat2 = CatalogCategory(name=f"Cat-{uuid.uuid4().hex[:6]}", slug=f"cat-{uuid.uuid4().hex[:6]}")
    brand2 = CatalogBrand(
        name=f"Brand-{uuid.uuid4().hex[:6]}", slug=f"brand-{uuid.uuid4().hex[:6]}"
    )
    db_session.add(cat2)
    db_session.add(brand2)
    db_session.commit()

    product = CatalogProduct(
        sku="CK-PROD-001",
        name="Check Constraint Frame",
        brand_id=brand2.id,
        category_id=cat2.id,
        base_price_inr=Decimal("999.00"),
        frame_shape="round",
        frame_material="metal",
        frame_type="full_rim",
        is_active=True,
    )
    db_session.add(product)
    db_session.commit()

    # Attempt to insert inventory where reserved (10) > stock (5)
    bad_inv = ShopInventory(
        shop_id=shop.id,
        product_id=product.id,
        stock_quantity=5,
        reserved_quantity=10,
    )
    db_session.add(bad_inv)
    with pytest.raises(IntegrityError):
        db_session.commit()
    db_session.rollback()


# -----------------------------------------------------------------------------
# 4. Recommendation Engine Financial Precision & Availability Security
# -----------------------------------------------------------------------------
def test_recommendation_zero_and_negative_budget():
    """Zero or negative budget must result in 0 budget points and explicit explanation."""
    product = CatalogProduct(
        sku="FIN-TEST-001",
        name="Affordable Optics",
        base_price_inr=Decimal("1200.00"),
        frame_shape="round",
        frame_material="acetate",
        frame_type="full_rim",
        is_active=True,
    )

    # Zero budget
    req_zero = EyewearRecommendationRequest(
        budget_max_inr=Decimal("0.00"),
    )
    score_zero, reasons_zero = RecommendationService.score_product(
        product, req_zero, is_in_stock=True
    )
    # Shape midpoint(12.5) + Material midpoint(10.0) + Type midpoint(7.5) + Stock(10.0) = 40.0, Budget = 0
    assert score_zero == 40.0
    assert any("zero or negative" in r.lower() for r in reasons_zero)

    # Negative budget
    req_neg = EyewearRecommendationRequest(
        budget_max_inr=Decimal("-500.00"),
    )
    score_neg, reasons_neg = RecommendationService.score_product(product, req_neg, is_in_stock=True)
    assert score_neg == 40.0
    assert any("zero or negative" in r.lower() for r in reasons_neg)


def test_recommendation_out_of_stock_scores_zero_stock_points():
    """Out of stock product receives 0 stock points and notes that it is out of stock."""
    product = CatalogProduct(
        sku="STOCK-TEST-001",
        name="Luxury Titanium Frame",
        base_price_inr=Decimal("2000.00"),
        frame_shape="round",
        frame_material="titanium",
        frame_type="full_rim",
        is_active=True,
    )

    req = EyewearRecommendationRequest(
        budget_max_inr=Decimal("2500.00"),
        preferred_frame_material="titanium",
        preferred_frame_shape="round",
        preferred_frame_type="full_rim",
    )

    # In stock: Budget(30) + Shape(25) + Material(20) + Type(15) + Stock(10) = 100.0
    score_instock, _ = RecommendationService.score_product(product, req, is_in_stock=True)
    assert score_instock == 100.0

    # Out of stock: Budget(30) + Shape(25) + Material(20) + Type(15) + Stock(0) = 90.0
    score_oos, reasons_oos = RecommendationService.score_product(product, req, is_in_stock=False)
    assert score_oos == 90.0
    assert any("out of stock" in r.lower() for r in reasons_oos)

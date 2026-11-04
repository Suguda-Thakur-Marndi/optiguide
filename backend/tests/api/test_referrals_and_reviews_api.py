import uuid

import pytest
from starlette.testclient import TestClient

from app.core.security import create_access_token
from app.models.screening_consent import ScreeningConsent
from app.models.screening_session import ScreeningSession
from app.models.user import User


@pytest.fixture
def patient_user(db_session) -> User:
    user = User(
        email=f"patient_{uuid.uuid4().hex[:8]}@example.com",
        hashed_password="mocked_argon2_hash",
        full_name="Referral Patient",
        role="patient",
        is_active=True,
    )
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)
    return user


@pytest.fixture
def optometrist_user(db_session) -> User:
    user = User(
        email=f"optom_{uuid.uuid4().hex[:8]}@example.com",
        hashed_password="mocked_argon2_hash",
        full_name="Dr. Jane Optometrist",
        role="optometrist",
        is_active=True,
        is_verified=False,
    )
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)
    return user


@pytest.fixture
def admin_user(db_session) -> User:
    user = User(
        email=f"admin_{uuid.uuid4().hex[:8]}@example.com",
        hashed_password="mocked_argon2_hash",
        full_name="System Admin",
        role="admin",
        is_active=True,
        is_verified=True,
    )
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)
    return user


@pytest.fixture
def active_session(db_session, patient_user) -> ScreeningSession:
    consent = ScreeningConsent(
        user_id=patient_user.id,
        consent_version="1.0.0",
        consent_text_hash="hash_value",
        is_active=True,
    )
    db_session.add(consent)
    db_session.commit()
    db_session.refresh(consent)

    sess = ScreeningSession(
        user_id=patient_user.id,
        consent_id=consent.id,
        status="completed",
    )
    db_session.add(sess)
    db_session.commit()
    db_session.refresh(sess)
    return sess


def test_professional_verification_workflow(
    client: TestClient, db_session, optometrist_user, admin_user
):
    """Verifies professional credential submission and administrative verification."""
    optom_token, _ = create_access_token(
        user_id=optometrist_user.id, email=optometrist_user.email, role="optometrist"
    )
    admin_token, _ = create_access_token(
        user_id=admin_user.id, email=admin_user.email, role="admin"
    )

    optom_headers = {"Authorization": f"Bearer {optom_token}"}
    admin_headers = {"Authorization": f"Bearer {admin_token}"}

    # 1. Optometrist submits verification application
    apply_payload = {
        "license_number": "OPT-IN-987654",
        "issuing_authority": "Optometry Council of India",
        "registration_year": 2018,
        "qualification_title": "Bachelor of Clinical Optometry (B.Optom)",
    }
    apply_res = client.post(
        "/api/v1/professionals/apply", json=apply_payload, headers=optom_headers
    )
    assert apply_res.status_code == 201
    prof_data = apply_res.json()
    assert prof_data["license_number"] == "OPT-IN-987654"
    assert prof_data["verification_status"] == "PENDING"
    profile_id = prof_data["id"]

    # 2. Admin inspects pending list
    pending_res = client.get("/api/v1/professionals/admin/pending", headers=admin_headers)
    assert pending_res.status_code == 200
    pending_items = pending_res.json()["items"]
    assert any(p["id"] == profile_id for p in pending_items)

    # 3. Admin approves credentials
    verify_res = client.post(
        f"/api/v1/professionals/admin/{profile_id}/verify",
        json={"action": "VERIFY"},
        headers=admin_headers,
    )
    assert verify_res.status_code == 200
    assert verify_res.json()["verification_status"] == "VERIFIED"

    # Refresh user in DB to check is_verified flag
    db_session.refresh(optometrist_user)
    assert optometrist_user.is_verified is True


def test_patient_referral_creation_and_sharing(
    client: TestClient, db_session, patient_user, optometrist_user, admin_user, active_session
):
    """Verifies full patient referral lifecycle: creation, sharing, professional review."""
    # First verify the optometrist
    optometrist_user.is_verified = True
    db_session.commit()

    from app.models.referral import ProfessionalProfile

    prof_profile = ProfessionalProfile(
        user_id=optometrist_user.id,
        license_number="OPT-12345",
        issuing_authority="State Council",
        registration_year=2020,
        qualification_title="B.Optom",
        verification_status="VERIFIED",
    )
    db_session.add(prof_profile)
    db_session.commit()

    patient_token, _ = create_access_token(
        user_id=patient_user.id, email=patient_user.email, role="patient"
    )
    optom_token, _ = create_access_token(
        user_id=optometrist_user.id, email=optometrist_user.email, role="optometrist"
    )

    patient_headers = {"Authorization": f"Bearer {patient_token}"}
    optom_headers = {"Authorization": f"Bearer {optom_token}"}

    # Record acuity assessment with logMAR 0.48 so PRIORITY priority is derived legitimately
    from app.models.screening_assessment import VisualAcuityAssessment

    acuity = VisualAcuityAssessment(
        session_id=active_session.id,
        user_id=patient_user.id,
        test_eye="right",
        snellen_fraction="6/18",
        logmar=0.48,
        decimal_acuity=0.33,
        tested_distance_meters=2.0,
        unassisted_or_corrected="unassisted",
    )
    db_session.add(acuity)
    db_session.commit()

    # 1. Patient creates referral from screening session
    ref_payload = {
        "session_id": str(active_session.id),
        "referral_reason": "Marked interocular acuity difference (0.48 logMAR) detected.",
        "clinical_priority": "PRIORITY",
        "notes": "Patient reported slight headaches in temple.",
    }
    create_ref_res = client.post("/api/v1/referrals", json=ref_payload, headers=patient_headers)
    assert create_ref_res.status_code == 201
    ref_data = create_ref_res.json()
    assert ref_data["status"] == "PENDING"
    assert ref_data["clinical_priority"] == "PRIORITY"
    referral_id = ref_data["id"]

    # 2. Patient shares referral with verified optometrist
    share_payload = {
        "professional_id": str(optometrist_user.id),
        "expires_in_days": 14,
    }
    share_res = client.post(
        f"/api/v1/referrals/{referral_id}/share", json=share_payload, headers=patient_headers
    )
    assert share_res.status_code == 201
    share_data = share_res.json()
    assert share_data["access_status"] == "ACTIVE"
    share_id = share_data["id"]

    # 3. Optometrist lists shared records
    shared_list_res = client.get("/api/v1/professionals/shared-records", headers=optom_headers)
    assert shared_list_res.status_code == 200
    shared_items = shared_list_res.json()["items"]
    assert any(s["referral_id"] == referral_id for s in shared_items)

    # 4. Optometrist retrieves detailed screening breakdown
    details_res = client.get(
        f"/api/v1/professionals/shared-records/{referral_id}", headers=optom_headers
    )
    assert details_res.status_code == 200
    details_data = details_res.json()
    assert details_data["referral"]["id"] == referral_id
    assert (
        "OptiGuide screening observations are strictly preliminary"
        in details_data["clinical_disclaimer"]
    )

    # 5. Optometrist records clinical review
    review_payload = {
        "professional_observations": "Confirmed asymmetry consistent with preliminary amblyopia risk. Comprehensive cycloplegic refraction required.",
        "in_person_exam_recommended": True,
        "recommended_exam_timeframe": "Within 1 to 2 weeks",
    }
    review_res = client.post(
        f"/api/v1/professionals/reviews/{referral_id}", json=review_payload, headers=optom_headers
    )
    assert review_res.status_code == 201
    review_data = review_res.json()
    assert review_data["review_status"] == "EXAMINATION_RECOMMENDED"
    assert review_data["in_person_exam_recommended"] is True

    # 6. Patient revokes access
    revoke_res = client.delete(
        f"/api/v1/referrals/{referral_id}/share/{share_id}", headers=patient_headers
    )
    assert revoke_res.status_code == 200
    assert revoke_res.json()["access_status"] == "REVOKED"


def test_referral_idor_and_unverified_protection(
    client: TestClient, db_session, patient_user, optometrist_user, active_session
):
    """Verifies that other patients cannot access referrals and unverified clinicians are rejected."""
    patient_token, _ = create_access_token(
        user_id=patient_user.id, email=patient_user.email, role="patient"
    )
    patient_headers = {"Authorization": f"Bearer {patient_token}"}

    # Create referral
    ref_res = client.post(
        "/api/v1/referrals",
        json={"session_id": str(active_session.id), "referral_reason": "Screening blur"},
        headers=patient_headers,
    )
    referral_id = ref_res.json()["id"]

    # Attempt to share with unverified optometrist (optometrist_user.is_verified is False)
    bad_share = client.post(
        f"/api/v1/referrals/{referral_id}/share",
        json={"professional_id": str(optometrist_user.id)},
        headers=patient_headers,
    )
    assert bad_share.status_code == 422 or bad_share.status_code == 400
    assert "verified" in bad_share.json()["error"]["message"].lower()

    # Another patient attempting to read this referral -> 404
    other_patient = User(
        email="stranger_patient@example.com",
        hashed_password="mock",
        full_name="Stranger Patient",
        role="patient",
        is_active=True,
    )
    db_session.add(other_patient)
    db_session.commit()

    other_token, _ = create_access_token(
        user_id=other_patient.id, email=other_patient.email, role="patient"
    )
    other_headers = {"Authorization": f"Bearer {other_token}"}

    idor_res = client.get(f"/api/v1/referrals/{referral_id}", headers=other_headers)
    assert idor_res.status_code == 404

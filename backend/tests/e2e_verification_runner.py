import json
import random
import urllib.error
import urllib.request

BASE_URL = "http://localhost:8000"


def make_request(path, method="GET", data=None, headers=None):
    url = f"{BASE_URL}{path}"
    req_headers = {"Content-Type": "application/json", "Accept": "application/json"}
    if headers:
        req_headers.update(headers)

    body = json.dumps(data).encode("utf-8") if data is not None else None
    req = urllib.request.Request(url, data=body, headers=req_headers, method=method)
    try:
        with urllib.request.urlopen(req) as resp:
            content = resp.read().decode("utf-8")
            return resp.status, json.loads(content) if content else {}
    except urllib.error.HTTPError as err:
        err_content = err.read().decode("utf-8")
        try:
            return err.status, json.loads(err_content)
        except Exception:  # noqa: BLE001
            return err.status, {"raw": err_content}


def run_all_journeys():
    print("=" * 70)
    print("OPTIGUIDE MANUAL END-TO-END VERIFICATION RUNNER")
    print("=" * 70)

    rand_id = random.randint(10000, 99999)
    email = f"e2e_user_{rand_id}@example.com"
    password = "SecurePassword123!"
    full_name = "E2E Verification Subject"

    # Journey 1: New user registration
    print("\n--- JOURNEY 1: New User Registration ---")
    st, data = make_request(
        "/api/v1/auth/register",
        method="POST",
        data={"email": email, "password": password, "full_name": full_name},
    )
    print(f"Status: {st}")
    assert st == 201, f"Expected 201, got {st}: {data}"
    user_id = data["user"]["id"]
    access_token = data["access_token"]
    refresh_token = data["refresh_token"]
    print(f"Created User: {data['user']['email']} (ID: {user_id})")
    print("JWT Access Token and Refresh Token received.")

    # Journey 2: Login with registered credentials
    print("\n--- JOURNEY 2: Login with Credentials ---")
    st, data = make_request(
        "/api/v1/auth/login", method="POST", data={"email": email, "password": password}
    )
    print(f"Status: {st}")
    assert st == 200, f"Expected 200, got {st}"
    access_token = data["access_token"]
    refresh_token = data["refresh_token"]
    print(f"Authenticated: {data['user']['email']}, Role: {data['user']['role']}")

    # Journey 3 & 4: Open protected dashboard & load user profile
    print("\n--- JOURNEY 3 & 4: Protected Dashboard & Profile Load ---")
    auth_header = {"Authorization": f"Bearer {access_token}"}
    st, data = make_request("/api/v1/users/me", method="GET", headers=auth_header)
    print(f"Status: {st}")
    assert st == 200
    print(f"Loaded Profile: {data['full_name']}, Email: {data['email']}, Role: {data['role']}")

    # Journey 5: Update profile
    print("\n--- JOURNEY 5: Update User Profile ---")
    st, data = make_request(
        "/api/v1/users/me",
        method="PATCH",
        data={"full_name": "Updated Subject Name", "phone_number": "+15551234567"},
        headers=auth_header,
    )
    print(f"Status: {st}")
    assert st == 200
    print(f"Updated Profile: Name={data['full_name']}, Phone={data['phone_number']}")

    # Journey 6: Refresh expired access token
    print("\n--- JOURNEY 6: Token Refresh (Rotation) ---")
    st, data = make_request(
        "/api/v1/auth/refresh", method="POST", data={"refresh_token": refresh_token}
    )
    print(f"Status: {st}")
    assert st == 200
    access_token = data["access_token"]
    refresh_token = data["refresh_token"]
    auth_header = {"Authorization": f"Bearer {access_token}"}
    print("Token rotation succeeded. New access token and replacement refresh token issued.")

    # Journey 7: Logout active session
    print("\n--- JOURNEY 7: Logout Active Session ---")
    st, data = make_request(
        "/api/v1/auth/logout", method="POST", data={"refresh_token": refresh_token}
    )
    print(f"Status: {st}")
    assert st == 200
    print(f"Logout response: {data.get('message')}")

    # Journey 8: Attempt to access protected route after logout
    # Note: access token expiration is 15 min, but testing refresh token reuse should be rejected:
    print("\n--- JOURNEY 8: Verify Revoked Refresh Token is Rejected ---")
    st, data = make_request(
        "/api/v1/auth/refresh", method="POST", data={"refresh_token": refresh_token}
    )
    print(f"Status: {st} (Expected 401)")
    assert st == 401, f"Expected 401 on revoked refresh token, got {st}"
    print("Revoked refresh token correctly rejected with 401.")

    # Journey 9: Log in again
    print("\n--- JOURNEY 9: Re-authenticate User ---")
    st, data = make_request(
        "/api/v1/auth/login", method="POST", data={"email": email, "password": password}
    )
    print(f"Status: {st}")
    assert st == 200
    access_token = data["access_token"]
    refresh_token = data["refresh_token"]
    auth_header = {"Authorization": f"Bearer {access_token}"}
    print("Re-login successful.")

    # Journey 10: View user sessions
    print("\n--- JOURNEY 10: View User Sessions ---")
    st, data = make_request("/api/v1/users/me/sessions", method="GET", headers=auth_header)
    print(f"Status: {st}")
    assert st == 200
    print(f"User Sessions Count: {len(data)}")
    for idx, s in enumerate(data, 1):
        print(f"  Session {idx}: ID={s['id'][:8]}..., Revoked={s['is_revoked']}")

    # Journey 11: Accept screening consent
    print("\n--- JOURNEY 11: Accept Screening Consent (v1.0.0) ---")
    st, data = make_request(
        "/api/v1/screening/consent/accept",
        method="POST",
        data={"version": "1.0.0"},
        headers=auth_header,
    )
    print(f"Status: {st}")
    assert st == 201 or st == 200
    print(
        f"Consent Accepted: v{data['consent_version']}, Hash={data['consent_text_hash'][:16]}..."
    )

    # Journey 12: Create a screening session
    print("\n--- JOURNEY 12: Initialize Screening Session ---")
    st, data = make_request(
        "/api/v1/screening/sessions", method="POST", data={}, headers=auth_header
    )
    print(f"Status: {st}")
    assert st == 201, f"Expected 201, got {st}: {data}"
    session_id = data["id"]
    print(f"Session Created: ID={session_id}, Status={data['status']}")

    # Journey 13: Record Visual Acuity (OD & OS) with Calibration
    print("\n--- JOURNEY 13: Record Distance Visual Acuity (OD & OS) ---")
    calibration_data = {
        "screen_width_px": 1920,
        "screen_height_px": 1080,
        "display_dpi": 96.0,
        "physical_optotype_mm": 1.45,
        "viewing_distance_cm": 100.0,
        "is_verified": True,
    }
    # OD (Right eye): 20/20, logMAR 0.0
    st_od, data_od = make_request(
        f"/api/v1/screening/sessions/{session_id}/acuity",
        method="POST",
        data={
            "test_eye": "right",
            "snellen_fraction": "20/20",
            "logmar": 0.0,
            "decimal_acuity": 1.0,
            "tested_distance_meters": 1.0,
            "is_calibrated": True,
            "calibration": calibration_data,
            "observations": "Clear tumbling E identification at 1 meter.",
        },
        headers=auth_header,
    )
    assert st_od == 201, f"Expected 201, got {st_od}: {data_od}"
    print(f"OD Acuity Recorded: {data_od['snellen_fraction']} (logMAR {data_od['logmar']})")

    # OS (Left eye): 20/60, logMAR 0.48 -> triggers referral threshold
    st_os, data_os = make_request(
        f"/api/v1/screening/sessions/{session_id}/acuity",
        method="POST",
        data={
            "test_eye": "left",
            "snellen_fraction": "20/60",
            "logmar": 0.48,
            "decimal_acuity": 0.33,
            "tested_distance_meters": 1.0,
            "is_calibrated": True,
            "calibration": calibration_data,
            "observations": "Difficulty reading smaller optotypes.",
        },
        headers=auth_header,
    )
    assert st_os == 201, f"Expected 201, got {st_os}: {data_os}"
    print(f"OS Acuity Recorded: {data_os['snellen_fraction']} (logMAR {data_os['logmar']})")

    # Journey 14: Record Astigmatism Clock Dial Screening
    print("\n--- JOURNEY 14: Record Astigmatism Radial Clock Dial ---")
    st_astig, data_astig = make_request(
        f"/api/v1/screening/sessions/{session_id}/astigmatism",
        method="POST",
        data={
            "chart_type": "clock_dial",
            "has_uniform_clarity": False,
            "indicated_axes": [12, 6],
            "sharpest_meridian_hour": 12,
            "screening_observation": "Vertical lines appeared notably darker and clearer.",
        },
        headers=auth_header,
    )
    assert st_astig == 201, f"Expected 201, got {st_astig}: {data_astig}"
    print(
        f"Astigmatism Recorded: Uniform={data_astig['has_uniform_clarity']}, SharpestHour={data_astig['sharpest_meridian_hour']}"
    )

    # Journey 15: Record Color Vision Pseudoisochromatic Plates
    print("\n--- JOURNEY 15: Record Pseudoisochromatic Color Plates ---")
    st_cv, data_cv = make_request(
        f"/api/v1/screening/sessions/{session_id}/color-vision",
        method="POST",
        data={
            "test_protocol": "pseudoisochromatic_plates",
            "total_plates_presented": 4,
            "correct_plate_count": 3,
            "deficiency_indicated": True,
            "deficiency_type": "protan_deutan_red_green",
            "responses_detail": [
                {"plate": 1, "input": "12", "correct": True},
                {"plate": 2, "input": "8", "correct": True},
                {"plate": 3, "input": "70", "correct": False},
                {"plate": 4, "input": "5", "correct": True},
            ],
        },
        headers=auth_header,
    )
    assert st_cv == 201, f"Expected 201, got {st_cv}: {data_cv}"
    print(
        f"Color Vision Recorded: Deficient={data_cv['deficiency_indicated']}, Type={data_cv['deficiency_type']}"
    )

    # Journey 16: Clinical Session Summary & Triage Verification
    print("\n--- JOURNEY 16: Retrieve Clinical Summary & Triage Referral ---")
    st_sum, data_sum = make_request(
        f"/api/v1/screening/sessions/{session_id}/summary",
        method="GET",
        headers=auth_header,
    )
    assert st_sum == 200, f"Expected 200, got {st_sum}: {data_sum}"
    print(f"Referral Recommended: {data_sum['referral_recommended']}")
    print(f"Referral Reasons: {data_sum['referral_reasons']}")
    assert data_sum["referral_recommended"] is True
    assert len(data_sum["referral_reasons"]) >= 2
    assert "OptiGuide is a preliminary vision screening aid" in data_sum["clinical_disclaimer"]

    # Journey 17: Complete the screening session
    print("\n--- JOURNEY 17: Complete Screening Session ---")
    st, data = make_request(
        f"/api/v1/screening/sessions/{session_id}/complete", method="POST", headers=auth_header
    )
    print(f"Status: {st}")
    assert st == 200
    print(
        f"Session Completed: ID={data['id']}, Status={data['status']}, CompletedAt={data['completed_at']}"
    )

    # Journey 18: Verify mutations are rejected on completed sessions
    print("\n--- JOURNEY 18: Status Protection on Completed Session ---")
    st_locked, _data_locked = make_request(
        f"/api/v1/screening/sessions/{session_id}/acuity",
        method="POST",
        data={"test_eye": "right", "snellen_fraction": "20/20", "logmar": 0.0, "decimal_acuity": 1.0},
        headers=auth_header,
    )
    assert st_locked == 400
    print("Mutations properly rejected on completed session (HTTP 400).")

    print("\n" + "=" * 70)
    print("ALL 18 END-TO-END VERIFICATION JOURNEYS PASSED SUCCESSFULLY!")
    print("=" * 70)


if __name__ == "__main__":
    run_all_journeys()

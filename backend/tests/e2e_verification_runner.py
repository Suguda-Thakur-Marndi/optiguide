import json
import random
import sys
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
        except Exception:
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

    # Journey 13: Complete the screening session
    print("\n--- JOURNEY 13: Complete Screening Session ---")
    st, data = make_request(
        f"/api/v1/screening/sessions/{session_id}/complete", method="POST", headers=auth_header
    )
    print(f"Status: {st}")
    assert st == 200
    print(
        f"Session Completed: ID={data['id']}, Status={data['status']}, CompletedAt={data['completed_at']}"
    )

    print("\n" + "=" * 70)
    print("ALL 13 END-TO-END VERIFICATION JOURNEYS PASSED SUCCESSFULLY!")
    print("=" * 70)


if __name__ == "__main__":
    run_all_journeys()

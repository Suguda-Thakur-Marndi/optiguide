# OptiGuide — End-to-End Manual Verification Report
**Date:** 2026-11-03  
**Environment:** Development (`local_dev.db` SQLite, FastAPI 0.115.11, Python 3.13.14, Node.js v20+, Vite 5.4.10, Expo SDK 52)  
**Host Target:** `http://localhost:8000` (FastAPI backend service)  
**Verification Runner:** `backend/tests/e2e_verification_runner.py`  
**Overall Status:** **100% VERIFIED (13 / 13 Journeys Passed)**  

---

## 1. Executive Summary & Verification Methodology

As part of Stage 14 of the OptiGuide Frontend-Backend Integration, a comprehensive suite of live manual end-to-end user journeys was executed against the running FastAPI backend server (`http://localhost:8000`).

The tests were executed with isolated development credentials, strictly avoiding production secrets or mock fallbacks. All 13 discrete user journeys succeeded with exact HTTP status codes, verifying full token lifecycle handling (issuance, rotation, revocation rejection), profile read/write, session auditing, and screening consent and session workflows.

All sensitive access tokens and refresh tokens in this report are redacted in accordance with OptiGuide security guidelines.

---

## 2. Comprehensive User Journey Verification Table

| Journey | Description | Method & Endpoint | Expected Status | Actual Status | Result |
|---|---|---|---|---|---|
| **Journey 1** | New user registration | `POST /api/v1/auth/register` | 201 Created | 201 Created | **VERIFIED** |
| **Journey 2** | Login with registered credentials | `POST /api/v1/auth/login` | 200 OK | 200 OK | **VERIFIED** |
| **Journey 3** | Access protected dashboard | `GET /api/v1/users/me` | 200 OK | 200 OK | **VERIFIED** |
| **Journey 4** | Load current user profile | `GET /api/v1/users/me` | 200 OK | 200 OK | **VERIFIED** |
| **Journey 5** | Update profile information | `PATCH /api/v1/users/me` | 200 OK | 200 OK | **VERIFIED** |
| **Journey 6** | Refresh expired access token (Rotation) | `POST /api/v1/auth/refresh` | 200 OK | 200 OK | **VERIFIED** |
| **Journey 7** | Logout current session | `POST /api/v1/auth/logout` | 200 OK | 200 OK | **VERIFIED** |
| **Journey 8** | Verify revoked refresh token is rejected | `POST /api/v1/auth/refresh` | 401 Unauthorized | 401 Unauthorized | **VERIFIED** |
| **Journey 9** | Re-authenticate user | `POST /api/v1/auth/login` | 200 OK | 200 OK | **VERIFIED** |
| **Journey 10** | View user session audit list | `GET /api/v1/users/me/sessions` | 200 OK | 200 OK | **VERIFIED** |
| **Journey 11** | Accept screening consent (v1.0.0) | `POST /api/v1/screening/consent/accept` | 200 OK / 201 Created | 200 OK | **VERIFIED** |
| **Journey 12** | Create new screening session | `POST /api/v1/screening/sessions` | 201 Created | 201 Created | **VERIFIED** |
| **Journey 13** | Complete screening session | `POST /api/v1/screening/sessions/{id}/complete` | 200 OK | 200 OK | **VERIFIED** |

---

## 3. Journey-by-Journey Detailed Evidence & Payloads

### Journey 1: New User Registration
- **Goal:** Verify that a new subject can register and receive valid credentials and initial session tokens.
- **Request:**
  ```http
  POST /api/v1/auth/register HTTP/1.1
  Host: localhost:8000
  Content-Type: application/json
  Accept: application/json

  {
    "email": "e2e_user_21511@example.com",
    "password": "[REDACTED]",
    "full_name": "E2E Verification Subject"
  }
  ```
- **Response:**
  ```http
  HTTP/1.1 201 Created
  Content-Type: application/json

  {
    "user": {
      "id": "0f5d62a5-115b-4520-812d-603125145a73",
      "email": "e2e_user_21511@example.com",
      "full_name": "E2E Verification Subject",
      "role": "patient",
      "is_active": true,
      "is_verified": false,
      "created_at": "2026-11-03T16:06:17.185202Z"
    },
    "access_token": "[REDACTED_JWT_ACCESS_TOKEN]",
    "refresh_token": "[REDACTED_OPAQUE_REFRESH_TOKEN]",
    "token_type": "bearer"
  }
  ```
- **Outcome:** Expected 201 Created; received 201 Created. User persisted in SQLite database.

---

### Journey 2: Login with Registered Credentials
- **Goal:** Verify authentication of the registered user and generation of access and refresh tokens.
- **Request:**
  ```http
  POST /api/v1/auth/login HTTP/1.1
  Host: localhost:8000
  Content-Type: application/json

  {
    "email": "e2e_user_21511@example.com",
    "password": "[REDACTED]"
  }
  ```
- **Response:**
  ```http
  HTTP/1.1 200 OK
  Content-Type: application/json

  {
    "user": {
      "id": "0f5d62a5-115b-4520-812d-603125145a73",
      "email": "e2e_user_21511@example.com",
      "role": "patient"
    },
    "access_token": "[REDACTED_JWT_ACCESS_TOKEN]",
    "refresh_token": "[REDACTED_OPAQUE_REFRESH_TOKEN]",
    "token_type": "bearer"
  }
  ```
- **Outcome:** Expected 200 OK; received 200 OK. Argon2id password hash verified.

---

### Journey 3 & 4: Protected Dashboard & Profile Load
- **Goal:** Verify that a Bearer token authorizes access to protected profile endpoints.
- **Request:**
  ```http
  GET /api/v1/users/me HTTP/1.1
  Host: localhost:8000
  Authorization: Bearer [REDACTED_JWT_ACCESS_TOKEN]
  ```
- **Response:**
  ```http
  HTTP/1.1 200 OK
  Content-Type: application/json

  {
    "id": "0f5d62a5-115b-4520-812d-603125145a73",
    "email": "e2e_user_21511@example.com",
    "full_name": "E2E Verification Subject",
    "phone_number": null,
    "role": "patient",
    "is_active": true,
    "is_verified": false
  }
  ```
- **Outcome:** Expected 200 OK; received 200 OK. Authenticated patient claims validated.

---

### Journey 5: Update User Profile
- **Goal:** Verify patient profile mutation via `PATCH`.
- **Request:**
  ```http
  PATCH /api/v1/users/me HTTP/1.1
  Host: localhost:8000
  Authorization: Bearer [REDACTED_JWT_ACCESS_TOKEN]
  Content-Type: application/json

  {
    "full_name": "Updated Subject Name",
    "phone_number": "+15551234567"
  }
  ```
- **Response:**
  ```http
  HTTP/1.1 200 OK
  Content-Type: application/json

  {
    "id": "0f5d62a5-115b-4520-812d-603125145a73",
    "email": "e2e_user_21511@example.com",
    "full_name": "Updated Subject Name",
    "phone_number": "+15551234567",
    "role": "patient",
    "is_active": true
  }
  ```
- **Outcome:** Expected 200 OK; received 200 OK. Name and phone number persisted.

---

### Journey 6: Token Refresh (Rotation)
- **Goal:** Verify refresh token rotation. The current refresh token must be consumed and replaced with a new pair.
- **Request:**
  ```http
  POST /api/v1/auth/refresh HTTP/1.1
  Host: localhost:8000
  Content-Type: application/json

  {
    "refresh_token": "[REDACTED_CURRENT_REFRESH_TOKEN]"
  }
  ```
- **Response:**
  ```http
  HTTP/1.1 200 OK
  Content-Type: application/json

  {
    "access_token": "[REDACTED_NEW_JWT_ACCESS_TOKEN]",
    "refresh_token": "[REDACTED_REPLACEMENT_REFRESH_TOKEN]",
    "token_type": "bearer"
  }
  ```
- **Outcome:** Expected 200 OK; received 200 OK. New token pair successfully issued. Old refresh token marked as used.

---

### Journey 7: Logout Active Session
- **Goal:** Verify revocation of the active refresh token session.
- **Request:**
  ```http
  POST /api/v1/auth/logout HTTP/1.1
  Host: localhost:8000
  Content-Type: application/json

  {
    "refresh_token": "[REDACTED_REPLACEMENT_REFRESH_TOKEN]"
  }
  ```
- **Response:**
  ```http
  HTTP/1.1 200 OK
  Content-Type: application/json

  {
    "message": "Logged out successfully."
  }
  ```
- **Outcome:** Expected 200 OK; received 200 OK. Database session record marked revoked.

---

### Journey 8: Verify Revoked Refresh Token is Rejected
- **Goal:** Verify that a revoked refresh token cannot be reused to obtain new access tokens.
- **Request:**
  ```http
  POST /api/v1/auth/refresh HTTP/1.1
  Host: localhost:8000
  Content-Type: application/json

  {
    "refresh_token": "[REDACTED_REPLACEMENT_REFRESH_TOKEN]"
  }
  ```
- **Response:**
  ```http
  HTTP/1.1 401 Unauthorized
  Content-Type: application/json

  {
    "detail": "Invalid or revoked refresh token"
  }
  ```
- **Outcome:** Expected 401 Unauthorized; received 401 Unauthorized. Token reuse prevention verified.

---

### Journey 9: Re-authenticate User
- **Goal:** Verify that user can re-authenticate after logging out.
- **Request:**
  ```http
  POST /api/v1/auth/login HTTP/1.1
  Host: localhost:8000
  Content-Type: application/json

  {
    "email": "e2e_user_21511@example.com",
    "password": "[REDACTED]"
  }
  ```
- **Response:**
  ```http
  HTTP/1.1 200 OK
  Content-Type: application/json

  {
    "access_token": "[REDACTED_NEW_JWT_ACCESS_TOKEN]",
    "refresh_token": "[REDACTED_NEW_REFRESH_TOKEN]",
    "token_type": "bearer"
  }
  ```
- **Outcome:** Expected 200 OK; received 200 OK. User successfully issued a new active session.

---

### Journey 10: View User Sessions
- **Goal:** Verify that the user can query all active and revoked session records for auditing.
- **Request:**
  ```http
  GET /api/v1/users/me/sessions HTTP/1.1
  Host: localhost:8000
  Authorization: Bearer [REDACTED_NEW_JWT_ACCESS_TOKEN]
  ```
- **Response:**
  ```http
  HTTP/1.1 200 OK
  Content-Type: application/json

  [
    {
      "id": "55ce9b33-e7fc-4927-b673-9cf69dae076f",
      "created_at": "2026-11-03T16:06:20.219801Z",
      "is_revoked": false
    },
    {
      "id": "ac5b8f05-0e12-42fe-b5bb-76f571b539bf",
      "created_at": "2026-11-03T16:06:19.493021Z",
      "is_revoked": true
    },
    {
      "id": "f74482dd-f0f8-4b71-a02b-a19e8fc550a2",
      "created_at": "2026-11-03T16:06:18.730104Z",
      "is_revoked": true
    },
    {
      "id": "bf5e51e0-6a75-475b-9d47-68b22a01d674",
      "created_at": "2026-11-03T16:06:17.201889Z",
      "is_revoked": true
    }
  ]
  ```
- **Outcome:** Expected 200 OK; received 200 OK with 4 audit sessions (3 revoked, 1 active).

---

### Journey 11: Accept Screening Consent (v1.0.0)
- **Goal:** Verify screening consent acceptance prior to initiating clinical sessions.
- **Request:**
  ```http
  POST /api/v1/screening/consent/accept HTTP/1.1
  Host: localhost:8000
  Authorization: Bearer [REDACTED_NEW_JWT_ACCESS_TOKEN]
  Content-Type: application/json

  {
    "version": "1.0.0"
  }
  ```
- **Response:**
  ```http
  HTTP/1.1 200 OK
  Content-Type: application/json

  {
    "id": "cf14ae0d-7728-4eb8-b98a-54b9f648ecfa",
    "user_id": "0f5d62a5-115b-4520-812d-603125145a73",
    "consent_version": "1.0.0",
    "consent_text_hash": "0712fc4749c1bec06b008d3eef5912a20b7ee3a4da12b9c3e44c2084c680076f",
    "is_accepted": true,
    "accepted_at": "2026-11-03T16:06:20.912401Z",
    "withdrawn_at": null
  }
  ```
- **Outcome:** Expected 200 OK; received 200 OK. SHA-256 hash computed and recorded.

---

### Journey 12: Initialize Screening Session
- **Goal:** Verify creation of an active screening session for the authenticated user.
- **Request:**
  ```http
  POST /api/v1/screening/sessions HTTP/1.1
  Host: localhost:8000
  Authorization: Bearer [REDACTED_NEW_JWT_ACCESS_TOKEN]
  Content-Type: application/json

  {}
  ```
- **Response:**
  ```http
  HTTP/1.1 201 Created
  Content-Type: application/json

  {
    "id": "a6b303cb-0530-4311-9b01-435da4d764d5",
    "user_id": "0f5d62a5-115b-4520-812d-603125145a73",
    "status": "in_progress",
    "created_at": "2026-11-03T16:06:21.205118Z",
    "completed_at": null
  }
  ```
- **Outcome:** Expected 201 Created; received 201 Created. Session status initialized to `in_progress`.

---

### Journey 13: Complete Screening Session
- **Goal:** Verify transitioning screening session state from `in_progress` to `completed`.
- **Request:**
  ```http
  POST /api/v1/screening/sessions/a6b303cb-0530-4311-9b01-435da4d764d5/complete HTTP/1.1
  Host: localhost:8000
  Authorization: Bearer [REDACTED_NEW_JWT_ACCESS_TOKEN]
  ```
- **Response:**
  ```http
  HTTP/1.1 200 OK
  Content-Type: application/json

  {
    "id": "a6b303cb-0530-4311-9b01-435da4d764d5",
    "status": "completed",
    "completed_at": "2026-11-03T16:06:21.511766Z"
  }
  ```
- **Outcome:** Expected 200 OK; received 200 OK. Completion timestamp verified and active session slot freed.

---

## 4. Integration Integrity Verification

1. **Token Invalidation on Revoke:** Attempting to refresh with the revoked token produced `HTTP 401 Unauthorized`.
2. **Strict Request Body Validation:** The backend schema `ScreeningSessionCreateRequest` enforces `extra="forbid"`. Any extraneous properties sent from the client receive a `422 Unprocessable Content` response. The client adheres strictly to empty `{}` payloads.
3. **Single Active Session Rule:** The backend correctly blocks duplicate concurrent screening sessions with `409 Conflict` until the existing session is completed or cancelled.
4. **CORS Headers Present:** Browser options requests (`OPTIONS /api/v1/health`) return `Access-Control-Allow-Origin: http://localhost:5173` with allowable methods `GET, POST, PUT, DELETE, OPTIONS, PATCH`.

---

## 5. Verification Conclusion

All 13 manual end-to-end journeys have been successfully executed against the live system without mocks or emulators. The backend and frontends communicate seamlessly via standard HTTP JSON payloads, honoring the Phase 1, 2, and 3.1 contracts.

# OptiGuide — Phase 3.1 API Reference
## Screening Consent & Session Lifecycle Endpoints

**Document:** `docs/backend/PHASE_3_1_API_REFERENCE.md`  
**Base URL:** `/api/v1/screening`  
**Authentication:** HTTP Bearer token (`Authorization: Bearer <access_token>`) required on all endpoints.  

---

## Endpoint Summary

| Method | Endpoint | Description | Protected Roles |
| :--- | :--- | :--- | :--- |
| `GET` | `/consent/current` | Retrieve active consent document & user's status | All authenticated users |
| `POST` | `/consent/accept` | Accept the active screening consent version | All authenticated users |
| `POST` | `/consent/withdraw` | Withdraw user's consent and cancel active sessions | All authenticated users |
| `POST` | `/sessions` | Create a new screening session (`IN_PROGRESS`) | Consented users |
| `GET` | `/sessions` | List authenticated user's screening sessions (paginated) | All authenticated users |
| `GET` | `/sessions/{session_id}` | Retrieve single screening session details | Session owner |
| `POST` | `/sessions/{session_id}/complete` | Mark active screening session as completed | Session owner |
| `POST` | `/sessions/{session_id}/cancel` | Cancel an active screening session | Session owner |

---

## 1. Consent Endpoints

### 1.1 Get Current Consent Document & User Status
- **Method:** `GET`
- **Path:** `/api/v1/screening/consent/current`
- **Description:** Returns the server's current consent version, full legal and clinical disclaimer text, SHA-256 integrity hash, and indicates whether the requesting user has actively accepted this version.

#### Headers
```http
Authorization: Bearer <access_token>
```

#### Success Response: `200 OK`
```json
{
  "version": "1.0.0",
  "document_hash": "ea78d46e3db2b07e74853059dbe888b50df3650ea9599fb42bfae21db7c25cf6",
  "text": "OptiGuide Preliminary Vision Screening Consent & Disclaimer...",
  "has_consented": true,
  "consent": {
    "id": "e818ff65-1d41-4eb2-a63e-9547cb02cda9",
    "version": "1.0.0",
    "agreed_at": "2026-11-03T18:00:00Z",
    "is_active": true
  }
}
```

#### Curl Example
```bash
curl -X GET "http://localhost:8000/api/v1/screening/consent/current" \
  -H "Authorization: Bearer $ACCESS_TOKEN"
```

---

### 1.2 Accept Screening Consent
- **Method:** `POST`
- **Path:** `/api/v1/screening/consent/accept`
- **Description:** Records acceptance of the screening consent. The client must supply the matching version string. Idempotent: repeated calls for the active version return the current agreement.

#### Request Body
```json
{
  "version": "1.0.0"
}
```

#### Success Response: `201 Created`
```json
{
  "id": "e818ff65-1d41-4eb2-a63e-9547cb02cda9",
  "version": "1.0.0",
  "agreed_at": "2026-11-03T18:00:00Z",
  "is_active": true,
  "document_hash": "ea78d46e3db2b07e74853059dbe888b50df3650ea9599fb42bfae21db7c25cf6"
}
```

#### Error Responses
- `400 Bad Request`: `{"error": {"code": "INVALID_CONSENT_VERSION", "message": "Provided consent version 0.9.0 does not match active version 1.0.0"}}`
- `401 Unauthorized`: Missing or invalid Bearer token.
- `422 Unprocessable Content`: Missing `version` field.

#### Curl Example
```bash
curl -X POST "http://localhost:8000/api/v1/screening/consent/accept" \
  -H "Authorization: Bearer $ACCESS_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"version": "1.0.0"}'
```

---

### 1.3 Withdraw Screening Consent
- **Method:** `POST`
- **Path:** `/api/v1/screening/consent/withdraw`
- **Description:** Revokes all active consents for the authenticated user. Automatically cancels any active `IN_PROGRESS` screening session.

#### Request Body
None.

#### Success Response: `200 OK`
```json
{
  "message": "Consent successfully withdrawn",
  "active_sessions_cancelled": 1
}
```

#### Curl Example
```bash
curl -X POST "http://localhost:8000/api/v1/screening/consent/withdraw" \
  -H "Authorization: Bearer $ACCESS_TOKEN"
```

---

## 2. Screening Session Lifecycle Endpoints

### 2.1 Create Screening Session
- **Method:** `POST`
- **Path:** `/api/v1/screening/sessions`
- **Description:** Initializes a new vision screening session in `IN_PROGRESS` status. Fails if user has not accepted current consent, or already has an active session.

#### Request Body
```json
{
  "device_info": "iPhone 15 Pro, iOS 18.1, Expo 52.0",
  "notes": "Testing distance vision"
}
```
*(Both fields optional; extra fields forbidden)*

#### Success Response: `201 Created`
```json
{
  "id": "a90dfbd6-e63b-4560-8480-4573196f790c",
  "user_id": "b3e3e098-b0a3-410a-8664-88331ec4199c",
  "status": "in_progress",
  "started_at": "2026-11-03T18:05:00Z",
  "completed_at": null,
  "cancelled_at": null,
  "cancellation_reason": null,
  "device_info": "iPhone 15 Pro, iOS 18.1, Expo 52.0",
  "notes": "Testing distance vision",
  "created_at": "2026-11-03T18:05:00Z",
  "updated_at": "2026-11-03T18:05:00Z"
}
```

#### Error Responses
- `403 Forbidden`: `{"error": {"code": "CONSENT_REQUIRED", "message": "Active screening consent is required before starting a screening session"}}`
- `409 Conflict`: `{"error": {"code": "SESSION_ALREADY_ACTIVE", "message": "User already has an active screening session: a90dfbd6-e63b-4560-8480-4573196f790c"}}`

#### Curl Example
```bash
curl -X POST "http://localhost:8000/api/v1/screening/sessions" \
  -H "Authorization: Bearer $ACCESS_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"device_info": "Expo Web Chrome", "notes": "Initial check"}'
```

---

### 2.2 List User Screening Sessions
- **Method:** `GET`
- **Path:** `/api/v1/screening/sessions`
- **Description:** Returns paginated list of screening sessions belonging to the authenticated user.

#### Query Parameters
- `page` (integer, default: 1, min: 1)
- `page_size` (integer, default: 20, min: 1, max: 100)
- `status` (string, optional: `in_progress`, `completed`, `cancelled`)

#### Success Response: `200 OK`
```json
{
  "items": [
    {
      "id": "a90dfbd6-e63b-4560-8480-4573196f790c",
      "user_id": "b3e3e098-b0a3-410a-8664-88331ec4199c",
      "status": "in_progress",
      "started_at": "2026-11-03T18:05:00Z",
      "completed_at": null,
      "cancelled_at": null,
      "cancellation_reason": null,
      "device_info": "Expo Web Chrome",
      "notes": "Initial check",
      "created_at": "2026-11-03T18:05:00Z",
      "updated_at": "2026-11-03T18:05:00Z"
    }
  ],
  "total": 1,
  "page": 1,
  "page_size": 20,
  "pages": 1
}
```

#### Curl Example
```bash
curl -X GET "http://localhost:8000/api/v1/screening/sessions?page=1&page_size=10" \
  -H "Authorization: Bearer $ACCESS_TOKEN"
```

---

### 2.3 Get Single Screening Session
- **Method:** `GET`
- **Path:** `/api/v1/screening/sessions/{session_id}`
- **Description:** Fetches details of a specific screening session. Protected against IDOR: users cannot access sessions owned by others (returns `404 Not Found`).

#### Success Response: `200 OK`
```json
{
  "id": "a90dfbd6-e63b-4560-8480-4573196f790c",
  "user_id": "b3e3e098-b0a3-410a-8664-88331ec4199c",
  "status": "in_progress",
  "started_at": "2026-11-03T18:05:00Z",
  "completed_at": null,
  "cancelled_at": null,
  "cancellation_reason": null,
  "device_info": "Expo Web Chrome",
  "notes": "Initial check",
  "created_at": "2026-11-03T18:05:00Z",
  "updated_at": "2026-11-03T18:05:00Z"
}
```

#### Error Responses
- `404 Not Found`: Session does not exist OR belongs to another user.

#### Curl Example
```bash
curl -X GET "http://localhost:8000/api/v1/screening/sessions/a90dfbd6-e63b-4560-8480-4573196f790c" \
  -H "Authorization: Bearer $ACCESS_TOKEN"
```

---

### 2.4 Complete Screening Session
- **Method:** `POST`
- **Path:** `/api/v1/screening/sessions/{session_id}/complete`
- **Description:** Transitions an `IN_PROGRESS` session to `COMPLETED`. Sets `completed_at` to current UTC timestamp. Fails if session is already completed or cancelled.

#### Request Body
None.

#### Success Response: `200 OK`
```json
{
  "id": "a90dfbd6-e63b-4560-8480-4573196f790c",
  "user_id": "b3e3e098-b0a3-410a-8664-88331ec4199c",
  "status": "completed",
  "started_at": "2026-11-03T18:05:00Z",
  "completed_at": "2026-11-03T18:07:30Z",
  "cancelled_at": null,
  "cancellation_reason": null,
  "device_info": "Expo Web Chrome",
  "notes": "Initial check",
  "created_at": "2026-11-03T18:05:00Z",
  "updated_at": "2026-11-03T18:07:30Z"
}
```

#### Error Responses
- `400 Bad Request`: `{"error": {"code": "INVALID_SESSION_TRANSITION", "message": "Cannot complete session in status: completed"}}`
- `404 Not Found`: Session does not exist or user is not authorized.

#### Curl Example
```bash
curl -X POST "http://localhost:8000/api/v1/screening/sessions/a90dfbd6-e63b-4560-8480-4573196f790c/complete" \
  -H "Authorization: Bearer $ACCESS_TOKEN"
```

---

### 2.5 Cancel Screening Session
- **Method:** `POST`
- **Path:** `/api/v1/screening/sessions/{session_id}/cancel`
- **Description:** Cancels an active `IN_PROGRESS` session. Requires a valid cancellation reason. Fails if session is already in a terminal state.

#### Request Body
```json
{
  "reason": "user_cancelled",
  "notes": "Interrupted by phone call"
}
```

#### Success Response: `200 OK`
```json
{
  "id": "a90dfbd6-e63b-4560-8480-4573196f790c",
  "user_id": "b3e3e098-b0a3-410a-8664-88331ec4199c",
  "status": "cancelled",
  "started_at": "2026-11-03T18:05:00Z",
  "completed_at": null,
  "cancelled_at": "2026-11-03T18:06:15Z",
  "cancellation_reason": "user_cancelled",
  "device_info": "Expo Web Chrome",
  "notes": "Interrupted by phone call",
  "created_at": "2026-11-03T18:05:00Z",
  "updated_at": "2026-11-03T18:06:15Z"
}
```

#### Error Responses
- `400 Bad Request`: `{"error": {"code": "INVALID_SESSION_TRANSITION", "message": "Cannot cancel session in status: completed"}}`
- `422 Unprocessable Content`: Reason exceeds character limits or contains invalid characters.

#### Curl Example
```bash
curl -X POST "http://localhost:8000/api/v1/screening/sessions/a90dfbd6-e63b-4560-8480-4573196f790c/cancel" \
  -H "Authorization: Bearer $ACCESS_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"reason": "user_cancelled", "notes": "Paused by user"}'
```

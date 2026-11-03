# OptiGuide — Phase 3.1 Security Review & Threat Analysis
## Consent Management, Screening Session Security & Boundary Auditing

**Document:** `docs/backend/PHASE_3_1_SECURITY_REVIEW.md`  
**Status:** AUDITED & VERIFIED  
**Lead Roles:** Senior Application Security Engineer, Principal Backend Architect  

---

## 1. Threat Modeling Overview

Phase 3.1 introduces patient consent and vision screening session lifecycles. Although OptiGuide is strictly a preliminary screening platform and does not produce clinical diagnoses or prescriptions, screening sessions constitute sensitive health data and privacy-governed operations.

The threat modeling analysis evaluates 6 primary attack categories:

```
+-----------------------------------------------------------------------------------+
|                            Phase 3.1 Threat Matrix                                |
+---------------------------+-----------------------+-------------------------------+
| Threat Vector             | Potential Severity    | Mitigation Implemented        |
+---------------------------+-----------------------+-------------------------------+
| IDOR on Sessions          | HIGH                  | Scoped query + 404 isolation  |
| Consent Text Tampering    | HIGH                  | Server SHA-256 integrity      |
| Concurrency Race on Active| MEDIUM                | Single active session guard   |
| State Machine Poisoning   | HIGH                  | Closed Enum + Transition Guard|
| Cross-Role Data Access    | HIGH                  | Strict RBAC + Referral gating |
| Audit Trail Repudiation   | MEDIUM                | Append-only audit table       |
+---------------------------+-----------------------+-------------------------------+
```

---

## 2. Threat Analysis & Mitigations

### 2.1 Insecure Direct Object References (IDOR)
- **Threat:** Malicious authenticated users or automated bots probing UUIDs (`GET /api/v1/screening/sessions/{id}`) to view or manipulate other patients' screening sessions.
- **Vulnerability Pattern:** Fetching session by ID without checking `session.user_id == current_user.id`, or returning HTTP 403 Forbidden which leaks the existence of another patient's session.
- **Mitigation Implemented:**
  1. All session queries in `ScreeningRepository.get_session_by_id` verify `session.user_id == user_id`.
  2. If the session does not exist OR belongs to another user, `EntityNotFoundException` is raised, resulting in a uniform `HTTP 404 NOT_FOUND`.
  3. No information regarding session existence or patient identity is disclosed.
- **Verification:** Tested in `test_session_idor_prevention` in `backend/tests/api/test_screening_api.py`.

### 2.2 Consent Tampering & Repudiation
- **Threat:** A client claims they consented to terms allowing medical prescription, or alters legal disclaimer text before submission.
- **Vulnerability Pattern:** Trusting client-supplied consent text or allowing clients to submit arbitrary versions.
- **Mitigation Implemented:**
  1. The consent document text is hardcoded on the server and versioned (`CURRENT_CONSENT_VERSION = "1.0.0"`).
  2. Server enforces SHA-256 document hashing (`ea78d46e3db2b07e74853059dbe888b50df3650ea9599fb42bfae21db7c25cf6`).
  3. Clients can only submit `{"version": "1.0.0"}`. Any differing version returns `HTTP 400 INVALID_CONSENT_VERSION`.
  4. Immutable audit record `CONSENT_ACCEPTED` logs the user ID, version, timestamp, document hash, and anti-spoofed client IP.
- **Verification:** Tested in `test_consent_text_hash_matches_official_content` and `test_consent_lifecycle_and_withdrawal`.

### 2.3 Single-Active-Session Concurrency & DoS
- **Threat:** Rapid parallel requests creating hundreds of orphan screening sessions, polluting the database and complicating clinical tracking.
- **Mitigation Implemented:**
  1. Before session creation, `ScreeningService.create_session` queries `ScreeningRepository.get_active_session_for_user`.
  2. If an `IN_PROGRESS` session is detected, a `SessionAlreadyActiveException` is raised (`HTTP 409 Conflict`) returning the existing active session ID.
  3. Clients must complete or cancel their active session before beginning a new one.
- **Verification:** Tested in `test_session_concurrency_single_active_constraint`.

### 2.4 State Machine Poisoning & Diagnostic Overreach
- **Threat:** Injecting medical states (e.g. `DIAGNOSED`, `PRESCRIBED`) or reverting completed/cancelled sessions to alter historical records.
- **Mitigation Implemented:**
  1. `ScreeningSessionStatus` is a strict Python Enum restricted to `IN_PROGRESS`, `COMPLETED`, `CANCELLED`.
  2. Valid transitions: `IN_PROGRESS` $\to$ `COMPLETED` and `IN_PROGRESS` $\to$ `CANCELLED`.
  3. All other transitions raise `InvalidSessionTransitionException` (`HTTP 400 INVALID_SESSION_TRANSITION`).
  4. Schema forbids extra fields (`extra = "forbid"`), preventing the addition of prescription metrics (`sphere`, `cylinder`, `axis`).
- **Verification:** Tested in `test_invalid_session_transitions_rejected`.

### 2.5 Cross-Role Data Access & Privacy Isolation
- **Threat:** Shopkeepers, non-clinical staff, or unverified eye-care professionals gaining unauthorized visibility into patient screening records.
- **Mitigation Implemented:**
  1. Direct session access is restricted to the owning patient.
  2. Shopkeepers and unverified optometrists are blocked with `HTTP 404 NOT_FOUND`.
  3. Even verified optometrists cannot access a patient's screening session without an explicit patient referral/transfer record (to be built in clinical module phases).
- **Verification:** Tested in `test_role_authorization_session_access_isolation`.

### 2.6 Audit Trail & Privacy Safeguards
- **Threat:** Tampering with screening history or leaking sensitive patient information in server logs.
- **Mitigation Implemented:**
  1. Audit events are stored in `screening_audit_events` which is append-only.
  2. No sensitive medical parameters or personally identifiable information (PII) beyond the authenticated user ID and device metadata are logged in audit payloads.
  3. Client IP extraction uses the anti-spoofing logic hardened in Phase 2.1 (ignoring untrusted `X-Forwarded-For` headers unless configured).
